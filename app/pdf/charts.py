"""Gráficos SVG generados en servidor desde los números de la persona."""

from __future__ import annotations

import math

from ..domain.pinnacle import Pinnacle

PRIMARY = "#4C1D95"
FUCHSIA_D = "#6D28D9"
ACCENT = "#D3AE36"
ACCENT_INK = "#96751B"
ACCENT_SOFT = "#F8EFD8"
ACCENT_DEEP = "#F0DFAE"
PAPER = "#FDFCFA"
INK = "#2A1E3E"
INK_SOFT = "#6B6280"
BORDER = "#E6DDEE"
DANGER = "#E8304F"
GREEN = "#8BC34A"
ROYAL = "#2047C5"
GREY = "#B2A9C6"


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


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg_root(view_box: str, width: int, height: int, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" '
        f'role="img" aria-label="{_esc(label)}">'
    )


def _text(
    x: float,
    y: float,
    value: str,
    *,
    size: float,
    fill: str = INK,
    family: str = "Open Sans, Arial, sans-serif",
    weight: int = 600,
    anchor: str = "middle",
    class_name: str | None = None,
    letter_spacing: str | None = None,
    dy: str | None = None,
) -> str:
    attrs = [
        f'x="{x:.1f}"',
        f'y="{y:.1f}"',
        f'fill="{fill}"',
        f'font-family="{family}"',
        f'font-size="{size}px"',
        f'font-weight="{weight}"',
        f'text-anchor="{anchor}"',
    ]
    if class_name:
        attrs.append(f'class="{class_name}"')
    if letter_spacing is not None:
        attrs.append(f'letter-spacing="{letter_spacing}"')
    if dy is not None:
        attrs.append(f'dy="{dy}"')
    return f"<text {' '.join(attrs)}>{_esc(value)}</text>"


def _center_text(
    x: float,
    y: float,
    value: str,
    *,
    size: float,
    fill: str = INK,
    family: str = "Open Sans, Arial, sans-serif",
    weight: int = 700,
    class_name: str | None = None,
) -> str:
    return _text(
        x,
        y,
        value,
        size=size,
        fill=fill,
        family=family,
        weight=weight,
        class_name=class_name,
        dy="0.35em",
    )


_PIN_LAYOUT = [
    ("H", 232, 84, "H · DESTINO", "destino"),
    ("G", 232, 166, "G · 3.ª ETAPA", "sup"),
    ("E", 146, 244, "E · 1.ª ETAPA", "sup"),
    ("I", 232, 244, "I · SEXTO SENTIDO", "sup"),
    ("F", 322, 244, "F · 2.ª ETAPA", "sup"),
    ("J", 400, 166, "J · ESPEJO / PAREJA", "sup"),
    ("A", 92, 325, "A · KARMA · mes", "hor"),
    ("B", 232, 325, "B · PERSONAL · día", "core"),
    ("C", 392, 325, "C · VIDA PASADA · año", "hor"),
    ("D", 502, 325, "D · MÁSCARA", "hor2"),
    ("X", 610, 325, "X · REACCIÓN", "ext"),
    ("Y", 688, 325, "Y · MISIÓN", "ext"),
    ("Z", 648, 228, "Z · REGALO DIVINO", "ext-dash"),
    ("K", 146, 420, "K · DESAFÍO", "inf"),
    ("O", 232, 420, "O · INCONSC. NEG.", "inf"),
    ("L", 322, 420, "L · DESAFÍO", "inf"),
    ("M", 232, 488, "M · DESAFÍO", "inf"),
    ("N", 232, 556, "N · DESAFÍO", "inf"),
    ("P", 44, 452, "P · SOMBRA", "shadow"),
    ("Q", 392, 488, "", "inf-sm"),
    ("R", 462, 488, "", "inf-sm"),
    ("S", 532, 488, "", "inf-sm"),
]

_LABEL_BELOW = {
    "H": 123,
    "A": 372,
    "B": 374,
    "C": 372,
    "D": 372,
    "X": 368,
    "Y": 368,
    "K": 456,
    "L": 456,
    "N": 592,
    "P": 490,
}
_LABEL_ABOVE = {"G": 171, "E": 290, "I": 212, "F": 290, "J": 163, "Z": 271, "O": 387, "M": 492}


