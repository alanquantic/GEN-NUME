"""Almacenamiento de PDFs en el Volume persistente de Railway.

El disco por defecto de un contenedor Railway es efímero (se pierde en cada
redeploy). Por eso los PDFs se escriben en el Volume montado en
`settings.storage_dir` (p. ej. /data) y se sirven vía HTTP desde ahí.

La carpeta por pedido usa md5(order_id) — igual que el original — para que la
ruta no sea trivialmente adivinable. Para endurecerlo más adelante se puede
firmar la URL de descarga con expiración.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .config import settings


def order_folder(order_id: str) -> str:
    return hashlib.md5(order_id.encode("utf-8")).hexdigest()


def relative_path(order_id: str, report_key: str) -> str:
    return f"{order_folder(order_id)}/{report_key}.pdf"


def save_pdf(order_id: str, report_key: str, data: bytes) -> tuple[Path, str]:
    """Guarda el PDF y devuelve (ruta_absoluta, url_publica)."""
    rel = relative_path(order_id, report_key)
    dest = settings.storage_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    url = f"{settings.public_base_url.rstrip('/')}/files/{rel}"
    return dest, url


def ensure_storage() -> None:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
