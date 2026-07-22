"""API FastAPI del generador de reportes.

Endpoints:
  GET  /health              -> healthcheck para Railway
  GET  /reports             -> lista de reportes disponibles
  POST /reports/generate    -> genera el PDF (requiere firma HMAC) y devuelve URL
  GET  /files/{...}         -> descarga del PDF desde el Volume

Flujo de integración con la tienda Next.js:
  1. Se paga un pedido en la tienda.
  2. Un route handler de Next.js firma el payload con el secreto compartido y
     hace POST a /reports/generate.
  3. El generador crea el PDF, lo guarda en el Volume y responde con la URL.
  4. La tienda guarda esa URL (Drizzle/Neon) y se la muestra/envía al cliente.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from . import static_reports
from .config import settings
from .registry import available_reports, build
from .schemas import GenerateRequest, GenerateResponse
from .security import verify_signature
from .storage import ensure_storage, save_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reportpdf")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Storage en %s | reportes: %s", settings.storage_dir, available_reports())
    yield


app = FastAPI(title="Generador de Reportes de Numerología", version="0.1.0", lifespan=lifespan)

# El Volume debe existir antes de montar los archivos estáticos.
ensure_storage()
app.mount("/files", StaticFiles(directory=str(settings.storage_dir)), name="files")

# PDFs pre-hechos (agenda, planeador, semestral) servidos desde assets/static.
static_reports.ensure_static_dir()
app.mount("/static", StaticFiles(directory=str(settings.static_pdf_dir)), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.get("/reports")
def reports() -> dict:
    return {
        "reports": available_reports(),               # reportes generados
        "static": static_reports.available_static(),  # PDFs pre-hechos
        "static_variants": static_reports.variants_map(),  # {clave: [variantes]}
    }


@app.post(
    "/reports/generate",
    response_model=GenerateResponse,
    responses={401: {"description": "Firma inválida"}, 400: {"description": "Reporte desconocido"}},
)
async def generate(request: Request, x_signature: str | None = Header(default=None)) -> JSONResponse:
    raw = await request.body()

    if not verify_signature(raw, x_signature):
        return JSONResponse(status_code=401, content={"ok": False, "error": "firma_invalida"})

    try:
        req = GenerateRequest.model_validate_json(raw)
    except ValidationError as exc:
        logger.warning("Payload inválido (422): %s", exc.errors())
        return JSONResponse(status_code=422, content={"ok": False, "error": "payload_invalido", "detail": exc.errors()})

    # Reportes estáticos (agenda, planeador, semestral): solo devolver la URL.
    if static_reports.is_static(req.report):
        # Productos con versiones (p. ej. colores): requieren `variant`.
        if static_reports.has_variants(req.report):
            opciones = static_reports.variants(req.report)
            if req.variant is None:
                return JSONResponse(status_code=400, content={
                    "ok": False, "error": "parametros_faltantes",
                    "detail": f"'{req.report}' requiere 'variant'. Opciones: {', '.join(opciones)}"})
            if req.variant not in opciones:
                return JSONResponse(status_code=400, content={
                    "ok": False, "error": "variant_invalido",
                    "detail": f"variant '{req.variant}' no válido. Opciones: {', '.join(opciones)}"})
        url = static_reports.static_url(req.report, req.variant)
        if url is None:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "pdf_no_disponible",
                         "detail": f"El PDF estático '{req.report}' ({req.variant or 'único'}) aún no se ha subido"},
            )
        filename = static_reports.filename_for(req.report, req.variant)
        return JSONResponse(content=GenerateResponse(
            ok=True, report=req.report, order_id=req.order_id, url=url, path=f"/static/{filename}",
        ).model_dump())

    # Reportes generados: requieren datos de la persona.
    if req.person is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "parametros_faltantes", "detail": "person es requerido para este reporte"},
        )

    try:
        report = build(req)
    except KeyError:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "reporte_desconocido", "detail": req.report},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "parametros_faltantes", "detail": str(exc)},
        )

    try:
        data = report.output()
        _, url = save_pdf(req.order_id, req.report, data, req.instance)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error generando el reporte %s", req.report)
        return JSONResponse(status_code=500, content={"ok": False, "error": "generacion_fallida", "detail": str(exc)})

    return JSONResponse(
        content=GenerateResponse(
            ok=True,
            report=req.report,
            order_id=req.order_id,
            url=url,
            path=f"/files/{url.split('/files/', 1)[1]}",
        ).model_dump()
    )
