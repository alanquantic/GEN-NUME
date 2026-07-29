"""Pruebas del Pináculo personal (24 posiciones).

Los valores esperados salen de los ejemplos resueltos del libro de Laura
(*LIBRO FINAL-LAURA de 26 de JULIO.docx*, capítulos IV–VII) y del diagrama
oficial de fórmulas.

    py -3 tests/test_pinnacle.py

Además de las aserciones, el script imprime un **informe de divergencias**
(`report_book_examples`) con los casos donde el libro y el diagrama no coinciden.
Eso NO es un fallo: es la lista de preguntas pendientes para Laura. Ver
`docs/reportes-dinamicos/pinaculo-formulas.md` §10.
"""

import io
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.pinnacle import Pinnacle, Vibration, reduce_tracked


# --------------------------------------------------------------------------- #
# Reducción y deuda kármica
# --------------------------------------------------------------------------- #
def test_reduce_conserva_maestros():
    assert reduce_tracked(20).value == 2
    assert reduce_tracked(11).value == 11
    assert reduce_tracked(22).value == 22
    assert reduce_tracked(1991).value == 2          # 1991 → 20 → 2


def test_deuda_karmica_se_marca():
    v = reduce_tracked(13)
    assert (v.value, v.karmic) == (4, 13)
    assert str(v) == "4*"

    for raw, base in ((13, 4), (14, 5), (16, 7), (19, 1)):
        v = reduce_tracked(raw)
        assert (v.value, v.karmic) == (base, raw), raw

    # 20 no es kármico y no debe marcarse
    assert reduce_tracked(20).karmic is None


def test_vibracion_base_baja_los_maestros():
    assert Vibration(11).base == 2
    assert Vibration(22).base == 4
    assert Vibration(7).base == 7


# --------------------------------------------------------------------------- #
# Caso de referencia — 20/11/1991
# Contrastado posición a posición contra la web (web-nume.vercel.app).
# --------------------------------------------------------------------------- #
REF = Pinnacle.from_date(date(1991, 11, 20))


def test_horizontal():
    assert REF.a.value == 11        # mes 11, maestro
    assert REF.b.value == 2         # día 20 → 2
    assert REF.c.value == 2         # 1991 → 20 → 2
    assert REF.d.value == 6         # 11+2+2 = 15 → 6


def test_ser_superior():
    assert REF.e.value == 4         # A+B = 13 → 4*
    assert REF.e.karmic == 13
    assert REF.f.value == 4         # B+C = 4
    assert REF.g.value == 8         # E+F = 8
    assert REF.h.value == 4         # A+C = 13 → 4*
    assert REF.i.value == 7         # E+F+G = 16 → 7*
    assert REF.i.karmic == 16
    assert REF.j.value == 1         # H+D = 10 → 1


def test_ser_inferior_todo_ceros_menos_la_sombra():
    # base(A)=2, base(B)=2, base(C)=2 → todas las restas dan 0
    assert (REF.k.value, REF.l.value, REF.m.value, REF.n.value) == (0, 0, 0, 0)
    assert REF.o.value == 0
    assert REF.p.value == 6         # D+O = 6+0
    assert (REF.q.value, REF.r.value, REF.s.value) == (0, 0, 0)


def test_coincide_con_la_web_en_la_zona_inferior():
    """La web da D=6, O=0, Q=R=S=0, P=6 para esta fecha."""
    assert (REF.d.value, REF.o.value, REF.p.value) == (6, 0, 6)
    assert (REF.q.value, REF.r.value, REF.s.value) == (0, 0, 0)


def test_exteriores():
    assert REF.x.value == 8         # B+D = 8
    assert REF.y.value == 11        # A+B+C+D+X = 29 → 11
    assert REF.z.value == 1         # 9+1 = 10 → 1


def test_ausencias():
    # presentes en 1..9: 2,6,4,8,7,1  →  faltan 3, 5, 9
    assert REF.absences == (3, 5, 9)


def test_pinaculo_especial_por_exceso_de_ceros():
    # 8 ceros en la zona inferior: la regla de la triplicidad no aplica
    assert REF.special_pinnacle is True
    assert REF.w is None
    assert REF.w_source is None