def _pin_fill(zone: str) -> tuple[str, str]:
    return {
        "destino": (ACCENT, "#fff"),
        "sup": (GREEN, "#fff"),
        "core": (PRIMARY, "#fff"),
        "hor": (PRIMARY, "#fff"),
        "hor2": (FUCHSIA_D, "#fff"),
        "shadow": (INK, "#fff"),
        "ext": ("#fff", ROYAL),
        "ext-dash": ("#fff", ROYAL),
        "inf": ("#fff", GREY),
        "inf-sm": ("#fff", GREY),
    }.get(zone, ("#fff", INK))


def pinnacle_svg(pin: Pinnacle) -> str:
    pos = pin.as_positions()
    parts = [_svg_root("0 0 720 640", 720, 640, "Pináculo personal")]
    parts.append('<path d="M230 46 L378 262 L82 262 Z" fill="#E4EFD3" opacity=".6"/>')
    parts.append('<rect x="28" y="292" width="536" height="66" rx="9" fill="#EDE3F8"/>')
    parts.append('<path d="M82 388 L378 388 L230 604 Z" fill="#FBDCE1" opacity=".55"/>')
    parts.append(_text(140, 34, "SER SUPERIOR · REALIZACIONES", size=8, fill="#7CB342", weight=700, letter_spacing=".16em"))
    parts.append(_text(120, 286, "HORIZONTAL · IDENTIDAD", size=8, fill="#6D28D9", weight=700, letter_spacing=".16em"))
    parts.append(_text(118, 382, "SER INFERIOR · DESAFÍOS", size=8, fill="#C0392B", weight=700, letter_spacing=".16em"))
    parts.append(
        '<g stroke="#CFC6DE" stroke-width="1" stroke-dasharray="3 3" fill="none">'
        '<path d="M92 320 L146 244 M232 320 L146 244 M232 320 L322 244 M392 320 L322 244 '
        'M146 244 L232 166 M322 244 L232 166 M232 166 L232 84 '
        'M322 244 L400 166 M232 84 L400 166 '
        'M92 320 L146 420 M232 320 L146 420 M232 320 L322 420 M392 320 L322 420 '
        'M146 420 L232 488 M322 420 L232 488 M232 488 L232 556"/></g>'
    )

    for key, cx, cy, label, zone in _PIN_LAYOUT:
        vib = pos[key]
        fill, ink = _pin_fill(zone)
        is_zero = vib.value == 0
        if key == "B":
            radius = 35
        elif zone in ("hor", "hor2"):
            radius = 27
        elif zone.startswith("ext"):
            radius = 25
        elif zone == "inf-sm":
            radius = 22
        elif zone in ("inf", "shadow"):
            radius = 24
        else:
            radius = 26

        stroke_bits = []
        if zone in ("inf", "inf-sm"):
            stroke_bits.append('stroke="#E8304F"')
            stroke_bits.append('stroke-width="1.6"')
        elif zone.startswith("ext"):
            stroke_bits.append('stroke="#2047C5"')
            stroke_bits.append('stroke-width="2"')
            if zone == "ext-dash":
                stroke_bits.append('stroke-dasharray="4 3"')
        if key == "B":
            stroke_bits = ['stroke="#D3AE36"', 'stroke-width="2.5"']

        circle = f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}"'
        if stroke_bits:
            circle += " " + " ".join(stroke_bits)
        circle += "/>"
        parts.append(circle)

        font_size = 27 if key == "B" else (18 if zone in ("inf", "inf-sm", "ext", "ext-dash") else 21)
        num_color = GREY if is_zero and zone in ("inf", "inf-sm") else ink
        family = "Georgia, serif" if key == "B" else "Open Sans, Arial, sans-serif"
        parts.append(_center_text(cx, cy, str(vib), size=font_size, fill=num_color, family=family))
        if label:
            ly = _LABEL_BELOW.get(key) or _LABEL_ABOVE.get(key)
            if ly:
                parts.append(_text(cx, ly, label, size=8.5, fill=INK_SOFT, weight=600, letter_spacing=".05em"))

    parts.append(_text(462, 520, "Q · R · S — SÚPER OCULTOS", size=8, fill="#C0392B", weight=700, letter_spacing=".16em"))
    aus = " · ".join(str(a) for a in pin.absences) or "—"
    parts.append(
        '<rect x="590" y="446" width="118" height="52" rx="8" fill="#fff" '
        'stroke="#E8304F" stroke-width="1.7" stroke-dasharray="5 4"/>'
    )
    parts.append(_text(649, 468, aus, size=17, fill="#C0392B", family="Georgia, serif", weight=700))
    parts.append(_text(649, 486, "T · AUSENCIAS", size=8.5, fill="#C0392B", weight=600, letter_spacing=".05em"))
    parts.append("</svg>")
    return "".join(parts)


