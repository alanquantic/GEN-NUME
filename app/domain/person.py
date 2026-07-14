"""Clase Person: todos los cálculos numerológicos de una persona.

Port fiel de `reports-pdf/src/Person.php`. Los nombres de método se mantienen
cercanos al original (en snake_case) para facilitar el cotejo 1:1.

Nota sobre "hoy": el original usaba `Carbon::now()` dentro de cada método. Aquí
inyectamos `today` en el constructor (por defecto la fecha actual) para poder
generar reportes deterministas y testear sin depender del reloj del sistema.
"""

from __future__ import annotations

from datetime import date

from .dates import format_long_date, parse_birth_date
from .numerology import reduce_number, reduce_number_for_sub

# Valores de letra por sistema pitagórico usado en el original.
_VOWEL_VALUES = {"a": 1, "e": 5, "i": 9, "o": 6, "u": 3}
_CONSONANT_VALUES = {
    "b": 2, "c": 3, "d": 4, "f": 6, "g": 7, "h": 8, "j": 1, "k": 11,
    "l": 3, "m": 4, "n": 5, "p": 7, "q": 8, "r": 9, "s": 1, "t": 2,
    "v": 22, "w": 5, "x": 6, "y": 7, "z": 8,
}
# `letterValue()` combina vocales + consonantes e incluye la ñ.
_LETTER_VALUES = {**_VOWEL_VALUES, **_CONSONANT_VALUES, "ñ": 5}


