"""Renderiza un reporte dinamico: JSON + numeros -> HTML -> PDF."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ..ai.numbers import Numbers
from . import charts

_DIR = Path(__file__).resolve().parent / "html_report"

AREA_HEX = {
    "primary": "#4C1D95",
    "area-amor": "#EC4899",
    "area-trabajo": "#3B82F6",
    "area-bienestar": "#059669",
    "area-espiritual": "#A855F7",
}

_LABEL = {
    "B": ("Esencia", "numero personal · el dia"),
    "A": ("Karma", "el mes · tu clan"),
    "C": ("Vida pasada", "el ano"),
    "D": ("Personalidad", "tu mascara"),
    "H": ("Destino", "a donde vas"),
    "I": ("Subconsciente", "tu brujula"),
    "J": ("Espejo", "lo que te atrae"),
    "P": ("Sombra", "tu punto ciego"),
    "ALMA": ("Alma", "vocales del nombre"),
    "EXPRESION": ("Expresion", "consonantes"),
    "NOMBRE": ("Nombre", "todas las letras"),
    "Z": ("Regalo divino", "tu don"),
    "Y": ("Mision", "tu sintesis"),
    "X": ("Reaccion", "como te ven"),
    "AP": ("Ano personal", "tu ano en curso"),
    "MADUREZ": ("Madurez", "la segunda mitad"),
    "PAREJA": ("Pareja", "la union"),
}

_FICHA = {
    "quien-soy": ["B", "A", "C", "D", "H", "I", "J", "P", "ALMA", "Z"],
    "amor": ["B", "J", "ALMA", "AP", "PAREJA", "A", "D", "P"],
    "trabajo": ["B", "H", "D", "EXPRESION", "NOMBRE", "AP", "Z"],
    "bienestar": ["B", "D", "P", "X", "A", "ALMA", "AP"],
    "proposito": ["B", "ALMA", "H", "MADUREZ", "Y", "Z", "D", "A"],
}

LEGAL_BASE = (
    "Este reporte esta redactado a partir del metodo y los textos de "
    "Numerologia Cotidiana de Laura L. Rodriguez. La numerologia es una "
    "herramienta de autoconocimiento; sus interpretaciones no sustituyen el "
    "criterio profesional en ninguna materia."
)
LEGAL_BIENESTAR = (
    " Este contenido trata de energia, habitos y bienestar general, y no "
    "constituye diagnóstico, consejo ni tratamiento medico o psicologico. "
    "Ante cualquier sintoma, consulta a un profesional de la salud."
)


def _mix(hex_color: str, target: str, ratio: float) -> str:
    """Mezcla dos colores hex para no depender de color-mix() en CSS."""
    ratio = max(0.0, min(1.0, ratio))

    def _rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    src = _rgb(hex_color)
    dst = _rgb(target)
    mixed = tuple(round(src[i] * (1 - ratio) + dst[i] * ratio) for i in range(3))
    return "#" + "".join(f"{c:02X}" for c in mixed)


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


def _ficha(report_key: str, numbers: Numbers) -> list[dict]:
    out = []
    for key in _FICHA.get(report_key, []):
        val = numbers.get(key)
        if not val or val == "0":
            continue
        title, sub = _LABEL.get(key, (key, ""))
        out.append(
            {
                "value": val,
                "title": title,
                "sub": sub,
                "karmic": val.endswith("*"),
            }
        )
    return out


def _numbers_note(numbers: Numbers) -> str:
    pin = numbers.pinnacle
    bits = []
    if pin.karmic_debts:
        bits.append(
            '<span class="star">*</span> Los numeros marcados son '
            "<b>karmicos</b>: deudas que este camino viene a saldar."
        )
    if pin.h_alternative is not None:
        bits.append(
            f"Tu destino puede vivirse como <b>{pin.h}</b> o elevarse a "
            f"su vibracion maestra <b>{pin.h_alternative}</b>."
        )
    if pin.absences:
        aus = ", ".join(str(a) for a in pin.absences)
        bits.append(f"Te faltan las vibraciones <b>{aus}</b>: tus tareas por integrar.")
    return " ".join(bits)


def _charts(report_key: str, numbers: Numbers, today_age: int, area: str) -> list[dict]:
    pin = numbers.pinnacle
    out: list[dict] = []

    def add(eyebrow, title, svg, caption="", kind="panel"):
        if svg:
            out.append(
                {
                    "eyebrow": eyebrow,
                    "title": title,
                    "svg": svg,
                    "caption": caption,
                    "kind": kind,
                }
            )

    if report_key == "quien-soy":
        cap = ""
        if pin.special_pinnacle:
            cap = (
                "Tu zona inferior esta llena de ceros: es un <b>Pinaculo "
                "Especial</b>, con la energia de los desafios volcada hacia "
                "lo colectivo."
            )
        add("Tu pinaculo personal", "Un mapa que no cambia jamas", charts.pinnacle_svg(pin), cap, kind="map")
        add(
            "El poder de tu nombre",
            "Cada letra, una vibracion",
            charts.name_strip_svg(numbers.name_sanitize, numbers.get("ALMA"), numbers.get("EXPRESION")),
            "Las vocales muestran lo que sientes; las consonantes, la forma en que esa energia se expresa hacia afuera.",
            kind="strip",
        )
    elif report_key == "proposito":
        add(
            "Tu linea de vida",
            "Tus cuatro etapas",
            charts.stages_svg(pin, today_age, area),
            "La franja mas solida marca la etapa que esta activa hoy en tu recorrido.",
            kind="timeline",
        )
        add("Tu pinaculo", "El mapa completo", charts.pinnacle_svg(pin), kind="map")
    elif report_key == "trabajo":
        add(
            "La energia de tu ano",
            "Donde estas en el ciclo",
            charts.personal_year_svg(numbers.get("AP"), area),
            "El sector encendido muestra la vibracion dominante de este ano y el centro resume el aprendizaje principal.",
            kind="wheel",
        )
        add(
            "El poder de tu nombre",
            "Tu canal de expresion",
            charts.name_strip_svg(numbers.name_sanitize, numbers.get("ALMA"), numbers.get("EXPRESION")),
            "Este trazado convierte tu nombre en ritmo: primero la emocion que mueve, luego la voz con la que sales al mundo.",
            kind="strip",
        )
    elif report_key == "amor":
        add(
            "La energia de tu ano",
            "Tu amor en el ciclo",
            charts.personal_year_svg(numbers.get("AP"), area),
            "No habla de destino fijo, sino del clima emocional que mas probablemente esta marcando tu ano.",
            kind="wheel",
        )
    elif report_key == "bienestar":
        add(
            "Presencias y ausencias",
            "Lo que te sobra y lo que te falta",
            charts.absences_svg(pin, area),
            "Los cuadros llenos se viven como recursos disponibles; los vacios piden conciencia, practica y paciencia.",
            kind="grid",
        )
        add(
            "La energia de tu ano",
            "Como cuidarte este ano",
            charts.personal_year_svg(numbers.get("AP"), area),
            "La rueda ayuda a leer en que tono conviene acompanar tus habitos, tus limites y tu recuperacion.",
            kind="wheel",
        )
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


def render_html(
    report_key: str,
    data: dict,
    numbers: Numbers,
    *,
    report_title: str,
    area_token: str,
    person_name: str,
    birth_long: str,
    today_long: str,
    today_age: int,
) -> str:
    area = AREA_HEX.get(area_token, AREA_HEX["primary"])
    legal = LEGAL_BASE + (LEGAL_BIENESTAR if report_key == "bienestar" else "")

    ctx = {
        "css": _css(),
        "data": data,
        "report_title": report_title,
        "area_hex": area,
        "area_soft": _mix(area, "#FFFFFF", 0.84),
        "area_soft_alt": _mix(area, "#FFFFFF", 0.92),
        "area_deep": _mix(area, "#120B1F", 0.38),
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
    """Renderiza el HTML a PDF con WeasyPrint."""
    try:
        from weasyprint import HTML
    except OSError as exc:
        raise RuntimeError(
            "WeasyPrint no pudo cargar sus librerias nativas (Pango/Cairo). "
            "En Windows es lo esperado; el PDF se genera en el deploy Linux. "
            f"Detalle: {exc}"
        ) from exc
    return HTML(string=html).write_pdf()


__all__ = ["render_html", "to_pdf", "AREA_HEX"]
