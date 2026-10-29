"""Renderiza un reporte dinámico: JSON + números -> HTML -> PDF."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from ..ai.numbers import Numbers
from ..domain.time_wheel import month_data, quarter_arcs
from . import charts
from .charts import _mix

_DIR = Path(__file__).resolve().parent / "html_report"

AREA_HEX = {
    "primary": "#4C1D95",
    "area-amor": "#EC4899",
    "area-trabajo": "#3B82F6",
    "area-bienestar": "#059669",
    "area-espiritual": "#A855F7",
}

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

_FICHA = {
    "quien-soy": ["B", "A", "C", "D", "H", "I", "J", "P", "ALMA", "Z"],
    "amor": ["B", "J", "ALMA", "AP", "PAREJA", "A", "D", "P"],
    "trabajo": ["B", "H", "D", "EXPRESION", "NOMBRE", "AP", "Z"],
    "bienestar": ["B", "D", "P", "X", "A", "ALMA", "AP"],
    "proposito": ["B", "ALMA", "H", "MADUREZ", "Y", "Z", "D", "A"],
}

# Número protagonista de la portada, por reporte: (clave, etiqueta).
# Si la clave no resuelve (p. ej. PAREJA sin pareja), se cae a B.
_COVER_FEATURE = {
    "quien-soy": ("B", "Tu número personal"),
    "amor": ("PAREJA", "Su número de pareja"),
    "trabajo": ("H", "Tu número de destino"),
    "bienestar": ("B", "Tu energía base"),
    "proposito": ("Y", "Tu número de misión"),
}

# Variantes visuales de los tiles del bento a partir del tercero (el 1.º es
# el héroe 2x2 y el 2.º el ancho): rompen la uniformidad de la retícula.
_BENTO_CYCLE = ["soft", "", "gold", "", "dark", "", "soft", ""]

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


@lru_cache(maxsize=1)
def _font_faces() -> str:
    """@font-face embebidas como data-URI: el HTML queda autocontenido y
    WeasyPrint no depende de las fuentes instaladas en el contenedor."""
    import base64

    faces = []
    for family, filename in [
        ("Mrs Saint Delafield", "MrsSaintDelafield-Regular.ttf"),
    ]:
        path = _DIR / "fonts" / filename
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        faces.append(
            f'@font-face{{font-family:"{family}";'
            f'src:url("data:font/ttf;base64,{b64}") format("truetype");'
            "font-weight:400;font-style:normal;}"
        )
    return "".join(faces)


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


def _bento_tiles(report_key: str, numbers: Numbers) -> list[dict]:
    """La ficha de números convertida en mosaico bento con jerarquía."""
    tiles = []
    for i, c in enumerate(_ficha(report_key, numbers)):
        if i == 0:
            variant = "hero"
        elif i == 1:
            variant = "wide"
        else:
            variant = _BENTO_CYCLE[(i - 2) % len(_BENTO_CYCLE)]
        tiles.append({**c, "value": c["value"].rstrip("*"), "variant": variant})
    return tiles


def _sec_chips(data: dict, numbers: Numbers) -> list[str]:
    """Por sección: 'Etiqueta valor · Etiqueta valor' en vez de claves crudas."""
    out = []
    for sec in data.get("secciones", []):
        chips = []
        for k in sec.get("numeros") or []:
            key = str(k).upper().rstrip("*")
            val = numbers.get(key)
            if val:
                label = _LABEL.get(key, (key, ""))[0]
                chips.append(f"{label} {val.rstrip('*')}")
        out.append(" · ".join(chips))
    return out


def _split_columns(paragraphs: list) -> tuple[list, list]:
    """Reparte párrafos en dos columnas equilibradas por longitud.

    El multicol de CSS (column-count) mete a WeasyPrint en loops infinitos de
    balanceo con ciertas alturas de contenido, así que las dos columnas se
    arman con flex y el reparto se decide aquí, de forma determinista.
    """
    paragraphs = list(paragraphs or [])
    if len(paragraphs) < 2:
        return paragraphs, []
    total = sum(len(p) for p in paragraphs)
    acc, cut = 0, 1
    for i, p in enumerate(paragraphs):
        acc += len(p)
        if acc >= total / 2:
            cut = min(i + 1, len(paragraphs) - 1)
            break
    return paragraphs[:cut], paragraphs[cut:]


def _cover_feature(report_key: str, numbers: Numbers) -> tuple[str, bool, str]:
    """(valor limpio, es kármico, etiqueta) del número protagonista de portada."""
    key, label = _COVER_FEATURE.get(report_key, ("B", "Tu número personal"))
    val = numbers.get(key)
    if not val:
        key, label = "B", "Tu número personal"
        val = numbers.get("B") or ""
    return val.rstrip("*"), val.endswith("*"), label


def _numbers_note(numbers: Numbers) -> str:
    pin = numbers.pinnacle
    bits = []
    if pin.karmic_debts:
        bits.append(
            '<span class="star">*</span> Los números marcados son '
            "<b>kármicos</b>: deudas que este camino viene a saldar."
        )
    if pin.h_alternative is not None:
        bits.append(
            f"Tu destino puede vivirse como <b>{pin.h}</b> o elevarse a "
            f"su vibración maestra <b>{pin.h_alternative}</b>."
        )
    if pin.absences:
        aus = ", ".join(str(a) for a in pin.absences)
        bits.append(f"Te faltan las vibraciones <b>{aus}</b>: tus tareas por integrar.")
    return " ".join(bits)


def _charts(
    report_key: str,
    numbers: Numbers,
    today_age: int,
    area: str,
    birth_date: date,
    today: date,
) -> list[dict]:
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

    def time_wheel() -> str:
        ap = int(numbers.get("AP") or 0)
        return charts.time_wheel_svg(
            numbers.get("AP") or "",
            today.year,
            month_data(ap, today.year),
            quarter_arcs(birth_date, today.year, today.month),
            today.month,
            area,
        )

    wheel_caption = (
        "Tu año, desglosado: el año personal al centro, los cuatrimestres en "
        "dorado (arrancan en tu mes de nacimiento, marcado con el rombo) y, por "
        "cada mes, su mes personal, el universal (en pequeño) y las cuatro "
        "semanas personales del borde. El sector sólido es tu mes en curso."
    )

    def add_pinnacle(title: str) -> None:
        """El pináculo como lectura visual autocontenida: el texto de estos
        reportes no lo explica, así que el caption lo presenta."""
        cap = (
            "Tu mapa de nacimiento: sale de tu fecha, no cambia jamás y de él "
            "nacen varios de los números que lee este reporte."
        )
        if pin.special_pinnacle:
            cap += (
                " Tu zona inferior está llena de ceros: es un <b>Pináculo "
                "Especial</b>, con la energía de los desafíos volcada hacia "
                "lo colectivo."
            )
        add("Tu pináculo personal", title, charts.pinnacle_svg(pin), cap, kind="map")
    name_caption = (
        "Cada letra de tu nombre aporta un número: arriba, las vocales que "
        "suman tu alma; abajo, las consonantes que suman tu expresión. Los "
        "círculos del final son el resultado de cada fila."
    )

    if report_key == "quien-soy":
        cap = ""
        if pin.special_pinnacle:
            cap = (
                "Tu zona inferior está llena de ceros: es un <b>Pináculo "
                "Especial</b>, con la energía de los desafíos volcada hacia "
                "lo colectivo."
            )
        add("Tu pináculo personal", "Un mapa que no cambia jamás", charts.pinnacle_svg(pin), cap, kind="map")
        add(
            "El poder de tu nombre",
            "Cada letra, una vibración",
            charts.name_table_svg(numbers.name_sanitize, numbers.get("ALMA"), numbers.get("EXPRESION"), area),
            name_caption,
            kind="strip",
        )
    elif report_key == "proposito":
        add(
            "Tu línea de vida",
            "Tus cuatro etapas",
            charts.stages_svg(pin, today_age, area),
            "La franja más sólida marca la etapa que está activa hoy en tu recorrido.",
            kind="timeline",
        )
        add("Tu pináculo", "El mapa completo", charts.pinnacle_svg(pin), kind="map")
    elif report_key == "trabajo":
        add_pinnacle("El mapa detrás de tu talento")
        add(
            "La energía de tu año",
            "El círculo de tu tiempo",
            time_wheel(),
            wheel_caption,
            kind="wheel-v2",
        )
        add(
            "El poder de tu nombre",
            "Tu canal de expresión",
            charts.name_table_svg(numbers.name_sanitize, numbers.get("ALMA"), numbers.get("EXPRESION"), area),
            name_caption,
            kind="strip",
        )
    elif report_key == "amor":
        add_pinnacle("El mapa con el que amas")
        add(
            "La energía de tu año",
            "Tu amor en el ciclo",
            time_wheel(),
            wheel_caption,
            kind="wheel-v2",
        )
    elif report_key == "bienestar":
        add_pinnacle("El mapa de tu energía")
        add(
            "Presencias y ausencias",
            "Lo que te sobra y lo que te falta",
            charts.absences_svg(pin, area),
            "Los cuadros llenos se viven como recursos disponibles; los vacíos piden conciencia, práctica y paciencia.",
            kind="grid",
        )
        add(
            "La energía de tu año",
            "Cómo cuidarte este año",
            time_wheel(),
            wheel_caption,
            kind="wheel-v2",
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
    birth_date: date,
    today: date,
    densities: dict[str, int] | None = None,
) -> str:
    area = AREA_HEX.get(area_token, AREA_HEX["primary"])
    legal = LEGAL_BASE + (LEGAL_BIENESTAR if report_key == "bienestar" else "")

    cover_val, cover_karmic, cover_label = _cover_feature(report_key, numbers)
    tension_keys = [
        str(k).upper().rstrip("*")
        for k in data.get("tension_central", {}).get("numeros", [])[:2]
    ]

    ctx = {
        "css": _css(),
        "font_faces": _font_faces(),
        "dens": densities or {},
        "data": data,
        "report_title": report_title,
        "area_hex": area,
        "area_soft": _mix(area, "#FFFFFF", 0.84),
        "area_soft_alt": _mix(area, "#FFFFFF", 0.92),
        "area_deep": _mix(area, "#120B1F", 0.38),
        "person_name": person_name,
        "birth_long": birth_long,
        "today_long": today_long,
        "ap_value": (numbers.get("AP") or "").rstrip("*"),
        "current_year": today.year,
        "cover_number_clean": cover_val,
        "cover_number_karmic": cover_karmic,
        "cover_number_label": cover_label,
        "bento_tiles": _bento_tiles(report_key, numbers),
        "numbers_note": _numbers_note(numbers),
        "charts": _charts(report_key, numbers, today_age, area, birth_date, today),
        "sec_rail": _sec_rail(data, numbers),
        "sec_chips": _sec_chips(data, numbers),
        "retrato_cols": _split_columns(data.get("retrato", {}).get("cuerpo", [])),
        "sec_cols": [
            _split_columns(s.get("cuerpo", [])) for s in data.get("secciones", [])
        ],
        "tension_cols": _split_columns(
            data.get("tension_central", {}).get("cuerpo", [])
        ),
        "tension_orbs": [o.rstrip("*") for o in _tension_orbs(data, numbers)],
        "tension_labels": [_LABEL.get(k, (k, ""))[0] for k in tension_keys],
        "legal": legal,
    }
    return _env().get_template("report.html.j2").render(**ctx)


def _weasy_html():
    try:
        from weasyprint import HTML
    except OSError as exc:
        raise RuntimeError(
            "WeasyPrint no pudo cargar sus librerias nativas (Pango/Cairo). "
            "En Windows es lo esperado; el PDF se genera en el deploy Linux. "
            f"Detalle: {exc}"
        ) from exc
    return HTML


def _finish_pdf(document) -> bytes:
    from ..config import settings
    from .compress import slim

    pdf = document.write_pdf(optimize_images=True, jpeg_quality=85, dpi=150)
    # Los dinámicos no llevan imágenes raster: con slim (sin pérdida) basta.
    return slim(pdf) if settings.pdf_compress != "off" else pdf


def to_pdf(html: str) -> bytes:
    """Renderiza el HTML a PDF con WeasyPrint y lo comprime."""
    return _finish_pdf(_weasy_html()(string=html).render())


# Bloques que aceptan densidad (clase d1/d2) cuando su texto no cabe en una
# página: el retrato, cada sección, la tensión central y el plan.
_FIT_MAX_DENSITY = 2
_FIT_EXTRA_RENDERS = 2


def _adjustable(key: str) -> bool:
    """¿El bloque (retrato, sec-N, tension, plan) admite compactarse?"""
    return key in ("retrato", "tension", "plan") or key.startswith("sec-")


# El contenido en flujo debe terminar por encima de la zona del folio
# (position:absolute, bottom:9mm). Si el marcador .pg-end de un bloque queda
# por debajo de este límite, el texto pisa el folio aunque quepa en la página.
_END_LIMIT_MM = 282
_MM_TO_PX = 96 / 25.4


def _overflow_by_block(document) -> dict[str, int]:
    """Páginas EXTRA que necesita compactar cada bloque ajustable.

    Cada <section class="page"> del template lleva un id pg-… y su contenido
    termina en un marcador end-…; WeasyPrint registra esas anclas por página
    con su posición. Un bloque desborda si su ancla pg-… queda a más de una
    página de la siguiente, o si su end-… cae en la zona del folio.
    """
    first_page: dict[str, int] = {}
    end_y: dict[str, float] = {}
    for idx, page in enumerate(document.pages):
        for name, rect in page.anchors.items():
            # rect = (x0, y0, x1, y1) en px CSS respecto al origen de la página
            if name.startswith("pg-"):
                first_page.setdefault(name, idx)
            elif name.startswith("end-"):
                key = name.removeprefix("end-")
                end_y[key] = max(end_y.get(key, 0.0), rect[1])

    ordered = sorted(first_page.items(), key=lambda kv: kv[1])
    out: dict[str, int] = {}
    for (name, start), (_, nxt) in zip(
        ordered, ordered[1:] + [("<fin>", len(document.pages))]
    ):
        key = name.removeprefix("pg-")
        extra = nxt - start - 1
        if _adjustable(key) and extra > 0:
            out[key] = extra

    limit = _END_LIMIT_MM * _MM_TO_PX
    for key, y in end_y.items():
        if key not in out and y > limit and _adjustable(key):
            out[key] = 1

    # Marcador ausente: el contenido creció tanto que WeasyPrint recortó el
    # final del bloque (las columnas flex no se fragmentan, se cortan). Eso
    # también es desborde, y de los graves: se perdería texto.
    for name in first_page:
        key = name.removeprefix("pg-")
        if _adjustable(key) and key not in end_y:
            out[key] = max(out.get(key, 0), 1)
    return out


def render_fitted(render) -> tuple[str, bytes]:
    """Renderiza con ajuste de densidad y devuelve (html, pdf).

    `render` es un callable `dict[str, int] -> str` (densidades -> HTML).
    Si un bloque derrama texto a una página extra (casi vacía), se le sube
    la densidad y se vuelve a renderizar, hasta d2 como máximo.
    """
    HTML = _weasy_html()
    densities: dict[str, int] = {}
    html = render(densities)
    document = HTML(string=html).render()

    for _ in range(_FIT_EXTRA_RENDERS):
        changed = False
        for key, extra in _overflow_by_block(document).items():
            bumped = min(densities.get(key, 0) + extra, _FIT_MAX_DENSITY)
            if bumped != densities.get(key, 0):
                densities[key] = bumped
                changed = True
        if not changed:
            break
        html = render(densities)
        document = HTML(string=html).render()

    return html, _finish_pdf(document)


__all__ = ["render_html", "render_fitted", "to_pdf", "AREA_HEX"]
