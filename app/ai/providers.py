"""Capa de proveedor: la ÚNICA parte del sistema que depende del modelo.

Todo lo demás (prompt, dossier, esquema, validación de anclaje) es idéntico
para cualquier proveedor. Aquí sólo cambia cómo se hace la llamada y cómo se
adapta el esquema JSON al dialecto de cada API.

    data, model, usage, stop = call(settings, system, user, schema)

Proveedores:
  · anthropic — Claude (Opus 5 por defecto). Salida estructurada garantizada
    con output_config.format y prompt cacheado.
  · google    — Gemini vía Google AI Studio. response_schema (subconjunto
    OpenAPI) y caché implícita de los modelos 2.5.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger("reportpdf.ai")

Result = tuple[dict, str, dict, str | None]

# Reintentos ante errores transitorios del proveedor (503 saturado, 429,
# 5xx, cortes de red). Un pico de demanda de un par de minutos no debe
# matar el reporte de un cliente. Esperas: 5s, 15s, 45s.
_RETRY_DELAYS = (5, 15, 45)
_TRANSIENT_CODES = {429, 500, 502, 503, 504, 529}


def _is_transient(exc: Exception) -> bool:
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value in _TRANSIENT_CODES
    # Errores de conexión/timeout de ambos SDKs, sin importarlos aquí.
    return type(exc).__name__ in {
        "APIConnectionError", "APITimeoutError", "ServerError",
        "ConnectionError", "TimeoutError",
    }


class ProviderUnavailableError(RuntimeError):
    """El modelo/servicio no está disponible tras agotar los reintentos
    inmediatos. El service la usa para programar un reintento diferido
    (y avisar por correo si también falla)."""

# Reintentos ante errores transitorios del proveedor (503 saturado, 429,
# 5xx, cortes de red). Un pico de demanda de un par de minutos no debe
# matar el reporte de un cliente. Esperas: 5s, 15s, 45s.
_RETRY_DELAYS = (5, 15, 45)
_TRANSIENT_CODES = {429, 500, 502, 503, 504, 529}


def _is_transient(exc: Exception) -> bool:
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value in _TRANSIENT_CODES
    # Errores de conexión/timeout de ambos SDKs, sin importarlos aquí.
    return type(exc).__name__ in {
        "APIConnectionError", "APITimeoutError", "ServerError",
        "ConnectionError", "TimeoutError",
    }


def call(settings, system: str, user: str, schema: dict) -> Result:
    from ._tls import ensure_system_trust
    ensure_system_trust()          # verifica contra el almacén del SO si hace falta
    provider = settings.ai_provider
    if provider == "anthropic":
        fn = _anthropic
    elif provider == "google":
        fn = _google
    else:
        raise ValueError(f"proveedor de IA desconocido: {provider!r} "
                         "(usa 'anthropic' o 'google')")

    last: Exception | None = None
    for delay in (0, *_RETRY_DELAYS):
        if delay:
            logger.warning(
                "Error transitorio del proveedor %s (%s); reintento en %ss",
                provider, last, delay,
            )
            time.sleep(delay)
        try:
            return fn(settings, system, user, schema)
        except Exception as exc:  # noqa: BLE001 — sólo se reintenta lo transitorio
            if not _is_transient(exc):
                raise
            last = exc
    raise ProviderUnavailableError(
        f"El proveedor {provider} sigue sin responder tras "
        f"{len(_RETRY_DELAYS) + 1} intentos: {last}"
    ) from last


# --------------------------------------------------------------------------- #
# Anthropic (Claude)
# --------------------------------------------------------------------------- #
def _anthropic(settings, system: str, user: str, schema: dict) -> Result:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    resp = client.messages.create(
        model=settings.resolved_model,
        max_tokens=settings.ai_max_tokens,
        system=[{"type": "text", "text": system,
                 "cache_control": {"type": "ephemeral"}}],
        thinking={"type": "adaptive"},
        output_config={
            "effort": settings.ai_effort,
            "format": {"type": "json_schema", "schema": schema},
        },
        messages=[{"role": "user", "content": user}],
    )

    if resp.stop_reason == "refusal":
        raise RuntimeError("El modelo rehusó la petición (stop_reason=refusal).")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("Respuesta truncada (max_tokens). Sube ai_max_tokens.")

    text = next((b.text for b in resp.content if b.type == "text"), None)
    if text is None:
        raise RuntimeError("La respuesta no trae bloque de texto.")

    usage = {
        "input": resp.usage.input_tokens,
        "output": resp.usage.output_tokens,
        "cache_read": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
        "cache_write": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
    }
    return json.loads(text), resp.model, usage, resp.stop_reason


# --------------------------------------------------------------------------- #
# Google (Gemini · AI Studio)
# --------------------------------------------------------------------------- #
def _google(settings, system: str, user: str, schema: dict) -> Result:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.google_api_key or None)
    model = settings.resolved_model
    resp = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=to_gemini_schema(schema),
            max_output_tokens=settings.ai_max_tokens,
        ),
    )

    # Motivo de corte: SAFETY / MAX_TOKENS / STOP…
    stop = None
    if resp.candidates:
        fr = resp.candidates[0].finish_reason
        stop = getattr(fr, "name", str(fr)) if fr is not None else None
    if stop in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST"):
        raise RuntimeError(f"Gemini bloqueó la respuesta ({stop}).")
    if stop == "MAX_TOKENS":
        raise RuntimeError("Respuesta truncada (MAX_TOKENS). Sube ai_max_tokens.")

    text = resp.text
    if not text:
        raise RuntimeError(f"Gemini no devolvió texto (finish_reason={stop}).")

    um = resp.usage_metadata
    usage = {
        "input": getattr(um, "prompt_token_count", 0) or 0,
        "output": getattr(um, "candidates_token_count", 0) or 0,
        "cache_read": getattr(um, "cached_content_token_count", 0) or 0,
        "cache_write": 0,
    }
    return json.loads(text), model, usage, stop


# --------------------------------------------------------------------------- #
# Adaptación de esquema: JSON Schema (Anthropic) → subconjunto OpenAPI (Gemini)
# --------------------------------------------------------------------------- #
def to_gemini_schema(node: Any) -> Any:
    """Convierte el esquema al dialecto que acepta Gemini.

    Cambios necesarios:
      · Se elimina `additionalProperties` (Gemini no lo admite).
      · `anyOf: [{type:null}, X]` (nuestro campo opcional) se colapsa a X con
        `nullable: true`.
      · Se mantiene `propertyOrdering` = orden de `properties` para que el modelo
        respete el orden de las secciones.
    """
    if isinstance(node, list):
        return [to_gemini_schema(x) for x in node]
    if not isinstance(node, dict):
        return node

    # anyOf con una rama null → nullable
    if "anyOf" in node:
        branches = node["anyOf"]
        non_null = [b for b in branches if b.get("type") != "null"]
        has_null = any(b.get("type") == "null" for b in branches)
        if has_null and len(non_null) == 1:
            merged = to_gemini_schema(non_null[0])
            if isinstance(merged, dict):
                merged["nullable"] = True
            return merged
        return {"anyOf": [to_gemini_schema(b) for b in non_null or branches]}

    out: dict = {}
    for key, value in node.items():
        if key == "additionalProperties":
            continue
        out[key] = to_gemini_schema(value)

    if out.get("type") == "object" and "properties" in out:
        out.setdefault("propertyOrdering", list(out["properties"].keys()))
    return out


__all__ = ["call", "to_gemini_schema", "Result"]
