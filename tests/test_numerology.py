"""Pruebas del dominio numerológico.

Valores esperados calculados a mano a partir de la lógica del proyecto original
(PHP). Se puede correr con pytest o directamente:  py -3 tests/test_numerology.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain import Person, Universal, reduce_number, reduce_number_for_sub

TODAY = date(2026, 7, 13)


def person():
    p = Person(
        "Juan Pedro Martinez Barragan",
        "1991-11-20",
        name_sanitize="juan-pedro-martinez-barragan",
        today=TODAY,
    )
    return p


def test_reduce_number():
    assert reduce_number(20) == 2
    assert reduce_number(11) == 11          # maestro, no se reduce
    assert reduce_number(22) == 22          # maestro, no se reduce
    assert reduce_number(29) == 11          # 2+9 = 11 (maestro)
    assert reduce_number(39) == 3           # 3+9=12 -> 3
    assert reduce_number(2057) == 5         # 2+0+5+7=14 -> 5


def test_reduce_number_for_sub():
    assert reduce_number_for_sub(11) == 2   # sin excepción de maestros
    assert reduce_number_for_sub(22) == 4


def test_personal_numbers():
    p = person()
    assert p.personal_number() == 2
    assert p.personal_year(2026) == 5
    assert p.personal_year(2022) == 1
    assert p.personal_year() == 5           # usa today (2026)
    assert p.personal_month() == 3          # julio 2026
    assert p.get_date() == "20 noviembre 1991"


def test_stages():
    p = person()
    assert p.get_stage(1) == 4
    assert p.get_stage_range(1) == "1991-2020"
    assert p.get_stage_age_range(1) == "0 - 30"
    assert p.get_stage(3) == 8
    assert p.calc_stage(2026) == 4          # 2026 cae en la 2da etapa


def test_soul_and_expression():
    p = person()
    assert p.get_soul_number() == 6
    assert p.calc_soul_expression_number() == 5


def test_professional_development():
    p = person()
    data = p.get_professional_development()
    assert set(data.keys()) == {"binomie", "letter"}
    assert "/" in data["binomie"]


def test_partner_and_synastry():
    p = person()
    p.set_partner("Andres Isaias Lomeli Sierra", "1997-11-30")
    assert p.calc_partner_year(2026) == 1
    assert p.synastry_a() == 22
    assert p.synastry_b() == 5
    assert p.synastry_c() == 1
    assert isinstance(p.synastry_w(), (int, str))


def test_universal():
    u = Universal(TODAY)
    assert u.universal_day() == 3
    assert u.universal_month() == 8
    assert u.universal_week() == 9


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
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
    if failures:
        print(f"{failures} prueba(s) fallaron")
        sys.exit(1)
    print("Todas las pruebas pasaron OK")