def test_triplicidad_expone_el_digito_repetido():
    """Busca una fecha con triplicidad real y comprueba W vs W_DIGIT."""
    from datetime import date as _date
    found = None
    for y in range(1970, 2001):
        for mo in range(1, 13):
            for da in range(1, 29):
                p = Pinnacle.from_date(_date(y, mo, da))
                if p.w is not None:
                    found = p
                    break
            if found:
                break
        if found:
            break
    assert found is not None, "no se encontró ninguna triplicidad en el rango"
    # W es 3, 6 o 9; W_DIGIT es el dígito que se triplicó (1..9)
    assert found.w.value in (3, 6, 9)
    assert found.w_source in range(1, 10)
    # coherencia: el dígito triplicado, x3 y reducido, da W
    assert reduce_tracked(found.w_source * 3).value == found.w.value


def test_h_confirmado_en_el_caso_de_referencia():
    # H = A+C = 13 → 4;  comprobación: 11 + 1991 = 2002 → 4.  Coinciden.
    assert REF.h.value == 4
    assert REF.h_alternative is None


def test_h_expone_la_maestra_como_potencial():
    """16/07/1968: vibraciones dan 4*, comprobación 7+1968 = 1975 → 22."""
    p = Pinnacle.from_date(date(1968, 7, 16))
    assert p.h.value == 4
    assert p.h_alternative is not None and p.h_alternative.value == 22


def test_comprobacion_de_h_puede_bajar_la_maestra():
    """21/12/1970: vibraciones dan 11, comprobación 12+1970 = 1982 → 2."""
    p = Pinnacle.from_date(date(1970, 12, 21))
    assert p.h.value == 2, f"esperado 2, obtenido {p.h}"
    assert p.h_alternative is not None and p.h_alternative.value == 11


def test_comprobacion_de_h_confirma():
    """23/09/2000: 9 + 2000 = 2009 → 11, igual que por vibraciones."""
    p = Pinnacle.from_date(date(2000, 9, 23))
    assert p.h.value == 11
    assert p.h_alternative is None


def test_deudas_karmicas_detectadas():
    posiciones = dict(REF.karmic_debts)
    assert posiciones["E"] == 13
    assert posiciones["H"] == 13
    assert posiciones["I"] == 16


# --------------------------------------------------------------------------- #
# Regla de comprobación de D — ejemplo del libro (cap. V)
# --------------------------------------------------------------------------- #
def test_comprobacion_de_d_confirma():
    """18/10/1981: vibraciones y crudos coinciden en 11 → D no cambia."""
    p = Pinnacle.from_date(date(1981, 10, 18))
    assert p.d.value == 11
    assert p.d_verified is False


def test_comprobacion_de_d_corrige():
    """10/04/1979: vibraciones dan 4*, crudos dan 22 → gana la comprobación."""
    p = Pinnacle.from_date(date(1979, 4, 10))
    assert p.d.value == 22, f"esperado 22, obtenido {p.d}"
    assert p.d_verified is True


# --------------------------------------------------------------------------- #
# Regalo Divino (Z)
# --------------------------------------------------------------------------- #
def test_regalo_divino():
    # 1968 → 6+8 = 14 → 1+4 = 5.
    # (El libro escribe "1 + 4 = 4" en este ejemplo: es una errata aritmética.)
    assert Pinnacle.from_date(date(1968, 7, 16)).z.value == 5
    assert Pinnacle.from_date(date(1991, 11, 20)).z.value == 1     # 9+1 = 10 → 1


def test_regalo_divino_regla_del_cero():
    """1900: 0+0 = 0 → se desplaza un dígito y se toma 9+0 = 9."""
    p = Pinnacle.from_date(date(1900, 6, 15))
    assert p.z.value == 9


# --------------------------------------------------------------------------- #
# Etapas de vida
# --------------------------------------------------------------------------- #
def test_primera_etapa_dura_36_menos_d():
    p = Pinnacle.from_date(date(1991, 11, 20))      # D = 6
    assert p.stages[0].start_age == 0
    assert p.stages[0].end_age == 30                # 36 − 6
    assert p.stages[1].start_age == 30
    assert p.stages[1].end_age == 39
    assert p.stages[3].end_age is None              # la cuarta queda abierta


def test_primera_etapa_con_d_maestro_usa_la_base():
    """Éste es el bug del código en producción: 36 − 11 en vez de 36 − 2."""
    p = Pinnacle.from_date(date(1981, 10, 18))      # D = 11
    assert p.d.value == 11
    assert p.stages[0].end_age == 34, "con D=11 la 1.ª etapa dura 36−2 = 34 años"


def test_etapas_emparejan_realizacion_y_desafio():
    p = REF
    assert [s.realization.value for s in p.stages] == [p.e.value, p.f.value,
                                                       p.g.value, p.h.value]
    assert [s.challenge.value for s in p.stages] == [p.k.value, p.l.value,
                                                     p.m.value, p.n.value]


