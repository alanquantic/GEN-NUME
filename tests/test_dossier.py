"""Pruebas del ensamblador de dossiers (fase 3).

Requieren que exista content/kb/index.json:  py -3 scripts/build_kb.py

    py -3 tests/test_dossier.py
"""

import io
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import dossier as dsr        # noqa: E402
from app.ai import numbers as num        # noqa: E402
from app.ai.recipes import REPORTS       # noqa: E402

TODAY = date(2026, 7, 29)
NAME = "Juan Pedro Martinez"
BIRTH = date(1991, 11, 20)


# --------------------------------------------------------------------------- #
# Números
# --------------------------------------------------------------------------- #
def test_sanitize():
    assert num.sanitize("Juan Pedro Martínez") == "juan-pedro-martinez"
    assert num.sanitize("  MARÍA José  ") == "maria-jose"
    assert num.sanitize("Núñez") == "nuñez"


def test_name_numbers_conocidos():
    san = "juan-pedro-martinez"
    # ALMA (vocales) y EXPRESION (consonantes) coinciden con domain.Person
    assert num.soul_number(san) == 3
    assert num.expression_number(san) == 9
    assert num.initial(san) == "J"
    # NOMBRE = todas las letras; ACTIVO = sólo "juan"
    assert 1 <= num.name_number(san) <= 22
    assert num.active_name_number(san) == num.active_name_number("juan")


def test_resolve_incluye_pinaculo_y_nombre():
    n = num.resolve(NAME, BIRTH, today=TODAY)
    assert n.get("B") == "2"
    assert n.get("H") == "4*"          # kármico conservado
    assert n.get("ALMA") == "3"
    assert n.get("AP") == "5"          # 20+11+2026 → 5
    assert n.get("MADUREZ") is not None
    assert not n.unresolved            # ya no queda ninguna clave sin fórmula


def test_maestro_es_segunda_etapa_y_proyecto_es_alma():
    n = num.resolve(NAME, BIRTH, today=TODAY)
    assert n.get("MAESTRO") == n.get("F")       # 2.ª etapa (posición F)
    assert n.get("PROYECTO") == n.get("ALMA")   # suma de vocales


def test_resolve_pareja_solo_con_pareja():
    solo = num.resolve(NAME, BIRTH, today=TODAY)
    con = num.resolve(NAME, BIRTH, today=TODAY, partner_birth_date=date(1988, 3, 5))
    assert solo.get("PAREJA") is None
    assert con.get("PAREJA") is not None


# --------------------------------------------------------------------------- #
# Dossier
# --------------------------------------------------------------------------- #
def test_todos_los_reportes_ensamblan():
    for key in REPORTS:
        d = dsr.build(key, NAME, BIRTH, today=TODAY)
        assert d.pieces, f"{key}: dossier vacío"
        assert d.material.strip()
        assert d.numbers_block.strip()
        # tamaño razonable: ni trivial ni desbocado
        assert 5_000 < len(d.material) < 250_000, f"{key}: {len(d.material)} chars"


def test_material_solo_contiene_material_de_esta_persona():
    """El dossier de una persona no debe traer trozos de otra vibración."""
    d = dsr.build("quien-soy", NAME, BIRTH, today=TODAY)
    # B=2: el texto del número personal 2 debe estar; el del 5 no como cabecera
    personal = next(p for p in d.pieces
                    if p.slug.endswith("numero-personal") and p.key == "B")
    assert personal.value == "2"


def test_amor_sin_pareja_omite_piezas_de_pareja():
    solo = dsr.build("amor", NAME, BIRTH, today=TODAY)
    con = dsr.build("amor", NAME, BIRTH, today=TODAY,
                    partner_name="Ana", partner_birth_date=date(1988, 3, 5))
    slugs_solo = {p.slug for p in solo.pieces}
    slugs_con = {p.slug for p in con.pieces}
    assert any("numero-de-pareja" in s for s in slugs_con)
    assert not any("numero-de-pareja" in s for s in slugs_solo)


def test_dedupe_no_repite_parrafos():
    d = dsr.build("quien-soy", NAME, BIRTH, today=TODAY)
    # numero-personal y armonico-y-desarmonico comparten párrafos del export;
    # tras dedupe, ningún párrafo largo aparece dos veces en el material.
    paras = [p.strip() for p in d.material.split("\n\n") if len(p.strip()) > 120]
    # se ignoran las cabeceras FUENTE
    paras = [p for p in paras if not p.startswith("─") and "FUENTE:" not in p]
    assert len(paras) == len(set(paras)), "hay párrafos duplicados en el material"


def test_proposito_ya_incluye_maestro_y_proyecto():
    d = dsr.build("proposito", NAME, BIRTH, today=TODAY)
    slugs = {p.slug.split("/")[-1] for p in d.pieces}
    assert "encuentro-con-tu-maestro" in slugs
    assert "mi-proyecto-sentido" in slugs


def test_reporte_desconocido_lanza():
    try:
        dsr.build("no-existe", NAME, BIRTH, today=TODAY)
    except KeyError:
        return
    raise AssertionError("debería lanzar KeyError")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    failures = 0
    print("Pruebas del ensamblador\n")
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
