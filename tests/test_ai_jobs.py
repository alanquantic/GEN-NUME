"""Pruebas del paso 6: jobs persistentes y API asíncrona para reportes IA.

    py -3 tests/test_ai_jobs.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.ai.generate import GeneratedReport, _load_mock  # noqa: E402
from app.ai.job_store import AIJobStore  # noqa: E402
from app.ai.schemas import GenerateAIRequest  # noqa: E402
from app.ai.service import AIReportService  # noqa: E402
from app.main import app  # noqa: E402
from app.security import sign  # noqa: E402
from app.storage import order_folder  # noqa: E402

TODAY = date(2026, 7, 30)


def _request(report: str = "quien-soy") -> GenerateAIRequest:
    return GenerateAIRequest(
        order_id="ORD-IA-1001",
        report=report,
        today=TODAY,
        person={
            "name": "Juan Pedro Martinez",
            "birth_date": "1991-11-20",
        },
    )


def test_job_store_persiste_estado_y_artefactos():
    with TemporaryDirectory() as tmp:
        store = AIJobStore(Path(tmp), "https://example.test")
        job = store.create(_request())
        assert job.status == "queued"

        saved = store.save_text_artifact(job.job_id, "report.json", '{"ok":true}')
        assert saved.path.endswith("/report.json")
        assert (Path(tmp) / "jobs" / job.job_id / "report.json").exists()

        updated = store.update(job.job_id, status="running", stage="generate_text")
        loaded = store.get(job.job_id)
        assert updated.status == "running"
        assert loaded.stage == "generate_text"


def test_service_procesa_job_y_guarda_salidas():
    import app.ai.service as svc

    mock_data, *_ = _load_mock("quien-soy")
    original_generate = svc.gen.generate
    original_to_pdf = svc.hr.to_pdf

    def fake_generate(*args, **kwargs):
        return GeneratedReport(
            report_key="quien-soy",
            data=mock_data,
            model="mock-test",
            usage={"input": 10, "output": 20, "cache_read": 0, "cache_write": 0},
            warnings=[],
            stop_reason="end_turn",
        )

    try:
        svc.gen.generate = fake_generate
        svc.hr.to_pdf = lambda html: b"%PDF-1.7 mock"

        with TemporaryDirectory() as tmp:
            store = AIJobStore(Path(tmp), "https://example.test")
            service = AIReportService(store)
            job = service.submit_job(_request())
            service.process_job(job.job_id)
            status = service.get_job_status(job.job_id)

            assert status.status == "done"
            assert status.result is not None
            assert status.result.pdf.path.endswith("/quien-soy.pdf")
            # El usage público lleva tokens acumulados y costo (null si el
            # modelo no está en la tabla de precios, como "mock-test").
            assert status.usage is not None
            assert status.usage.model == "mock-test"
            assert status.usage.input_tokens == 10
            assert status.usage.output_tokens == 20
            assert status.usage.total_tokens == 30
            assert status.usage.token_cost_usd is None
            assert (Path(tmp) / "jobs" / job.job_id / "report.json").exists()
            assert (Path(tmp) / "jobs" / job.job_id / "report.html").exists()
            assert (
                Path(tmp) / order_folder("ORD-IA-1001") / "quien-soy.pdf"
            ).exists()
    finally:
        svc.gen.generate = original_generate
        svc.hr.to_pdf = original_to_pdf


def test_webhook_reporta_usage_junto_a_result():
    import app.ai.service as svc

    mock_data, *_ = _load_mock("quien-soy")
    captured: dict = {}

    class _FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=10):
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse()

    def fake_generate(*args, **kwargs):
        return GeneratedReport(
            report_key="quien-soy",
            data=mock_data,
            model="claude-opus-5",
            usage={"input": 1_000_000, "output": 200_000,
                   "cache_read": 0, "cache_write": 0},
            warnings=[],
            stop_reason="end_turn",
        )

    originals = (svc.gen.generate, svc.hr.to_pdf, svc.urlopen)
    try:
        svc.gen.generate = fake_generate
        svc.hr.to_pdf = lambda html: b"%PDF-1.7 mock"
        svc.urlopen = fake_urlopen

        with TemporaryDirectory() as tmp:
            store = AIJobStore(Path(tmp), "https://example.test")
            service = AIReportService(store)
            request = GenerateAIRequest.model_validate({
                **_request().model_dump(mode="python"),
                "notify": {
                    "callback_url": "https://tienda.test/api/callback",
                    "callback_secret": "secreto",
                    "report_row_id": "row-1",
                },
            })
            job = service.submit_job(request)
            service.process_job(job.job_id)

        payload = captured["payload"]
        assert payload["status"] == "done"
        assert payload["result"] is not None
        usage = payload["usage"]
        assert usage["model"] == "claude-opus-5"
        assert usage["input_tokens"] == 1_000_000
        assert usage["output_tokens"] == 200_000
        assert usage["total_tokens"] == 1_200_000
        assert usage["token_cost_usd"] == 10.0       # 5 + 0.2·25 USD
        assert usage["production_cost_usd"] == 10.0
    finally:
        svc.gen.generate, svc.hr.to_pdf, svc.urlopen = originals


def test_api_generate_ai_acepta_y_consulta_job():
    import app.main as main_mod

    class FakeService:
        def __init__(self):
            self.job = None

        def submit_job(self, request):
            from datetime import datetime, timezone
            from app.ai.schemas import StoredJob

            now = datetime.now(timezone.utc)
            self.job = StoredJob(
                job_id="job_test_api",
                status="queued",
                stage="queued",
                report=request.report,
                order_id=request.order_id,
                request=request,
                created_at=now,
                updated_at=now,
            )
            return self.job

        def process_job(self, job_id):
            return None

        def get_job_status(self, job_id):
            if self.job is None or self.job.job_id != job_id:
                raise KeyError(job_id)
            return self.job.public_view()

    original_service = main_mod.ai_service
    try:
        main_mod.ai_service = FakeService()
        client = TestClient(app)

        payload = {
            "order_id": "ORD-API-1",
            "report": "quien-soy",
            "today": "2026-07-30",
            "person": {"name": "Juan Pedro Martinez", "birth_date": "1991-11-20"},
        }
        body = json.dumps(payload)
        res = client.post(
            "/reports/generate-ai",
            data=body,
            headers={"Content-Type": "application/json", "X-Signature": sign(body.encode("utf-8"))},
        )
        assert res.status_code == 202, res.text
        assert res.json()["job_id"] == "job_test_api"

        status = client.get("/reports/jobs/job_test_api")
        assert status.status_code == 200, status.text
        assert status.json()["status"] == "queued"
        assert status.json()["report"] == "quien-soy"
    finally:
        main_mod.ai_service = original_service


if __name__ == "__main__":
    failures = 0
    print("Pruebas de jobs IA\n")
    for name, fn in sorted(dict(globals()).items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print()
    print(f"{failures} fallaron" if failures else "Todas las pruebas pasaron OK")
    sys.exit(1 if failures else 0)
