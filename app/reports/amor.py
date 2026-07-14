"""Reporte amor / año personal — port de Amor.php."""

from __future__ import annotations

from .report_base import Report


class Amor(Report):
    def set_amor(self, generic: bool = False) -> None:
        self.generic = generic
        self.personal_year = self.person.personal_year()
        self._page1()
        self._page2()
        self._page3()
        self._page4()

    def _background_path(self, page: int) -> str:
        return f"amor/{self.personal_year}/{page}"

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))

    def _page3(self) -> None:
        self.add_page()
        self.set_background(self._background_path(3))

    def _page4(self) -> None:
        # En el original la condición usa `$this->partnerYear`, propiedad que
        # NUNCA se asigna en Amor -> la página 4 nunca se renderiza. Se replica
        # ese comportamiento. Para habilitarla con la intención probable
        # (año personal 6 u 11) usar: if self.personal_year in (6, 11): ...
        return
