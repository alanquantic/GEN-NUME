"""Pruebas de la fase 4 que NO tocan la red.

Cubre el armado del mensaje, el esquema y la validación de anclaje. La llamada
real al modelo (`_call_model`) sólo se ejerce con `scripts/generate_report.py`
y una clave de API.

    py -3 tests/test_generate.py
"""

import io
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import dossier as dsr        # noqa: E402
from app.ai import generate as gen       # noqa: E402
from app.ai import prompts               # noqa: E402
from app.ai.recipes import REPORTS       # noqa: E402

TODAY = date(2026, 7, 29)
NAME = "Juan Pedro Martinez"
BIRTH = date(1991, 11, 20)


def _dossier(key="quien-soy", **kw):
    return dsr.build(key, NAME, BIRTH, today=TODAY, **kw)


# --------------------------------------------------------------------------- #
# Prompt de sistema
# --------------------------------------------------------------------------- #
def test_system_prompt_por_reporte():
    for key in REPORTS:
        sp = prompts.system_prompt(key)
        assert "REGLA DE ANCLAJE" in sp
        assert "{ENCARGO}" not in sp          # el encargo quedó sustituido
        assert prompts.ENCARGO[key].splitlines()[0] in sp


def test_bienestar_lleva_prohibicion_de_salud():
    sp = prompts.system_prompt("bienestar")
    assert "dolencias, órganos, síntomas" in sp


# --------------------------------------------------------------------------- #
# Esquema
# --------------------------------------------------------------------------- #
def test_esquema_estructura():
    s = prompts.SCHEMA
    assert s["additionalProperties"] is False
    # todo lo requerido está en properties
    assert set(s["required"]) <= set(s["properties"])
    sec = s["properties"]["secciones"]["items"]
    assert sec["additionalProperties"] is False
    assert "numeros" in sec["required"]        # anclaje obligatorio por sección
    # destacado admite null
    tipos = sec["properties"]["destacado"]["anyOf"]
    assert any(t.get("type") == "null" for t in tipos)


# --------------------------------------------------------------------------- #
# Mensaje de usuario
# --------------------------------------------------------------------------- #
def test_mensaje_incluye_numeros_y_material():
    d = _dossier()
    msg = gen.build_user_message(
        d, NAME, "20 de noviembre de 1991", "29 de julio de 2026")
    assert "<numeros>" in msg and "</numeros>" in msg
    assert "<material>" in msg and "</material>" in msg
    assert "Juan" in msg                        # nombre de pila
    assert d.numbers_block in msg
    assert d.material in msg


def test_mensaje_con_pareja_incluye_bloque_pareja():
    d = _dossier("amor", partner_name="Ana", partner_birth_date=date(1988, 3, 5))
    msg = gen.build_user_message(
        d, NAME, "20 de noviembre de 1991", "29 de julio de 2026",
        partner_name="Ana Belen", partner_birth_long="5 de marzo de 1988")
    assert "<pareja>" in msg
    assert "Ana Belen" in msg


# --------------------------------------------------------------------------- #
# Validación de anclaje
# --------------------------------------------------------------------------- #
def test_anclaje_acepta_claves_reales():
    d = _dossier()
    data = {
        "secciones": [{"id": "esencia", "numeros": ["B", "A"]}],
        "tension_central": {"numeros": ["B", "A"]},
    }
    assert gen.validate_anchoring(d, data) == []


def test_anclaje_detecta_clave_inventada():
    d = _dossier()
    data = {
        "secciones": [{"id": "x", "numeros": ["B", "ZZ"]}],
        "tension_central": {"numeros": []},
    }
    warnings = gen.validate_anchoring(d, data)
    assert len(warnings) == 1 and "ZZ" in warnings[0]


def test_anclaje_ignora_asterisco_karmico():
    d = _dossier()
    # H se declara como "H" aunque su valor sea 4*; la clave existe
    data = {"secciones": [{"id": "destino", "numeros": ["H"]}],
            "tension_central": {"numeros": []}}
    assert gen.validate_anchoring(d, data) == []


# --------------------------------------------------------------------------- #
# Modo de prueba (mock) — sin red
# --------------------------------------------------------------------------- #
def test_mock_genera_y_valida_anclaje():
    d = _dossier("quien-soy")
    r = gen.generate(d, person_name=NAME,
                     birth_long="20 de noviembre de 1991",
                     today_long="29 de julio de 2026", mock=True)
    assert r.model.startswith("mock")
    assert r.data["titulo"]
    assert len(r.data["secciones"]) == 9
    # el ejemplo está anclado: no debe disparar avisos
    assert r.warnings == [], r.warnings


def test_mock_cumple_el_esquema():
    d = _dossier("quien-soy")
    r = gen.generate(d, person_name=NAME, birth_long="x", today_long="y", mock=True)
    # todas las claves top del esquema presentes
    for k in prompts.SCHEMA["required"]:
        assert k in r.data, f"falta {k}"
    # cada sección con los campos requeridos
    req = prompts.SCHEMA["properties"]["secciones"]["items"]["required"]
    for sec in r.data["secciones"]:
        assert all(k in sec for k in req)


def test_mock_reporte_sin_ejemplo_avisa():
    d = _dossier("trabajo")
    try:
        gen.generate(d, person_name=NAME, birth_long="x", today_long="y", mock=True)
    except FileNotFoundError:
        return
    raise AssertionError("debería avisar de que no hay ejemplo para 'trabajo'")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    failures = 0
    print("Pruebas de generación (sin red)\n")
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
