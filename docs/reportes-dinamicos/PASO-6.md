# Paso 6 - Propuesta operativa

Estado a 30 de julio de 2026: las fases 1 a 5 ya viven en el repo. Este paso
abre el contrato de producción para los cinco reportes dinámicos con IA sin
tocar el flujo legacy de `/reports/generate`.

## Objetivo

Separar el producto nuevo del catálogo viejo:

- `POST /reports/generate` sigue atendiendo los 16 reportes heredados.
- `POST /reports/generate-ai` encola los 5 reportes dinámicos.
- `GET /reports/jobs/{job_id}` deja a la tienda consultar estado y URLs finales.

## Contrato

### `POST /reports/generate-ai`

Header:

- `X-Signature`: HMAC-SHA256 del body crudo, igual que en el endpoint legacy.

Body:

```json
{
  "order_id": "ORD-1001",
  "report": "quien-soy",
  "person": {
    "name": "Juan Pedro Martinez",
    "birth_date": "1991-11-20"
  }
}
```

Respuesta:

```json
{
  "ok": true,
  "job_id": "job_...",
  "status": "queued"
}
```

### `GET /reports/jobs/{job_id}`

Respuesta cuando termina:

```json
{
  "ok": true,
  "job_id": "job_...",
  "status": "done",
  "stage": "done",
  "report": "quien-soy",
  "order_id": "ORD-1001",
  "result": {
    "pdf": { "path": "/files/...", "url": "https://..." },
    "html": { "path": "/files/jobs/.../report.html", "url": "https://..." },
    "json": { "path": "/files/jobs/.../report.json", "url": "https://..." }
  }
}
```

Estados posibles:

- `queued`
- `running`
- `done`
- `error`

Etapas internas actuales:

- `queued`
- `build_dossier`
- `generate_text`
- `render_html`
- `render_pdf`
- `save_outputs`
- `done`
- `failed`

## Persistencia

Los jobs se guardan en el mismo `storage_dir` del servicio:

- `data/jobs/<job_id>.json` - estado del job
- `data/jobs/<job_id>/report.json` - salida estructurada del modelo
- `data/jobs/<job_id>/report.html` - maqueta HTML final
- `data/<md5(order_id)>/<report>.pdf` - entregable final

Esto evita añadir infraestructura nueva en esta fase y sobrevive a reinicios del
proceso mientras el Volume de Railway siga montado.

## Implementación actual en el repo

- [app/ai/schemas.py](/C:/Users/andre/Documents/claude/GEN/GENERADOR/app/ai/schemas.py)
- [app/ai/job_store.py](/C:/Users/andre/Documents/claude/GEN/GENERADOR/app/ai/job_store.py)
- [app/ai/service.py](/C:/Users/andre/Documents/claude/GEN/GENERADOR/app/ai/service.py)
- [app/main.py](/C:/Users/andre/Documents/claude/GEN/GENERADOR/app/main.py)
- [tests/test_ai_jobs.py](/C:/Users/andre/Documents/claude/GEN/GENERADOR/tests/test_ai_jobs.py)

## Lo siguiente

1. Conectar la tienda a `POST /reports/generate-ai` sólo para los 5 reportes nuevos.
2. Hacer polling de `GET /reports/jobs/{job_id}` hasta `done` o `error`.
3. Mostrar al cliente la `html.url` como vista móvil y el `pdf.url` como descarga.
4. Si más adelante hay más de una réplica o worker separado, mover el job store a Neon o Redis.
