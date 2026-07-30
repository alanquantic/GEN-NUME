"""Renderiza un reporte dinámico: JSON (fase 4) + números → HTML → PDF.

La generación de HTML es pura y testeable en cualquier sistema. El paso final a
PDF usa WeasyPrint, que en el deploy (Linux/Docker) funciona con cuatro paquetes
de sistema; en Windows suele fallar al importar (faltan libs nativas), así que
`to_pdf` da un error claro y `render_html` sigue siendo utilizable por sí solo.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ..ai.numbers import Numbers
from . import charts

_DIR = Path(__file__).resolve().parent / "html_report"

# Color de área por reporte (tokens del sitio → hex).
AREA_HEX = {
    "primary": "#4C1D95",
    "area-amor": "#EC4899",
    "area-trabajo": "#3B82F6",
    "area-bienestar": "#059669",
    "area-espiritual": "#A855F7",
}

# Etiqueta corta de cada clave para la ficha y el margen.
_LABEL = {
    "B": ("Esencia", "número personal · el día"),
    "A": ("Karma", "el mes · tu clan"),
    "C": ("Vida pasada", "el año"),
    "D": ("Personalidad", "tu máscara"),
    "H": ("Destino", "a dónde vas"),
    "I": ("Subconsciente", "tu brújula"),
    "J": ("Espejo", "lo que te atrae"),
    "P": ("Sombra", "tu punto ciego"),
    "ALMA": ("Alma", "vocales del nombre"),
    "EXPRESION": ("Expresión", "consonantes"),
    "NOMBRE": ("Nombre", "todas las letras"),
    "Z": ("Regalo divino", "tu don"),
    "Y": ("Misión", "tu síntesis"),
    "X": ("Reacción", "cómo te ven"),
    "AP": ("Año personal", "tu año en curso"),
    "MADUREZ": ("Madurez", "la segunda mitad"),
    "PAREJA": ("Pareja", "la unión"),
}

# Qué claves muestra la ficha de cada reporte (en orden), si existen.
_FICHA = {
    "quien-soy": ["B", "A", "C", "D", "H", "I", "J", "P", "ALMA", "Z"],
    "amor": ["B", "J", "ALMA", "AP", "PAREJA", "A", "D", "P"],
    "trabajo": ["B", "H", "D", "EXPRESION", "NOMBRE", "AP", "Z"],
    "bienestar": ["B", "D", "P", "X", "A", "ALMA", "AP"],
    "proposito": ["B", "ALMA", "H", "MADUREZ", "Y", "Z", "D", "A"],
}

LEGAL_BASE = (
    "Este reporte está redactado a partir del método y los textos de "
    "Numerología Cotidiana de Laura L. Rodríguez. La numerología es una "
    "herramienta de autoconocimiento; sus interpretaciones no sustituyen el "
    "criterio profesional en ninguna materia."
)
LEGAL_BIENESTAR = (
    " Este contenido trata de energía, hábitos y bienestar general, y no "
    "constituye diagnóstico, consejo ni tratamiento médico o psicológico. "
    "Ante cualquier síntoma, consulta a un profesional de la salud."
)


@lru_cache(maxsize=1)
def _env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    return Environment(
        loader=FileSystemLoader(str(_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )


@lru_cache(maxsize=1)
def _css() -> str:
    return (_DIR / "report.css").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
def _ficha(report_key: str, numbers: Numbers) -> list[dict]:
    out = []
    for key in _FICHA.get(report_key, []):
        val = numbers.get(key)
        if not val or val == "0":
            continue
        title, sub = _LABEL.get(key, (key, ""))
        out.append({"value": val, "title": title, "sub": sub,
                    "karmic": val.endswith("*")})
    return out


def _numbers_note(numbers: Numbers) -> str:
    pin = numbers.pinnacle
    bits = []
    if pin.karmic_debts:
        bits.append('<span class="star">*</span> Los números marcados son '
                    '<b>kármicos</b>: deudas que este camino viene a saldar.')
    if pin.h_alternative is not None:
        bits.append(f'Tu destino puede vivirse como <b>{pin.h}</b> o elevarse a '
                    f'su vibración maestra <b>{pin.h_alternative}</b>.')
    if pin.absences:
        aus = ", ".join(str(a) for a in pin.absences)
        bits.append(f'Te faltan las vibraciones <b>{aus}</b>: tus tareas por integrar.')
    return " ".join(bits)


def _charts(report_key: str, numbers: Numbers, today_age: int, area: str) -> list[dict]:
    pin = numbers.pinnacle
    out: list[dict] = []

    def add(eyebrow, title, svg, caption=""):
        if svg:
            out.append({"eyebrow": eyebrow, "title": title, "svg": svg,
                        "caption": caption})

    if report_key == "quien-soy":
        cap = ""
        if pin.special_pinnacle:
            cap = ("Tu zona inferior está llena de ceros: es un <b>Pináculo "
                   "Especial</b>, con la energía de los desafíos volcada hacia "
                   "lo colectivo.")
        add("Tu pináculo personal", "Un mapa que no cambia jamás",
            charts.pinnacle_svg(pin), cap)
        add("El poder de tu nombre", "Cada letra, una vibración",
            charts.name_strip_svg(numbers.name_sanitize, numbers.get("ALMA"),
                                  numbers.get("EXPRESION")))
    elif report_key == "proposito":
        add("Tu línea de vida", "Tus cuatro etapas",
            charts.stages_svg(pin, today_age, area))
        add("Tu pináculo", "El mapa completo", charts.pinnacle_svg(pin))
    elif report_key == "trabajo":
        add("La energía de tu año", "Dónde estás en el ciclo",
            charts.personal_year_svg(numbers.get("AP"), area))
        add("El poder de tu nombre", "Tu canal de expresión",
            charts.name_strip_svg(numbers.name_sanitize, numbers.get("ALMA"),
                                  numbers.get("EXPRESION")))
    elif report_key == "amor":
        add("La energía de tu año", "Tu amor en el ciclo",
            charts.personal_year_svg(numbers.get("AP"), area))
    elif report_key == "bienestar":
        add("Presencias y ausencias", "Lo que te sobra y lo que te falta",
            charts.absences_svg(pin, area))
        add("La energía de tu año", "Cómo cuidarte este año",
            charts.personal_year_svg(numbers.get("AP"), area))
    return out


def _sec_rail(data: dict, numbers: Numbers) -> list[dict | None]:
    rails = []
    for sec in data.get("secciones", []):
        keys = sec.get("numeros") or []
        rail = None
        for k in keys:
            key = str(k).upper().rstrip("*")
            val = numbers.get(key)
            if val:
                label = _LABEL.get(key, (key, ""))[0]
                rail = {"value": val, "label": label}
                break
        rails.append(rail)
    return rails


def _tension_orbs(data: dict, numbers: Numbers) -> list[str]:
    keys = data.get("tension_central", {}).get("numeros", [])[:2]
    return [numbers.get(str(k).upper().rstrip("*")) or str(k) for k in keys]


# --------------------------------------------------------------------------- #
def render_html(report_key: str, data: dict, numbers: Numbers, *,
                report_title: str, area_token: str,
                person_name: str, birth_long: str, today_long: str,
                today_age: int) -> str:
    area = AREA_HEX.get(area_token, AREA_HEX["primary"])
    legal = LEGAL_BASE + (LEGAL_BIENESTAR if report_key == "bienestar" else "")

    ctx = {
        "css": _css(),
        "data": data,
        "report_title": report_title,
        "area_hex": area,
        "person_name": person_name,
        "birth_long": birth_long,
        "today_long": today_long,
        "cover_number": numbers.get("B") or "",
        "numbers_ficha": _ficha(report_key, numbers),
        "numbers_note": _numbers_note(numbers),
        "charts": _charts(report_key, numbers, today_age, area),
        "sec_rail": _sec_rail(data, numbers),
        "tension_orbs": _tension_orbs(data, numbers),
        "legal": legal,
    }
    return _env().get_template("report.html.j2").render(**ctx)


def to_pdf(html: str) -> bytes:
    """Renderiza el HTML a PDF con WeasyPrint.

    Falla con un mensaje claro si WeasyPrint no puede cargar sus librerías
    nativas (caso típico en Windows sin GTK). En Docker/Railway funciona con
    libpango, libpangoft2, libharfbuzz y libgdk-pixbuf instalados.
    """
    try:
        from weasyprint import HTML
    except OSError as exc:  # libs nativas ausentes
        raise RuntimeError(
            "WeasyPrint no pudo cargar sus librerías nativas (Pango/Cairo). "
            "En Windows es lo esperado; el PDF se genera en el deploy Linux. "
            f"Detalle: {exc}"
        ) from exc
    return HTML(string=html).write_pdf()


__all__ = ["render_html", "to_pdf", "AREA_HEX"]