def test_etapa_vigente():
    p = REF
    stage = p.stage_at(date(2026, 7, 28))
    assert p.age_at(date(2026, 7, 28)) == 34        # cumple en noviembre
    assert stage.number == 2


def test_edad_antes_y_despues_del_cumple():
    p = REF
    assert p.age_at(date(2026, 11, 19)) == 34
    assert p.age_at(date(2026, 11, 20)) == 35


# --------------------------------------------------------------------------- #
# Bloque para el prompt
# --------------------------------------------------------------------------- #
def test_to_numbers_incluye_kármicos_y_ausencias():
    numbers = REF.to_numbers()
    assert numbers["B"] == "2"
    assert numbers["E"] == "4*"                     # el asterisco viaja al prompt
    assert numbers["T"] == "3, 5, 9"
    assert "W" not in numbers                       # pináculo especial
    assert "H_POTENCIAL" not in numbers             # aquí H está confirmado
    assert Pinnacle.from_date(date(1968, 7, 16)).to_numbers()["H_POTENCIAL"] == "22"


# --------------------------------------------------------------------------- #
# Informe de divergencias (no es una aserción)
# --------------------------------------------------------------------------- #
BOOK_EXAMPLES = [
    # (fecha, posición, valor del libro, de dónde sale)
    (date(1968, 7, 16), "E", 5,  "cap. VIII: 07 + 16 = 23 → 5 (crudos)"),
    (date(1968, 7, 16), "F", 22, "cap. VIII: 16 + 1968 = 1984 → 22 (crudos)"),
    (date(1968, 7, 16), "G", 9,  "cap. VIII: E + F = 5 + 22 = 27 → 9"),
    (date(1968, 7, 16), "I", 9,  "cap. VIII: E + F + G = 36 → 9"),
    (date(1968, 7, 16), "H", 4,  "cap. III: mes 7 + dígitos del año 24 = 31 → 4"),
]


def test_convencion_raw_reproduce_el_ejemplo_del_libro():
    """Con stage_convention="raw", F sale 22 como en el capítulo VIII."""
    p = Pinnacle.from_date(date(1968, 7, 16), stage_convention="raw")
    assert p.e.value == 5           # 7 + 16 = 23 → 5
    assert p.f.value == 22          # 16 + 1968 = 1984 → 22
    assert p.g.value == 9           # 5 + 22 = 27 → 9
    assert p.i.value == 9           # 5 + 22 + 9 = 36 → 9


def test_las_dos_convenciones_solo_difieren_en_maestros():
    """Fuera de los maestros, ambas vías dan lo mismo (congruencia mod 9)."""
    for birth in (date(1991, 11, 20), date(1981, 10, 18), date(1955, 10, 28)):
        v = Pinnacle.from_date(birth, stage_convention="vibration")
        r = Pinnacle.from_date(birth, stage_convention="raw")
        for key in ("E", "F"):
            a, b = v.as_positions()[key], r.as_positions()[key]
            assert a.value == b.value or 11 in (a.value, b.value) or 22 in (a.value, b.value), \
                f"{birth} {key}: {a} vs {b} difieren sin maestro de por medio"


def report_book_examples() -> int:
    """Compara las dos convenciones contra los ejemplos resueltos del libro."""
    print("\nInforme de convenciones — ejemplos resueltos del libro")
    print("-" * 78)
    print(f"  {'fecha':<12} {'pos':<4} {'vibración':>10} {'raw':>6} {'libro':>7}   fuente")
    divergences = 0
    for birth, key, expected, source in BOOK_EXAMPLES:
        v = Pinnacle.from_date(birth).as_positions()[key]
        r = Pinnacle.from_date(birth, stage_convention="raw").as_positions()[key]
        if v.value != expected:
            divergences += 1
        flag = " " if v.value == expected else "←"
        print(f"  {str(birth):<12} {key:<4} {str(v):>10}{flag} {str(r):>6} {expected:>7}   {source}")
    print("-" * 78)
    if divergences:
        print(f"{divergences} divergencia(s) con la convención por defecto.")
        print("La convención \"raw\" reproduce el libro; la \"vibration\" sigue el")
        print("diagrama oficial. Sólo difieren cuando aflora un maestro.")
        print("Pendiente de confirmar con Laura — ver pinaculo-formulas.md §10.")
    else:
        print("Sin divergencias.")
    return divergences


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    failures = 0
    print("Pruebas del Pináculo\n")
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

    report_book_examples()

    print()
    if failures:
        print(f"{failures} prueba(s) fallaron")
        sys.exit(1)
    print("Todas las pruebas pasaron OK")
