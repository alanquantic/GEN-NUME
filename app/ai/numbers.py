"""Resuelve el valor de cada clave de receta para una persona concreta.

El ensamblador necesita traducir claves abstractas (`B`, `ALMA`, `AP`, `J`…) a
los valores numéricos de *esta* persona, para después buscar el trozo de corpus
correspondiente. Aquí se reúne todo lo que hace falta:

  * el Pináculo (A–S, X, Y, Z, W, ausencias, etapas) desde `domain.Pinnacle`,
  * los números del nombre (ALMA, EXPRESIÓN, NOMBRE, ACTIVO, INICIAL),
  * los de tiempo (año/mes personal, realización vigente),
  * los de pareja (PAREJA, año de la relación),

y se devuelve un único diccionario `clave -> valor` (como texto, porque el 11 y
el 22 se conservan y los kármicos llevan asterisco).

Las claves sin fórmula conocida (MAESTRO, PROYECTO) **no se inventan**: se
omiten y el ensamblador las registra como piezas no resueltas. Ver
`docs/reportes-dinamicos/pinaculo-formulas.md` §11.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import date

from ..domain.numerology import reduce_number
from ..domain.pinnacle import Pinnacle, reduce_tracked

# Valores de letra del sistema pitagórico (idénticos a los de domain.person).
_VOWELS = {"a": 1, "e": 5, "i": 9, "o": 6, "u": 3}
_CONSONANTS = {
    "b": 2, "c": 3, "d": 4, "f": 6, "g": 7, "h": 8, "j": 1, "k": 11,
    "l": 3, "m": 4, "n": 5, "p": 7, "q": 8, "r": 9, "s": 1, "t": 2,
    "v": 22, "w": 5, "x": 6, "y": 7, "z": 8,
}
_LETTER_VALUES = {**_VOWELS, **_CONSONANTS, "ñ": 5}

# Claves sin calculador: los documentos existen, la fórmula no.
# (vacío: MAESTRO y PROYECTO resultaron ser alias de F y ALMA — ver resolve())
UNRESOLVED: frozenset[str] = frozenset()


# --------------------------------------------------------------------------- #
# Nombre
# --------------------------------------------------------------------------- #
def sanitize(name: str) -> str:
    """Normaliza un nombre a minúsculas sin acentos, palabras unidas por '-'.

    'Juan Pedro Martínez' -> 'juan-pedro-martinez'. Conserva la ñ.
    """
    lowered = name.strip().lower()
    out = []
    for ch in lowered:
        if ch == "ñ":
            out.append(ch)
        elif ch.isspace() or ch in "-_":
            out.append(" ")
        else:
            # quita tildes descomponiendo y soltando los diacríticos
            base = unicodedata.normalize("NFD", ch)
            base = "".join(c for c in base if unicodedata.category(c) != "Mn")
            if base.isalpha():
                out.append(base)
    return "-".join("".join(out).split())


def _letters(sanitized: str) -> list[str]:
    return [c for c in sanitized.replace("-", "") if c in _LETTER_VALUES]


def name_number(sanitized: str) -> int:
    """NOMBRE: suma de TODAS las letras del nombre completo."""
    return reduce_number(sum(_LETTER_VALUES[c] for c in _letters(sanitized)))


def active_name_number(sanitized: str) -> int:
    """ACTIVO: suma de las letras del primer nombre (sin apellidos)."""
    first = sanitized.split("-", 1)[0]
    return reduce_number(sum(_LETTER_VALUES[c] for c in _letters(first)))


def soul_number(sanitized: str) -> int:
    """ALMA: suma de las vocales."""
    return reduce_number(sum(_VOWELS.get(c, 0) for c in _letters(sanitized)))


def expression_number(sanitized: str) -> int:
    """EXPRESIÓN: suma de las consonantes."""
    return reduce_number(sum(_CONSONANTS.get(c, 0) for c in _letters(sanitized)))


def initial(sanitized: str) -> str:
    """INICIAL: primera letra del nombre, en mayúscula (clave A–Z del corpus)."""
    for c in _letters(sanitized):
        return c.upper()
    return ""


# --------------------------------------------------------------------------- #
# Resolución completa
# --------------------------------------------------------------------------- #
@dataclass
class Numbers:
    """Todos los valores calculados de una persona, listos para el prompt."""

    values: dict[str, str]                     # clave -> valor (texto)
    pinnacle: Pinnacle
    absences: tuple[int, ...]
    name_sanitize: str = ""                    # para los gráficos del nombre
    unresolved: set[str] = field(default_factory=set)

    def get(self, key: str) -> str | None:
        return self.values.get(key)


def resolve(
    name: str,
    birth_date: date,
    *,
    today: date,
    partner_birth_date: date | None = None,
    relationship_start: date | None = None,
    name_sanitize: str | None = None,
    stage_convention: str = "vibration",
) -> Numbers:
    san = name_sanitize or sanitize(name)
    pin = Pinnacle.from_date(birth_date, stage_convention=stage_convention)

    values: dict[str, str] = {k: str(v) for k, v in pin.as_positions().items()}

    # Nombre
    d_value = pin.d.value
    nombre = name_number(san)
    alma = soul_number(san)
    values.update({
        "ALMA": str(alma),
        "EXPRESION": str(expression_number(san)),
        "NOMBRE": str(nombre),
        "ACTIVO": str(active_name_number(san)),
        "INICIAL": initial(san),
        # MADUREZ = Personalidad (D) + Poder del Nombre → reducir
        "MADUREZ": str(reduce_tracked(d_value + nombre)),
        # El corpus define estas dos como alias de posiciones ya calculadas:
        #   «Encuentro con tu Maestro» = la 2.ª etapa (posición F)
        #   «Mi Proyecto Sentido»      = la suma de vocales (= ALMA)
        "MAESTRO": str(pin.f),
        "PROYECTO": str(alma),
    })

    # Tiempo
    day, month = birth_date.day, birth_date.month
    ap = reduce_number(day + month + today.year)
    values["AP"] = str(ap)
    values["MP"] = str(reduce_number(ap + today.month))

    # Realización vigente: la etapa que contiene la edad de hoy
    stage = pin.stage_at(today)
    values["REALIZACION"] = str(stage.realization)
    for n, st in enumerate(pin.stages, start=1):
        values[f"E{n}"] = str(st.realization)

    # Triplicidad: W es la herida (3/6/9) que ve el modelo; W_DIGIT es el dígito
    # que se triplicó (1..9), y es la clave por la que el libro indexa el texto.
    if pin.w is not None:
        values["W"] = str(pin.w)
    if pin.w_source is not None:
        values["W_DIGIT"] = str(pin.w_source)

    # Pareja
    if partner_birth_date is not None:
        composite_day = day + partner_birth_date.day
        composite_month = month + partner_birth_date.month
        values["PAREJA"] = str(reduce_number(
            reduce_number(day) + reduce_number(partner_birth_date.day)))
        rel_year = (relationship_start or today).year
        values["ANIO_REL"] = str(reduce_number(
            rel_year + composite_day + composite_month))

    return Numbers(
        values=values,
        pinnacle=pin,
        absences=pin.absences,
        name_sanitize=san,
        unresolved=set(UNRESOLVED),
    )


__all__ = ["Numbers", "resolve", "sanitize", "name_number",
           "active_name_number", "soul_number", "expression_number",
           "initial", "UNRESOLVED"]
