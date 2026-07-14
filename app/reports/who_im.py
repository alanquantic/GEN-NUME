"""Reporte "¿Quién soy?" — port de `reports-pdf/src/reports/WhoIm.php`.

Sirve de PLANTILLA DE REFERENCIA para portar el resto de reportes: cada uno es
una clase que extiende Report, añade páginas con `add_page()` + fondo, y coloca
texto con coordenadas absolutas y `write_html` para los bloques largos.
"""

from __future__ import annotations

from ..content import get_text
from .report_base import Report


class WhoIm(Report):
    def set_who_im(self, generic: bool = False) -> None:
        self.generic = generic
        self._page1()
        self._page2()
        self._page3()

    def _background_path(self, page: int) -> str:
        if self.generic:
            return f"quien-soy-g/{self.person.personal_number()}/{page}"
        return f"quien-soy/{page}"

    def _page1(self) -> None:
        self.add_page()
        self.set_background(self._background_path(1))
        # Nombre
        self.font("opensans", "B", 15)
        self.set_color("white")
        self.text(32, 123, self.format_text(self.person.get_name(), uppercase=True))
        if not self.generic:
            # Número personal
            self.font("opensans", "B", 35)
            self.set_color("black")
            self.text(100, 210, self.format_text(self.person.personal_number()))

    def _page2(self) -> None:
        self.add_page()
        self.set_background(self._background_path(2))
        # Nombre
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(35, 30, self.format_text(self.person.get_name(), uppercase=True))
        # Fecha de nacimiento
        self.font("opensans", "B", 12)
        self.set_color("main")
        self.text(72, 40, self.format_text(self.person.get_date(), uppercase=True))
        if not self.generic:
            n = self.person.personal_number()
            # Número personal (grande)
            self.font("opensans", "B", 50)
            self.set_color("white")
            self.vibration_position(self.format_text(n), 168, 56, 163, 56)
            # Texto
            self.font("opensans", "", 8)
            self.set_color("black")
            self.write_html_at(85, self.format_text(get_text("getTextWhoIm1", n)))

    def _page3(self) -> None:
        self.add_page()
        self.set_background(self._background_path(3))
        if not self.generic:
            n = self.person.personal_number()
            self.font("opensans", "", 10)
            self.set_color("black")
            self.write_html_at(18, self.format_text(get_text("getTextWhoIm2", n)))
            self.font("opensans", "", 10)
            self.set_color("black")
            self.write_html_at(143, self.format_text(get_text("getTextWhoIm3", n)))
