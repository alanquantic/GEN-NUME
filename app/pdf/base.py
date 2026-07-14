"""ReportPDF: subclase de fpdf2 con las utilidades comunes de los reportes.

fpdf2 es un port de FPDF, por lo que el sistema de coordenadas es idéntico al
original (milímetros, A4 = 210 x 298) y las llamadas `text(x, y, s)` colocan el
texto en la misma posición. Ventajas sobre el original:

  * `write_html()` viene incluido → se eliminan las clases HTMLinPDF y
    PDF_WriteTag del proyecto original.
  * Fuentes TTF unicode nativas → se elimina el `utf8_decode` y los problemas
    de acentos. El texto se pasa tal cual en UTF-8.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fpdf import FPDF

from ..config import settings

logger = logging.getLogger("reportpdf")

# Fuentes unicode del sistema para usar como reserva si faltan las TTF de marca.
# Evita que la app truene con acentos/comillas cuando aún no se cargan los
# assets del cliente (dev, CI, primer arranque en Railway).
_FALLBACK_CANDIDATES = [
    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf",
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
]


def _find_fallback_font() -> Path | None:
    for candidate in _FALLBACK_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


# El aviso de fuentes faltantes se emite una sola vez por proceso.
_font_warning_emitted = False

PAGE_W = 210
PAGE_H = 298  # el original dibuja los fondos a 298mm (A4 real = 297)

# Paleta de colores por "vibración", portada de Report.php::setColor().
COLORS: dict[object, tuple[int, int, int]] = {
    "main": (51, 2, 51),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "blue": (39, 70, 111),
    "gray": (111, 110, 111),
    1: (199, 6, 4),
    2: (253, 130, 0),
    3: (229, 160, 6),
    4: (106, 196, 43),
    5: (13, 170, 226),
    6: (13, 0, 106),
    7: (123, 1, 106),
    8: (239, 52, 125),
    9: (177, 126, 73),
    11: (97, 97, 96),
    22: (56, 85, 101),
}

# Fuente lógica (familia, estilo) -> (familia fpdf, estilo fpdf, archivo .ttf).
# Los estilos EB/SB/EBI no son estilos estándar de fpdf2, así que se registran
# como familias propias.
FONT_MAP: dict[tuple[str, str], tuple[str, str, str]] = {
    ("opensans", ""):   ("opensans", "", "OpenSans-Regular.ttf"),
    ("opensans", "B"):  ("opensans", "B", "OpenSans-Bold.ttf"),
    ("opensans", "I"):  ("opensans", "I", "OpenSans-Italic.ttf"),
    ("opensans", "BI"): ("opensans", "BI", "OpenSans-BoldItalic.ttf"),
    ("opensans", "SB"): ("opensans-sb", "", "OpenSans-SemiBold.ttf"),
    ("opensans", "EB"): ("opensans-eb", "", "OpenSans-ExtraBold.ttf"),
    ("opensans", "EBI"): ("opensans-eb", "I", "OpenSans-ExtraBoldItalic.ttf"),
    ("PassionOne", ""): ("PassionOne", "", "PassionOne-Regular.ttf"),
    ("LazyDog", ""):    ("LazyDog", "", "LazyDog.ttf"),
}


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(False)
        self.set_margins(left=12, top=10, right=12)
        self._registered: set[tuple[str, str]] = set()
        self._register_fonts()
        self.report_font("opensans", "", 12)
        self.set_text_color(0, 0, 0)

    # ------------------------------------------------------------------ #
    # Fuentes
    # ------------------------------------------------------------------ #
    def _register_fonts(self) -> None:
        fonts_dir: Path = settings.fonts_dir
        missing: list[tuple[str, str, str]] = []
        for (fpdf_family, fpdf_style, filename) in FONT_MAP.values():
            if (fpdf_family, fpdf_style) in self._registered:
                continue
            path = fonts_dir / filename
            if not path.exists():
                missing.append((fpdf_family, fpdf_style, filename))
                continue
            self.add_font(family=fpdf_family, style=fpdf_style, fname=str(path))
            self._registered.add((fpdf_family, fpdf_style))

        if missing:
            global _font_warning_emitted
            fallback = _find_fallback_font()
            names = ", ".join(sorted({m[2] for m in missing}))
            if fallback is not None:
                # Registrar las combinaciones faltantes con la fuente unicode
                # de reserva para que el render no falle con acentos.
                for fpdf_family, fpdf_style, _ in missing:
                    self.add_font(family=fpdf_family, style=fpdf_style, fname=str(fallback))
                    self._registered.add((fpdf_family, fpdf_style))
                if not _font_warning_emitted:
                    logger.warning(
                        "Fuentes TTF faltantes en %s (%s). Usando reserva unicode: %s. "
                        "Coloca los .ttf de marca para el render final.",
                        fonts_dir, names, fallback.name,
                    )
                    _font_warning_emitted = True
            elif not _font_warning_emitted:
                logger.warning(
                    "Fuentes TTF faltantes en %s: %s y sin reserva unicode. "
                    "El texto con acentos puede fallar.",
                    fonts_dir, names,
                )
                _font_warning_emitted = True

    def report_font(self, family: str, style: str, size: float) -> None:
        """Selecciona fuente usando los nombres lógicos del original."""
        fpdf_family, fpdf_style, _ = FONT_MAP.get(
            (family, style), ("opensans", "", "")
        )
        if (fpdf_family, fpdf_style) in self._registered:
            self.set_font(fpdf_family, fpdf_style, size)
        elif ("opensans", "") in self._registered:
            self.set_font("opensans", "", size)
        else:
            self.set_font("helvetica", "", size)

    # ------------------------------------------------------------------ #
    # Color / fondo / texto
    # ------------------------------------------------------------------ #
    def set_color(self, key: object) -> None:
        r, g, b = COLORS.get(key, (255, 255, 255))
        self.set_text_color(r, g, b)

    def set_background(self, rel_path: str, ext: str = "jpg") -> None:
        """Dibuja el fondo de página completa.

        Robusto: prueba la extensión dada y luego jpg/png/jpeg (resuelve que
        algunas plantillas del original estén en .jpg aunque el código pidiera
        .png). Si no encuentra el archivo, registra un aviso y continúa sin
        fondo en vez de tumbar el reporte con un 500.
        """
        base = settings.report_templates_dir / rel_path
        for e in dict.fromkeys([ext, "jpg", "png", "jpeg"]):
            candidate = base.with_name(f"{base.name}.{e}")
            if candidate.exists():
                self.image(str(candidate), x=0, y=0, w=PAGE_W, h=PAGE_H)
                return
        logger.warning("Fondo no encontrado: %s (.%s) — página sin fondo", rel_path, ext)

    @staticmethod
    def format_text(text: object, uppercase: bool = False) -> str:
        s = str(text)
        return s.upper() if uppercase else s

    def write_html_at(self, y: float, html: str) -> None:
        self.set_y(y)
        self.write_html(html)

    def multi_cell_at(self, x: float, y: float, w: float, h: float, text: str, align: str = "C") -> None:
        """Equivale a setXY(x,y) + MultiCell(w,h,text,0,align) del original."""
        self.set_xy(x, y)
        self.multi_cell(w, h, text=text, align=align)

    def multi_cell_here(self, w: float, h: float, text: str, align: str = "C") -> None:
        """MultiCell en la posición actual (sin resetear x/y)."""
        self.multi_cell(w, h, text=text, align=align)

    def write_tag(self, html: str, x: float, y: float, size: float = 12, align: str = "J") -> None:
        """Aproxima WriteTag/SetStyle del PDF_WriteTag original usando write_html.

        write_html interpreta <p>, <b>, <ul>, <li>, <h1>, <h4>, <em>, <i>. La
        tipografía fina (pesos EB/SB) es trabajo de calibración con las TTF de
        marca; el contenido y el flujo se respetan.
        """
        self.report_font("opensans", "", size)
        self.set_text_color(0, 0, 0)
        self.set_xy(x, y)
        self.write_html(html)

    def vibration_position(self, vibration, x1, y1, x2, y2) -> None:
        """Un dígito vs. dos dígitos (11/22) se colocan en distinta X."""
        if len(str(vibration)) == 1:
            self.text(x1, y1, str(vibration))
        else:
            self.text(x2, y2, str(vibration))
