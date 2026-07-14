"""Genera una muestra en PDF de cada reporte del catálogo con datos simulados.

- Plantillas: se leen de reports-pdf/assets/report (sin copiar 2.1 GB), con
  deteccion de extension (.jpg/.png) y salto de paginas faltantes.
- Fuentes: OpenSans reales (assets/fonts). PassionOne/LazyDog usan reserva.

Salida: carpeta samples/ + tabla resumen.
Ejecutar:  .venv/Scripts/python.exe scripts/generate_samples.py
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ORIG_REPORT = (ROOT / ".." / "reports-pdf" / "assets" / "report").resolve()
os.environ["ASSETS_DIR"] = str(ROOT / "assets")
os.environ["STORAGE_DIR"] = str(ROOT / "data")

from app.domain import Person  # noqa: E402
from app.pdf.base import ReportPDF  # noqa: E402
from app.reports import (  # noqa: E402
    Amor, Antidote, CoupleReading, Horoscopo, Master, Partner,
    PartnerPersonality, Stages, WhoIm, WhoImExtended, Wound,
)
from app.reports.report_base import Report  # noqa: E402

_missing: dict[str, int] = {}
_current = {"name": "?"}


def _patched_set_background(self, rel, ext="jpg"):
    for e in (ext, "jpg", "png", "jpeg"):
        f = ORIG_REPORT / f"{rel}.{e}"
        if f.exists():
            self.image(str(f), x=0, y=0, w=210, h=298)
            return
    _missing[_current["name"]] = _missing.get(_current["name"], 0) + 1


ReportPDF.set_background = _patched_set_background
Report.background_exists = lambda self, rel, ext="jpg": any(
    (ORIG_REPORT / f"{rel}.{e}").exists() for e in (ext, "jpg", "png")
)


def person(partner: bool = True) -> Person:
    p = Person("Juan Pedro Martinez Barragan", "1991-11-20", today=date(2026, 7, 13))
    if partner:
        p.set_partner("Ana Belen de los Santos Hernandez", "1991-04-21")
    return p


def _quien_soy():     r = WhoIm(person()); r.set_who_im(True); return r
def _quien_soy_ext(): r = WhoImExtended(person()); r.set_who_im_extended(True); return r
def _etapa_vida():    r = Stages(person()); r.set_stages(True); return r
def _horoscopo():     r = Horoscopo(person()); r.set_horoscopo(True); return r
def _amor():          r = Amor(person()); r.set_amor(True); return r
def _pareja():        r = Partner(person()); r.set_partner(True, 2026); return r
def _pareja_2023():   r = Partner(person()); r.set_partner(True, 2023); return r
def _bonus_pareja():  r = Partner(person()); r.set_partner(False); return r
def _maestro():       r = Master(person()); r.set_master(True); return r
def _herida():        r = Wound(person()); r.set_wound(True); return r
def _antidoto():      r = Antidote(person()); r.set_antidote(True); return r
def _personalidad():  r = PartnerPersonality(person()); r.set_partner_personality(True); return r
def _lectura():       r = CoupleReading(person()); r.set_couple_reading(True); return r


SAMPLES = [
    ("reporte-quien-soy", _quien_soy),
    ("reporte-quien-soy-extended", _quien_soy_ext),
    ("reporte-etapa-de-vida", _etapa_vida),
    ("horoscopo", _horoscopo),
    ("amor-pareja-ano-personal", _amor),
    ("reporte-pareja", _pareja),
    ("reporte-pareja-2023", _pareja_2023),
    ("bonus-pareja", _bonus_pareja),
    ("reporte-maestro", _maestro),
    ("reporte-herida", _herida),
    ("reporte-antidoto", _antidoto),
    ("reporte-personalidad-pareja", _personalidad),
    ("reporte-lectura-pareja", _lectura),
]


def main() -> int:
    out_dir = ROOT / "samples"
    out_dir.mkdir(exist_ok=True)
    results = []
    for name, fn in SAMPLES:
        _current["name"] = name
        _missing.setdefault(name, 0)
        try:
            report = fn()
            pages = report.pdf.page
            data = report.output()
            (out_dir / f"{name}.pdf").write_bytes(data)
            results.append((name, pages, _missing[name], len(data), "OK"))
        except Exception as exc:  # noqa: BLE001
            results.append((name, 0, _missing.get(name, 0), 0, f"ERROR {type(exc).__name__}: {exc}"))

    print(f"\n{'REPORTE':<32}{'PAGS':>5}{'FALTAN':>8}{'KB':>8}  ESTADO")
    print("-" * 70)
    ok = 0
    for name, pages, miss, size, status in results:
        if status == "OK":
            ok += 1
        print(f"{name:<32}{pages:>5}{miss:>8}{size // 1024:>8}  {status}")
    print("-" * 70)
    print(f"{ok}/{len(results)} generados en {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
