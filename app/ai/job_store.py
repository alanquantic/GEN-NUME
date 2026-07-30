"""Persistencia simple de jobs IA sobre el Volume del servicio."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..storage import relative_path
from .schemas import GenerateAIRequest, JobArtifact, StoredJob


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIJobStore:
    def __init__(self, storage_dir: Path, public_base_url: str):
        self.storage_dir = Path(storage_dir)
        self.public_base_url = public_base_url.rstrip("/")
        self.jobs_dir = self.storage_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def create(self, request: GenerateAIRequest) -> StoredJob:
        now = _utcnow()
        job = StoredJob(
            job_id=f"job_{uuid4().hex}",
            status="queued",
            stage="queued",
            report=request.report,
            order_id=request.order_id,
            request=request,
            created_at=now,
            updated_at=now,
        )
        self._write_job(job)
        return job

    def get(self, job_id: str) -> StoredJob:
        path = self._job_path(job_id)
        if not path.exists():
            raise KeyError(job_id)
        return StoredJob.model_validate_json(path.read_text(encoding="utf-8"))

    def update(self, job_id: str, **changes) -> StoredJob:
        job = self.get(job_id)
        payload = job.model_dump(mode="python")
        payload.update(changes)
        payload["updated_at"] = _utcnow()
        updated = StoredJob.model_validate(payload)
        self._write_job(updated)
        return updated

    def save_text_artifact(self, job_id: str, filename: str, text: str) -> JobArtifact:
        rel = self._artifact_relative(job_id, filename)
        dest = self.storage_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        return self._artifact(job_id, filename)

    def save_bytes_artifact(self, job_id: str, filename: str, data: bytes) -> JobArtifact:
        rel = self._artifact_relative(job_id, filename)
        dest = self.storage_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self._artifact(job_id, filename)

    def save_report_pdf(self, order_id: str, report_key: str, data: bytes, instance: str | None) -> JobArtifact:
        rel = Path(relative_path(order_id, report_key, instance))
        dest = self.storage_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        rel_posix = rel.as_posix()
        return JobArtifact(
            path=f"/files/{rel_posix}",
            url=f"{self.public_base_url}/files/{rel_posix}",
        )

    def _artifact(self, job_id: str, filename: str) -> JobArtifact:
        rel = self._artifact_relative(job_id, filename)
        return JobArtifact(
            path=f"/files/{rel.as_posix()}",
            url=f"{self.public_base_url}/files/{rel.as_posix()}",
        )

    def _artifact_relative(self, job_id: str, filename: str) -> Path:
        return Path("jobs") / job_id / filename

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def _write_job(self, job: StoredJob) -> None:
        path = self._job_path(job.job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(job.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)
