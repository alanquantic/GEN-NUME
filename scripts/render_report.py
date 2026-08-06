"""Maqueta un reporte: JSON (fase 4/mock) + números → HTML → PDF.

    # desde el ejemplo mock, sin API ni PDF nativo (genera HTML siempre):
    py -3 scripts/render_report.py quien-soy "Juan Pedro Martinez" 1991-11-20 --mock

    # desde un JSON ya generado:
    py -3 scripts/render_report.py amor "Ana" 1988-03-05 --json ruta/al/reporte.json

Escribe el HTML (y el PDF si WeasyPrint puede cargar sus libs nativas) en el
scratchpad. El HTML se puede abrir en el navegador para revisar la maqueta.
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai import generate as gen         # noqa: E402
from app.ai import numbers as num          # noqa: E402
from app.ai.recipes import REPORTS         # noqa: E402
from app.domain.dates import format_long_date  # noqa: E402
from app.pdf import html_renderer as hr    # noqa: E402

OUT = Path(r"C:/Users/andre/AppData/Local/Temp/claude/"
           r"C--Users-andre-Documents-claude-GEN/"
           r"61004e3c-909a-46cd-b3e6-df09ec4b615f/scratchpad")


def _date(s: str) -> date:
    return date.fromisoformat(s)


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3:
        print(__doc__)
        print("Reportes:", ", ".join(REPORTS))
        return 1

    report_key, name, birth = args[0], args[1], _date(args[2])
    today = date(2026, 7, 29)
    mock = "--mock" in args
    json_path = None
    partner_name = partner_birth = None

    if "--json" in args:
        json_path = Path(args[args.index("--json") + 1])
    if "--partner" in args:
        i = args.index("--partner")
        partner_name, partner_birth = args[i + 1], _date(args[i + 2])
    if "--today" in args:
        today = _date(args[args.index("--today") + 1])

    if report_key not in REPORTS:
        print(f"Reporte desconocido: {report_key}")
        return 1
    report = REPORTS[report_key]

    # Los números (para gráficos, ficha, márgenes)
    numbers = num.resolve(name, birth, today=today,
                          partner_birth_date=partner_birth)

    # El contenido: de un JSON, del mock, o error
    if json_path:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        data.pop("_mock", None)
    elif mock:
        data, *_ = gen._load_mock(report_key)   # respuesta de ejemplo
    else:
        print("Indica --mock o --json <ruta>. (La llamada real al modelo es "
              "scripts/generate_report.py.)")
        return 1

    html = hr.render_html(
        report_key, data, numbers,
        report_title=report.title, area_token=report.area,
        person_name=name, birth_long=format_long_date(birth),
        today_long=format_long_date(today),
        today_age=numbers.pinnacle.age_at(today),
        birth_date=birth,
        today=today,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    html_path = OUT / f"maqueta-{report_key}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML -> {html_path}  ({len(html):,} chars)")
    print(f"       páginas ≈ {html.count('class=\"page\"')}")

    try:
        pdf = hr.to_pdf(html)
        pdf_path = OUT / f"maqueta-{report_key}.pdf"
        pdf_path.write_bytes(pdf)
        print(f"PDF  -> {pdf_path}  ({len(pdf):,} bytes)")
    except RuntimeError as exc:
        print(f"PDF  -> no generado: {exc}")
        print("       (el HTML es válido; el PDF sale en el deploy Linux)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
