"""Verifica que cada reporte del catálogo renderiza completo con los assets
optimizados de assets/report (cuenta fondos faltantes por reporte).

Ejecutar:  .venv/Scripts/python.exe scripts/verify_assets.py
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ASSETS_DIR"] = str(ROOT / "assets")
os.environ["STORAGE_DIR"] = str(Path(tempfile.mkdtemp(prefix="gen_verify_")))

from app.registry import REGISTRY, build  # noqa: E402
from app.schemas import GenerateRequest  # noqa: E402

_missing = {"n": 0}


class _Counter(logging.Handler):
    def emit(self, record):
        if "Fondo no encontrado" in record.getMessage():
            _missing["n"] += 1


_log = logging.getLogger("reportpdf")
_log.addHandler(_Counter())
_log.setLevel(logging.WARNING)
_log.propagate = False  # no imprimir cada aviso


def req(key: str) -> GenerateRequest:
    return GenerateRequest.model_validate({
        "order_id": "VERIFY",
        "report": key,
        "person": {"name": "Juan Pedro Martinez Barragan", "birth_date": "1991-11-20"},
        "partner": {"name": "Ana Belen de los Santos", "birth_date": "1991-04-21"},
    })


def main() -> int:
    print(f"{'REPORTE':<32}{'PAGS':>5}{'FALTAN':>8}{'KB':>8}")
    print("-" * 55)
    total_missing = 0
    for key in sorted(REGISTRY.keys()):
        _missing["n"] = 0
        report = build(req(key))
        pages = report.pdf.page
        data = report.output()
        total_missing += _missing["n"]
        flag = "" if _missing["n"] == 0 else "  <-- revisar"
        print(f"{key:<32}{pages:>5}{_missing['n']:>8}{len(data)//1024:>8}{flag}")
    print("-" * 55)
    if total_missing == 0:
        print("Todos los reportes renderizaron con TODOS sus fondos presentes.")
        return 0
    print(f"{total_missing} fondo(s) faltante(s) en total.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
