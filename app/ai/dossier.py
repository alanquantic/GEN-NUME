"""Ensambla el dossier de un reporte: números + material, listo para el prompt.

Junta las tres piezas de la fase 2 en el mensaje que recibe el modelo:

    receta (recipes)  +  números (numbers)  +  corpus (knowledge)  ->  Dossier

El `Dossier` no llama al modelo — sólo prepara el `<numeros>` y el `<material>`.
Quien invoca la API es `generate.py` (fase 4). Separarlo permite inspeccionar y
medir el dossier sin gastar un token.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import numbers as num
from .knowledge import KnowledgeBase, dedupe, get_kb
from .recipes import PARTNER_ONLY, REPORTS, Report


@dataclass
class Piece:
    """Un trozo resuelto del dossier."""

    slug: str
    selector: str
    key: str | None
    value: str | None
    doc_title: str
    text: str


@dataclass
class Dossier:
    report: Report
    numbers: num.Numbers
    pieces: list[Piece]
    skipped: list[tuple[str, str, str]]     # (slug, selector, motivo)
    material: str
    numbers_block: str

    @property
    def approx_tokens(self) -> int:
        return (len(self.material) + len(self.numbers_block)) // 4


# --------------------------------------------------------------------------- #
def _resolve_piece(
    kb: KnowledgeBase, numbers: num.Numbers, slug: str, selector: str,
) -> tuple[list[Piece], str | None]:
    """Devuelve (piezas, motivo_de_omisión).

    Casi siempre una sola pieza; AUSENCIAS expande a varias (una por dígito
    ausente de la persona).
    """
    title = kb.title(slug)

    if kb.document(slug) is None:
        return [], "documento inexistente"

    if selector == "@whole":
        text = kb.whole(slug)
        return ([Piece(slug, selector, None, None, title, text)] if text else [],
                None if text else "documento vacío")
    if selector == "@intro":
        text = kb.intro(slug)
        return ([Piece(slug, selector, None, None, title, text)] if text else [],
                None if text else "intro vacía")

    mode, key = selector.split(":", 1)

    # AUSENCIAS: una pieza por cada dígito que le falta a la persona
    if key == "AUSENCIAS":
        pieces = []
        for absent in numbers.absences:
            text = kb.slice(slug, str(absent))
            if text:
                pieces.append(Piece(slug, selector, "AUSENCIAS", str(absent),
                                    title, text))
        return (pieces, None) if pieces else ([], "sin ausencias con texto")

    value = numbers.get(key)
    if value is None:
        motivo = ("clave sin fórmula" if key in numbers.unresolved
                  else "clave no calculada")
        return [], motivo

    # El asterisco kármico (4*) no forma parte de la cabecera del corpus.
    lookup = value.rstrip("*")
    text = kb.slice(slug, lookup)
    if text is None:
        return [], f"sin trozo para {key}={value}"
    return [Piece(slug, selector, key, value, title, text)], None


def build(
    report_key: str,
    name: str,
    birth_date: date,
    *,
    today: date | None = None,
    partner_name: str | None = None,
    partner_birth_date: date | None = None,
    relationship_start: date | None = None,
    name_sanitize: str | None = None,
    kb: KnowledgeBase | None = None,
) -> Dossier:
    report = REPORTS.get(report_key)
    if report is None:
        raise KeyError(f"reporte desconocido: {report_key}")
    today = today or date.today()
    kb = kb or get_kb()
    has_partner = partner_birth_date is not None

    numbers = num.resolve(
        name, birth_date, today=today,
        partner_birth_date=partner_birth_date,
        relationship_start=relationship_start,
        name_sanitize=name_sanitize,
    )

    pieces: list[Piece] = []
    skipped: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for slug, selector in report.pieces:
        # Las piezas de pareja se omiten limpiamente si no hay pareja.
        if (slug, selector) in PARTNER_ONLY and not has_partner:
            continue
        resolved, motivo = _resolve_piece(kb, numbers, slug, selector)
        if not resolved:
            skipped.append((slug, selector, motivo or "?"))
            continue
        for piece in resolved:
            deduped = dedupe(piece.text, seen)
            if deduped.strip():
                pieces.append(Piece(piece.slug, piece.selector, piece.key,
                                    piece.value, piece.doc_title, deduped))

    material = _render_material(pieces)
    numbers_block = _render_numbers(report, numbers, has_partner)

    return Dossier(report, numbers, pieces, skipped, material, numbers_block)


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def _render_material(pieces: list[Piece]) -> str:
    rule = "─" * 73
    out = []
    for p in pieces:
        if p.value is not None:
            head = f"FUENTE: {p.doc_title} — vibración {p.value}"
        else:
            head = f"FUENTE: {p.doc_title}"
        out.append(f"{rule}\n{head}\n{rule}\n{p.text}")
    return "\n\n".join(out)


# Orden y etiqueta de cada clave en el bloque <numeros>.
_LABELS = [
    ("B",  "Número personal (esencia, día)"),
    ("A",  "Número del karma (mes)"),
    ("C",  "Número de vida pasada (año)"),
    ("D",  "Número de la personalidad (máscara)"),
    ("H",  "Número del destino"),
    ("I",  "Número del subconsciente"),
    ("J",  "Número del inconsciente / espejo / pareja ideal"),
    ("P",  "Número de sombra"),
    ("O",  "Inconsciente negativo"),
    ("Q",  "Súper oculto (papá y mamá)"),
    ("R",  "Súper oculto (propio)"),
    ("S",  "Súper oculto (arma secreta)"),
    ("K",  "1.er desafío"),
    ("L",  "2.º desafío"),
    ("M",  "3.er desafío"),
    ("N",  "4.º desafío"),
    ("X",  "Número de reacción"),
    ("Y",  "Número de síntesis / misión"),
    ("Z",  "Regalo divino"),
    ("W",  "Triplicidad (sombra emocional)"),
    ("ALMA",      "Número del alma (vocales)"),
    ("EXPRESION", "Expresión / personalidad (consonantes)"),
    ("NOMBRE",    "Número del nombre completo"),
    ("ACTIVO",    "Número del nombre activo"),
    ("INICIAL",   "Primera letra del nombre"),
    ("MADUREZ",   "Número de la madurez"),
    ("AP",        "Año personal en curso"),
    ("MP",        "Mes personal en curso"),
    ("REALIZACION", "Realización vigente"),
    ("PAREJA",    "Número de la pareja"),
    ("ANIO_REL",  "Año personal de la relación"),
]


def _render_numbers(report: Report, numbers: num.Numbers, has_partner: bool) -> str:
    lines = ["Estos valores están calculados y son correctos. Úsalos tal cual.", ""]
    for key, label in _LABELS:
        value = numbers.get(key)
        if value:
            lines.append(f"  {key:<10} {label} = {value}")

    if numbers.absences:
        aus = ", ".join(str(a) for a in numbers.absences)
        lines.append(f"  {'AUSENCIAS':<10} Números ausentes del pináculo = {aus}")

    pin = numbers.pinnacle
    if pin.karmic_debts:
        deudas = ", ".join(f"{k}={v}" for k, v in pin.karmic_debts)
        lines.append(f"  {'DEUDAS':<10} Deudas kármicas = {deudas}")

    if pin.h_alternative is not None:
        lines.append(f"  {'H_POTENCIAL':<10} H puede elevarse a la maestra = {pin.h_alternative}")

    # Etapas con años y edades (para el reporte de propósito, sobre todo)
    lines.append("")
    lines.append("  Etapas de vida:")
    for st in pin.stages:
        lines.append(f"    Etapa {st.number} · vibración {st.realization} · "
                     f"{st.year_range} · {st.age_range} años")

    return "\n".join(lines)


__all__ = ["Dossier", "Piece", "build"]
