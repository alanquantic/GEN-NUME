"""Inspecciona el dossier de un reporte sin llamar al modelo.

    py -3 scripts/preview_dossier.py amor "Juan Pedro Martinez" 1991-11-20
    py -3 scripts/preview_dossier.py amor "Ana" 1988-03-05 --partner "Luis" 1985-07-12
    py -3 scripts/preview_dossier.py quien-soy "Ana" 1988-03-05 --dump

Muestra los números resueltos, las piezas incluidas, las omitidas (con motivo)
y el tamaño del dossier. Con --dump vuelca el material completo a un fichero del
scratchpad para leerlo entero.
"""

from __future__ import annotations

import io
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai import dossier as dsr  # noqa: E402
from app.ai.recipes import REPORTS  # noqa: E402


def _date(s: str) -> date:
    return date.fromisoformat(s)


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3:
        print(__doc__)
        print("Reportes:", ", ".join(REPORTS))
        return 1

    report_key, name, birth = args[0], args[1], _date(args[2])
    partner_name = partner_birth = None
    today = date(2026, 7, 29)
    dump = "--dump" in args

    if "--partner" in args:
        i = args.index("--partner")
        partner_name, partner_birth = args[i + 1], _date(args[i + 2])
    if "--today" in args:
        today = _date(args[args.index("--today") + 1])

    if report_key not in REPORTS:
        print(f"Reporte desconocido: {report_key}\nDisponibles: {', '.join(REPORTS)}")
        return 1

    d = dsr.build(
        report_key, name, birth, today=today,
        partner_name=partner_name, partner_birth_date=partner_birth,
    )

    print(f"Reporte : {d.report.title}  ({report_key})")
    print(f"Persona : {name}  ·  {birth}  ·  hoy {today}")
    if partner_name:
        print(f"Pareja  : {partner_name}  ·  {partner_birth}")
    print()

    print("NÚMEROS")
    print("-" * 78)
    for line in d.numbers_block.splitlines():
        print("  " + line if line.strip() else line)
    print()

    print("PIEZAS INCLUIDAS")
    print("-" * 78)
    for p in d.pieces:
        tag = f"{p.key}={p.value}" if p.value else p.selector
        print(f"  ✓ {p.doc_title[:44]:<46} {tag:<14} {len(p.text):>6,} chars")

    if d.skipped:
        print("\nPIEZAS OMITIDAS")
        print("-" * 78)
        for slug, selector, motivo in d.skipped:
            print(f"  ✗ {slug.split('/')[-1]:<44} {selector:<16} {motivo}")

    print("\n" + "=" * 78)
    print(f"  {len(d.pieces)} piezas · material {len(d.material):,} chars · "
          f"~{d.approx_tokens:,} tokens")
    if d.numbers.unresolved:
        print(f"  claves sin fórmula (omitidas): {', '.join(sorted(d.numbers.unresolved))}")

    if dump:
        out = ROOT / ".." / ".." / "scratchpad" if False else Path(
            r"C:/Users/andre/AppData/Local/Temp/claude/"
            r"C--Users-andre-Documents-claude-GEN/"
            r"61004e3c-909a-46cd-b3e6-df09ec4b615f/scratchpad") / f"dossier-{report_key}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            f"# {d.report.title}\n\n## NÚMEROS\n\n{d.numbers_block}\n\n"
            f"## MATERIAL\n\n{d.material}\n", encoding="utf-8")
        print(f"\n  volcado -> {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
