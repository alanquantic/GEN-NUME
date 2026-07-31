"""Graficos SVG generados en servidor desde los numeros de la persona."""

from __future__ import annotations

import math

from ..domain.pinnacle import Pinnacle

PRIMARY = "#4C1D95"
FUCHSIA_D = "#6D28D9"
ACCENT = "#D3AE36"
INK = "#2A1E3E"
INK_SOFT = "#6B6280"
BORDER = "#E6DDEE"
DANGER = "#E8304F"
GREEN = "#8BC34A"
ROYAL = "#2047C5"
GREY = "#B2A9C6"


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


def name_strip_svg(name_sanitize: str, alma: str, expresion: str) -> str:
    letters = [c for c in name_sanitize.replace("-", "") if c in _VOWELS or c in _CONS]
    if not letters:
        return ""
    width = 720
    step = min(34, (width - 40) / max(len(letters), 1))
    x0 = (width - step * (len(letters) - 1)) / 2

    parts = [_svg_root(f"0 0 {width} 200", width, 200, "Valor de cada letra del nombre")]
    parts.append(_text(6, 16, f"VOCALES · ALMA {alma}", size=8.5, fill="#96751B", weight=600, anchor="start", letter_spacing=".14em"))
    parts.append(_text(6, 192, f"CONSONANTES · EXPRESIÓN {expresion}", size=8.5, fill=PRIMARY, weight=600, anchor="start", letter_spacing=".14em"))
    parts.append(f'<line x1="0" y1="100" x2="{width - 42}" y2="100" stroke="{BORDER}"/>')

    for i, ch in enumerate(letters):
        x = x0 + i * step
        parts.append(_center_text(x, 100, ch.upper(), class_name="lt", size=20, fill=INK, family="Georgia, serif", weight=400))
        if ch in _VOWELS:
            parts.append(_center_text(x, 60, str(_VOWELS[ch]), class_name="lv", size=11, fill="#96751B", weight=600))
            parts.append(f'<circle cx="{x:.1f}" cy="76" r="2.4" fill="{ACCENT}"/>')
        else:
            parts.append(_center_text(x, 140, str(_CONS[ch]), class_name="lv", size=11, fill="#5B21B6", weight=600))

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


def personal_year_svg(ap: str, area: str = PRIMARY) -> str:
    ring = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    active = "2" if ap == "11" else ap
    radius = 92
    inner = 42
    parts = [_svg_root("0 0 300 210", 300, 210, "Año personal")]
    parts.append('<g transform="translate(150 105)">')

    for idx, label in enumerate(ring):
        a0 = -math.pi / 2 + idx * 2 * math.pi / 9
        a1 = -math.pi / 2 + (idx + 1) * 2 * math.pi / 9
        x0, y0 = radius * math.cos(a0), radius * math.sin(a0)
        x1, y1 = radius * math.cos(a1), radius * math.sin(a1)
        opacity = "1" if label == active else ".13"
        parts.append(
            f'<path d="M0 0 L{x0:.1f} {y0:.1f} A{radius} {radius} 0 0 1 {x1:.1f} {y1:.1f} Z" '
            f'fill="{area}" opacity="{opacity}"/>'
        )
        am = (a0 + a1) / 2
        lx, ly = (radius - 14) * math.cos(am), (radius - 14) * math.sin(am)
        col = "#fff" if label == active else INK
        parts.append(_center_text(lx, ly, label, size=11, fill=col, weight=700))

    parts.append(f'<circle cx="0" cy="0" r="{inner}" fill="#fff" stroke="{BORDER}"/>')
    parts.append(_text(0, -4, ap, size=32, fill=area, family="Georgia, serif", weight=800))
    parts.append(_text(0, 18, "AÑO PERSONAL", size=7.5, fill=INK_SOFT, weight=700, letter_spacing=".14em"))
    parts.append("</g></svg>")
    return "".join(parts)


__all__ = ["pinnacle_svg", "name_strip_svg", "absences_svg", "stages_svg", "personal_year_svg"]
