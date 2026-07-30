"""Gráficos SVG generados en servidor desde los números de la persona.

Cada función devuelve una cadena `<svg>…</svg>` autónoma (sin JS, sin recursos
externos) lista para incrustar en el HTML que WeasyPrint convierte a PDF. Todo
sale de `domain.Pinnacle` y del diccionario de números — cero trabajo manual por
persona.

Los colores se pasan por parámetro (`area`) para que cada reporte pinte sus
gráficos con su color de área sin duplicar código.
"""

from __future__ import annotations

from ..domain.pinnacle import Pinnacle

# Paleta base (coincide con las variables del sitio).
PRIMARY = "#4C1D95"
FUCHSIA_D = "#6D28D9"
ACCENT = "#D3AE36"
INK = "#2A1E3E"
INK_SOFT = "#6B6280"
BORDER = "#E6DDEE"
DANGER = "#E8304F"
GREEN = "#8BC34A"
GREEN_D = "#7CB342"
ROYAL = "#2047C5"
GREY = "#B2A9C6"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- #
# 1 · El Pináculo completo (24 posiciones)
# --------------------------------------------------------------------------- #
# Layout fijo: (clave, cx, cy, etiqueta corta, zona). Zonas: sup, hor, inf, ext.
_PIN_LAYOUT = [
    ("H", 232, 84,  "H · DESTINO", "destino"),
    ("G", 232, 166, "G · 3.ª ETAPA", "sup"),
    ("E", 146, 244, "E · 1.ª ETAPA", "sup"),
    ("I", 232, 244, "I · SEXTO SENTIDO", "sup"),
    ("F", 322, 244, "F · 2.ª ETAPA", "sup"),
    ("J", 400, 166, "J · ESPEJO / PAREJA", "sup"),
    ("A", 92,  325, "A · KARMA · mes", "hor"),
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
    ("P", 44,  452, "P · SOMBRA", "shadow"),
    ("Q", 392, 488, "", "inf-sm"),
    ("R", 462, 488, "", "inf-sm"),
    ("S", 532, 488, "", "inf-sm"),
]

_LABEL_BELOW = {"H": 123, "A": 372, "B": 374, "C": 372, "D": 372, "X": 368,
                "Y": 368, "K": 456, "L": 456, "N": 592, "P": 490}
_LABEL_ABOVE = {"G": 171, "E": 290, "I": 212, "F": 290, "J": 163, "Z": 271,
                "O": 387, "M": 492}


def _pin_fill(zone: str) -> tuple[str, str]:
    """(relleno, color-del-número) por zona."""
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
    p: list[str] = []
    p.append('<svg viewBox="0 0 720 640" role="img" '
              'aria-label="Pináculo personal">')
    p.append(
        '<defs><style>'
        '.pn{font:700 21px sans-serif;fill:#fff;text-anchor:middle;dominant-baseline:central}'
        '.pk{font:600 8.5px sans-serif;fill:#6B6280;text-anchor:middle;letter-spacing:.05em}'
        '.pf{font:600 8px sans-serif;fill:#A99FBF;text-anchor:middle}'
        '.pz{font:700 8px sans-serif;text-anchor:middle;letter-spacing:.16em}'
        '</style></defs>'
    )
    # zonas
    p.append('<path d="M230 46 L378 262 L82 262 Z" fill="#E4EFD3" opacity=".6"/>')
    p.append('<rect x="28" y="292" width="536" height="66" rx="9" fill="#EDE3F8"/>')
    p.append('<path d="M82 388 L378 388 L230 604 Z" fill="#FBDCE1" opacity=".55"/>')
    p.append('<text class="pz" x="140" y="34" fill="#7CB342">SER SUPERIOR · REALIZACIONES</text>')
    p.append('<text class="pz" x="120" y="286" fill="#6D28D9">HORIZONTAL · IDENTIDAD</text>')
    p.append('<text class="pz" x="118" y="382" fill="#C0392B">SER INFERIOR · DESAFÍOS</text>')
    # conectores
    p.append(
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
        r = 27 if zone in ("hor", "hor2") else (25 if zone.startswith("ext") else
             (22 if zone == "inf-sm" else (24 if zone in ("inf", "shadow") else 26)))
        if key == "B":
            r = 35
        stroke = ""
        if zone in ("inf", "inf-sm"):
            stroke = ' stroke="#E8304F" stroke-width="1.6"'
        elif zone.startswith("ext"):
            dash = ' stroke-dasharray="4 3"' if zone == "ext-dash" else ""
            stroke = f' stroke="#2047C5" stroke-width="2"{dash}'
        num_color = GREY if is_zero and zone in ("inf", "inf-sm") else ink
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{stroke}'
                 + (' stroke="#D3AE36" stroke-width="2.5"' if key == "B" else "") + '/>')
        fs = 27 if key == "B" else (18 if zone in ("inf", "inf-sm", "ext", "ext-dash") else 21)
        p.append(f'<text x="{cx}" y="{cy}" style="font:700 {fs}px sans-serif;'
                 f'fill:{num_color};text-anchor:middle;dominant-baseline:central">'
                 f'{_esc(str(vib))}</text>')
        if label:
            ly = _LABEL_BELOW.get(key) or _LABEL_ABOVE.get(key)
            if ly:
                p.append(f'<text class="pk" x="{cx}" y="{ly}">{_esc(label)}</text>')

    # súper ocultos etiqueta común
    p.append('<text class="pz" x="462" y="520" fill="#C0392B">Q · R · S — SÚPER OCULTOS</text>')

    # ausencias (T)
    aus = " · ".join(str(a) for a in pin.absences) or "—"
    p.append('<rect x="590" y="446" width="118" height="52" rx="8" fill="#fff" '
             'stroke="#E8304F" stroke-width="1.7" stroke-dasharray="5 4"/>')
    p.append(f'<text x="649" y="468" style="font:700 17px serif;fill:#C0392B;'
             f'text-anchor:middle">{_esc(aus)}</text>')
    p.append('<text class="pk" x="649" y="486" fill="#C0392B">T · AUSENCIAS</text>')

    p.append('</svg>')
    return "".join(p)