_VOWELS = {"a": 1, "e": 5, "i": 9, "o": 6, "u": 3}
_CONS = {
    "b": 2,
    "c": 3,
    "d": 4,
    "f": 6,
    "g": 7,
    "h": 8,
    "j": 1,
    "k": 11,
    "l": 3,
    "m": 4,
    "n": 5,
    "p": 7,
    "q": 8,
    "r": 9,
    "s": 1,
    "t": 2,
    "v": 22,
    "w": 5,
    "x": 6,
    "y": 7,
    "z": 8,
    "ñ": 5,
}


def name_table_svg(
    name_sanitize: str,
    alma: str,
    expresion: str,
    area: str = PRIMARY,
) -> str:
    """El nombre como tabla de 3 filas: valores de vocales / letras / valores
    de consonantes, con la suma de cada fila como chip al final.
    """
    words = [w for w in name_sanitize.split("-") if w]
    letters: list[tuple[str, bool]] = []      # (letra, ¿inicia palabra?)
    for w in words:
        for j, ch in enumerate(w):
            if ch in _VOWELS or ch in _CONS:
                letters.append((ch, j == 0 and bool(letters)))
    if not letters:
        return ""

    W, H = 720, 196
    table_x0, table_x1 = 8, 664          # a la derecha quedan los chips de suma
    y_v0, y_v1 = 30, 68                  # banda de vocales
    y_l0, y_l1 = 68, 122                 # banda de letras
    y_c0, y_c1 = 122, 160                # banda de consonantes

    n_gaps = sum(1 for _, brk in letters if brk)
    slots = len(letters) + 0.7 * n_gaps
    step = min(40.0, (table_x1 - table_x0 - 24) / max(slots - 1, 1))
    span = step * (len(letters) - 1 + 0.7 * n_gaps)
    x = table_x0 + ((table_x1 - table_x0) - span) / 2

    parts = [_svg_root(f"0 0 {W} {H}", W, H, "Tabla de valores del nombre")]
    parts.append(_text(8, 16, f"VOCALES · ALMA {alma}", size=8.5, fill=ACCENT_INK,
                       weight=600, anchor="start", letter_spacing=".14em"))
    parts.append(_text(8, 188, f"CONSONANTES · EXPRESIÓN {expresion}", size=8.5,
                       fill=area, weight=600, anchor="start", letter_spacing=".14em"))

    tw = table_x1 - table_x0
    # bandas: vocales (dorado suave, esquinas superiores), letras (blanco),
    # consonantes (tinte del área, esquinas inferiores)
    parts.append(
        f'<path d="M{table_x0} {y_v1} V{y_v0 + 9} Q{table_x0} {y_v0} {table_x0 + 9} {y_v0} '
        f'H{table_x1 - 9} Q{table_x1} {y_v0} {table_x1} {y_v0 + 9} V{y_v1} Z" '
        f'fill="{ACCENT_SOFT}"/>'
    )
    parts.append(f'<rect x="{table_x0}" y="{y_l0}" width="{tw}" height="{y_l1 - y_l0}" fill="#fff"/>')
    area_band = _mix(area, "#FFFFFF", 0.9)
    parts.append(
        f'<path d="M{table_x0} {y_c0} H{table_x1} V{y_c1 - 9} '
        f'Q{table_x1} {y_c1} {table_x1 - 9} {y_c1} H{table_x0 + 9} '
        f'Q{table_x0} {y_c1} {table_x0} {y_c1 - 9} Z" fill="{area_band}"/>'
    )
    # contorno + divisores horizontales
    parts.append(
        f'<rect x="{table_x0}" y="{y_v0}" width="{tw}" height="{y_c1 - y_v0}" '
        f'rx="9" fill="none" stroke="{BORDER}" stroke-width="1.2"/>'
    )
    for yy in (y_v1, y_c0):
        parts.append(
            f'<line x1="{table_x0}" y1="{yy}" x2="{table_x1}" y2="{yy}" '
            f'stroke="{BORDER}" stroke-width="1"/>'
        )

    xs: list[float] = []
    for ch, brk in letters:
        if brk:
            x += step * 0.7
        xs.append(x)
        x += step

    # separadores de columna (no en los cortes de palabra)
    for i in range(1, len(letters)):
        if letters[i][1]:
            continue
        mid = (xs[i - 1] + xs[i]) / 2
        parts.append(
            f'<line x1="{mid:.1f}" y1="{y_v0 + 5}" x2="{mid:.1f}" y2="{y_c1 - 5}" '
            f'stroke="{BORDER}" stroke-width="1" opacity=".55"/>'
        )

    y_letter = (y_l0 + y_l1) / 2
    y_vowel = (y_v0 + y_v1) / 2
    y_cons = (y_c0 + y_c1) / 2
    area_ink = _mix(area, "#120B1F", 0.25)
    for (ch, _), cx in zip(letters, xs):
        parts.append(_center_text(cx, y_letter, ch.upper(), size=21, fill=INK,
                                  family="Georgia, serif", weight=400))
        if ch in _VOWELS:
            parts.append(_center_text(cx, y_vowel, str(_VOWELS[ch]),
                                      size=12, fill=ACCENT_INK, weight=700))
        else:
            parts.append(_center_text(cx, y_cons, str(_CONS[ch]),
                                      size=12, fill=area_ink, weight=700))

    # chips de suma al final de cada fila de valores
    chip_x = table_x1 + 27
    parts.append(f'<line x1="{table_x1 + 4}" y1="{y_vowel:.0f}" x2="{chip_x - 15}" y2="{y_vowel:.0f}" stroke="{ACCENT}" stroke-width="1.4"/>')
    parts.append(f'<circle cx="{chip_x}" cy="{y_vowel:.0f}" r="14" fill="{ACCENT}"/>')
    parts.append(_center_text(chip_x, y_vowel, alma, size=12.5, fill="#fff", weight=800))
    parts.append(f'<line x1="{table_x1 + 4}" y1="{y_cons:.0f}" x2="{chip_x - 15}" y2="{y_cons:.0f}" stroke="{area}" stroke-width="1.4"/>')
    parts.append(f'<circle cx="{chip_x}" cy="{y_cons:.0f}" r="14" fill="{area}"/>')
    parts.append(_center_text(chip_x, y_cons, expresion, size=12.5, fill="#fff", weight=800))

    parts.append("</svg>")
    return "".join(parts)


