"""Construye la base de conocimiento: trocea el corpus de Laura por vibración.

    py -3 scripts/build_kb.py                 # construye content/kb/index.json
    py -3 scripts/build_kb.py --check         # sólo valida, no escribe

Lee `docs/new-reports/**/*.md` y produce un índice `(documento, clave) -> texto`
que el ensamblador de dossiers consulta en O(1). No hay embeddings ni búsqueda
aproximada: la clave se conoce exactamente porque se acaba de calcular.

El corpus usa tres formas de trocear, y las tres se detectan a máquina:

  1. `### Número N`          tras `## Significados por número`   (37 documentos)
  2. `### Valor numérico N:` en la tabla de letras
  3. `### **-X-**`           por letra inicial

Además de construir, el script **valida las recetas contra el dominio real de
cada posición**, no contra una persona de ejemplo. El dominio se calcula por
fuerza bruta (`compute_domains`), enumerando todas las fechas de nacimiento
plausibles: dar por hecho que toda posición recorre 1–9, 11 y 22 produce avisos
falsos. El Año Personal, por ejemplo, **nunca vale 2 ni 22** en los años en que
el producto va a operar.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai.recipes import (  # noqa: E402
    DERIVED_KEYS, NAME_KEYS, PARTNER_KEYS, PARTNER_ONLY, PENDING_KEYS,
    PINNACLE_KEYS, REPORTS, TIME_KEYS, keys_used,
)

# Dos fuentes: el export de WordPress y las interpretaciones del libro
# (que `scripts/extract_book.py` normaliza al mismo formato).
SOURCES = {
    "web": ROOT / "docs" / "new-reports",
    "libro": ROOT / "docs" / "libro",
    # Material rescatado de otras fuentes (PDFs del catálogo original, blog)
    # para tapar huecos del export. Se fusiona sobre el documento que declare.
    "complementos": ROOT / "docs" / "complementos",
}
TARGET = ROOT / "content" / "kb" / "index.json"

LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

# Ventanas sobre las que se calcula el dominio real de cada posición.
BIRTH_YEARS = range(1935, 2016)      # clientes plausibles
OPERATING_YEARS = range(2025, 2036)  # años en que el producto estará vivo

# Claves cuyo valor depende del nombre: no se pueden enumerar por fuerza bruta,
# así que se asume el rango completo.
NAME_DOMAIN = frozenset(str(n) for n in range(1, 10)) | {"11", "22"}

_SPLIT_MEANINGS = re.compile(r"^## Significados por n[uú]mero\s*$", re.M)
_NUMBER_HEAD = re.compile(r"^### N[uú]mero\s+([0-9]{1,2})\s*$", re.M)
_VALUE_HEAD = re.compile(r"^### Valor num[eé]rico\s+([0-9]{1,2})\s*:?\s*$", re.M)
_LETTER_HEAD = re.compile(r"^###\s*\*{0,2}-\s*([A-ZÑ])\s*-\*{0,2}\s*$", re.M)
_TITLE = re.compile(r"^#\s+(.+)$", re.M)
_SUMMARY = re.compile(r"^>\s+(.+)$", re.M)
_EXTENDS = re.compile(r"<!--\s*extiende:\s*(\S+)\s*-->")


# --------------------------------------------------------------------------- #
# Troceado
# --------------------------------------------------------------------------- #
def split_by(pattern: re.Pattern[str], text: str) -> tuple[str, dict[str, str]]:
    """Parte `text` por las cabeceras de `pattern`. Devuelve (antes, trozos)."""
    parts = pattern.split(text)
    if len(parts) < 3:
        return text, {}
    head, slices = parts[0], {}
    for i in range(1, len(parts), 2):
        key, body = parts[i].strip().upper(), parts[i + 1].strip()
        if body:
            # Un documento puede repetir la misma cabecera (varias fuentes del
            # export): se concatenan en vez de pisarse.
            slices[key] = f"{slices[key]}\n\n{body}" if key in slices else body
    return head, slices


def parse_document(path: Path, source: Path, prefix: str) -> dict:
    text = path.read_text(encoding="utf-8")
    rel = str(path.relative_to(source)).replace("\\", "/")[: -len(".md")]
    slug = rel if prefix == "web" else f"{prefix}/{rel}"

    title_m = _TITLE.search(text)
    summary_m = _SUMMARY.search(text)

    # 1) el patrón principal, acotado tras "## Significados por número"
    parts = _SPLIT_MEANINGS.split(text, maxsplit=1)
    intro, body = parts[0], (parts[1] if len(parts) > 1 else "")
    _, slices = split_by(_NUMBER_HEAD, body)
    kind = "numero" if slices else None

    # 2) tabla de valores numéricos
    if not slices:
        head, slices = split_by(_VALUE_HEAD, text)
        if slices:
            intro, kind = head, "valor"

    # 3) por letra inicial
    if not slices:
        head, slices = split_by(_LETTER_HEAD, text)
        if slices:
            intro, kind = head, "letra"

    extends_m = _EXTENDS.search(text)

    return {
        "slug": slug,
        "source": prefix,
        "extends": extends_m.group(1) if extends_m else None,
        "title": title_m.group(1).strip() if title_m else slug,
        "summary": summary_m.group(1).strip() if summary_m else "",
        "kind": kind or "metodo",
        "intro": intro.strip(),
        "slices": slices,
    }


def build() -> dict:
    docs = {}
    for prefix, source in SOURCES.items():
        if not source.exists():
            continue
        for path in sorted(source.rglob("*.md")):
            if path.name == "README.md":
                continue
            doc = parse_document(path, source, prefix)
            docs[doc["slug"]] = doc
    return apply_overlays(docs)


def apply_overlays(docs: dict) -> dict:
    """Fusiona los complementos sobre el documento que declaran extender.

    Un complemento lleva `<!-- extiende: <slug> -->` en la cabecera. Sus trozos
    se añaden a los del documento destino **sin pisar los que ya existan**: el
    export original manda, el complemento sólo tapa huecos. Así el rescate de
    material no obliga a tocar las recetas.
    """
    overlays = [d for d in docs.values() if d["extends"]]
    if overlays:
        print("Complementos aplicados")
        print("-" * 78)
    for overlay in overlays:
        target = docs.get(overlay["extends"])
        if target is None:
            print(f"  ✗ {overlay['slug']}: no existe el destino "
                  f"{overlay['extends']}")
            continue
        added = []
        for key, body in overlay["slices"].items():
            if key in target["slices"]:
                continue
            target["slices"][key] = body
            added.append(key)
        target.setdefault("completed_by", []).append(
            {"slug": overlay["slug"], "keys": sort_vibrations(added)}
        )
        print(f"  ✓ {overlay['extends'].split('/')[-1]:<40} "
              f"+{','.join(sort_vibrations(added)) or 'nada'}  "
              f"(desde {overlay['slug'].split('/')[-1]})")
        docs.pop(overlay["slug"], None)
    if overlays:
        print()
    return docs


# --------------------------------------------------------------------------- #
# Dominio real de cada posición
# --------------------------------------------------------------------------- #
def compute_domains() -> dict[str, set[str]]:
    """Qué valores puede tomar de verdad cada clave, por fuerza bruta.

    Asumir que toda posición recorre 1–9, 11 y 22 produce avisos falsos. El
    Año Personal es el ejemplo claro: **el 2 es imposible**, porque para
    reducir a 2 habría que pasar por 20 (inalcanzable) o por 11, que al ser
    maestro se queda en 11. Lo mismo con el 22.

    Se enumeran todas las fechas de nacimiento plausibles y todos los años de
    operación, y se recoge lo que sale. Nada de suposiciones.
    """
    import calendar
    from datetime import date

    from app.domain.numerology import reduce_number
    from app.domain.pinnacle import Pinnacle

    domains: dict[str, set[str]] = {}

    def add(key: str, value) -> None:
        domains.setdefault(key, set()).add(str(value))

    for year in BIRTH_YEARS:
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                pin = Pinnacle.from_date(date(year, month, day))
                for key, vib in pin.as_positions().items():
                    add(key, vib.value)
                for n, stage in enumerate(pin.stages, start=1):
                    add(f"E{n}", stage.realization.value)
                if pin.w is not None:
                    add("W", pin.w.value)
                if pin.w_source is not None:
                    add("W_DIGIT", pin.w_source)
                for absent in pin.absences:
                    add("AUSENCIAS", absent)

    # Año personal / mes personal sobre los años de operación
    for oper in OPERATING_YEARS:
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(2024, month)[1] + 1):
                add("AP", reduce_number(day + month + oper))
                for cur in range(1, 13):
                    add("MP", reduce_number(reduce_number(day + month + oper) + cur))

    # La realización vigente es una de las cuatro etapas
    domains["REALIZACION"] = set().union(*(domains[f"E{n}"] for n in range(1, 5)))
    # Pareja: la suma de dos personales, y el año de la relación
    domains["PAREJA"] = domains["ANIO_REL"] = NAME_DOMAIN | {"0"}
    for key in ("ALMA", "EXPRESION", "NOMBRE", "ACTIVO"):
        domains[key] = set(NAME_DOMAIN)
    domains["INICIAL"] = set(LETTERS)
    domains["MADUREZ"] = set(NAME_DOMAIN)           # D + NOMBRE
    domains["MAESTRO"] = set(domains["F"])          # = 2.ª etapa (posición F)
    domains["PROYECTO"] = set(domains["ALMA"])      # = suma de vocales (ALMA)

    return domains


def sort_vibrations(values) -> list[str]:
    return sorted(values, key=lambda v: (len(v), v))


# --------------------------------------------------------------------------- #
# Validación de cobertura
# --------------------------------------------------------------------------- #
def check_coverage(docs: dict, domains: dict[str, set[str]]) -> tuple[int, int]:
    """Comprueba que cada pieza tenga texto para cada valor REALMENTE posible."""
    print("Cobertura de las recetas (contra el dominio real de cada posición)")
    print("=" * 78)

    problems, warnings = 0, 0
    for report in REPORTS.values():
        print(f"\n  {report.key}  ·  {report.title}")
        for slug, selector in report.pieces:
            doc = docs.get(slug)
            optional = " (sólo con pareja)" if (slug, selector) in PARTNER_ONLY else ""
            label = f"    {slug.split('/')[-1]:<42} {selector:<18}"

            if doc is None:
                print(f"{label} ✗ DOCUMENTO INEXISTENTE")
                problems += 1
                continue

            if selector in ("@intro", "@whole"):
                size = len(doc["intro"])
                flag = "✓" if size > 400 else "!"
                if flag == "!":
                    warnings += 1
                print(f"{label} {flag} {size:>7,} chars{optional}")
                continue

            mode, key = selector.split(":", 1)
            expected = domains.get(key)
            if expected is None:
                print(f"{label} ✗ CLAVE SIN DOMINIO CONOCIDO")
                problems += 1
                continue

            missing = sort_vibrations(expected - set(doc["slices"]))
            present = len(doc["slices"])
            if missing:
                warnings += 1
                print(f"{label} ! {present:>2} trozos · faltan {','.join(missing)}"
                      f" (de {len(expected)} posibles){optional}")
            else:
                print(f"{label} ✓ {present:>2} trozos cubren los "
                      f"{len(expected)} posibles{optional}")

    print("\n" + "=" * 78)
    return problems, warnings


def check_keys() -> None:
    """Qué claves de número hace falta calcular, y cuáles no existen aún."""
    used: set[str] = set()
    for report in REPORTS.values():
        used |= keys_used(report)

    known = PINNACLE_KEYS | NAME_KEYS | TIME_KEYS | PARTNER_KEYS | DERIVED_KEYS
    pending = sorted(used & PENDING_KEYS)
    unknown = sorted(used - known - PENDING_KEYS)

    print("\nClaves de número que usan las recetas")
    print("-" * 78)
    print(f"  ya calculadas ({len(used & known)}): {', '.join(sorted(used & known))}")
    if pending:
        print(f"  SIN CALCULADOR ({len(pending)}): {', '.join(pending)}")
        print("     → los documentos existen; falta la fórmula. Fase 3.")
    if unknown:
        print(f"  DESCONOCIDAS ({len(unknown)}): {', '.join(unknown)}")


def report_sizes(docs: dict) -> None:
    """Estima el tamaño del dossier de cada reporte.

    Como el trozo concreto depende de la persona, se usa la **mediana** de los
    trozos de cada documento y se marca el peor caso. Es lo que hay que vigilar
    para que ninguna petición se dispare de coste.
    """
    print("\nTamaño estimado del dossier (mediana / peor caso)")
    print("-" * 78)
    print(f"  {'reporte':<12} {'piezas':>7} {'mediana':>12} {'~tokens':>9} {'peor caso':>12}")
    for report in REPORTS.values():
        median = worst = 0
        for slug, selector in report.pieces:
            doc = docs.get(slug)
            if doc is None:
                continue
            if selector in ("@intro", "@whole"):
                median += len(doc["intro"])
                worst += len(doc["intro"])
                continue
            sizes = sorted(len(s) for s in doc["slices"].values())
            if not sizes:
                continue
            median += sizes[len(sizes) // 2]
            worst += sizes[-1]
        print(f"  {report.key:<12} {len(report.pieces):>7} {median:>11,} "
              f"{median // 4:>9,} {worst:>11,}")
    print("  (~4 chars por token; el ensamblador deduplica y recorta si hace falta)")


def report_gaps(docs: dict) -> None:
    """Posiciones del Pináculo que no tienen NINGÚN documento asociado."""
    covered = {
        selector.split(":", 1)[1]
        for report in REPORTS.values()
        for _, selector in report.pieces
        if ":" in selector
    }
    orphan = sorted(PINNACLE_KEYS - covered)
    print("\nPosiciones del Pináculo sin material en el corpus")
    print("-" * 78)
    print(f"  {', '.join(orphan)}")
    print("  Se pueden calcular y dibujar, pero el modelo no puede interpretarlas")
    print("  (regla de anclaje). Es la petición de autoría pendiente para Laura.")


# --------------------------------------------------------------------------- #
def main() -> int:
    if not SOURCES["web"].exists():
        print(f"No encuentro el corpus en {SOURCES['web']}")
        return 1
    if not SOURCES["libro"].exists():
        print("AVISO: falta docs/libro/ — ejecuta antes scripts/extract_book.py\n")

    docs = build()

    sliceable = [d for d in docs.values() if d["slices"]]
    total_chars = sum(len(d["intro"]) + sum(len(s) for s in d["slices"].values())
                      for d in docs.values())
    total_slices = sum(len(d["slices"]) for d in docs.values())

    by_source: dict[str, int] = {}
    for d in docs.values():
        by_source[d["source"]] = by_source.get(d["source"], 0) + 1
    print("Corpus  : " + " · ".join(f"{k}={v} docs" for k, v in sorted(by_source.items())))
    print(f"          {len(docs)} documentos · {total_chars:,} chars "
          f"(~{total_chars // 4:,} tokens)")
    print(f"Troceado: {len(sliceable)}/{len(docs)} documentos · {total_slices} trozos")
    by_kind: dict[str, int] = {}
    for d in docs.values():
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
    print(f"          por tipo: " + " · ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    print()

    print("Calculando el dominio real de cada posición...", flush=True)
    domains = compute_domains()
    print("\nDominio real de las posiciones que dependen de la fecha")
    print("-" * 78)
    for key in ("A", "B", "C", "D", "H", "J", "P", "X", "Y", "Z", "AP", "W"):
        vals = sort_vibrations(domains[key])
        print(f"  {key:<4} {len(vals):>2} valores: {', '.join(vals)}")
    print()
    problems, warnings = check_coverage(docs, domains)
    check_keys()
    report_sizes(docs)
    report_gaps(docs)

    if "--check" not in sys.argv:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sources": {k: str(v.relative_to(ROOT)).replace("\\", "/")
                        for k, v in SOURCES.items()},
            "documents": len(docs),
            "slices": total_slices,
            "domains": {k: sort_vibrations(v) for k, v in domains.items()},
            "docs": docs,
        }
        # sort_keys + separators fijos → build determinista, diff legible.
        TARGET.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1),
            encoding="utf-8",
        )
        size = TARGET.stat().st_size
        print(f"\nEscrito {TARGET.relative_to(ROOT)}  ({size:,} bytes)")

    print(f"\n{problems} problema(s) · {warnings} aviso(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
