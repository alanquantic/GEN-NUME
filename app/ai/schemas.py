"""Esquemas del paso 6: contrato asíncrono para reportes dinámicos con IA."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

JobStatus = Literal["queued", "running", "done", "error"]


class PersonIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    birth_date: date
    name_sanitize: str | None = None


class PartnerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    birth_date: date


class NotifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    callback_url: str = Field(min_length=1)
    callback_secret: str = Field(min_length=1)
    report_row_id: str = Field(min_length=1)


class GenerateAIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1, description="Id de pedido en la tienda")
    report: str = Field(min_length=1, description="Clave del reporte dinámico")
    person: PersonIn
    partner: PartnerIn | None = None
    instance: str | None = None
    relationship_start: date | None = None
    notify: NotifyIn | None = None
    today: date | None = Field(
        default=None,
        description="Fecha de cálculo reproducible; si no llega, usa hoy.",
    )


class JobArtifact(BaseModel):
    path: str
    url: str


class JobResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pdf: JobArtifact
    html: JobArtifact
    json_report: JobArtifact = Field(alias="json")


class GenerateAIAcceptedResponse(BaseModel):
    ok: bool = True
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    ok: bool = True
    job_id: str
    status: JobStatus
    stage: str | None = None
    report: str
    order_id: str
    created_at: datetime
    updated_at: datetime
    result: JobResult | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    model: str | None = None
    usage: dict[str, int] | None = None


class StoredJob(BaseModel):
    """Representación completa del job en disco."""

    job_id: str
    status: JobStatus
    stage: str | None = None
    report: str
    order_id: str
    request: GenerateAIRequest
    created_at: datetime
    updated_at: datetime
    result: JobResult | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    model: str | None = None
    usage: dict[str, int] | None = None

    def public_view(self) -> JobStatusResponse:
        return JobStatusResponse.model_validate(
            self.model_dump(mode="python", exclude={"request"})
        )
