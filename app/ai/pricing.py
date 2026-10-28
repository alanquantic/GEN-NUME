"""Precios por modelo y armado del objeto `usage` que se reporta a la tienda.

El job guarda el consumo crudo que devuelve el proveedor
({input, output, cache_read, cache_write}, acumulado entre llamadas); aquí se
convierte al objeto `usage` del contrato: tokens totales y costo en USD.

La tabla de precios va en USD por millón de tokens, con el PREFIJO del id del
modelo como clave (gana el prefijo más largo, así "claude-opus-5-5" no cae en
la fila de "claude-opus-5"). Se puede ampliar o corregir sin desplegar con la
variable de entorno AI_PRICE_TABLE (JSON que se fusiona sobre los defaults):

    AI_PRICE_TABLE={"gemini-3.5-flash": {"input": 0.30, "output": 2.50}}

Un modelo sin fila en la tabla reporta los tokens igual, con costos en null.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..config import settings

# USD por millón de tokens. cache_read/cache_write omitidos caen al estándar
# de Anthropic: 10% y 125% del precio de input respectivamente.
DEFAULT_PRICE_TABLE: dict[str, dict[str, float]] = {
    # Anthropic (tarifas first-party, oct 2026)
    "claude-fable-5":   {"input": 10.0, "output": 50.0},
    "claude-opus-5-5":  {"input": 4.0,  "output": 20.0, "cache_read": 0.20},
    "claude-opus-5":    {"input": 5.0,  "output": 25.0},
    "claude-opus-4":    {"input": 5.0,  "output": 25.0},
    "claude-sonnet-5":  {"input": 2.0,  "output": 10.0, "cache_read": 0.20},
    "claude-sonnet-4":  {"input": 3.0,  "output": 15.0},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
    "claude-haiku-4-5": {"input": 1.0,  "output": 5.0},
    # Google AI Studio. Los Gemini 3.x no tienen fila (precio no confirmado):
    # agrégalos vía AI_PRICE_TABLE o sus jobs reportan costos null.
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro":   {"input": 1.25, "output": 10.0},
}


class JobUsage(BaseModel):
    """Consumo del job en el contrato con la tienda.

    input_tokens incluye los tokens de caché (todo lo que entró al modelo);
    el costo sí se calcula con la tarifa propia de cada categoría.
    """

    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    token_cost_usd: float | None = None
    production_cost_usd: float | None = None


def price_for(model: str | None) -> dict[str, float] | None:
    if not model:
        return None
    table = {**DEFAULT_PRICE_TABLE, **settings.ai_price_table}
    best: str | None = None
    for prefix in table:
        if model.startswith(prefix) and (best is None or len(prefix) > len(best)):
            best = prefix
    if best is None:
        return None
    prices = dict(table[best])
    prices.setdefault("cache_read", prices["input"] * 0.10)
    prices.setdefault("cache_write", prices["input"] * 1.25)
    return prices


def merge_usage(prev: dict[str, int] | None,
                new: dict[str, int] | None) -> dict[str, int] | None:
    """Acumula el consumo de varias llamadas al modelo dentro de un job."""
    if not prev:
        return dict(new) if new else None
    if not new:
        return dict(prev)
    return {k: int(prev.get(k, 0)) + int(new.get(k, 0))
            for k in set(prev) | set(new)}


def build_usage(model: str | None,
                usage: dict[str, int] | None) -> JobUsage | None:
    if usage is None:
        return None
    inp = int(usage.get("input", 0))
    out = int(usage.get("output", 0))
    cache_read = int(usage.get("cache_read", 0))
    cache_write = int(usage.get("cache_write", 0))
    input_tokens = inp + cache_read + cache_write

    prices = price_for(model)
    token_cost = production_cost = None
    if prices is not None:
        token_cost = round(
            (inp * prices["input"]
             + out * prices["output"]
             + cache_read * prices["cache_read"]
             + cache_write * prices["cache_write"]) / 1_000_000,
            6,
        )
        production_cost = round(
            token_cost + settings.ai_production_overhead_usd, 6)

    return JobUsage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=out,
        total_tokens=input_tokens + out,
        token_cost_usd=token_cost,
        production_cost_usd=production_cost,
    )


__all__ = ["DEFAULT_PRICE_TABLE", "JobUsage", "price_for", "merge_usage",
           "build_usage"]