def absences_svg(pin: Pinnacle, area: str = PRIMARY) -> str:
    absent = set(pin.absences)
    parts = [_svg_root("0 0 300 216", 300, 216, "Números presentes y ausentes")]
    for idx in range(9):
        n = idx + 1
        col, row = idx % 3, idx // 3
        x, y = 34 + col * 83, 18 + row * 62
        if n in absent:
            parts.append(
                f'<rect x="{x}" y="{y}" width="66" height="52" rx="7" fill="none" '
                f'stroke="#D9D2E6" stroke-width="2" stroke-dasharray="5 4"/>'
            )
            parts.append(_center_text(x + 33, y + 26, str(n), size=26, fill="#C9C0D8", weight=800))
        else:
            parts.append(f'<rect x="{x}" y="{y}" width="66" height="52" rx="7" fill="{area}"/>')
            parts.append(_center_text(x + 33, y + 26, str(n), size=26, fill="#fff", weight=800))
    parts.append("</svg>")
    return "".join(parts)


def stages_svg(pin: Pinnacle, today_age: int, area: str = PRIMARY) -> str:
    stages = pin.stages
    width = 720
    lengths = [(s.end_age - s.start_age) if s.end_age is not None else 9 for s in stages]
    total = sum(lengths)
    parts = [_svg_root(f"0 0 {width} 130", width, 130, "Etapas de vida")]
    x = 10
    avail = width - 20
    current = None

    for idx, stage in enumerate(stages):
        w = avail * lengths[idx] / total
        active = stage.contains_age(today_age)
        opacity = "1" if active else (".5" if idx % 2 == 0 else ".34")
        parts.append(
            f'<rect x="{x:.0f}" y="46" width="{w - 4:.0f}" height="42" rx="4" '
            f'fill="{area}" opacity="{opacity}"/>'
        )
        cx = x + w / 2
        parts.append(_center_text(cx, 67, str(stage.realization), size=20, fill="#fff", weight=700))
        parts.append(_text(cx, 106, stage.year_range, size=10, fill=INK_SOFT, weight=600))
        parts.append(_text(cx, 120, f"{stage.age_range} años", size=9.5, fill="#A99FBF", weight=500))
        if active:
            current = cx
        x += w

    if current is not None:
        parts.append(_text(current, 14, f"ESTÁS AQUÍ · {today_age} AÑOS", size=8.5, fill=PRIMARY, weight=700, letter_spacing=".14em"))
        parts.append(f'<path d="M{current:.0f} 20 L{current:.0f} 40" stroke="{area}" stroke-width="2"/>')
        parts.append(f'<circle cx="{current:.0f}" cy="42" r="4" fill="{area}"/>')

    parts.append("</svg>")
    return "".join(parts)


