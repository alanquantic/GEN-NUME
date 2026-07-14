"""Reporte de pareja — port de Partner.php."""

from __future__ import annotations

from .report_base import Report


class Partner(Report):
    def set_partner(self, generic: bool = False, year_over: int = 0) -> None:
        self.generic = generic
        self.partner_year = self.person.calc_partner_year(year_over) if year_over else self.person.calc_partner_year()
        self._page1()
        self._page_bonus()
        self._page2()
        self._page3()
        self._page4()

    def _background_path(self, page) -> str:
        if self.generic:
            if page in (1, "bonus", 2026):
                return f"pareja-g/_{page}"
            return f"pareja-g/{self.partner_year}/{page}"
        return f"pareja/{self.partner_year}/{page}"

    def _page1(self) -> None:
        self.add_page()
        # El original usa la clave de página 2026 en ambas ramas.
        self.set_background(self._background_path(2026))
        self.font("opensans", "B", 15)
        self.set_color("white")
        self.text(32, 123, self.format_text(self.person.get_name(), uppercase=True))

    def _page_bonus(self) -> None:
        if not self.generic:
            return
        self.add_page()
        self.set_background(self._background_path("bonus"))
        self.draw_synastry_grid()

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))
        self._couple_header(22, 32, 55, 65)

    def _page3(self) -> None:
        self.add_page()
        self.set_background(self._background_path(3))

    def _page4(self) -> None:
        self.add_page()
        self.set_background(self._background_path(4))

    def _couple_header(self, y_name: float, y_date: float, y_pname: float, y_pdate: float) -> None:
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, y_name, self.format_text(self.person.get_name(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, y_date, self.format_text(self.person.get_date(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, y_pname, self.format_text(self.person.partner_name, uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, y_pdate, self.format_text(self.person.get_partner_date(), uppercase=True))
