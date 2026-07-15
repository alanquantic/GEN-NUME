"""Esquemas de entrada/salida (Pydantic v2).

Validación automática de la petición: si `birth_date` no es una fecha válida o
falta un campo requerido, FastAPI responde 422 antes de tocar la lógica. Ese
control no existía en el original.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PersonIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    birth_date: date
    # Nombre normalizado (sin acentos, minúsculas, separado por '-').
    # Requerido solo por reportes que calculan alma/expresión/desarrollo.
    name_sanitize: str | None = None


class PartnerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    birth_date: date


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1, description="Id de pedido de la tienda")
    report: str = Field(min_length=1, description="Clave del reporte (ver /reports)")
    # person es requerido para reportes generados; los estáticos (agenda,
    # planeador, semestral) no lo necesitan y puede omitirse.
    person: PersonIn | None = None
    partner: PartnerIn | None = None

    # Parámetros opcionales según el reporte
    month: int | None = Field(default=None, ge=1, le=12)
    week: int | None = Field(default=None, ge=1, le=4)
    year: int | None = Field(default=None, ge=1900, le=2100)


class GenerateResponse(BaseModel):
    ok: bool
    report: str
    order_id: str
    url: str
    path: str


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    detail: str | None = None
