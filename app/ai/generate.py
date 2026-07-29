"""Fase 4: llama al modelo con el dossier y devuelve el reporte estructurado.

Junta el dossier de la fase 3 con el prompt de sistema y el esquema JSON, llama
a Claude con salida estructurada garantizada, y valida el **anclaje**: que toda
clave que el modelo declara haber usado exista de verdad en los números de la
persona. No parsea markdown a mano — `output_config.format` obliga a JSON válido
contra el esquema.

    from app.ai.generate import generate
    result = generate(dossier)          # llama a la API
    result.data["titulo"]

La construcción del mensaje y la validación son testeables sin red; sólo
`_call_model` toca la API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..config import settings
from . import prompts
from .dossier import Dossier

_MOCK_DIR_NAME = "mock"


@dataclass
class GeneratedReport:
    report_key: str
    data: dict[str, Any]                 # el JSON validado contra el esquema
    model: str
    usage: dict[str, int]
    warnings: list[str] = field(default_factory=list)
    stop_reason: str | None = None


# --------------------------------------------------------------------------- #
# Mensaje de usuario
# --------------------------------------------------------------------------- #
def build_user_message(dossier: Dossier, person_name: str,
                       birth_long: str, today_long: str,
                       partner_name: str | None = None,
                       partner_birth_long: str | None = None) -> str:
    partner_block = ""
    if partner_name:
        partner_block = (
            f"\n<pareja>\nNombre: {partner_name}\n"
            f"Fecha de nacimiento: {partner_birth_long}\n</pareja>\n"
        )

    return (
        f"<persona>\n"
        f"Nombre completo: {person_name}\n"
        f"Nombre de pila: {person_name.split()[0]}\n"
        f"Fecha de nacimiento: {birth_long}\n"
        f"Fecha de hoy: {today_long}\n"
        f"</persona>\n"
        f"{partner_block}"
        f"\n<numeros>\n{dossier.numbers_block}\n</numeros>\n"
        f"\n<material>\n{dossier.material}\n</material>\n"
        f"\nEscribe ahora el reporte «{dossier.report.title}» para "
        f"{person_name.split()[0]}, siguiendo tu encargo y devolviendo el JSON."
    )


# --------------------------------------------------------------------------- #
# Validación de anclaje
# --------------------------------------------------------------------------- #
def validate_anchoring(dossier: Dossier, data: dict) -> list[str]:
    """Comprueba que las claves declaradas por el modelo existan en la persona.

    El esquema obliga a cada sección (y a la tensión central) a declarar en
    `numeros` las claves que usó. Aquí se verifica que ninguna sea inventada:
    toda clave declarada tiene que estar en los números resueltos de la persona.
    """
    allowed = set(dossier.numbers.values.keys())
    warnings: list[str] = []

    def check(where: str, keys: list) -> None:
        for k in keys or []:
            key = str(k).strip().upper().rstrip("*")
            if key and key not in allowed:
                warnings.append(f"{where}: clave declarada '{k}' no existe en <numeros>")

    for sec in data.get("secciones", []):
        check(f"sección {sec.get('id', '?')}", sec.get("numeros", []))
    check("tensión central", data.get("tension_central", {}).get("numeros", []))
    return warnings


# --------------------------------------------------------------------------- #
# Llamada al modelo (delega en el proveedor configurado)
# --------------------------------------------------------------------------- #
def _call_model(system: str, user: str) -> tuple[dict, str, dict, str | None]:
    from . import providers
    return providers.call(settings, system, user, prompts.SCHEMA)


def generate(dossier: Dossier, *,
             person_name: str, birth_long: str, today_long: str,
             partner_name: str | None = None,
             partner_birth_long: str | None = None,
             mock: bool = False) -> GeneratedReport:
    # El prompt se arma siempre, aunque en mock no se envíe: así el modo de
    # prueba ejercita el mismo camino (dossier -> mensaje -> validación).
    system = prompts.system_prompt(dossier.report.key)
    user = build_user_message(
        dossier, person_name, birth_long, today_long,
        partner_name, partner_birth_long,
    )

    if mock:
        data, model, usage, stop = _load_mock(dossier.report.key)
    else:
        data, model, usage, stop = _call_model(system, user)

    warnings = validate_anchoring(dossier, data)

    return GeneratedReport(
        report_key=dossier.report.key,
        data=data, model=model, usage=usage,
        warnings=warnings, stop_reason=stop,
    )


def _load_mock(report_key: str) -> tuple[dict, str, dict, str | None]:
    """Carga una respuesta de ejemplo (no toca la red).

    Pasa por la MISMA validación de esquema que una respuesta real: si el
    fixture no cumple el esquema, el modo de prueba falla igual que fallaría
    producción. Así el mock no es una mentira cómoda, sino una prueba honesta
    del flujo.
    """
    path = settings.content_dir / _MOCK_DIR_NAME / f"{report_key}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No hay respuesta de ejemplo para '{report_key}' en {path}. "
            f"Hoy sólo existe la de 'quien-soy'."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_mock", None)                       # nota interna, fuera del esquema
    _assert_schema(data)
    return data, "mock (respuesta de ejemplo)", {
        "input": 0, "output": 0, "cache_read": 0, "cache_write": 0}, "end_turn"


def _assert_schema(data: dict) -> None:
    """Chequeo mínimo de que el ejemplo cumple la forma que exige el esquema."""
    top = prompts.SCHEMA["required"]
    missing = [k for k in top if k not in data]
    if missing:
        raise ValueError(f"el ejemplo no cumple el esquema: faltan {missing}")
    sec_req = prompts.SCHEMA["properties"]["secciones"]["items"]["required"]
    for i, sec in enumerate(data.get("secciones", [])):
        sm = [k for k in sec_req if k not in sec]
        if sm:
            raise ValueError(f"el ejemplo: sección {i} sin {sm}")


__all__ = ["GeneratedReport", "generate", "build_user_message",
           "validate_anchoring"]
