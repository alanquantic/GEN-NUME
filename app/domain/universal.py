"""Clase Universal: día/semana/mes "universal" (no dependen de la persona).

Port fiel de `reports-pdf/src/Universal.php`.
"""

from __future__ import annotations

from datetime import date

from .numerology import reduce_number


class Universal:
    def __init__(self, ref_date: date | None = None):
        self.date = ref_date or date.today()

    def universal_day(self, day: date | None = None) -> int:
        d = day or self.date
        year = reduce_number(d.year)
        return reduce_number(d.day + d.month + year)

    def universal_week(self, day: date | None = None) -> int:
        d = day or self.date
        month = reduce_number(d.month)
        year = reduce_number(d.year)

        week_one = reduce_number(month + year)
        if d.day < 8:
            return week_one
        week_two = reduce_number(week_one + year)
        if 7 < d.day < 15:
            return week_two
        week_three = reduce_number(week_one + week_two)
        if 14 < d.day < 22:
            return week_three
        return reduce_number(month + week_one)

    def universal_month(self, month_date: date | None = None) -> int:
        d = month_date or self.date
        month = reduce_number(d.month)
        year = reduce_number(d.year)
        return reduce_number(month + year)
