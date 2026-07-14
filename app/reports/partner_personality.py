"""Reporte de personalidad de pareja — port de PartnerPersonality.php."""

from __future__ import annotations

from .report_base import Report


class PartnerPersonality(Report):
    def set_partner_personality(self, generic: bool = True) -> None:
        self.generic = generic
        self._page1()
        self._page2()
        self._page3()
        self._page4()

    def _background_path(self, page) -> str:
        if self.generic:
            if page in (1, 2, 3):
                return f"personalidad-pareja-g/_{page}"
            return f"personalidad-pareja-g/{self.person.synastry_d()}/{page}"
        return f"personalidad-pareja/{self.person.synastry_d()}/{page}"

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

    def _page4(self) -> None:
        self.add_page()
        self.set_background(self._background_path(4))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 22, self.format_text(self.person.get_name(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 32, self.format_text(self.person.get_date(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 57, self.format_text(self.person.partner_name, uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 67, self.format_text(self.person.get_partner_date(), uppercase=True))
