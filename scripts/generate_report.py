"""Genera un reporte. Con el modelo real (requiere ANTHROPIC_API_KEY) o en modo
de prueba (--mock), que usa una respuesta de ejemplo sin tocar la red.

    # modo de prueba, sin API — para ver el flujo completo hasta el texto:
    py -3 scripts/generate_report.py quien-soy "Juan Pedro Martinez" 1991-11-20 --mock

    # real:
    export ANTHROPIC_API_KEY=sk-ant-...       # o en .env
    py -3 scripts/generate_report.py amor "Juan Pedro Martinez" 1991-11-20
    py -3 scripts/generate_report.py amor "Ana" 1988-03-05 --partner "Luis" 1985-07-12

Guarda el JSON en el scratchpad e imprime un resumen legible (títulos de
sección, tokens, coste estimado y avisos de anclaje). No maqueta el PDF — eso es
la fase 5; aquí se valida que el TEXTO merece la pena.
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

from app.ai import dossier as dsr        # noqa: E402
from app.ai import generate as gen       # noqa: E402
from app.ai.recipes import REPORTS       # noqa: E402
from app.config import settings          # noqa: E402
from app.domain.dates import format_long_date  # noqa: E402

OUT = Path(r"C:/Users/andre/AppData/Local/Temp/claude/"
           r"C--Users-andre-Documents-claude-GEN/"
           r"61004e3c-909a-46cd-b3e6-df09ec4b615f/scratchpad")

# Precios por millón de tokens (entrada, salida). Gemini 2.5 Flash tiene un
# tier gratuito generoso en AI Studio; los precios listados son de pago.
PRICE = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "gemini-2.5-pro": (1.25, 10.0),
    "gemini-2.5-flash": (0.30, 2.50),
}


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
    mock = "--mock" in args

    if "--partner" in args:
        i = args.index("--partner")
        partner_name, partner_birth = args[i + 1], _date(args[i + 2])
    if "--today" in args:
        today = _date(args[args.index("--today") + 1])

    if report_key not in REPORTS:
        print(f"Reporte desconocido: {report_key}")
        return 1
    if not mock and not _has_key():
        env = "GOOGLE_API_KEY" if settings.ai_provider == "google" else "ANTHROPIC_API_KEY"
        print(f"Falta {env} (en el entorno o en .env).")
        print("Para ver el flujo sin clave, añade  --mock")
        return 1

    d = dsr.build(report_key, name, birth, today=today,
                  partner_name=partner_name, partner_birth_date=partner_birth)

    label = "MODO DE PRUEBA (respuesta de ejemplo)" if mock else \
        f"{settings.ai_provider} · {settings.resolved_model}"
    print(f"Generando «{d.report.title}» para {name} ({birth})…")
    print(f"Modelo: {label}"
          + ("" if mock or settings.ai_provider != "anthropic"
             else f" · effort {settings.ai_effort}")
          + f" · dossier ~{d.approx_tokens:,} tokens")
    if d.skipped:
        print(f"Piezas omitidas: {len(d.skipped)} "
              f"({', '.join(s[0].split('/')[-1] for s in d.skipped)})")
    print()

    result = gen.generate(
        d,
        person_name=name,
        birth_long=format_long_date(birth),
        today_long=format_long_date(today),
        partner_name=partner_name,
        partner_birth_long=format_long_date(partner_birth) if partner_birth else None,
        mock=mock,
    )

    _print_summary(result)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"reporte-{report_key}.json"
    out.write_text(json.dumps(result.data, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    txt = OUT / f"reporte-{report_key}.txt"
    txt.write_text(_render_readable(result.data), encoding="utf-8")
    print(f"\nJSON  -> {out}")
    print(f"Texto -> {txt}")
    return 0


def _has_key() -> bool:
    import os
    if settings.ai_provider == "google":
        return bool(settings.google_api_key or os.environ.get("GOOGLE_API_KEY")
                    or os.environ.get("GEMINI_API_KEY"))
    return bool(settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"))


def _print_summary(r: gen.GeneratedReport) -> None:
    d = r.data
    print("=" * 72)
    print(f"  {d.get('titulo', '?')}")
    print(f"  {d.get('subtitulo', '')}")
    print(f"  «{d.get('frase_clave', '')}»")
    print("=" * 72)
    print(f"\n  Retrato: {d.get('retrato', {}).get('titulo', '')}")
    for sec in d.get("secciones", []):
        nums = ", ".join(sec.get("numeros", []))
        print(f"    · {sec.get('id', '?'):<14} {sec.get('titulo', ''):<38} [{nums}]")
    t = d.get("tension_central", {})
    print(f"\n  Tensión central: {t.get('titulo', '')} "
          f"({' vs '.join(t.get('numeros', []))})")
    print(f"  Plan: {len(d.get('plan', []))} prácticas")

    inp, out = r.usage["input"], r.usage["output"]
    cr = r.usage["cache_read"]
    print(f"\n  Tokens: entrada {inp:,} (cache {cr:,}) · salida {out:,}")
    if r.model in PRICE:
        pin, pout = PRICE[r.model]
        cost = (inp - cr) / 1e6 * pin + cr / 1e6 * pin * 0.1 + out / 1e6 * pout
        print(f"  Coste estimado: ${cost:.3f}")

    if r.warnings:
        print(f"\n  ⚠ AVISOS DE ANCLAJE ({len(r.warnings)}):")
        for w in r.warnings:
            print(f"     - {w}")
    else:
        print("\n  ✓ anclaje correcto: toda clave declarada existe en <numeros>")


def _render_readable(d: dict) -> str:
    lines = [d.get("titulo", ""), d.get("subtitulo", ""),
             f"«{d.get('frase_clave', '')}»", "", d.get("resumen_portada", ""), ""]
    r = d.get("retrato", {})
    lines += [f"== {r.get('titulo', 'Retrato')} =="] + r.get("cuerpo", []) + [""]
    for sec in d.get("secciones", []):
        lines.append(f"== {sec.get('titulo', '')} ==")
        if sec.get("entradilla"):
            lines.append(f"[{sec['entradilla']}]")
        lines += sec.get("cuerpo", [])
        dest = sec.get("destacado")
        if dest:
            lines.append(f"  » ({dest.get('tipo')}) {dest.get('texto')}")
        if sec.get("cierre_accionable"):
            lines.append(f"  → {sec['cierre_accionable']}")
        lines.append("")
    t = d.get("tension_central", {})
    lines += [f"== {t.get('titulo', 'La tensión central')} =="] + t.get("cuerpo", [])
    lines.append(f"  → {t.get('como_resolverla', '')}")
    lines.append("")
    lines.append("== Tu plan ==")
    for p in d.get("plan", []):
        lines.append(f"  • {p.get('titulo')}: {p.get('texto')}")
    lines += ["", d.get("cierre", "")]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
