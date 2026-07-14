"""Extrae los textos `getTextXxx($n)` del helpers.php original a content/texts.json.

Uso:
    py -3 scripts/extract_content.py ../reports-pdf/src/helpers.php content/texts.json

Es una herramienta de migración de una sola vez: evita transcribir a mano los
bloques largos de texto en español (y los errores que eso conlleva).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FUNC_RE = re.compile(r"function\s+(getText\w+)\s*\(\s*\$n\s*\)\s*\{", re.S)
# Cadena PHP entre comillas simples: '...'; respeta \' y \\
CASE_RE = re.compile(r"case\s*(\d+)\s*:\s*return\s*'((?:[^'\\]|\\.)*)'\s*;", re.S)


def unescape_php_single_quoted(s: str) -> str:
    # En PHP con comillas simples solo se escapan \' y \\
    return s.replace("\\'", "'").replace("\\\\", "\\")


def extract(php_source: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    matches = list(FUNC_RE.finditer(php_source))
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(php_source)
        body = php_source[start:end]
        cases = {
            num: unescape_php_single_quoted(text)
            for num, text in CASE_RE.findall(body)
        }
        if cases:
            result[name] = cases
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    source = src_path.read_text(encoding="utf-8")
    data = extract(source)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(len(v) for v in data.values())
    print(f"Funciones extraidas: {len(data)}  |  casos totales: {total}")
    for name, cases in sorted(data.items()):
        print(f"  {name}: {len(cases)} numeros -> {', '.join(sorted(cases, key=int))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
