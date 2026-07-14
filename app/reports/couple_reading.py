"""Reporte de lectura de pareja — port de CoupleReading.php. 11 secciones."""

from __future__ import annotations

from .report_base import Report


class CoupleReading(Report):
    def set_couple_reading(self, generic: bool = False) -> None:
        self.generic = generic
        self._page1()
        self._page2()
        self._page3()
        self._page4()
        self._page5()
        self._page6()
        self._page7()
        self._page8()
        self._page9()
        self._page10()
        self._page11()

    def _background_path(self, page, calc: str | None = None, calc_v=0) -> str:
        path = "lectura-pareja-g" if self.generic else "lectura-pareja"
        if calc:
            if page == 0:
                return f"{path}/{calc}/{calc_v}"
            return f"{path}/{calc}/{calc_v}/{page}"
        return f"{path}/_{page}"

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 77, self.format_text(self.person.get_name(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 87, self.format_text(self.person.get_date(), uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(85, 110, self.format_text(self.person.partner_name, uppercase=True))
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(123, 120, self.format_text(self.person.get_partner_date(), uppercase=True))

    def _page3(self) -> None:
        self.add_page()
        self.set_background(self._background_path(3))
        self.draw_synastry_grid()

    def _page4(self) -> None:
        self.add_page()
        self.set_background(self._background_path(4))

    def _page5(self) -> None:
        a = self.person.synastry_a()
        self.add_page()
        self.set_background(self._background_path(1, "A", a))
        self.add_page()
        self.set_background(self._background_path(2, "A", a))

    def _page6(self) -> None:
        self.add_page()
        self.set_background(self._background_path(6))

    def _page7(self) -> None:
        b = self.person.synastry_b()
        for p in (1, 2, 3):
            self.add_page()
            self.set_background(self._background_path(p, "B", b))

    def _page8(self) -> None:
        self.add_page()
        self.set_background(self._background_path(8))

    def _page9(self) -> None:
        c = self.person.synastry_c()
        self.add_page()
        self.set_background(self._background_path(1, "C", c))
        # 9.2 solo si la plantilla existe (intención del file_exists original)
        self.add_page_with_background_if_exists(self._background_path(2, "C", c))

    def _page10(self) -> None:
        self.add_page()
        self.set_background(self._background_path(10))

    def _page11(self) -> None:
        d = self.person.synastry_d()
        self.add_page()
        self.set_background(self._background_path(0, "D", d))
