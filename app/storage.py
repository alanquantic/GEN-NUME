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
import re
from pathlib import Path

from .config import settings

# Solo caracteres seguros para un nombre de archivo. Evita path traversal
# ("../") y rarezas del sistema de archivos si la tienda manda un `instance`
# inesperado; todo lo demás se colapsa a "-".
_INSTANCE_UNSAFE = re.compile(r"[^A-Za-z0-9_-]+")


def order_folder(order_id: str) -> str:
    return hashlib.md5(order_id.encode("utf-8")).hexdigest()


def _sanitize_instance(instance: str | None) -> str | None:
    """Normaliza `instance` a algo seguro para un nombre de archivo.

    Devuelve None si tras limpiar no queda nada útil, con lo que se conserva la
    ruta clásica `<report>.pdf` (comportamiento previo intacto).
    """
    if instance is None:
        return None
    cleaned = _INSTANCE_UNSAFE.sub("-", instance.strip()).strip("-")
    return cleaned or None


def relative_path(order_id: str, report_key: str, instance: str | None = None) -> str:
    inst = _sanitize_instance(instance)
    suffix = f"-{inst}" if inst else ""
    return f"{order_folder(order_id)}/{report_key}{suffix}.pdf"


def save_pdf(order_id: str, report_key: str, data: bytes, instance: str | None = None) -> tuple[Path, str]:
    """Guarda el PDF y devuelve (ruta_absoluta, url_publica).

    `instance` diferencia el archivo cuando un mismo pedido genera el mismo
    `report` para personas distintas; sin él, el segundo PDF pisaría al primero.
    """
    rel = relative_path(order_id, report_key, instance)
    dest = settings.storage_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    url = f"{settings.public_base_url.rstrip('/')}/files/{rel}"
    return dest, url


def ensure_storage() -> None:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