# --------------------------------------------------------------------------- #
# 2 · La tira del nombre
# --------------------------------------------------------------------------- #
_VOWELS = {"a": 1, "e": 5, "i": 9, "o": 6, "u": 3}
_CONS = {
    "b": 2, "c": 3, "d": 4, "f": 6, "g": 7, "h": 8, "j": 1, "k": 11, "l": 3,
    "m": 4, "n": 5, "p": 7, "q": 8, "r": 9, "s": 1, "t": 2, "v": 22, "w": 5,
    "x": 6, "y": 7, "z": 8, "ñ": 5,
}


def name_strip_svg(name_sanitize: str, alma: str, expresion: str) -> str:
    letters = [c for c in name_sanitize.replace("-", "") if c in _VOWELS or c in _CONS]
    n = len(letters)
    if n == 0:
        return ""
    W = 720
    step = min(34, (W - 40) / max(n, 1))
    x0 = (W - step * (n - 1)) / 2

    p = [f'<svg viewBox="0 0 {W} 200" role="img" aria-label="Valor de cada letra del nombre">']
    p.append(
        '<defs><style>'
        '.lt{font:400 20px serif;fill:#2A1E3E;text-anchor:middle;dominant-baseline:central}'
        '.lv{font:600 11px sans-serif;text-anchor:middle;dominant-baseline:central}'
        '.lh{font:600 8.5px sans-serif;letter-spacing:.14em}'
        '</style></defs>'
    )
    p.append(f'<text class="lh" x="6" y="16" fill="#96751B">VOCALES · ALMA {_esc(alma)}</text>')
    p.append(f'<text class="lh" x="6" y="192" fill="#4C1D95">CONSONANTES · EXPRESIÓN {_esc(expresion)}</text>')
    p.append(f'<line x1="0" y1="100" x2="{W-42}" y2="100" stroke="#E6DDEE"/>')

    for i, ch in enumerate(letters):
        x = x0 + i * step
        p.append(f'<text class="lt" x="{x:.0f}" y="100">{_esc(ch.upper())}</text>')
        if ch in _VOWELS:
            p.append(f'<text class="lv" x="{x:.0f}" y="60" fill="#96751B">{_VOWELS[ch]}</text>')
            p.append(f'<circle cx="{x:.0f}" cy="76" r="2.4" fill="#D3AE36"/>')
        else:
            p.append(f'<text class="lv" x="{x:.0f}" y="140" fill="#5B21B6">{_CONS[ch]}</text>')
    p.append('</svg>')
    return "".join(p)


# --------------------------------------------------------------------------- #
# 3 · Cuadrícula de presencias y ausencias (1–9)
# --------------------------------------------------------------------------- #
def absences_svg(pin: Pinnacle, area: str = PRIMARY) -> str:
    absent = set(pin.absences)
    p = ['<svg viewBox="0 0 300 216" role="img" aria-label="Números presentes y ausentes">']
    p.append('<defs><style>.gg{font:800 26px sans-serif;text-anchor:middle;'
             'dominant-baseline:central}</style></defs>')
    for idx in range(9):
        n = idx + 1
        col, row = idx % 3, idx // 3
        x, y = 34 + col * 83, 18 + row * 62
        if n in absent:
            p.append(f'<rect x="{x}" y="{y}" width="66" height="52" rx="7" fill="none" '
                     f'stroke="#D9D2E6" stroke-width="2" stroke-dasharray="5 4"/>')
            p.append(f'<text class="gg" x="{x+33}" y="{y+26}" fill="#C9C0D8">{n}</text>')
        else:
            p.append(f'<rect x="{x}" y="{y}" width="66" height="52" rx="7" fill="{area}"/>')
            p.append(f'<text class="gg" x="{x+33}" y="{y+26}" fill="#fff">{n}</text>')
    p.append('</svg>')
    return "".join(p)


