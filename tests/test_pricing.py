"""Pruebas del costeo del `usage` reportado a la tienda.

    py -3 tests/test_pricing.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import pricing  # noqa: E402
from app.config import settings  # noqa: E402


def test_costo_claude_opus_5():
    u = pricing.build_usage("claude-opus-5", {
        "input": 1_000_000, "output": 1_000_000,
        "cache_read": 0, "cache_write": 0,
    })
    assert u.model == "claude-opus-5"
    assert u.input_tokens == 1_000_000
    assert u.output_tokens == 1_000_000
    assert u.total_tokens == 2_000_000
    assert u.token_cost_usd == 30.0          # 5 + 25 USD/MTok
    assert u.production_cost_usd == 30.0     # sin overhead, igual al de tokens


def test_cache_cuenta_en_tokens_y_costo():
    u = pricing.build_usage("claude-opus-5", {
        "input": 0, "output": 0,
        "cache_read": 1_000_000, "cache_write": 1_000_000,
    })
    assert u.input_tokens == 2_000_000       # la caché entra en input_tokens
    assert u.total_tokens == 2_000_000
    # cache_read al 10% de input (0.50) y cache_write al 125% (6.25)
    assert u.token_cost_usd == 6.75


def test_prefijo_mas_largo_gana():
    assert pricing.price_for("claude-opus-5-5")["input"] == 4.0
    assert pricing.price_for("claude-opus-5")["input"] == 5.0
    assert pricing.price_for("claude-sonnet-5-5")["input"] == 2.0


def test_modelo_desconocido_reporta_costos_null():
    u = pricing.build_usage("modelo-inventado", {"input": 10, "output": 5})
    assert u.total_tokens == 15
    assert u.token_cost_usd is None
    assert u.production_cost_usd is None


def test_sin_usage_no_hay_objeto():
    assert pricing.build_usage("claude-opus-5", None) is None


def test_merge_acumula_llamadas():
    a = {"input": 10, "output": 5, "cache_read": 1, "cache_write": 0}
    b = {"input": 3, "output": 2, "cache_read": 0, "cache_write": 4}
    assert pricing.merge_usage(a, b) == {
        "input": 13, "output": 7, "cache_read": 1, "cache_write": 4}
    assert pricing.merge_usage(None, b) == b
    assert pricing.merge_usage(a, None) == a
    assert pricing.merge_usage(None, None) is None


def test_tabla_por_env_sobreescribe_defaults():
    original = settings.ai_price_table
    try:
        settings.ai_price_table = {"modelo-inventado": {"input": 1.0, "output": 2.0}}
        u = pricing.build_usage("modelo-inventado-v2", {
            "input": 1_000_000, "output": 1_000_000})
        assert u.token_cost_usd == 3.0
    finally:
        settings.ai_price_table = original


def test_overhead_de_produccion_se_suma():
    original = settings.ai_production_overhead_usd
    try:
        settings.ai_production_overhead_usd = 0.05
        u = pricing.build_usage("claude-opus-5", {"input": 1_000_000, "output": 0})
        assert u.token_cost_usd == 5.0
        assert u.production_cost_usd == 5.05
    finally:
        settings.ai_production_overhead_usd = original


if __name__ == "__main__":
    failures = 0
    print("Pruebas de costeo del usage\n")
    for name, fn in sorted(dict(globals()).items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print()
    print(f"{failures} fallaron" if failures else "Todas las pruebas pasaron OK")
    sys.exit(1 if failures else 0)
