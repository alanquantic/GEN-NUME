"""Reporte "¿Quién soy?" extendido — port de WhoImExtended.php. 13 páginas."""

from __future__ import annotations

from .report_base import Report


class WhoImExtended(Report):
    def set_who_im_extended(self, generic: bool = False) -> None:
        self.generic = generic
        self._page1()
        for page in range(2, 14):
            self.add_page()
            self.set_background(self._background_path(page))

    def _background_path(self, page: int) -> str:
        if self.generic:
            return f"quien-soy-e/{self.person.personal_number()}/{page}"
        return f"quien-soy-e/{page}"

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))
        self.font("opensans", "B", 17)
        self.set_color("white")
        x = 63 + 15
        self.text(x, 140, self.format_text(self.person.get_name(), uppercase=True))
        self.text(x, 150, self.format_text(self.person.get_date(), uppercase=True))
        if not self.generic:
            self.font("opensans", "B", 35)
            self.set_color("black")
            self.text(100, 210, self.format_text(self.person.personal_number(), uppercase=True))