def _pol(r: float, ang: float) -> tuple[float, float]:
    return r * math.cos(ang), r * math.sin(ang)


def _annular(r_in: float, r_out: float, a0: float, a1: float) -> str:
    """Sector de anillo (dona) entre dos radios y dos ángulos."""
    x0o, y0o = _pol(r_out, a0)
    x1o, y1o = _pol(r_out, a1)
    x0i, y0i = _pol(r_in, a0)
    x1i, y1i = _pol(r_in, a1)
    large = 1 if (a1 - a0) > math.pi else 0
    return (
        f"M{x0o:.1f} {y0o:.1f} A{r_out} {r_out} 0 {large} 1 {x1o:.1f} {y1o:.1f} "
        f"L{x1i:.1f} {y1i:.1f} A{r_in} {r_in} 0 {large} 0 {x0i:.1f} {y0i:.1f} Z"
    )


def time_wheel_svg(
    ap: str,
    year: int,
    months: list[dict],
    cuatrimestres: list[dict],
    current_month: int,          # 1..12
    area: str = PRIMARY,
) -> str:
    """Rueda del año desglosada: AP al centro, cuatrimestres, mes personal/
    universal y semanas personales. Sólo fills planos (cero shadings extra).

    `months` y `cuatrimestres` vienen de `domain.time_wheel` (month_data y
    quarter_arcs).
    """
    parts = [_svg_root("0 0 440 440", 440, 440, f"Círculo del tiempo {year}")]
    parts.append('<g transform="translate(220 220)">')

    def ang(i: float) -> float:
        return -math.pi / 2 + i * 2 * math.pi / 12

    # --- Banda de cuatrimestres (tinte dorado, anclada al mes natal) ------- #
    gap = math.radians(1.6)
    for cu in cuatrimestres:
        a0 = ang(cu["start"]) + gap
        a1 = ang(cu["start"] + cu["span"]) - gap
        fill = ACCENT_DEEP if cu.get("active") else ACCENT_SOFT
        parts.append(f'<path d="{_annular(74, 106, a0, a1)}" fill="{fill}"/>')
        am = (a0 + a1) / 2
        cx, cy = _pol(90, am)
        parts.append(_center_text(cx, cy - 5, cu["value"], size=15,
                                  fill=ACCENT_INK, family="Georgia, serif"))
        parts.append(_text(cx, cy + 12, cu["range"], size=6, fill=ACCENT_INK,
                           weight=700, letter_spacing=".14em"))
    # rombo dorado en el arranque del ciclo (el mes de nacimiento)
    if cuatrimestres:
        a_start = ang(cuatrimestres[0]["start"])
        dx, dy_ = _pol(110, a_start)
        parts.append(
            f'<path d="M{dx:.1f} {dy_ - 4:.1f} L{dx + 3.2:.1f} {dy_:.1f} '
            f'L{dx:.1f} {dy_ + 4:.1f} L{dx - 3.2:.1f} {dy_:.1f} Z" fill="{ACCENT}"/>'
        )

    # --- Meses + semanas --------------------------------------------------- #
    for i, mo in enumerate(months):
        a0, a1 = ang(i), ang(i + 1)
        am = (a0 + a1) / 2
        m_num = i + 1
        is_now = m_num == current_month
        is_past = m_num < current_month

        if is_now:
            op_m, op_w = "1", "1"
        elif is_past:
            op_m, op_w = ".08", ".06"
        else:
            op_m, op_w = ".16", ".09"

        # sector del mes (r 112–164) y de sus semanas (r 168–200)
        parts.append(
            f'<path d="{_annular(112, 164, a0, a1)}" fill="{area}" '
            f'opacity="{op_m}" stroke="{PAPER}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<path d="{_annular(168, 200, a0, a1)}" fill="{area}" '
            f'opacity="{op_w}" stroke="{PAPER}" stroke-width="1.5"/>'
        )

        name_fill = "#fff" if is_now else (INK_SOFT if not is_past else "#A89EBB")
        val_fill = "#fff" if is_now else (INK if not is_past else "#A89EBB")
        uni_fill = _mix("#FFFFFF", area, 0.25) if is_now else "#9A91AD"

        nx, ny = _pol(150, am)
        parts.append(_text(nx, ny + 2, mo["abbr"], size=6.8, fill=name_fill,
                           weight=700, letter_spacing=".16em"))
        vx, vy = _pol(130, am)
        parts.append(
            f'<text x="{vx:.1f}" y="{vy:.1f}" dy="0.35em" text-anchor="middle" '
            f'font-family="Open Sans, Arial, sans-serif">'
            f'<tspan font-size="11px" font-weight="700" fill="{val_fill}">{mo["mp"]}</tspan>'
            f'<tspan font-size="8px" font-weight="600" fill="{uni_fill}"> /{mo["mu"]}</tspan>'
            f"</text>"
        )

        # 4 semanas personales por mes
        wk_fill = "#fff" if is_now else (INK_SOFT if not is_past else "#B6AEC6")
        for k, wv in enumerate(mo["weeks"]):
            aw = a0 + (a1 - a0) * (2 * k + 1) / 8
            wx, wy = _pol(184, aw)
            parts.append(_center_text(wx, wy, wv, size=7, fill=wk_fill, weight=600))
        # separadores de semana (ticks finos)
        for k in (1, 2, 3):
            at = a0 + (a1 - a0) * k / 4
            x0t, y0t = _pol(170, at)
            x1t, y1t = _pol(198, at)
            parts.append(
                f'<line x1="{x0t:.1f}" y1="{y0t:.1f}" x2="{x1t:.1f}" y2="{y1t:.1f}" '
                f'stroke="{PAPER}" stroke-width="1" opacity=".8"/>'
            )

    # --- Centro ------------------------------------------------------------ #
    parts.append(f'<circle cx="0" cy="0" r="62" fill="#fff" stroke="{BORDER}"/>')
    parts.append(_text(0, -30, str(year), size=7.5, fill=ACCENT_INK, weight=700,
                       letter_spacing=".3em"))
    parts.append(_text(0, 10, ap, size=38, fill=area,
                       family="Georgia, serif", weight=800))
    parts.append(_text(0, 32, "AÑO PERSONAL", size=7.5, fill=INK_SOFT,
                       weight=700, letter_spacing=".14em"))

    parts.append("</g></svg>")
    return "".join(parts)


__all__ = ["pinnacle_svg", "name_table_svg", "absences_svg", "stages_svg", "time_wheel_svg"]
