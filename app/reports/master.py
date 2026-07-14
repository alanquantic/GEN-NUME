"""Reporte maestro (pareja) — port de Master.php. 7 páginas."""

from __future__ import annotations

from .report_base import Report


class Master(Report):
    def set_master(self, generic: bool = False) -> None:
        self.generic = generic
        self.partner_year = self.person.calc_partner_master()
        self._page1()
        self._page2()
        for page in range(3, 8):
            self.add_page()
            self.set_background(self._background_path(page))

    def _background_path(self, page) -> str:
        if self.generic:
            if page in (1, 2, 3):
                return f"maestro-g/_{page}"
            return f"maestro-g/{self.partner_year}/{page}"
        return f"maestro/{self.partner_year}/{page}"

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))
        self.font("opensans", "B", 15)
        self.set_color("white")
        self.text(32, 123, self.format_text(self.person.get_name(), uppercase=True))

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 20, self.format_text(self.person.get_name(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 30, self.format_text(self.person.get_date(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 55, self.format_text(self.person.partner_name, uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 65, self.format_text(self.person.get_partner_date(), uppercase=True))
        self.font("opensans", "EB", 38)
        self.set_color("main")
        self.text(30, 97, self.format_text(self.partner_year, uppercase=True))
