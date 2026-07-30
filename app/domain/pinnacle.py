"""Pináculo personal completo — las 24 posiciones del método de Laura L. Rodríguez.

Fuente autoritativa: *LIBRO FINAL-LAURA de 26 de JULIO.docx*, capítulos IV–VII,
y el diagrama oficial de fórmulas reproducido en
`docs/reportes-dinamicos/pinaculo-diagrama-oficial.png`.

La especificación en prosa está en `docs/reportes-dinamicos/pinaculo-formulas.md`.

Este módulo es independiente de `Person`: recibe una fecha y devuelve un objeto
de sólo lectura. `Person` lo compone (no hereda) para no tocar el
comportamiento ya probado de los 16 reportes en producción.

    >>> p = Pinnacle.from_date(date(1991, 11, 20))
    >>> p.b.value, p.d.value, p.p.value
    (2, 6, 6)
    >>> p.absences
    (3, 5, 9)

CONVENCIÓN DE CÁLCULO
---------------------
Las fórmulas se aplican sobre las **vibraciones ya reducidas** (A, B, C…), que
es lo que dice el diagrama oficial. Algunos ejemplos resueltos del libro operan
en cambio sobre los números crudos (p. ej. `F = 16 + 1968 = 1984 → 22` en vez de
`F = B + C = 7 + 6 = 13 → 4`).

Las dos vías coinciden siempre **salvo cuando aparece un número maestro**,
porque la reducción teosófica conserva la congruencia módulo 9 pero el 11 y el
22 rompen esa equivalencia. Ver `docs/reportes-dinamicos/pinaculo-formulas.md`
§10 y `tests/test_pinnacle.py`, que informa de las divergencias en los ejemplos
del libro sin darlas por resueltas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

from .numerology import reduce_number

# Números que, apareciendo en la cadena de reducción, marcan deuda kármica.
KARMIC_NUMBERS = (13, 14, 16, 19)
MASTER_NUMBERS = (11, 22)

# Posiciones que entran en el recuento de ausencias (T): las 3 zonas del
# Pináculo. Quedan fuera las exteriores X, Y, Z (y la propia W).
ABSENCE_POSITIONS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
                     "K", "L", "M", "N", "O", "P", "Q", "R", "S")

# Posiciones sobre las que se busca la triplicidad (W).
LOWER_POSITIONS = ("K", "L", "M", "N", "O", "P", "Q", "R", "S")


# --------------------------------------------------------------------------- #
# Vibración
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Vibration:
    """Un valor del Pináculo, con su posible deuda kármica.

    `karmic` guarda el número kármico original (13, 14, 16 o 19) cuando apareció
    en la cadena de reducción. El valor con el que se sigue operando es siempre
    `value`; el asterisco es información de interpretación.
    """

    value: int
    karmic: int | None = None

    @property
    def is_master(self) -> bool:
        return self.value in MASTER_NUMBERS

    @property
    def base(self) -> int:
        """Vibración base: los maestros bajan a su dígito (11→2, 22→4).

        El libro la exige para restar en la zona inferior y para calcular la
        duración de la primera etapa.
        """
        if self.value == 11:
            return 2
        if self.value == 22:
            return 4
        return self.value

    def __str__(self) -> str:
        return f"{self.value}*" if self.karmic else str(self.value)

    def __int__(self) -> int:
        return self.value


def _digits(n: int) -> Iterable[int]:
    return (int(d) for d in str(abs(int(n))))


def reduce_tracked(value: int) -> Vibration:
    """Reduce conservando 11 y 22, y anota si pasó por un número kármico."""
    n = int(value)
    karmic = n if n in KARMIC_NUMBERS else None
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(_digits(n))
        if karmic is None and n in KARMIC_NUMBERS:
            karmic = n
    return Vibration(n, karmic)


def _vib(*parts: Vibration | int) -> Vibration:
    """Suma vibraciones (o enteros) y reduce."""
    total = sum(p.value if isinstance(p, Vibration) else int(p) for p in parts)
    return reduce_tracked(total)


def _sub(a: Vibration, b: Vibration) -> Vibration:
    """Resta de la zona inferior: valor absoluto sobre las vibraciones base.

    Reglas del libro: no hay negativos (mayor − menor) y los maestros se
    reducen a su base antes de restar.
    """
    return reduce_tracked(abs(a.base - b.base))


# --------------------------------------------------------------------------- #
# Etapas
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Stage:
    """Una de las cuatro Etapas de Realización, con su desafío emparejado."""

    number: int              # 1..4
    realization: Vibration   # E, F, G, H
    challenge: Vibration     # K, L, M, N
    start_age: int
    end_age: int | None      # None en la cuarta (abierta)
    start_year: int
    end_year: int | None

    @property
    def age_range(self) -> str:
        return f"{self.start_age} – {self.end_age}" if self.end_age is not None \
            else f"{self.start_age} – ..."

    @property
    def year_range(self) -> str:
        return f"{self.start_year} – {self.end_year}" if self.end_year is not None \
            else f"{self.start_year} – ..."

    def contains_age(self, age: int) -> bool:
        if age < self.start_age:
            return False
        return self.end_age is None or age < self.end_age


# --------------------------------------------------------------------------- #
# Pináculo
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Pinnacle:
    """Las 24 posiciones del Pináculo personal."""

    birth_date: date

    # Horizontal — identidad
    a: Vibration            # Karma (mes)
    b: Vibration            # Personal (día)
    c: Vibration            # Vida pasada (año)
    d: Vibration            # Personalidad (A+B+C, con comprobación)

    # Ser Superior — realizaciones
    e: Vibration            # 1.ª etapa   A+B
    f: Vibration            # 2.ª etapa   B+C
    g: Vibration            # 3.ª etapa   E+F
    h: Vibration            # 4.ª etapa / destino   A+C (con comprobación)
    i: Vibration            # Inconsciente positivo   E+F+G
    j: Vibration            # Espejo / pareja   H+D

    # Ser Inferior — desafíos y sombra
    k: Vibration            # 1.er desafío   A−B
    l: Vibration            # 2.º desafío    B−C
    m: Vibration            # 3.er desafío   K−L
    n: Vibration            # 4.º desafío    A−C
    o: Vibration            # Inconsciente negativo   K+L+M
    p: Vibration            # Sombra   D+O
    q: Vibration            # Súper oculto   K+M
    r: Vibration            # Súper oculto   L+M
    s: Vibration            # Súper oculto   Q+R

    # Exteriores
    x: Vibration            # Reacción   B+D
    y: Vibration            # Síntesis / misión   A+B+C+D+X
    z: Vibration            # Regalo divino

    absences: tuple[int, ...]           # T
    w: Vibration | None                 # Triplicidad (3, 6 o 9), o None
    w_source: int | None                # el dígito que se triplicó (1..9), o None
    special_pinnacle: bool              # 4+ vibraciones iguales en la zona inferior

    d_verified: bool                    # la comprobación cambió D
    h_alternative: Vibration | None     # la maestra a la que H se puede elevar

    stages: tuple[Stage, ...] = field(default=())

    # ---------------------------------------------------------------- #
    # Construcción
    # ---------------------------------------------------------------- #
    @classmethod
    def from_date(
        cls,
        birth_date: date,
        stage_convention: str = "vibration",
    ) -> "Pinnacle":
        """Construye el Pináculo.

        `stage_convention` decide cómo se calculan E y F, la única cuestión
        abierta del método (ver el módulo y `tests/test_pinnacle.py`):

        * ``"vibration"`` (por defecto) — `E = A + B`, `F = B + C` sobre las
          vibraciones reducidas, tal como dice el diagrama oficial.
        * ``"raw"`` — `E = mes + día`, `F = día + año` sobre los enteros crudos,
          como en el ejemplo resuelto del capítulo VIII.

        Sólo difieren cuando el resultado crudo es 11 o 22. Con `"raw"` afloran
        maestros que la vía reducida se come: para 16/07/1968, F = 22 en vez
        de 4. Nada más del Pináculo cambia de convención.
        """
        if stage_convention not in ("vibration", "raw"):
            raise ValueError(f"stage_convention desconocida: {stage_convention!r}")

        month, day, year = birth_date.month, birth_date.day, birth_date.year

        a = reduce_tracked(month)
        b = reduce_tracked(day)
        c = reduce_tracked(year)

        # --- D con regla de comprobación --------------------------------- #
        # "Se comprueba haciendo una suma simple de los números iniciales antes
        # de reducirlos a vibración": se suman mes, día y año COMO ENTEROS y se
        # reduce el total. Verificado con los dos ejemplos del cap. V:
        #   18/10/1981 → 18+10+1981 = 2009 → 11  (confirma)
        #   10/04/1979 → 10+ 4+1979 = 1993 → 22  (corrige el 4* de vibraciones)
        d = _vib(a, b, c)
        d_verified = False
        if d.value in (2, 4, 11, 22):
            check = reduce_tracked(month + day + year)
            if check.value != d.value:
                # El libro: "El resultado correcto será el de la comprobación,
                # el cual usaremos para todos los demás cálculos."
                d, d_verified = check, True

        # --- Ser Superior ------------------------------------------------- #
        if stage_convention == "raw":
            e = reduce_tracked(month + day)
            f = reduce_tracked(day + year)
        else:
            e = _vib(a, b)
            f = _vib(b, c)
        g = _vib(e, f)

        # --- H con regla de comprobación ---------------------------------- #
        # Misma mecánica que D, con mes + año. Verificado con el cap. V:
        #   23/09/2000 →  9+2000 = 2009 → 11  (confirma)
        #   21/12/1970 → 12+1970 = 1982 →  2  (difiere del 11 de vibraciones)
        h = _vib(a, c)
        h_alternative: Vibration | None = None
        if h.value in (2, 4, 11, 22):
            check = reduce_tracked(month + year)
            if check.value != h.value:
                # El libro NO resuelve este caso: "elegir entre uno y otro
                # dependerá del trabajo de evolución y apertura de conciencia".
                # Nos quedamos con la base y exponemos la maestra como potencial.
                if h.is_master and not check.is_master:
                    h, h_alternative = check, Vibration(h.value, h.karmic)
                else:
                    h_alternative = check

        i = _vib(e, f, g)
        # OJO: J depende de H, así que elevar H a su maestra cambia también J.
        j = _vib(h, d)

        # --- Ser Inferior -------------------------------------------------- #
        k = _sub(a, b)
        l = _sub(b, c)
        m = _sub(k, l)
        n = _sub(a, c)
        o = _vib(k, l, m)
        p = _vib(d, o)
        q = _vib(k, m)
        r = _vib(l, m)
        s = _vib(q, r)

        # --- Exteriores ---------------------------------------------------- #
        x = _vib(b, d)
        y = _vib(a, b, c, d, x)
        z = cls._divine_gift(year)

        positions = {
            "A": a, "B": b, "C": c, "D": d, "E": e, "F": f, "G": g, "H": h,
            "I": i, "J": j, "K": k, "L": l, "M": m, "N": n, "O": o, "P": p,
            "Q": q, "R": r, "S": s,
        }
        absences = cls._absences(positions)
        w, w_source, special = cls._triplicity(positions)

        obj = cls(
            birth_date=birth_date,
            a=a, b=b, c=c, d=d, e=e, f=f, g=g, h=h, i=i, j=j,
            k=k, l=l, m=m, n=n, o=o, p=p, q=q, r=r, s=s,
            x=x, y=y, z=z,
            absences=absences, w=w, w_source=w_source, special_pinnacle=special,
            d_verified=d_verified, h_alternative=h_alternative,
        )
        object.__setattr__(obj, "stages", obj._build_stages())
        return obj

    # ---------------------------------------------------------------- #
    # Reglas auxiliares
    # ---------------------------------------------------------------- #
    @staticmethod
    def _divine_gift(year: int) -> Vibration:
        """Z: suma de los 2 últimos dígitos del año.

        Si da 0 se desplaza un dígito a la izquierda (regla explícita del libro:
        1900 → 0+0 = 0 → se toma 9+0 = 9).
        """
        digits = [int(ch) for ch in str(year)]
        for offset in range(len(digits) - 1):
            pair = digits[len(digits) - 2 - offset: len(digits) - offset]
            vib = reduce_tracked(sum(pair))
            if vib.value != 0:
                return vib
        return reduce_tracked(sum(digits))

    @staticmethod
    def _absences(positions: dict[str, Vibration]) -> tuple[int, ...]:
        """T: vibraciones de la escala 1–9 que no aparecen en las 3 zonas.

        Los maestros no cuentan como ausencia ni como presencia de su base:
        un 11 es un 11, no un 2.
        """
        present = {
            positions[key].value
            for key in ABSENCE_POSITIONS
            if 1 <= positions[key].value <= 9
        }
        return tuple(n for n in range(1, 10) if n not in present)

    @staticmethod
    def _triplicity(
        positions: dict[str, Vibration],
    ) -> tuple[Vibration | None, int | None, bool]:
        """W: suma de 3 vibraciones iguales de la zona inferior.

        Devuelve (W, dígito_triplicado, es_pináculo_especial). Con 4 o más
        repeticiones la regla no aplica y W queda vacía. El resultado válido es
        siempre 3, 6 o 9 — si no lo es (caso del 0), no hay triplicidad.

        `dígito_triplicado` es el valor que se repitió tres veces (1..9); el
        libro indexa las interpretaciones de la triplicidad por él, no por W.
        """
        counts: dict[int, int] = {}
        for key in LOWER_POSITIONS:
            v = positions[key].value
            counts[v] = counts.get(v, 0) + 1

        if any(count >= 4 for count in counts.values()):
            return None, None, True

        triples = [value for value, count in counts.items() if count == 3 and value != 0]
        if len(triples) != 1:
            return None, None, False

        source = triples[0]
        w = reduce_tracked(source * 3)
        return (w, source, False) if w.value in (3, 6, 9) else (None, None, False)

    def _build_stages(self) -> tuple[Stage, ...]:
        """Cuatro etapas: la 1.ª dura 36 − base(D) años, las demás 9 exactos."""
        first_length = 36 - self.d.base
        year = self.birth_date.year
        spec = [
            (1, self.e, self.k, first_length),
            (2, self.f, self.l, 9),
            (3, self.g, self.m, 9),
            (4, self.h, self.n, None),
        ]

        stages, start_age = [], 0
        for number, realization, challenge, length in spec:
            end_age = None if length is None else start_age + length
            stages.append(Stage(
                number=number,
                realization=realization,
                challenge=challenge,
                start_age=start_age,
                end_age=end_age,
                start_year=year + start_age,
                end_year=None if end_age is None else year + end_age,
            ))
            if end_age is not None:
                start_age = end_age
        return tuple(stages)

    # ---------------------------------------------------------------- #
    # Consultas
    # ---------------------------------------------------------------- #
    def age_at(self, today: date) -> int:
        """Edad cumplida."""
        had_birthday = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - (0 if had_birthday else 1)

    def stage_at(self, today: date) -> Stage:
        age = self.age_at(today)
        for stage in self.stages:
            if stage.contains_age(age):
                return stage
        return self.stages[-1]

    @property
    def karmic_debts(self) -> tuple[tuple[str, int], ...]:
        """Deudas kármicas detectadas: (posición, 13|14|16|19)."""
        return tuple(
            (key, vib.karmic)
            for key, vib in self.as_positions().items()
            if vib.karmic is not None
        )

    def as_positions(self) -> dict[str, Vibration]:
        return {
            "A": self.a, "B": self.b, "C": self.c, "D": self.d,
            "E": self.e, "F": self.f, "G": self.g, "H": self.h,
            "I": self.i, "J": self.j,
            "K": self.k, "L": self.l, "M": self.m, "N": self.n,
            "O": self.o, "P": self.p, "Q": self.q, "R": self.r, "S": self.s,
            "X": self.x, "Y": self.y, "Z": self.z,
        }

    def to_numbers(self) -> dict[str, str]:
        """Bloque `<numeros>` del prompt: sólo lo que el modelo debe leer."""
        numbers = {key: str(vib) for key, vib in self.as_positions().items()}
        numbers["T"] = ", ".join(str(n) for n in self.absences) or "ninguna"
        if self.w is not None:
            numbers["W"] = str(self.w)
        if self.h_alternative is not None:
            numbers["H_POTENCIAL"] = str(self.h_alternative)
        if self.karmic_debts:
            numbers["DEUDAS"] = ", ".join(f"{k}={v}" for k, v in self.karmic_debts)
        return numbers


__all__ = ["Pinnacle", "Stage", "Vibration", "reduce_tracked",
           "KARMIC_NUMBERS", "MASTER_NUMBERS"]
