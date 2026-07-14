"""Reporte de etapas de vida — port de Stages.php."""

from __future__ import annotations

from .report_base import Report

# Posiciones (x1, y1, x2, y2) de la vibración de cada etapa en la página 2.
_STAGE_VIB = {
    1: (30, 103, 29, 103),
    2: (57, 90, 56, 90),
    3: (84, 82, 83, 82),
    4: (110, 80, 109, 80),
    5: (137, 82, 136, 82),
    6: (163, 90, 162, 90),
    7: (190, 103, 189, 103),
}
# Posiciones (x) de los rangos de años/edad por etapa.
_STAGE_RANGE_X = {1: 23, 2: 50, 3: 77, 4: 103, 5: 130, 6: 155, 7: 183}
_STAGE_AGE_X = {1: 25, 2: 50, 3: 77, 4: 103, 5: 130, 6: 155, 7: 183}


class Stages(Report):
    def set_stages(self, generic: bool = False) -> None:
        self.generic = generic
        self._page1()
        self._page2()
        self._page3()
        self._page4()
        self._page5()

    def _background_path(self, page: int) -> str:
        base = "etapa-vida-g" if self.generic else "etapa-vida"
        return f"{base}/{self.person.calc_stage()}/{page}"

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))
        self.font("opensans", "B", 15)
        self.set_color("white")
        self.text(32, 123, self.format_text(self.person.get_name(), uppercase=True))
        self.font("PassionOne", "", 60)
        self.set_color("main")
        self.text(180, 178, self.format_text(self.person.calc_stage(), uppercase=True))

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(40, 36, self.format_text(self.person.get_name(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.vibration_position(self.format_text(self.person.get_date(), uppercase=True), 75, 50, 74, 50)
        self.font("PassionOne", "", 60)
        self.set_color("main")
        self.text(178, 40, self.format_text(self.person.calc_stage(), uppercase=True))
        # Vibración de cada etapa
        self.set_color("main")
        self.font("PassionOne", "", 20)
        for stage, (x1, y1, x2, y2) in _STAGE_VIB.items():
            self.vibration_position(self.format_text(self.person.get_stage(stage), uppercase=True), x1, y1, x2, y2)
        # Rangos de años y edad
        self.font("opensans", "B", 10)
        for stage in range(1, 8):
            self.text(_STAGE_RANGE_X[stage], 117, self.format_text(self.person.get_stage_range(stage), uppercase=True))
            self.text(_STAGE_AGE_X[stage], 122, self.format_text(self.person.get_stage_age_range(stage), uppercase=True))

    def _page3(self) -> None:
        self.add_page()
        self.set_background(self._background_path(3))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(65, 34, self.format_text(self.person.calc_stage_range()))

    def _page4(self) -> None:
        self.add_page()
        self.set_background(self._background_path(4))

    def _page5(self) -> None:
        self.add_page()
        self.set_background(self._background_path(5))
