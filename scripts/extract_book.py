"""Extrae del libro de Laura las interpretaciones que faltaban en el corpus web.

    py -3 scripts/extract_book.py

El export de WordPress (`docs/new-reports/`) cubre bien las posiciones clásicas
del Pináculo, pero **no tiene texto por vibración** para trece de ellas:
K, L, M, N (desafíos), O, Q, R, S (ser inferior), T (ausencias), W (triplicidad),
X (reacción), Y (síntesis) y Z (regalo divino).

El capítulo VIII del libro sí las interpreta, una por una. Este script las saca
del `.docx` y las escribe en `docs/libro/` **con la misma estructura que el
corpus web** (`## Significados por número` + `### Número N`), de modo que
`build_kb.py` las trocea con el mismo código, sin ramas especiales.

En el `.docx` estos subtítulos son párrafos normales, sin estilo de encabezado,
así que se detectan por patrón de texto. Cada patrón está verificado contando
los trozos que produce (ver la columna «esperado»).
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
BOOK = ROOT / "docs" / "new-reports" / "LIBRO FINAL-LAURA de 26 de JULIO.docx FINAL.docx"
TARGET = ROOT / "docs" / "libro"

# (ancla de la sección, patrón del subtítulo, slug, título, resumen, esperados)
# El ancla y el subtítulo NO coinciden: el libro titula la sección "Número del
# Inconsciente Negativo (O)" pero encabeza cada trozo con "Inconsciente Negativo
# Número 3". Por eso van separados.
SECTIONS = [
    (r"significados de los 4 Desaf",   r"Desaf[íi]o N[úu]mero",           "desafios-k-l-m-n",
     "Los 4 Desafíos de Vida (K, L, M, N)",
     "El desafío específico a superar en cada etapa. K↔E, L↔F, M↔G, N↔H.", 9),
    (r"Inconsciente Negativo \(O\)",   r"Inconsciente Negativo N[úu]mero", "inconsciente-negativo-o",
     "Número del Inconsciente Negativo (O)",
     "Los frenos invisibles: el «no se puede» heredado del clan.", 8),
    (r"de Sombra \(P\)",               r"Sombra N[úu]mero",                "sombra-p",
     "Número de la Sombra (P)",
     "Lo que rechazamos de nuestro ser y opera sin que lo veamos.", 9),
    (r"Ser Inferior \(Q",               r"Ser Inferior",                    "super-ocultos-q-r-s",
     "Números Súper Ocultos (Q, R, S)",
     "Las estrategias que usamos y nos producen culpa: lo imperdonable, "
     "lo inconfesable y lo impensable.", 10),
    (r"N[úu]meros Ausentes \(T\)",     r"N[úu]mero Ausente",               "ausencias-t",
     "Números Ausentes (T)",
     "Las vibraciones que no aparecen en el Pináculo y se expresan sin control.", 9),
    (r"de Triplicidad \(W\)",          r"Triplicidad N[úu]mero",           "triplicidad-w",
     "Número de la Triplicidad (W)",
     "La sombra emocional que nace de tres vibraciones iguales.", 9),
    (r"de Reacci[óo]n \(X\)",          r"N[úu]mero de Reacci[óo]n",        "reaccion-x",
     "Número de Reacción (X)",
     "La personalidad energética ante el mundo: comportamiento, postura, "
     "somatizaciones y cómo te ven los demás.", 11),
    (r"S[íi]ntesis \(Y\)",             r"N[úu]mero de Misi[óo]n",          "sintesis-y",
     "Número de Síntesis o Misión (Y)",
     "La confirmación de la misión de vida.", 11),
    (r"Regalo Divino \(Z\)",           r"Regalo Divino",                   "regalo-divino-z",
     "Número del Regalo Divino (Z)",
     "El don espiritual innato que sostiene en la crisis.", 9),
]

# Un subtítulo válido es: <patrón> <número> y, como mucho, una coletilla tras
# un guion, dos puntos o un paréntesis. Así se descartan las líneas de fórmula
# («Regalo Divino (Z) = 4») y las de ejemplo.
def heading_re(prefix: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\s*{prefix}\s+(0|[1-9]|1[12]|22)\s*(?:[–—:\-(].*)?$",
        re.IGNORECASE,
    )


def read_paragraphs(path: Path) -> list[str]:
    xml = zipfile.ZipFile(path).read("word/document.xml")
    root = ET.fromstring(xml)
    out = []
    for p in root.iter(f"{W}p"):
        text = "".join(t.text or "" for t in p.iter(f"{W}t")).strip()
        if text:
            out.append(text)
    return out


def slice_section(lines: list[str], start: int, end: int,
                  pattern: re.Pattern[str]) -> dict[str, list[str]]:
    """Trocea [start, end) por las cabeceras que casen con `pattern`."""
    slices: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines[start:end]:
        m = pattern.match(line)
        if m:
            current = m.group(1)
            slices.setdefault(current, [])
            continue
        if current is not None:
            slices[current].append(line)
    return {k: v for k, v in slices.items() if v}


def main() -> int:
    if not BOOK.exists():
        print(f"No encuentro el libro en {BOOK}")
        return 1

    lines = read_paragraphs(BOOK)
    print(f"Libro: {len(lines):,} párrafos\n")

    # Índices de cada bloque «Interpretaciones ... (LETRA)»
    marks = [i for i, l in enumerate(lines) if re.match(r"^Interpretaci", l)]
    marks.append(len(lines))

    TARGET.mkdir(parents=True, exist_ok=True)
    print(f"{'documento':<26} {'trozos':>7} {'esperado':>9} {'chars':>10}")
    print("-" * 58)

    problems = 0
    for anchor_re, prefix, slug, title, summary, expected in SECTIONS:
        # el bloque cuyo encabezado contiene el patrón de esta posición
        anchor = next(
            (m for m in marks[:-1] if re.search(anchor_re, lines[m], re.IGNORECASE)),
            None,
        )
        if anchor is None:
            print(f"{slug:<26} {'—':>7}   sección no encontrada")
            problems += 1
            continue
        end = next(m for m in marks if m > anchor)

        slices = slice_section(lines, anchor, end, heading_re(prefix))
        if not slices:
            print(f"{slug:<26} {'—':>7}   sin trozos (revisar patrón)")
            problems += 1
            continue

        body = [f"# {title}", "", f"> {summary}", "",
                "_Fuente: LIBRO FINAL-LAURA de 26 de JULIO · capítulo VIII_", "",
                "## Significados por número", ""]
        for key in sorted(slices, key=lambda k: (len(k), int(k))):
            body += [f"### Número {key}", ""] + slices[key] + [""]
        text = "\n".join(body)

        (TARGET / f"{slug}.md").write_text(text, encoding="utf-8")
        flag = " " if len(slices) >= expected else "!"
        if len(slices) < expected:
            problems += 1
        print(f"{slug:<26} {len(slices):>7}{flag} {expected:>8} {len(text):>10,}")

    print("-" * 58)
    print(f"\nEscrito en {TARGET.relative_to(ROOT)}/")
    print(f"{problems} sección(es) con problemas")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
