"""Registro de reportes: clave -> función constructora.

Catálogo final (16 claves). Añadir un reporte = escribir su clase y registrar
aquí una entrada. Ningún reporte del catálogo requiere datos externos.

Cada builder recibe el `GenerateRequest` ya validado y devuelve un Report
renderizado (listo para `.output()`).
"""

from __future__ import annotations

from datetime import date
from typing import Callable

from .domain import Person
from .reports import (
    Amor,
    Antidote,
    CoupleReading,
    Horoscopo,
    Master,
    Partner,
    PartnerPersonality,
    Report,
    Stages,
    WhoIm,
    WhoImExtended,
    Wound,
)
from .schemas import GenerateRequest

Builder = Callable[[GenerateRequest], Report]

REGISTRY: dict[str, Builder] = {}


def register(*keys: str) -> Callable[[Builder], Builder]:
    def decorator(fn: Builder) -> Builder:
        for key in keys:
            REGISTRY[key] = fn
        return fn
    return decorator


def _person(req: GenerateRequest) -> Person:
    p = Person(
        req.person.name,
        req.person.birth_date,
        name_sanitize=req.person.name_sanitize,
        today=date.today(),
    )
    if req.partner is not None:
        p.set_partner(req.partner.name, req.partner.birth_date)
    return p


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def available_reports() -> list[str]:
    return sorted(REGISTRY.keys())


def build(req: GenerateRequest) -> Report:
    builder = REGISTRY.get(req.report)
    if builder is None:
        raise KeyError(req.report)
    return builder(req)


# --------------------------------------------------------------------- #
# Individuales (persona sola)
# --------------------------------------------------------------------- #
@register("reporte-quien-soy")
def _who_im(req: GenerateRequest) -> Report:
    r = WhoIm(_person(req))
    r.set_who_im(generic=True)
    return r


@register("reporte-quien-soy-extended")
def _who_im_extended(req: GenerateRequest) -> Report:
    r = WhoImExtended(_person(req))
    r.set_who_im_extended(generic=True)
    return r


@register("reporte-etapa-de-vida-2022", "reporte-etapa-de-vida-2023", "reporte-etapa-de-vida-2026")
def _stages(req: GenerateRequest) -> Report:
    r = Stages(_person(req))
    r.set_stages(generic=True)
    return r


@register("horoscopo")
def _horoscopo(req: GenerateRequest) -> Report:
    r = Horoscopo(_person(req))
    r.set_horoscopo(generic=True)
    return r


@register("amor-pareja-ano-personal")
def _amor(req: GenerateRequest) -> Report:
    r = Amor(_person(req))
    r.set_amor(generic=True)
    return r


# --------------------------------------------------------------------- #
# Pareja (requieren partner)
# --------------------------------------------------------------------- #
@register("reporte-pareja", "reporte-pareja-2025")
def _partner_2026(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte de pareja requiere partner")
    r = Partner(_person(req))
    r.set_partner(generic=True, year_over=2026)
    return r


@register("reporte-pareja-2023")
def _partner_2023(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte de pareja requiere partner")
    r = Partner(_person(req))
    r.set_partner(generic=True, year_over=2023)
    return r


@register("bonus-pareja")
def _partner_bonus(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "bonus-pareja requiere partner")
    r = Partner(_person(req))
    r.set_partner(generic=False)
    return r


@register("reporte-maestro")
def _master(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte-maestro requiere partner")
    r = Master(_person(req))
    r.set_master(generic=True)
    return r


@register("reporte-herida")
def _wound(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte-herida requiere partner")
    r = Wound(_person(req))
    r.set_wound(generic=True)
    return r


@register("reporte-antidoto")
def _antidote(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte-antidoto requiere partner")
    r = Antidote(_person(req))
    r.set_antidote(generic=True)
    return r


@register("reporte-personalidad-pareja")
def _partner_personality(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte-personalidad-pareja requiere partner")
    r = PartnerPersonality(_person(req))
    r.set_partner_personality(generic=True)
    return r


@register("reporte-lectura-pareja")
def _couple_reading(req: GenerateRequest) -> Report:
    _require(req.partner is not None, "reporte-lectura-pareja requiere partner")
    r = CoupleReading(_person(req))
    r.set_couple_reading(generic=True)
    return r