class Person:
    def __init__(
        self,
        name: str,
        birth_date: str | date,
        name_sanitize: str | None = None,
        today: date | None = None,
    ):
        self.name = name
        self.birth_date = parse_birth_date(birth_date)
        self.name_sanitize = name_sanitize
        self.today = today or date.today()
        self.partner_name: str | None = None
        self.partner_birth_date: date | None = None

    # ------------------------------------------------------------------ #
    # Datos básicos
    # ------------------------------------------------------------------ #
    def get_name(self) -> str:
        return self.name

    def get_date(self) -> str:
        return format_long_date(self.birth_date)

    def set_sanitize_name(self, value: str) -> None:
        self.name_sanitize = value

    def get_sanitize_name(self) -> str:
        if self.name_sanitize is None:
            raise ValueError("name_sanitize no definido para esta persona")
        return self.name_sanitize

    def set_partner(self, partner_name: str, partner_birth_date: str | date) -> None:
        self.partner_name = partner_name
        self.partner_birth_date = parse_birth_date(partner_birth_date)

    def get_partner_date(self) -> str:
        return format_long_date(self._require_partner())

    # ------------------------------------------------------------------ #
    # Números personales
    # ------------------------------------------------------------------ #
    def personal_number(self) -> int:
        return reduce_number(self.birth_date.day)

    def personal_year(self, year: int = 0) -> int:
        if year == 0:
            year = self.today.year
        return reduce_number(self.birth_date.day + self.birth_date.month + year)

    def personal_month(self, month_date: date | None = None) -> int:
        if month_date is None:
            month_date = self.today
        base = reduce_number(month_date.year + self.birth_date.month + self.birth_date.day)
        return reduce_number(base + month_date.month)

    def personal_day(self, day_date: date | None = None) -> int:
        if day_date is None:
            day_date = self.today
        return reduce_number(self.personal_year() + day_date.day + day_date.month)

    def personal_week(self, week_date: date | None = None) -> int:
        if week_date is None:
            week_date = self.today
        personal_year = self.personal_year()
        month = week_date.month
        week_one = reduce_number(personal_year + month)
        if 1 <= week_date.day <= 7:
            return week_one
        week_two = reduce_number(personal_year + week_one)
        if 8 <= week_date.day <= 14:
            return week_two
        week_three = reduce_number(week_two + week_one)
        if 15 <= week_date.day <= 21:
            return week_three
        return reduce_number(month + week_one)  # 22+

    # ------------------------------------------------------------------ #
    # Etapas de vida
    # ------------------------------------------------------------------ #
    def _stages_timeline(self) -> list[dict]:
        day = self.birth_date.day
        month = self.birth_date.month
        year = self.birth_date.year

        reduce_sum = reduce_number(day + month + year)
        stage_one = reduce_number(month + day)
        stage_two = reduce_number(day + year)
        stage_thr = reduce_number(stage_one + stage_two)
        stage_fou = reduce_number(month + year)

        first_stage_length = 36 - reduce_sum
        stage_years = [
            (stage_one, first_stage_length),
            (stage_two, 9),
            (stage_thr, 9),
            (stage_fou, 9),
            (stage_thr, 9),
            (stage_two, 9),
            (stage_one, None),
        ]

        timeline: list[dict] = []
        start_year = year
        start_age = 0
        for index, (value, length) in enumerate(stage_years):
            end_year = None if length is None else start_year + length - 1
            end_age = None if length is None else start_age + length - 1
            timeline.append(
                {
                    "stage": index + 1,
                    "value": value,
                    "start_year": start_year,
                    "end_year": end_year,
                    "start_age": start_age,
                    "end_age": end_age,
                }
            )
            if length is not None:
                start_year = end_year + 1
                start_age = end_age + 1
        return timeline

    def _stage_data(self, stage: int) -> dict:
        timeline = self._stages_timeline()
        index = stage - 1
        return timeline[index] if 0 <= index < len(timeline) else timeline[0]

    def calc_stage(self, year: int = 0) -> int:
        if year == 0:
            year = self.today.year
        for s in self._stages_timeline():
            if year >= s["start_year"] and (s["end_year"] is None or year <= s["end_year"]):
                return s["value"]
        return self._stages_timeline()[0]["value"]

    def calc_stage_range(self, year: int = 0) -> str:
        """Rango de años (' al ') de la etapa vigente en `year` (hoy por defecto)."""
        if year == 0:
            year = self.today.year
        for s in self._stages_timeline():
            if year >= s["start_year"] and (s["end_year"] is None or year <= s["end_year"]):
                return self._format_year_range(s)
        return self._format_year_range(self._stages_timeline()[0])

    def get_stage(self, stage: int = 1) -> int:
        return self._stage_data(stage)["value"]

    def get_stage_range(self, stage: int = 1) -> str:
        return self._format_year_range(self._stage_data(stage), "-")

    def get_stage_age_range(self, stage: int = 1) -> str:
        return self._format_age_range(self._stage_data(stage))

    @staticmethod
    def _format_year_range(stage_data: dict, separator: str = " al ") -> str:
        if stage_data["end_year"] is None:
            return f"{stage_data['start_year']}{separator}..."
        return f"{stage_data['start_year']}{separator}{stage_data['end_year']}"

    @staticmethod
    def _format_age_range(stage_data: dict) -> str:
        if stage_data["end_age"] is None:
            return f"{stage_data['start_age']} - ..."
        return f"{stage_data['start_age']} - {stage_data['end_age'] + 1}"

    # ------------------------------------------------------------------ #
    # Alma / expresión / desarrollo profesional (requieren name_sanitize)
    # ------------------------------------------------------------------ #
    def _sanitized_letters(self) -> list[str]:
        return list(self.get_sanitize_name().replace("-", ""))

    def get_soul_number(self) -> int:
        total = sum(_VOWEL_VALUES.get(ch, 0) for ch in self._sanitized_letters())
        return reduce_number(total)

    def calc_soul_expression_number(self) -> int:
        total = sum(_CONSONANT_VALUES.get(ch, 0) for ch in self._sanitized_letters())
        return reduce_number(total)

    def calculate_years(self) -> int:
        """Edad en años (diferencia de años, como el original)."""
        return self.today.year - self.birth_date.year

    def get_professional_development(self) -> dict:
        letters = self._sanitized_letters()
        years = self.calculate_years()

        development: list[dict] = []
        for ch in letters:
            value = _LETTER_VALUES.get(ch, 0)
            for i in range(1, value + 1):
                development.append({"num": i, "deno": value, "char": ch.upper()})

        item = development[years]
        return {
            "binomie": f"{reduce_number(item['num'])}/{item['deno']}",
            "letter": item["char"],
        }

    # ------------------------------------------------------------------ #
    # Pareja
    # ------------------------------------------------------------------ #
    def _require_partner(self) -> date:
        if self.partner_birth_date is None:
            raise ValueError("La pareja no ha sido definida (set_partner)")
        return self.partner_birth_date

    def calc_partner_year(self, year: int = 0) -> int:
        p = self._require_partner()
        composite_day = self.birth_date.day + p.day
        composite_month = self.birth_date.month + p.month
        if year == 0:
            year = self.today.year
        return reduce_number(year + composite_day + composite_month)

    def calc_partner_master(self) -> int:
        p = self._require_partner()
        partner_personal = reduce_number(p.day)
        return reduce_number(self.personal_number() + partner_personal)

    # -- Sinastría A..J (suma) ----------------------------------------- #
    def synastry_a(self) -> int:
        return reduce_number(self.birth_date.month + self._require_partner().month)

    def synastry_b(self) -> int:
        return reduce_number(self.birth_date.day + self._require_partner().day)

    def synastry_c(self) -> int:
        return reduce_number(self.birth_date.year + self._require_partner().year)

    def synastry_d(self) -> int:
        return reduce_number(self.synastry_a() + self.synastry_b() + self.synastry_c())

    def synastry_e(self) -> int:
        return reduce_number(self.synastry_a() + self.synastry_b())

    def synastry_f(self) -> int:
        return reduce_number(self.synastry_c() + self.synastry_b())

    def synastry_g(self) -> int:
        return reduce_number(self.synastry_e() + self.synastry_f())

    def synastry_h(self) -> int:
        return reduce_number(self.synastry_a() + self.synastry_c())

    def synastry_i(self) -> int:
        return reduce_number(self.synastry_e() + self.synastry_f() + self.synastry_g())

    def synastry_j(self) -> int:
        return reduce_number(self.synastry_h() + self.synastry_d())

    # -- Sinastría A'..C' (para restas) -------------------------------- #
    def synastry_as(self) -> int:
        return reduce_number_for_sub(self.birth_date.month + self._require_partner().month)

    def synastry_bs(self) -> int:
        return reduce_number_for_sub(self.birth_date.day + self._require_partner().day)

    def synastry_cs(self) -> int:
        return reduce_number_for_sub(self.birth_date.year + self._require_partner().year)

    # -- Sinastría K..W (resta / vibración menor) ---------------------- #
    def synastry_k(self) -> int:
        return abs(reduce_number(self.synastry_as() - self.synastry_bs()))

    def synastry_l(self) -> int:
        return abs(reduce_number(self.synastry_bs() - self.synastry_cs()))

    def synastry_m(self) -> int:
        return abs(reduce_number(self.synastry_k() - self.synastry_l()))

    def synastry_n(self) -> int:
        return abs(reduce_number(self.synastry_as() - self.synastry_cs()))

    def synastry_o(self) -> int:
        return reduce_number(self.synastry_m() + self.synastry_k() + self.synastry_l())

    def synastry_p(self) -> int:
        return reduce_number(self.synastry_d() + self.synastry_o())

    def synastry_q(self) -> int:
        return reduce_number(self.synastry_m() + self.synastry_k())

    def synastry_r(self) -> int:
        return reduce_number(self.synastry_m() + self.synastry_l())

    def synastry_s(self) -> int:
        return reduce_number(self.synastry_q() + self.synastry_r())

    def synastry_w(self):
        lower = [
            self.synastry_k(), self.synastry_l(), self.synastry_m(),
            self.synastry_n(), self.synastry_o(), self.synastry_p(),
            self.synastry_q(), self.synastry_r(), self.synastry_s(),
        ]
        occurrences: dict[int, int] = {}
        for v in lower:
            occurrences[v] = occurrences.get(v, 0) + 1
        for k, v in occurrences.items():
            if v == 3:
                return reduce_number(k * 3)
        return "-"
