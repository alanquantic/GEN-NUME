# Generador de Reportes de Numerología

Nueva versión (Python · FastAPI · fpdf2) del generador de reportes en PDF,
lista para desplegar en **Railway** y ser invocada por webhook desde una tienda
**Next.js** cuando se paga un pedido.

Reescritura de la versión original en PHP conservando **exactamente** la lógica
numerológica y el modelo de maquetado de FPDF (coordenadas en mm sobre
plantillas .jpg de página completa), pero con:

- Validación de entrada (Pydantic) y **webhook firmado con HMAC** — el original
  aceptaba `$_REQUEST` abierto.
- Configuración por variables de entorno — sin rutas ni secretos hardcodeados.
- `write_html()` de fpdf2 — se eliminan las clases custom `HTMLinPDF` y
  `PDF_WriteTag`.
- Fuentes TTF unicode nativas — se elimina el `utf8_decode` y los problemas de
  acentos.
- Contenido de textos fuera del código (`content/texts.json`).
- Registro de reportes (dict) en vez de ~40 ramas `if`.

## Estructura

```
app/
  main.py            # FastAPI: /health, /reports, /reports/generate, /files
  config.py          # settings por entorno (pydantic-settings)
  security.py        # firma HMAC del webhook
  schemas.py         # modelos de petición/respuesta (Pydantic)
  storage.py         # guardado de PDFs en el Volume de Railway
  content.py         # carga de textos desde content/texts.json
  registry.py        # clave de reporte -> constructor
  domain/            # NÚCLEO numerológico (sin dependencias de PDF/web)
    numerology.py    #   reduce_number / reduce_number_for_sub
    person.py        #   Person: números personales, etapas, sinastría
    universal.py     #   Universal: día/semana/mes universal
    dates.py         #   meses en español, formato de fecha
  pdf/base.py        # ReportPDF (subclase fpdf2): fuentes, colores, fondo
  reports/
    report_base.py   # clase base Report
    who_im.py        # reporte "¿Quién soy?" (PLANTILLA DE REFERENCIA)
content/texts.json   # textos por número (generado desde el PHP original)
assets/
  report/            # plantillas .jpg del cliente (no versionadas)
  fonts/             # TTF de marca: OpenSans-*, PassionOne, LazyDog
scripts/
  extract_content.py # migra los textos del helpers.php original a JSON
  smoke_test.py      # prueba de humo de extremo a extremo
tests/
  test_numerology.py # pruebas del dominio (valores verificados a mano)
```

## Desarrollo local

```bash
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt # Linux/mac

cp .env.example .env            # y edita WEBHOOK_SECRET

# Pruebas del dominio (no requieren dependencias):
py -3 tests/test_numerology.py

# Prueba de humo de extremo a extremo (genera un PDF real):
.venv/Scripts/python.exe scripts/smoke_test.py

# Servidor:
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# -> http://localhost:8000/docs  (Swagger автогenerado)
```

## Variables de entorno

| Variable            | Descripción                                             | Ejemplo |
|---------------------|---------------------------------------------------------|---------|
| `WEBHOOK_SECRET`    | Secreto HMAC compartido con la tienda                   | `s3cr3t…` |
| `REQUIRE_SIGNATURE` | Exigir firma en el webhook (`true` en producción)       | `true` |
| `STORAGE_DIR`       | Carpeta persistente (Volume de Railway)                 | `/data` |
| `PUBLIC_BASE_URL`   | URL pública del servicio (para los enlaces de descarga) | `https://x.up.railway.app` |
| `ASSETS_DIR`        | Carpeta de plantillas y fuentes                         | `assets` |
| `CONTENT_DIR`       | Carpeta de textos                                       | `content` |
| `ENVIRONMENT`       | `development` / `production`                            | `production` |

## Endpoints

| Método | Ruta                 | Descripción |
|--------|----------------------|-------------|
| GET    | `/health`            | Healthcheck (usado por Railway) |
| GET    | `/reports`           | Lista de claves de reporte disponibles |
| POST   | `/reports/generate`  | Genera el PDF (requiere firma) y devuelve la URL |
| GET    | `/files/{hash}/{key}.pdf` | Descarga del PDF |

