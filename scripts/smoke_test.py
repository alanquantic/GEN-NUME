"""Prueba de humo: renderiza TODOS los reportes del catálogo de extremo a extremo.

Se hace monkeypatch de los fondos (no-op) para no depender de los assets del
cliente; así se ejercita todo el pipeline (texto/HTML/tablas/sinastría) y se
verifica que cada reporte produce un PDF válido. También prueba la firma HMAC.

Ejecutar:  .venv/Scripts/python.exe scripts/smoke_test.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_tmp = Path(tempfile.mkdtemp(prefix="gen_smoke_"))
os.environ["ASSETS_DIR"] = str(_tmp / "assets")
os.environ["STORAGE_DIR"] = str(_tmp / "data")
os.environ["WEBHOOK_SECRET"] = "secreto-de-prueba"
(_tmp / "assets" / "fonts").mkdir(parents=True, exist_ok=True)

from app.pdf.base import ReportPDF  # noqa: E402
from app.registry import REGISTRY, build  # noqa: E402
from app.reports.report_base import Report  # noqa: E402
from app.schemas import GenerateRequest  # noqa: E402
from app.security import sign, verify_signature  # noqa: E402

# Fondos no-op: no dependemos de los assets reales
ReportPDF.set_background = lambda self, rel, ext="jpg": None
Report.set_background = lambda self, rel, ext="jpg": None
Report.background_exists = lambda self, rel, ext="jpg": True

failures = 0


def check(name: str, ok: bool, extra: str = "") -> None:
    global failures
    if ok:
        print(f"  PASS  {name}")
    else:
        failures += 1
        print(f"  FAIL  {name} {extra}")


def valid_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF" and len(data) > 1000


def build_request(report_key: str) -> GenerateRequest:
    return GenerateRequest.model_validate({
        "order_id": "ORD-TEST",
        "report": report_key,
        "person": {"name": "Juan Pedro Martinez Barragan", "birth_date": "1991-11-20"},
        "partner": {"name": "Ana Belen de los Santos", "birth_date": "1991-04-21"},
    })


def main() -> int:
    # 1) Cada reporte del catálogo
    for key in sorted(REGISTRY.keys()):
        try:
            data = build(build_request(key)).output()
            check(f"registry:{key}", valid_pdf(data))
        except Exception as exc:  # noqa: BLE001
            check(f"registry:{key}", False, f"{type(exc).__name__}: {exc}")

    # 2) Firma HMAC
    body = build_request("reporte-quien-soy").model_dump_json().encode("utf-8")
    sig = sign(body)
    check("hmac: firma valida se acepta", verify_signature(body, sig) is True)
    check("hmac: firma invalida se rechaza", verify_signature(body, "deadbeef") is False)

    # 3) Reporte desconocido
    try:
        build(GenerateRequest.model_validate(
            {"order_id": "X", "report": "no-existe",
             "person": {"name": "A", "birth_date": "2000-01-01"}}
        ))
        check("registry: reporte desconocido lanza KeyError", False)
    except KeyError:
        check("registry: reporte desconocido lanza KeyError", True)

    print()
    if failures:
        print(f"{failures} fallaron")
        return 1
    print(f"Catálogo completo ({len(REGISTRY)} claves) + firma OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
