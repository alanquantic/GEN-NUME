"""Alertas por correo cuando un reporte IA falla definitivamente.

Se envía UN correo por job, sólo cuando el proveedor de IA siguió sin
responder tras los reintentos diferidos. Requiere SMTP configurado por
entorno (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM);
sin configuración, se registra un warning y el flujo continúa — la
alerta jamás debe tumbar al servicio.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from .config import settings

logger = logging.getLogger("reportpdf.alerts")


def _person_lines(request) -> list[str]:
    lines = [
        f"  · Nombre:            {request.person.name}",
        f"  · Fecha nacimiento:  {request.person.birth_date}",
    ]
    if request.partner is not None:
        lines.append(
            f"  · Pareja:            {request.partner.name} "
            f"({request.partner.birth_date})"
        )
    return lines


def build_failure_message(job) -> EmailMessage:
    """Arma el correo de alerta a partir del job fallido."""
    from .ai.recipes import REPORTS

    report = REPORTS.get(job.report)
    title = report.title if report else job.report

    msg = EmailMessage()
    msg["Subject"] = (
        f"[Numerología] Falló el reporte «{title}» · pedido {job.order_id}"
    )
    msg["From"] = settings.smtp_from or settings.smtp_user or "alertas@localhost"
    msg["To"] = settings.alert_email

    intentos = 1 + job.attempts
    instance = job.request.instance or "—"
    status_url = f"{settings.public_base_url}/reports/jobs/{job.job_id}"

    msg.set_content(
        "\n".join(
            [
                "Un reporte con IA no pudo generarse: el modelo/servicio siguió",
                f"sin estar disponible tras {intentos} intentos (incluyendo "
                f"{job.attempts} reintentos diferidos).",
                "",
                "REPORTE",
                f"  · Tipo:      {title} ({job.report})",
                f"  · Pedido:    {job.order_id}",
                f"  · Instancia: {instance}",
                f"  · Job:       {job.job_id}",
                f"  · Estado:    {status_url}",
                "",
                "CLIENTE",
                *_person_lines(job.request),
                "",
                "ERROR",
                f"  {job.error or '(sin detalle)'}",
                "",
                f"Creado: {job.created_at:%Y-%m-%d %H:%M:%S} UTC · "
                f"Último intento: {job.updated_at:%Y-%m-%d %H:%M:%S} UTC",
                "",
                "El job se puede relanzar re-enviando el mismo POST "
                "/reports/generate-ai desde la tienda (o su cron).",
            ]
        )
    )
    return msg


def send_report_failure(job) -> bool:
    """Envía la alerta. Devuelve True si salió; nunca lanza excepción."""
    if not settings.smtp_host:
        logger.warning(
            "SMTP no configurado (SMTP_HOST vacío): se omite la alerta por "
            "correo del job %s", job.job_id,
        )
        return False
    try:
        msg = build_failure_message(job)
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port,
                                  timeout=30) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password or "")
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port,
                              timeout=30) as smtp:
                smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password or "")
                smtp.send_message(msg)
        logger.info("Alerta de fallo enviada a %s (job %s)",
                    settings.alert_email, job.job_id)
        return True
    except Exception:  # noqa: BLE001 — la alerta nunca tumba el flujo
        logger.exception("No se pudo enviar la alerta del job %s", job.job_id)
        return False


__all__ = ["send_report_failure", "build_failure_message"]
