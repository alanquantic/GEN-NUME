"""Carga la base de conocimiento troceada y sirve trozos por (documento, clave).

`content/kb/index.json` lo produce `scripts/build_kb.py`. Aquí sólo se lee y se
consulta en memoria: no hay embeddings ni búsqueda difusa, la clave se conoce
exactamente.
"""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from ..config import settings

_PARA = re.compile(r"\n\s*\n")


class KnowledgeBase:
    def __init__(self, docs: dict):
        self._docs = docs

    @classmethod
    def load(cls, path: Path | None = None) -> "KnowledgeBase":
        path = path or (settings.content_dir / "kb" / "index.json")
        if not path.exists():
            raise FileNotFoundError(
                f"No existe {path}. Ejecuta antes:  py -3 scripts/build_kb.py"
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(payload["docs"])

    # ------------------------------------------------------------------ #
    def document(self, slug: str) -> dict | None:
        return self._docs.get(slug)

    def slice(self, slug: str, key: str) -> str | None:
        """Trozo del documento `slug` para la vibración/letra `key`."""
        doc = self._docs.get(slug)
        if doc is None:
            return None
        return doc["slices"].get(str(key))

    def intro(self, slug: str) -> str | None:
        doc = self._docs.get(slug)
        return doc["intro"] if doc else None

    def whole(self, slug: str) -> str | None:
        """Documento completo: intro + todos los trozos (para los cortos)."""
        doc = self._docs.get(slug)
        if doc is None:
            return None
        parts = [doc["intro"]] if doc["intro"] else []
        parts.extend(doc["slices"].values())
        return "\n\n".join(parts)

    def title(self, slug: str) -> str:
        doc = self._docs.get(slug)
        return doc["title"] if doc else slug


@lru_cache(maxsize=1)
def get_kb() -> KnowledgeBase:
    """KB cacheada por proceso (el índice es de sólo lectura)."""
    return KnowledgeBase.load()


# --------------------------------------------------------------------------- #
# Deduplicación de párrafos
# --------------------------------------------------------------------------- #
def _para_key(paragraph: str) -> str:
    return hashlib.md5(re.sub(r"\W+", "", paragraph.lower()).encode()).hexdigest()


def dedupe(text: str, seen: set[str]) -> str:
    """Quita párrafos largos ya vistos (mutando `seen`).

    El export repite bloques enteros entre entradas de blog; sin esto, el mismo
    párrafo entraría varias veces en el dossier y el modelo le daría más peso.
    Los párrafos cortos (< 120 chars: títulos, citas) se dejan pasar siempre.
    """
    out = []
    for para in _PARA.split(text):
        stripped = para.strip()
        if not stripped:
            continue
        if len(stripped) > 120:
            key = _para_key(stripped)
            if key in seen:
                continue
            seen.add(key)
        out.append(stripped)
    return "\n\n".join(out)


__all__ = ["KnowledgeBase", "get_kb", "dedupe"]
