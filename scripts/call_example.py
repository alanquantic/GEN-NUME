"""Ejemplo de uso: firma la petición (HMAC) y llama al endpoint del generador.

Simula lo que hará tu tienda Next.js al confirmarse un pedido.

Uso:
    .venv/Scripts/python.exe scripts/call_example.py reporte-quien-soy
    .venv/Scripts/python.exe scripts/call_example.py reporte-pareja   (requiere pareja)

Variables de entorno (con valores por defecto para local):
    GENERATOR_URL   (http://localhost:8000)
    WEBHOOK_SECRET  (demo-secret-local)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import urllib.request

GENERATOR_URL = os.environ.get("GENERATOR_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "demo-secret-local")


def build_payload(report: str) -> dict:
    payload = {
        "order_id": "ORD-DEMO-1001",
        "report": report,
        "person": {"name": "Juan Pedro Martinez Barragan", "birth_date": "1991-11-20"},
    }
    # Los reportes de pareja necesitan partner.
    if "pareja" in report or report in ("reporte-maestro", "reporte-herida", "reporte-antidoto"):
        payload["partner"] = {"name": "Ana Belen de los Santos", "birth_date": "1991-04-21"}
    return payload


def main() -> int:
    report = sys.argv[1] if len(sys.argv) > 1 else "reporte-quien-soy"
    payload = build_payload(report)
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    req = urllib.request.Request(
        f"{GENERATOR_URL}/reports/generate",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-Signature": signature},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"HTTP {resp.status}")
            print(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}")
        print(exc.read().decode("utf-8"))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