# --------------------------------------------------------------------------- #
# 4 · Línea de las cuatro etapas de vida
# --------------------------------------------------------------------------- #
def stages_svg(pin: Pinnacle, today_age: int, area: str = PRIMARY) -> str:
    stages = pin.stages
    W = 720
    # ancho proporcional a la duración; la 4.ª (abierta) se dibuja fija
    lengths = []
    for s in stages:
        lengths.append((s.end_age - s.start_age) if s.end_age is not None else 9)
    total = sum(lengths)
    p = [f'<svg viewBox="0 0 {W} 130" role="img" aria-label="Etapas de vida">']
    p.append('<defs><style>'
             '.en{font:700 20px sans-serif;fill:#fff;text-anchor:middle;dominant-baseline:central}'
             '.ey{font:600 10px sans-serif;fill:#6B6280;text-anchor:middle}'
             '.ee{font:500 9.5px sans-serif;fill:#A99FBF;text-anchor:middle}'
             '.eh{font:700 8.5px sans-serif;fill:#4C1D95;text-anchor:middle;letter-spacing:.14em}'
             '</style></defs>')
    x = 10
    avail = W - 20
    cur = None
    for i, s in enumerate(stages):
        w = avail * lengths[i] / total
        active = s.contains_age(today_age)
        op = "1" if active else (".5" if i % 2 == 0 else ".34")
        p.append(f'<rect x="{x:.0f}" y="46" width="{w-4:.0f}" height="42" rx="4" '
                 f'fill="{area}" opacity="{op}"/>')
        cx = x + w / 2
        p.append(f'<text class="en" x="{cx:.0f}" y="67">{_esc(str(s.realization))}</text>')
        p.append(f'<text class="ey" x="{cx:.0f}" y="106">{_esc(s.year_range)}</text>')
        p.append(f'<text class="ee" x="{cx:.0f}" y="120">{_esc(s.age_range)} años</text>')
        if active:
            cur = cx
        x += w
    if cur is not None:
        p.append(f'<text class="eh" x="{cur:.0f}" y="14">ESTÁS AQUÍ · {today_age} AÑOS</text>')
        p.append(f'<path d="M{cur:.0f} 20 L{cur:.0f} 40" stroke="{area}" stroke-width="2"/>')
        p.append(f'<circle cx="{cur:.0f}" cy="42" r="4" fill="{area}"/>')
    p.append('</svg>')
    return "".join(p)


# --------------------------------------------------------------------------- #
# 5 · Rueda del año personal (1→9, con 11)
# --------------------------------------------------------------------------- #
def personal_year_svg(ap: str, area: str = PRIMARY) -> str:
    import math
    ring = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    # el 11 (año personal) se resalta en el centro; en la rueda va sobre el "2"
    active = "2" if ap == "11" else ap
    p = ['<svg viewBox="0 0 300 210" role="img" aria-label="Año personal">']
    cx, cy, R = 150, 105, 92
    for i, lab in enumerate(ring):
        a0 = -math.pi / 2 + i * 2 * math.pi / 9
        a1 = -math.pi / 2 + (i + 1) * 2 * math.pi / 9
        x0, y0 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        op = "1" if lab == active else ".13"
        p.append(f'<path d="M{cx} {cy} L{x0:.1f} {y0:.1f} A{R} {R} 0 0 1 '
                 f'{x1:.1f} {y1:.1f} Z" fill="{area}" opacity="{op}"/>')
        am = (a0 + a1) / 2
        lx, ly = cx + (R - 14) * math.cos(am), cy + (R - 14) * math.sin(am)
        col = "#fff" if lab == active else INK
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" style="font:700 11px sans-serif;'
                 f'fill:{col};text-anchor:middle;dominant-baseline:central">{lab}</text>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="42" fill="#fff" stroke="#E6DDEE"/>')
    p.append(f'<text x="{cx}" y="{cy-4}" style="font:800 32px serif;fill:{area};'
             f'text-anchor:middle">{_esc(ap)}</text>')
    p.append(f'<text x="{cx}" y="{cy+18}" style="font:700 7.5px sans-serif;'
             f'fill:#6B6280;text-anchor:middle;letter-spacing:.14em">AÑO PERSONAL</text>')
    p.append('</svg>')
    return "".join(p)


__all__ = ["pinnacle_svg", "name_strip_svg", "absences_svg", "stages_svg",
           "personal_year_svg"]
