"""Compresión de los PDF generados.

Dos niveles:

* ``slim(data)`` — recompresión **estructural sin pérdida**: re-deflata los
  streams, agrupa objetos en object streams y descarta lo no referenciado.
  Se aplica automáticamente a todo PDF que sale del generador (dinámicos de
  WeasyPrint y clásicos de fpdf2). Si ``pikepdf`` no está disponible (p. ej.
  un entorno local sin wheels), devuelve el PDF tal cual: nunca es fatal.

* ``slim_images(data, ...)`` — además re-encoda las imágenes JPEG grandes
  (los fondos a página completa de los reportes clásicos). Es **con pérdida**
  y por eso no se aplica sola: la usa ``scripts/compress_pdf.py`` para
  aligerar archivos existentes cuando se decide a mano.
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def slim(data: bytes) -> bytes:
    """Recompresión estructural. Devuelve el original si no mejora o falla."""
    try:
        import pikepdf
    except ImportError:
        return data

    try:
        dst = io.BytesIO()
        with pikepdf.open(io.BytesIO(data)) as pdf:
            pdf.save(
                dst,
                compress_streams=True,
                recompress_flate=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )
        out = dst.getvalue()
    except Exception:  # noqa: BLE001 — comprimir jamás debe tumbar un job
        logger.exception("Compresión PDF falló; se entrega sin comprimir")
        return data

    return out if len(out) < len(data) else data


def slim_images(data: bytes, *, max_px: int = 1600, jpeg_quality: int = 80) -> bytes:
    """slim() + re-encodado de JPEGs más anchos/altos que ``max_px``.

    Solo toca imágenes DCTDecode sin máscara y en RGB/Gris: exactamente el
    caso de los fondos de los reportes clásicos. Cualquier otra se deja igual.
    """
    try:
        import pikepdf
        from PIL import Image
    except ImportError:
        return slim(data)

    try:
        dst = io.BytesIO()
        with pikepdf.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                xobjects = page.get("/Resources", {}).get("/XObject", {})
                for name in list(xobjects.keys()):
                    raw = xobjects[name]
                    if raw.get("/Subtype") != "/Image" or "/SMask" in raw:
                        continue
                    pimg = pikepdf.PdfImage(raw)
                    if pimg.filters != ["/DCTDecode"]:
                        continue
                    try:
                        pil = pimg.as_pil_image()
                    except Exception:  # noqa: BLE001 — imagen rara: se deja
                        continue
                    if pil.mode not in ("RGB", "L") or max(pil.size) <= max_px:
                        continue
                    ratio = max_px / max(pil.size)
                    pil = pil.resize(
                        (round(pil.width * ratio), round(pil.height * ratio)),
                        Image.LANCZOS,
                    )
                    buf = io.BytesIO()
                    pil.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
                    raw.write(buf.getvalue(), filter=pikepdf.Name("/DCTDecode"))
                    raw.Width, raw.Height = pil.width, pil.height
                    raw.ColorSpace = pikepdf.Name(
                        "/DeviceRGB" if pil.mode == "RGB" else "/DeviceGray"
                    )
                    raw.BitsPerComponent = 8
            pdf.save(
                dst,
                compress_streams=True,
                recompress_flate=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )
        out = dst.getvalue()
    except Exception:  # noqa: BLE001
        logger.exception("Compresión de imágenes falló; se intenta slim()")
        return slim(data)

    return out if len(out) < len(data) else data


__all__ = ["slim", "slim_images"]
