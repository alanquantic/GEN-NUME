"""Carga de textos de contenido.

Los textos largos (descripciones por número numerológico) viven en
`content/texts.json`, generado desde el proyecto original con
`scripts/extract_content.py`. Así el contenido queda fuera del código, a
diferencia del original que lo tenía incrustado en helpers.php.

Estructura del JSON:
    { "getTextWhoIm1": { "1": "<p>...</p>", "2": "...", ... }, ... }
"""

from __future__ import annotations

import json
from functools import lru_cache

from .config import settings


@lru_cache
def _all_texts() -> dict[str, dict[str, str]]:
    path = settings.content_dir / "texts.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_text(function_name: str, number: int | str) -> str:
    """Devuelve el HTML del texto para un `getTextXxx` y un número dado."""
    return _all_texts().get(function_name, {}).get(str(number), "")
