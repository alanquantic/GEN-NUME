"""Reportes estáticos: PDFs ya creados que solo se suben y se sirven.

No se generan (no dependen de los datos de la persona): son productos digitales
iguales para todos. La tienda pide su clave y recibe la URL del PDF.

Un estático puede tener **variantes** (p. ej. colores de portada): en ese caso
el valor es un dict {variante: archivo} y la petición debe incluir `variant`.

Los archivos se colocan en `assets/static/` (ver assets/static/README.md).
"""

from __future__ import annotations

from .config import settings

# clave del producto -> archivo, o -> {variante: archivo}
STATIC_REPORTS: dict[str, str | dict[str, str]] = {
    "reporte-semestral": "reporte-semestral.pdf",
    "agenda-numerologica-2026": "agenda-numerologica-2026.pdf",
    "planeador-numerologico-2026": "planeador-numerologico-2026.pdf",
    "agenda-numerologica-2025": {
        "verde": "agenda-numerologica-2025-verde.pdf",
        "azul": "agenda-numerologica-2025-azul.pdf",
        "naranja": "agenda-numerologica-2025-naranja.pdf",
        "morado": "agenda-numerologica-2025-morado.pdf",
    },
}


def is_static(report_key: str) -> bool:
    return report_key in STATIC_REPORTS


def has_variants(report_key: str) -> bool:
    return isinstance(STATIC_REPORTS.get(report_key), dict)


def variants(report_key: str) -> list[str]:
    entry = STATIC_REPORTS.get(report_key)
    return sorted(entry.keys()) if isinstance(entry, dict) else []


def available_static() -> list[str]:
    return sorted(STATIC_REPORTS.keys())


def variants_map() -> dict[str, list[str]]:
    """{clave: [variantes]} solo para productos con versiones."""
    return {k: sorted(v.keys()) for k, v in STATIC_REPORTS.items() if isinstance(v, dict)}


def filename_for(report_key: str, variant: str | None = None) -> str | None:
    entry = STATIC_REPORTS.get(report_key)
    if entry is None:
        return None
    if isinstance(entry, str):
        return entry
    if variant is None:
        return None
    return entry.get(variant)


def file_exists(report_key: str, variant: str | None = None) -> bool:
    filename = filename_for(report_key, variant)
    return bool(filename) and (settings.static_pdf_dir / filename).exists()


def static_url(report_key: str, variant: str | None = None) -> str | None:
    """URL pública del PDF estático, o None si aún no se ha subido."""
    filename = filename_for(report_key, variant)
    if not filename:
        return None
    if not (settings.static_pdf_dir / filename).exists():
        return None
    return f"{settings.public_base_url.rstrip('/')}/static/{filename}"


def ensure_static_dir() -> None:
    settings.static_pdf_dir.mkdir(parents=True, exist_ok=True)
