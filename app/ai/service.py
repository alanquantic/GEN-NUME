"""Orquestación del paso 6: dossier -> LLM -> HTML -> PDF -> artefactos."""

from __future__ import annotations

import json
import logging
from datetime import date
from urllib.error import URLError
from urllib.request import Request, urlopen

from ..domain.dates import format_long_date
from ..pdf import html_renderer as hr
from ..security import sign
from . import dossier as dsr
from . import generate as gen
from .job_store import AIJobStore
from .recipes import REPORTS
from .schemas import GenerateAIRequest, JobArtifact, JobResult, JobStatusResponse, StoredJob

logger = logging.getLogger("reportpdf.ai")


class AIReportService:
    def __init__(self, store: AIJobStore):
        self.store = store

    def submit_job(self, request: GenerateAIRequest):
        report = REPORTS.get(request.report)
        if report is None:
            raise ValueError("reporte_desconocido")
        if report.needs_partner and request.partner is None:
            raise ValueError("partner_requerido")
        return self.store.create(request)

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        return self.store.get(job_id).public_view()

    def process_job(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job.status == "done":
            return

        request = job.request
        today = request.today or date.today()

        try:
            self.store.update(job_id, status="running", stage="build_dossier", error=None)
            dossier = dsr.build(
                request.report,
                request.person.name,
                request.person.birth_date,
                today=today,
                partner_name=request.partner.name if request.partner else None,
                partner_birth_date=request.partner.birth_date if request.partner else None,
                relationship_start=request.relationship_start,
                name_sanitize=request.person.name_sanitize,
            )

            self.store.update(job_id, stage="generate_text")
            generated = gen.generate(
                dossier,
                person_name=request.person.name,
                birth_long=format_long_date(request.person.birth_date),
                today_long=format_long_date(today),
                partner_name=request.partner.name if request.partner else None,
                partner_birth_long=(
                    format_long_date(request.partner.birth_date) if request.partner else None
                ),
            )

            self.store.update(
                job_id,
                stage="render_html",
                warnings=generated.warnings,
                model=generated.model,
                usage=generated.usage,
            )
            report = REPORTS[request.report]
            html = hr.render_html(
                request.report,
                generated.data,
                dossier.numbers,
                report_title=report.title,
                area_token=report.area,
                person_name=request.person.name,
                birth_long=format_long_date(request.person.birth_date),
                today_long=format_long_date(today),
                today_age=dossier.numbers.pinnacle.age_at(today),
            )

            json_art = self.store.save_text_artifact(
                job_id,
                "report.json",
                json.dumps(generated.data, ensure_ascii=False, indent=2),
            )
            html_art = self.store.save_text_artifact(job_id, "report.html", html)

            self.store.update(job_id, stage="render_pdf")
            pdf = hr.to_pdf(html)

            self.store.update(job_id, stage="save_outputs")
            pdf_art = self._save_pdf_artifact(request, pdf)
            result = JobResult(pdf=pdf_art, html=html_art, json_report=json_art)

            done_job = self.store.update(
                job_id,
                status="done",
                stage="done",
                result=result,
                warnings=generated.warnings,
                model=generated.model,
                usage=generated.usage,
                error=None,
            )
            self._notify_callback(done_job)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error en job IA %s", job_id)
            error_job = self.store.update(job_id, status="error", stage="failed", error=str(exc))
            self._notify_callback(error_job)

    def _save_pdf_artifact(self, request: GenerateAIRequest, pdf: bytes) -> JobArtifact:
        return self.store.save_report_pdf(
            request.order_id,
            request.report,
            pdf,
            request.instance,
        )

    def _notify_callback(self, job: StoredJob) -> None:
        notify = job.request.notify
        if notify is None:
            return

        payload = {
            "event": "report.completed",
            "job_id": job.job_id,
            "report_row_id": notify.report_row_id,
            "order_id": job.order_id,
            "report": job.report,
            "status": job.status,
            "result": job.result.model_dump(mode="json", by_alias=True) if job.result else None,
            "error": job.error,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Signature": sign(body, notify.callback_secret),
        }
        req = Request(notify.callback_url, data=body, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=10) as response:
                if response.status >= 400:
                    logger.warning("Callback de reporte %s respondió %s", job.job_id, response.status)
        except URLError as exc:
            logger.warning("No se pudo notificar callback del job %s: %s", job.job_id, exc)
