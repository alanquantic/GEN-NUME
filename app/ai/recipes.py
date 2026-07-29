"""Recetas: qué trozos del corpus alimentan cada reporte dinámico.

Una receta es una lista ordenada de piezas. Cada pieza dice **de qué documento**
sale el texto y **cómo se elige el trozo**:

    "num:B"        → el trozo del número que valga la posición B de la persona
    "letter:INICIAL" → el trozo de la letra inicial de su nombre
    "@intro"       → la parte de método del documento (antes de los significados)
    "@whole"       → el documento entero (sólo para los cortos)

El orden importa: es el orden en que las piezas entran en el prompt, y es fijo
para que dos peticiones del mismo reporte compartan prefijo y la caché funcione.

Las claves (`B`, `ALMA`, `AP`…) se resuelven contra el diccionario de números de
la persona. `scripts/build_kb.py` valida que toda pieza tenga texto para **todas**
las vibraciones posibles, no sólo para una persona de ejemplo.
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Claves de número
# --------------------------------------------------------------------------- #
# Las que ya calcula app.domain.Pinnacle
PINNACLE_KEYS = frozenset("ABCDEFGHIJKLMNOPQRSXYZ")

# Las que dependen del nombre — Person ya calcula ALMA y EXPRESION.
NAME_KEYS = frozenset({"ALMA", "EXPRESION", "NOMBRE", "ACTIVO", "INICIAL"})

# Las que dependen del tiempo — Person ya calcula AP y MP.
TIME_KEYS = frozenset({"AP", "MP", "AU", "REALIZACION"})

# Las de pareja.
PARTNER_KEYS = frozenset({"PAREJA", "ANIO_REL"})

# Derivadas de Pinnacle/Person: etapas, ausencias, triplicidad, y los dos alias
# que el corpus define (MAESTRO = 2.ª etapa F, PROYECTO = vocales = ALMA).
DERIVED_KEYS = frozenset({
    "E1", "E2", "E3", "E4", "AUSENCIAS", "W", "W_DIGIT",
    "MADUREZ", "MAESTRO", "PROYECTO",
})

# Sin calculador conocido. Vacío: todas las claves de las recetas tienen fórmula.
PENDING_KEYS: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Report:
    key: str
    title: str
    area: str                    # token de color del sitio
    needs_partner: bool
    pieces: tuple[tuple[str, str], ...]   # (documento, selector)


# --------------------------------------------------------------------------- #
# Las cinco recetas
# --------------------------------------------------------------------------- #
_D = "02-calculos-de-fecha-de-nacimiento"
_N = "03-calculos-del-nombre"
_T = "04-calculos-de-tiempo"
_P = "05-calculos-de-pareja"
_M = "01-metodo"
_O = "06-otros-calculos"
_L = "libro"          # interpretaciones extraídas del libro de Laura

REPORTS: dict[str, Report] = {}


def _add(report: Report) -> None:
    REPORTS[report.key] = report


_add(Report(
    key="quien-soy",
    title="¿Quién soy?",
    area="primary",
    needs_partner=False,
    pieces=(
        (f"{_M}/significado-espiritual-de-los-numeros", "num:B"),
        (f"{_D}/numero-personal", "num:B"),
        (f"{_D}/diferencia-por-dia-de-nacimiento", "num:B"),
        (f"{_D}/numero-del-karma", "num:A"),
        (f"{_D}/numero-de-vida-pasada", "num:C"),
        (f"{_D}/numero-de-la-personalidad", "num:D"),
        (f"{_D}/tu-destino", "num:H"),
        (f"{_D}/numero-del-subconsciente", "num:I"),
        (f"{_D}/numero-espejo", "num:J"),
        (f"{_D}/mi-sombra-numero-oculto", "num:P"),
        (f"{_D}/armonico-y-desarmonico", "num:B"),
        (f"{_D}/numero-del-alma", "num:ALMA"),
        (f"{_N}/numero-del-nombre", "num:NOMBRE"),
        (f"{_N}/expresion-del-alma-y-personalidad", "num:EXPRESION"),
        (f"{_N}/nombre-activo", "num:ACTIVO"),
        (f"{_N}/primera-letra-del-nombre", "letter:INICIAL"),
        (f"{_L}/inconsciente-negativo-o", "num:O"),
        (f"{_L}/super-ocultos-q-r-s", "num:Q"),
        (f"{_L}/regalo-divino-z", "num:Z"),
    ),
))

_add(Report(
    key="amor",
    title="Numerología en el amor",
    area="area-amor",
    needs_partner=False,      # funciona con y sin pareja
    pieces=(
        (f"{_D}/numero-espejo", "num:J"),
        (f"{_D}/numero-personal", "num:B"),
        (f"{_D}/numero-del-alma", "num:ALMA"),
        (f"{_P}/relacion-entre-numeros", "num:B"),
        (f"{_P}/relacion-entre-numeros", "num:J"),
        (f"{_P}/el-amor-segun-tu-ano-personal", "num:AP"),
        (f"{_P}/almas-gemelas-karmicas-y-dharmicas", "@whole"),
        (f"{_P}/sinastria-numerologica", "@intro"),
        (f"{_L}/inconsciente-negativo-o", "num:O"),
        # sólo con pareja:
        (f"{_P}/numero-de-pareja", "num:PAREJA"),
        (f"{_P}/ciclo-de-vida-de-la-pareja", "num:ANIO_REL"),
    ),
))

_add(Report(
    key="trabajo",
    title="Numerología en el trabajo",
    area="area-trabajo",
    needs_partner=False,
    pieces=(
        (f"{_D}/talentos-personales-y-profesionales", "num:B"),
        (f"{_D}/talentos-personales-y-profesionales", "num:H"),
        (f"{_D}/tu-destino", "num:H"),
        (f"{_D}/numero-personal", "num:B"),
        (f"{_N}/expresion-del-alma-y-personalidad", "num:EXPRESION"),
        (f"{_N}/numero-del-nombre", "num:NOMBRE"),
        (f"{_T}/ano-personal", "num:AP"),
        (f"{_T}/binomios-energeticos", "num:AP"),
        (f"{_T}/realizaciones-y-metas-del-ciclo-de-vida", "num:REALIZACION"),
        (f"{_L}/desafios-k-l-m-n", "num:N"),
    ),
))

_add(Report(
    key="bienestar",
    title="Mi energía vital y bienestar",
    area="area-bienestar",
    needs_partner=False,
    pieces=(
        (f"{_M}/significado-espiritual-de-los-numeros", "num:B"),
        (f"{_D}/armonico-y-desarmonico", "num:B"),
        (f"{_D}/armonico-y-desarmonico", "num:D"),
        (f"{_D}/mi-sombra-numero-oculto", "num:P"),
        (f"{_D}/tarea-no-aprendida-y-ausencias", "num:AUSENCIAS"),
        (f"{_D}/como-potencializar-mi-energia", "@whole"),
        (f"{_O}/deudas-karmicas", "@whole"),
        (f"{_L}/reaccion-x", "num:X"),
        (f"{_L}/ausencias-t", "num:AUSENCIAS"),
        (f"{_L}/triplicidad-w", "num:W_DIGIT"),
        (f"{_L}/desafios-k-l-m-n", "num:K"),
        (f"{_T}/ano-personal", "num:AP"),
    ),
))

_add(Report(
    key="proposito",
    title="Mi propósito y camino de vida",
    area="area-espiritual",
    needs_partner=False,
    pieces=(
        (f"{_M}/significado-espiritual-de-los-numeros", "num:B"),
        (f"{_D}/numero-del-alma", "num:ALMA"),
        (f"{_D}/tu-destino", "num:H"),
        (f"{_D}/mision-del-numero-personal", "num:B"),
        (f"{_D}/numero-de-la-madurez", "num:MADUREZ"),
        (f"{_D}/reidentificacion-con-tu-yo", "num:B"),
        (f"{_D}/encuentro-con-tu-maestro", "num:MAESTRO"),
        (f"{_D}/mi-proyecto-sentido", "num:PROYECTO"),
        (f"{_T}/etapas-y-ciclos-de-vida", "num:E1"),
        (f"{_T}/etapas-y-ciclos-de-vida", "num:E2"),
        (f"{_T}/etapas-y-ciclos-de-vida", "num:E3"),
        (f"{_T}/etapas-y-ciclos-de-vida", "num:E4"),
        (f"{_T}/realizaciones-y-metas-del-ciclo-de-vida", "num:REALIZACION"),
        (f"{_L}/sintesis-y", "num:Y"),
        (f"{_L}/regalo-divino-z", "num:Z"),
    ),
))

# Piezas que sólo se incluyen cuando la petición trae pareja.
PARTNER_ONLY = frozenset({
    (f"{_P}/numero-de-pareja", "num:PAREJA"),
    (f"{_P}/ciclo-de-vida-de-la-pareja", "num:ANIO_REL"),
})


def keys_used(report: Report) -> set[str]:
    """Claves de número que hace falta calcular para este reporte."""
    return {
        selector.split(":", 1)[1]
        for _, selector in report.pieces
        if ":" in selector
    }


__all__ = ["Report", "REPORTS", "PARTNER_ONLY", "keys_used",
           "PINNACLE_KEYS", "NAME_KEYS", "TIME_KEYS", "PARTNER_KEYS",
           "DERIVED_KEYS", "PENDING_KEYS"]
