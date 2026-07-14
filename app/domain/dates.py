"""Utilidades de fecha independientes de locale.

El original usaba Carbon con `setlocale(es_ES)` para obtener los nombres de mes
en español. Para no depender del locale del sistema (que en un contenedor de
Railway puede no estar instalado), resolvemos los nombres con un diccionario
explícito. Esto replica `month_esp()` de helpers.php y `formatLocalized('%B')`.
"""

from __future__ import annotations

from datetime import date, datetime

MONTHS_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def month_es(month: int) -> str:
    """Nombre del mes en español, minúsculas. Equivale a `month_esp()`."""
    return MONTHS_ES[int(month)]


def parse_birth_date(value: str | date) -> date:
    """Acepta 'YYYY-MM-DD' o un objeto date y devuelve `date`."""
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_long_date(value: str | date) -> str:
    """'20 noviembre 1991' — equivale a `Person::getDate()` del original."""
    d = parse_birth_date(value)
    return f"{d.day} {month_es(d.month)} {d.year}"
