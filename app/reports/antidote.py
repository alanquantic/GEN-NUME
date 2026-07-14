"""Reporte antídoto (pareja) — port de Antidote.php. Solo modo genérico."""

from __future__ import annotations

from .report_base import Report


class Antidote(Report):
    def set_antidote(self, generic: bool = True) -> None:
        self.generic = generic
        self._page1()
        self._page2()
        self._page3()
        self._page4()

    def _background_path(self, page) -> str | None:
        if self.generic:
            if page in (1, 2, 3):
                return f"antidoto-g/_{page}"
            return f"antidoto-g/{self.person.synastry_c()}/{page}"
        return None  # el original no define modo no-genérico

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))
        self.font("opensans", "B", 15)
        self.set_color("white")
        self.text(32, 123, self.format_text(self.person.get_name(), uppercase=True))

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))
        self.draw_synastry_grid()

    def _page3(self) -> None:
        self.add_page()
        self.set_background(self._background_path(3))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 215, self.format_text(self.person.get_name(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 225, self.format_text(self.person.get_date(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 248, self.format_text(self.person.partner_name, uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 258, self.format_text(self.person.get_partner_date(), uppercase=True))
        self.font("opensans", "B", 38)
        self.set_color("main")
        self.vibration_position(self.format_text(self.person.synastry_c(), uppercase=True), 28, 290.5, 24, 290.5)

    def _page4(self) -> None:
        self.add_page()
        self.set_background(self._background_path(4))
