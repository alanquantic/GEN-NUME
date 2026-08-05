"""Prueba el correo de alerta de fallo con la configuración SMTP actual.

    # con las variables SMTP_* en .env (o el entorno):
    py -3 scripts/test_alert_email.py           # imprime el correo, no lo envía
    py -3 scripts/test_alert_email.py --enviar  # lo envía de verdad

Construye un job falso de ejemplo y usa exactamente el mismo código que
producción (app/alerts.py). Útil para validar las credenciales SMTP en
Railway antes de necesitarlas de verdad.
"""

from __future__ import annotations

import io
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import alerts                       # noqa: E402
from app.ai.schemas import GenerateAIRequest, StoredJob  # noqa: E402


def fake_job() -> StoredJob:
    now = datetime.now(timezone.utc)
    request = GenerateAIRequest.model_validate({
        "order_id": "ORD-PRUEBA-123",
        "report": "proposito",
        "instance": "abc123def456",
        "person": {"name": "Juan Pedro Martinez", "birth_date": "1991-11-20"},
    })
    return StoredJob(
        job_id="job_prueba_correo",
        status="error",
        stage="failed",
        report=request.report,
        order_id=request.order_id,
        request=request,
        created_at=now,
        updated_at=now,
        error=("generate_text: proveedor no disponible: El proveedor google "
               "sigue sin responder tras 4 intentos: 503 UNAVAILABLE"),
        attempts=2,
    )


def main() -> int:
    job = fake_job()
    msg = alerts.build_failure_message(job)
    print("=" * 70)
    print("Para:   ", msg["To"])
    print("De:     ", msg["From"])
    print("Asunto: ", msg["Subject"])
    print("=" * 70)
    print(msg.get_content())

    if "--enviar" in sys.argv:
        ok = alerts.send_report_failure(job)
        print("Enviado ✓" if ok else "NO se envió (revisa SMTP_* y los logs)")
        return 0 if ok else 1
    print("(simulación: usa --enviar para mandarlo de verdad)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
