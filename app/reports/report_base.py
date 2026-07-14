"""Clase base Report — equivalente a `reports-pdf/src/reports/Report.php`.

Mantiene helpers de conveniencia que delegan en ReportPDF, para que las clases
de reporte porten casi 1:1 desde el PHP original (`self.set_background(...)`,
`self.set_color(...)`, `self.pdf.text(...)`, etc.).
"""

from __future__ import annotations

from ..config import settings
from ..domain import Person
from ..pdf import ReportPDF

# Grilla de sinastría compartida por Partner, Wound, Antidote,
# PartnerPersonality y CoupleReading (coordenadas idénticas en el original).
# (letra, tamaño, x1, y1, x2, y2) — letra = sufijo del método person.synastry_*
SYNASTRY_GRID = [
    ("a", 10, 108, 106, 107, 106),
    ("b", 13, 135, 106, 133, 106),
    ("c", 10, 163.5, 106, 162.8, 106),
    ("d", 10, 182, 106, 181, 106),
    ("e", 10, 120, 84.5, 119, 84.5),
    ("i", 10, 135, 84.5, 133.8, 84.5),
    ("f", 10, 151, 84.5, 150, 84.5),
    ("g", 10, 135, 69.5, 133.5, 69.5),
    ("h", 10, 135, 53.5, 133.5, 53.5),
    ("j", 10, 172.5, 68.5, 171.5, 68.5),
    ("k", 10, 120, 126, 119, 126),
    ("o", 10, 135, 126, 133.8, 126),
    ("l", 10, 151, 126, 149.8, 126),
    ("m", 10, 135, 142.5, 133.8, 142.5),
    ("n", 10, 135, 158.5, 133.8, 158.5),
    ("q", 10, 120.5, 174.3, 119, 174.3),
    ("r", 10, 135, 174.3, 133.8, 174.3),
    ("s", 10, 150.5, 174.3, 149.5, 174.3),
    ("p", 10, 113.5, 158.5, 112.5, 158.5),
    ("w", 10, 107.5, 142.5, 106.2, 142.5),
]


class Report:
    def __init__(self, person: Person):
        self.person = person
        self.pdf = ReportPDF()
        self.generic: bool = False

    # -- helpers que reflejan la API del original ---------------------- #
    def add_page(self) -> None:
        self.pdf.add_page()

    def set_background(self, rel_path: str, ext: str = "jpg") -> None:
        self.pdf.set_background(rel_path, ext)

    def background_exists(self, rel_path: str, ext: str = "jpg") -> bool:
        base = settings.report_templates_dir / rel_path
        return any(base.with_name(f"{base.name}.{e}").exists() for e in (ext, "jpg", "png", "jpeg"))

    def add_page_with_background_if_exists(self, rel_path: str, ext: str = "jpg") -> bool:
        """Agrega página solo si la plantilla existe (usado por CoupleReading).

        En el original el `file_exists` comprobaba una ruta sin prefijo ni
        extensión (siempre falso); aquí se comprueba el asset real, que es la
        intención."""
        if not self.background_exists(rel_path, ext):
            return False
        self.add_page()
        self.set_background(rel_path, ext)
        return True

    def draw_synastry_grid(self) -> None:
        """Dibuja la grilla de sinastría A–W (blanco) compartida por varios reportes."""
        for letter, size, x1, y1, x2, y2 in SYNASTRY_GRID:
            value = getattr(self.person, f"synastry_{letter}")()
            self.font("opensans", "B", size)
            self.set_color("white")
            self.vibration_position(self.format_text(value, uppercase=True), x1, y1, x2, y2)

    def set_color(self, key: object) -> None:
        self.pdf.set_color(key)

    def font(self, family: str, style: str, size: float) -> None:
        self.pdf.report_font(family, style, size)

    def format_text(self, text: object, uppercase: bool = False) -> str:
        return self.pdf.format_text(text, uppercase)

    def text(self, x: float, y: float, s: str) -> None:
        self.pdf.text(x, y, s)

    def vibration_position(self, vibration, x1, y1, x2, y2) -> None:
        self.pdf.vibration_position(vibration, x1, y1, x2, y2)

    def write_html_at(self, y: float, html: str) -> None:
        self.pdf.write_html_at(y, html)

    def multi_cell(self, x: float, y: float, w: float, h: float, text: str, align: str = "C") -> None:
        self.pdf.multi_cell_at(x, y, w, h, text, align)

    def multi_cell_here(self, w: float, h: float, text: str, align: str = "C") -> None:
        self.pdf.multi_cell_here(w, h, text, align)

    def write_tag(self, html: str, x: float, y: float, size: float = 12, align: str = "J") -> None:
        self.pdf.write_tag(html, x, y, size, align)

    def set_xy(self, x: float, y: float) -> None:
        self.pdf.set_xy(x, y)

    def get_x(self) -> float:
        return self.pdf.get_x()

    def get_y(self) -> float:
        return self.pdf.get_y()

    def output(self) -> bytes:
        """Devuelve el PDF como bytes (sin tocar el sistema de archivos)."""
        return bytes(self.pdf.output())
