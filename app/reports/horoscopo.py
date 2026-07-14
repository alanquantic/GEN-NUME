"""Reporte horóscopo — port de Horoscopo.php. 7 páginas de fondo."""

from __future__ import annotations

from .report_base import Report


class Horoscopo(Report):
    def set_horoscopo(self, generic: bool = False) -> None:
        self.generic = generic
        for page in range(1, 8):
            self.add_page()
            self.set_background(self._background_path(page))

    def _background_path(self, page: int) -> str:
        return f"horoscopo/{self.person.personal_year()}/{page}"
