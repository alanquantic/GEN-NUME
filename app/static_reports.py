"""Reportes estáticos: PDFs ya creados que solo se suben y se sirven.

No se generan (no dependen de los datos de la persona): son productos digitales
iguales para todos. La tienda pide su clave y recibe la URL del PDF.

Los archivos se colocan en `assets/static/` (ver assets/static/README.md).
"""

from __future__ import annotations

from .config import settings

# clave del producto -> nombre de archivo esperado en assets/static/
STATIC_REPORTS: dict[str, str] = {
    "reporte-semestral": "reporte-semestral.pdf",
    "agenda-numerologica-2026": "agenda-numerologica-2026.pdf",
    "planeador-numerologico-2026": "planeador-numerologico-2026.pdf",
}


def is_static(report_key: str) -> bool:
    return report_key in STATIC_REPORTS


def available_static() -> list[str]:
    return sorted(STATIC_REPORTS.keys())


def filename_for(report_key: str) -> str | None:
    return STATIC_REPORTS.get(report_key)


def file_exists(report_key: str) -> bool:
    filename = STATIC_REPORTS.get(report_key)
    return bool(filename) and (settings.static_pdf_dir / filename).exists()


def static_url(report_key: str) -> str | None:
    """URL pública del PDF estático, o None si aún no se ha subido."""
    filename = STATIC_REPORTS.get(report_key)
    if not filename:
        return None
    if not (settings.static_pdf_dir / filename).exists():
        return None
    return f"{settings.public_base_url.rstrip('/')}/static/{filename}"


def ensure_static_dir() -> None:
    settings.static_pdf_dir.mkdir(parents=True, exist_ok=True)
