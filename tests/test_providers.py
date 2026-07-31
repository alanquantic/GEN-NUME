"""Pruebas de la capa de proveedor (sin red).

Verifica la adaptación de esquema a Gemini y el despacho por proveedor. La
llamada real a cada API se ejerce con `scripts/generate_report.py` y una clave.

    py -3 tests/test_providers.py
"""

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import prompts, providers   # noqa: E402


# --------------------------------------------------------------------------- #
# Adaptación de esquema
# --------------------------------------------------------------------------- #
def test_gemini_quita_additional_properties():
    g = providers.to_gemini_schema(prompts.SCHEMA)
    assert "additionalProperties" not in json.dumps(g)


def test_gemini_colapsa_anyof_null_a_nullable():
    g = providers.to_gemini_schema(prompts.SCHEMA)
    dest = g["properties"]["secciones"]["items"]["properties"]["destacado"]
    assert dest.get("nullable") is True
    assert dest.get("type") == "object"
    assert "anyOf" not in dest


def test_gemini_mantiene_orden_de_propiedades():
    g = providers.to_gemini_schema(prompts.SCHEMA)
    assert g["propertyOrdering"] == list(prompts.SCHEMA["properties"].keys())


def test_gemini_conserva_required_y_enum():
    g = providers.to_gemini_schema(prompts.SCHEMA)
    sec = g["properties"]["secciones"]["items"]
    assert "numeros" in sec["required"]
    tipo = sec["properties"]["destacado"]["properties"]["tipo"]
    assert set(tipo["enum"]) == {"cita", "dato", "alerta"}


def test_esquema_valido_para_el_sdk_de_gemini():
    from google.genai import types
    g = providers.to_gemini_schema(prompts.SCHEMA)
    sc = types.Schema.model_validate(g)          # lo que hace el SDK en la llamada
    assert sc.type.name == "OBJECT"


# --------------------------------------------------------------------------- #
# Despacho
# --------------------------------------------------------------------------- #
class _FakeSettings:
    ai_provider = "desconocido"
    ai_model = "x"


def test_proveedor_desconocido_falla_claro():
    try:
        providers.call(_FakeSettings(), "s", "u", {})
        assert False, "debió lanzar"
    except ValueError as e:
        assert "desconocido" in str(e)


def test_resolved_model_google_por_defecto():
    from app.config import Settings
    # _env_file=None → hermético, ignora el .env real de desarrollo
    s = Settings(ai_provider="google", ai_model="claude-opus-5", _env_file=None)
    assert s.resolved_model == "gemini-3.5-flash"
    s2 = Settings(ai_provider="google", ai_model="gemini-2.5-flash", _env_file=None)
    assert s2.resolved_model == "gemini-2.5-flash"
    s3 = Settings(ai_provider="anthropic", ai_model="claude-opus-5", _env_file=None)
    assert s3.resolved_model == "claude-opus-5"


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    failures = 0
    print("Pruebas de proveedor (sin red)\n")
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