`POST /reports/generate` — cuerpo:

```json
{
  "order_id": "ORD-1001",
  "report": "quiensoy",
  "person": { "name": "Juan Pedro Martinez", "birth_date": "1991-11-20" },
  "partner": { "name": "Ana Belen", "birth_date": "1991-04-21" },
  "month": null, "week": null, "year": null
}
```

Respuesta:

```json
{ "ok": true, "report": "quiensoy", "order_id": "ORD-1001",
  "url": "https://x.up.railway.app/files/<hash>/quiensoy.pdf",
  "path": "/files/<hash>/quiensoy.pdf" }
```

## Integración con la tienda Next.js

📖 **Guía completa de integración: [`docs/INTEGRACION.md`](docs/INTEGRACION.md)**
(contrato de la API, catálogo, firma HMAC, esquema Drizzle, disparo al pago,
idempotencia, reintentos y checklist).

Cliente reutilizable (server-side; nunca expongas `WEBHOOK_SECRET` al navegador):

```ts
// lib/report-generator.ts
import { createHmac } from "crypto";

const GENERATOR_URL = process.env.REPORT_GENERATOR_URL!;   // https://…railway.app
const WEBHOOK_SECRET = process.env.REPORT_WEBHOOK_SECRET!;

type GenerateInput = {
  orderId: string;
  report: string;
  person: { name: string; birthDate: string; nameSanitize?: string };
  partner?: { name: string; birthDate: string };
  month?: number; week?: number; year?: number;
};

export async function generateReport(input: GenerateInput) {
  const payload = {
    order_id: input.orderId,
    report: input.report,
    person: {
      name: input.person.name,
      birth_date: input.person.birthDate,          // "YYYY-MM-DD"
      name_sanitize: input.person.nameSanitize,
    },
    partner: input.partner && {
      name: input.partner.name,
      birth_date: input.partner.birthDate,
    },
    month: input.month, week: input.week, year: input.year,
  };

  const body = JSON.stringify(payload);            // se firma EXACTAMENTE lo que se envía
  const signature = createHmac("sha256", WEBHOOK_SECRET).update(body).digest("hex");

  const res = await fetch(`${GENERATOR_URL}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Signature": signature },
    body,
  });
  if (!res.ok) throw new Error(`Generador ${res.status}: ${await res.text()}`);
  return (await res.json()) as { ok: boolean; url: string; path: string };
}
```

Disparo al confirmarse el pago (route handler del proveedor de pagos), guardando
la URL con Drizzle/Neon:

```ts
// app/api/orders/paid/route.ts
import { generateReport } from "@/lib/report-generator";
import { db } from "@/db";
import { orders } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function POST(req: Request) {
  const order = await req.json();                  // valida antes la firma de TU proveedor

  const { url } = await generateReport({
    orderId: order.id,
    report: order.reportKey,                        // p. ej. "quiensoy"
    person: { name: order.customerName, birthDate: order.birthDate },
  });

  await db.update(orders).set({ reportUrl: url }).where(eq(orders.id, order.id));
  return Response.json({ ok: true, url });
}
```

> Recomendado: para no bloquear el checkout, dispara la generación en segundo
> plano (una cola / `after()` / job) y actualiza `reportUrl` cuando termine.

## Despliegue en Railway

1. Sube este proyecto a un repo y conéctalo a un servicio nuevo en Railway
   (detecta el `Dockerfile`).
2. Crea un **Volume** y móntalo en `/data`.
3. Configura las **Variables**: `WEBHOOK_SECRET`, `PUBLIC_BASE_URL`
   (la URL pública del servicio), `STORAGE_DIR=/data`, `ENVIRONMENT=production`.
4. Coloca los **assets** (`assets/report/**` y `assets/fonts/*.ttf`) en el
   contexto de build antes de desplegar (ver siguiente sección).

## Assets y fuentes

Los assets del catálogo activo ya están **incluidos y optimizados** en el
proyecto (`assets/report/**`, ~110 MB; se recomprimieron de 264 MB con
`scripts/optimize_assets.py` a ~150 DPI). Viajan con el deploy.

- **Fuentes** (`assets/fonts/`): Open Sans (7 pesos) incluidas. Faltan
  `PassionOne-Regular.ttf` y `LazyDog.ttf` (en el original solo existían en
  formato FPDF); mientras no se agreguen, esos textos usan una fuente unicode de
  reserva y la app avisa por log.
- **Re-optimizar / traer otra carpeta**: edita la lista `NEEDED` en
  `scripts/optimize_assets.py` y ejecútalo; toma las carpetas de
  `../reports-pdf/assets/report`, las recomprime y las escribe en `assets/report`.
- **Fondo faltante**: `set_background` prueba `.jpg`/`.png` y, si no encuentra el
  archivo, registra un aviso y sigue (no tumba el reporte). `bonus-pareja` tiene
  así su portada sin fondo: el original pide `pareja/{n}/2026` pero la carpeta
  no-genérica solo trae `1..4.jpg` (arreglable cambiando la clave de portada a `1`).

## Añadir un reporte nuevo

1. Crea `app/reports/<nombre>.py` con una clase que extienda `Report`, siguiendo
   el patrón de `who_im.py` (una función por página: `add_page()` + fondo +
   `text(x, y, …)` + `write_html_at(y, html)`).
2. Registra su clave en `app/registry.py` con `@register("clave")`.
3. Si usa textos largos, añádelos vía `content.get_text(...)`.

Portar cada reporte desde el PHP original es mecánico: las coordenadas `Text(x,y)`
pasan casi 1:1 a `self.text(x, y, …)`.

## Migración de contenido

```bash
py -3 scripts/extract_content.py ../reports-pdf/src/helpers.php content/texts.json
```

Extrae los textos `getTextXxx($n)` del original a JSON (evita transcribir a mano).

## Catálogo de reportes (16 claves)

Todos verificados de extremo a extremo con `scripts/smoke_test.py`. **Ninguno
requiere datos externos** (no hay dependencia de la API WordPress ni de Google
Sheets).

**Individuales**

| Clave | Reporte |
|---|---|
| `reporte-quien-soy` | ¿Quién soy? |
| `reporte-quien-soy-extended` | ¿Quién soy? extendido (13 págs) |
| `reporte-etapa-de-vida-2022` / `-2023` / `-2026` | Etapas de vida (las 3 son iguales) |
| `horoscopo` | Horóscopo |
| `amor-pareja-ano-personal` | Amor / año personal |

**Pareja** (requieren `partner` en la petición)

| Clave | Reporte |
|---|---|
| `reporte-pareja` / `reporte-pareja-2025` | Pareja (año 2026) |
| `reporte-pareja-2023` | Pareja (año 2023) |
| `bonus-pareja` | Pareja (bonus) |
| `reporte-maestro` | Maestro |
| `reporte-herida` | Herida |
| `reporte-antidoto` | Antídoto |
| `reporte-personalidad-pareja` | Personalidad de pareja |
| `reporte-lectura-pareja` | Lectura de pareja |

## Estado

- ✅ Dominio numerológico completo y **probado** (`Person`, `Universal`, reduce).
- ✅ Infraestructura: FastAPI, HMAC, storage en Volume, config por entorno.
- ✅ Catálogo de 16 reportes verificado con `scripts/smoke_test.py` (cada uno
  produce un PDF válido) y muestras reales en `scripts/generate_samples.py`.

### Calibración pendiente (no bloqueante)

- Colocar los **assets** reales (.jpg/.png y .ttf de marca) para el render
  final; sin ellos la app corre con fuente de reserva y fondos ausentes.
- Falta `PassionOne-Regular.ttf` y `LazyDog.ttf` como TTF (solo existen en
  formato FPDF en el original); bájalas de Google Fonts a `assets/fonts/`.
