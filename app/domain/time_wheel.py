"""Datos del «círculo del tiempo»: cuatrimestres, meses y semanas personales.

Meses y semanas son port de `reports-pdf/src/Person.php` y `Universal.php`
(las mismas fórmulas que `domain.person`), con seguimiento de kármicos.

Los cuatrimestres son port de `sf-nume-ts/src/resources/Person.ts`
(getQuarterOne/Two/Three + getQuarterMonth, y sus variantes ISK):

  * El ciclo arranca en el MES DE NACIMIENTO (getCustomMonths) y se reparte
    5 + 4 + 3 meses:
      C1 = mes natal + 4 siguientes → C, vida pasada = reduce(año natal)
      C2 = 4 meses siguientes      → reduce(añoCiclo − D)  (D con 11→2, 22→4)
      C3 = 3 meses restantes       → reduce(C1 + C2)
  * añoCiclo = año calendario en que arrancó el ciclo: para los meses que caen
    después del cambio de año es `year − 1` (lógica indexEnero del original).
    Si C2/C3 cruzan enero dentro del mismo año calendario su valor cambia y el
    arco se parte (p. ej. nacidos en julio: C2 = DIC con un valor y ENE·MAR
    con otro).
"""

from __future__ import annotations

from datetime import date

from .numerology import reduce_number
from .pinnacle import reduce_tracked

MONTH_ABBR = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
              "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]


def month_data(ap: int, year: int) -> list[dict]:
    """Por mes: mes personal, mes universal y las 4 semanas personales."""
    uy = reduce_number(year)
    out = []
    for m in range(1, 13):
        mp = reduce_tracked(ap + m)
        mu = reduce_tracked(reduce_number(m) + uy)
        w1 = reduce_tracked(ap + m)
        w2 = reduce_tracked(ap + w1.value)
        w3 = reduce_tracked(w1.value + w2.value)
        w4 = reduce_tracked(m + w1.value)
        out.append({
            "abbr": MONTH_ABBR[m - 1],
            "mp": str(mp),
            "mu": str(mu),
            "weeks": [str(w1), str(w2), str(w3), str(w4)],
        })
    return out


def _norm_master(n: int) -> int:
    """normalizeMasterNumberForSubtraction de sf-nume-ts/utils/numbers.ts."""
    return {11: 2, 22: 4}.get(n, n)


def quarter_arcs(birth: date, wheel_year: int, current_month: int) -> list[dict]:
    """Arcos de cuatrimestre para la rueda del año `wheel_year`.

    Cada arco agrupa meses calendario contiguos (circularmente, desde el mes
    natal) que comparten cuatrimestre y valor: `start` es el índice de mes
    (0 = enero, puede superar 11 para conservar la continuidad circular),
    `span` cuántos meses cubre, `value` la vibración («n» o «n*» si kármica),
    `range` la etiqueta «ENE · MAY» y `active` si contiene el mes en curso.
    """
    d_pers = reduce_number(birth.day + birth.month + birth.year)
    q1 = reduce_tracked(birth.year)

    def month_quarter(m: int) -> tuple[int, str]:
        idx = (m - birth.month) % 12
        cycle_year = wheel_year - 1 if (m < birth.month and birth.month != 1) else wheel_year
        if idx < 5:
            return 1, str(q1)
        q2 = reduce_tracked(cycle_year - _norm_master(d_pers))
        if idx < 9:
            return 2, str(q2)
        q3 = reduce_tracked(reduce_number(birth.year) + q2.value)
        return 3, str(q3)

    arcs: list[dict] = []
    for k in range(12):
        m = (birth.month - 1 + k) % 12 + 1
        qn, val = month_quarter(m)
        if arcs and (arcs[-1]["q"], arcs[-1]["value"]) == (qn, val):
            arcs[-1]["span"] += 1
        else:
            arcs.append({"q": qn, "value": val, "start": birth.month - 1 + k, "span": 1})
    for a in arcs:
        first = MONTH_ABBR[a["start"] % 12]
        last = MONTH_ABBR[(a["start"] + a["span"] - 1) % 12]
        a["range"] = first if a["span"] == 1 else f"{first} · {last}"
        a["active"] = ((current_month - 1) - a["start"]) % 12 < a["span"]
    return arcs


__all__ = ["MONTH_ABBR", "month_data", "quarter_arcs"]
