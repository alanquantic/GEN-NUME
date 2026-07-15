# Integración con la tienda — generar reportes al comprar

Documentación para conectar la tienda online (Next.js 14 · App Router · Drizzle ·
Neon) con el generador de reportes desplegado en Railway, de modo que **cada
compra de un reporte genere su PDF** y la tienda reciba la URL de descarga.

---

## 1. Flujo

```
Cliente compra un reporte
        │
        ▼
Pago confirmado (webhook del proveedor de pagos o callback de checkout)
        │  por cada reporte del pedido:
        ▼
Tienda Next.js  ──(POST firmado con HMAC)──►  Generador (Railway)
        │                                          │ genera el PDF
        │                                          │ lo guarda en el Volume
        ◄──────────( { ok, url } )─────────────────┘
        │
        ▼
Tienda guarda la URL (Neon/Drizzle) y la entrega al cliente (página / correo)
```

Puntos clave:
- La tienda **firma** cada petición (HMAC-SHA256) con un secreto compartido.
- El generador es **idempotente**: reintentar la misma `(order_id, report)`
  sobrescribe el mismo PDF y devuelve la misma URL.
- No hay datos externos: el reporte se arma solo con los datos que envía la tienda.

---

## 2. Variables de entorno (en la tienda)

```
REPORT_GENERATOR_URL=https://<tu-servicio>.up.railway.app
REPORT_WEBHOOK_SECRET=<el mismo WEBHOOK_SECRET configurado en Railway>
```

> El secreto debe ser **idéntico** en Railway (`WEBHOOK_SECRET`) y en la tienda
> (`REPORT_WEBHOOK_SECRET`). Nunca lo expongas al navegador: úsalo solo en
> código de servidor.

---

## 3. Catálogo de reportes

La clave (`report`) es uno de estos 16 valores. Consulta en vivo con
`GET <URL>/reports`.

| Clave | Reporte | ¿Requiere `partner`? |
|---|---|:--:|
| `reporte-quien-soy` | ¿Quién soy? | No |
| `reporte-quien-soy-extended` | ¿Quién soy? extendido | No |
| `reporte-etapa-de-vida-2022` | Etapas de vida | No |
| `reporte-etapa-de-vida-2023` | Etapas de vida | No |
| `reporte-etapa-de-vida-2026` | Etapas de vida | No |
| `horoscopo` | Horóscopo | No |
| `amor-pareja-ano-personal` | Amor / año personal | No |
| `reporte-pareja` | Pareja (2026) | **Sí** |
| `reporte-pareja-2025` | Pareja (2026) | **Sí** |
| `reporte-pareja-2023` | Pareja (2023) | **Sí** |
| `bonus-pareja` | Pareja (bonus) | **Sí** |
| `reporte-maestro` | Maestro | **Sí** |
| `reporte-herida` | Herida | **Sí** |
| `reporte-antidoto` | Antídoto | **Sí** |
| `reporte-personalidad-pareja` | Personalidad de pareja | **Sí** |
| `reporte-lectura-pareja` | Lectura de pareja | **Sí** |

> `amor-pareja-ano-personal` NO requiere pareja pese al nombre (usa solo los
> datos de la persona).
>
> `reporte-pareja` es el **"año personal de la pareja 2026"** (usa las plantillas
> `pareja-g`). `horoscopo` usa las plantillas `horoscopo`.

### Reportes estáticos (PDF pre-hecho, no se generan)

Productos digitales iguales para todos: el generador solo devuelve la URL del PDF
ya subido. **No requieren `person` ni `partner`.**

| Clave (`report`) | Producto |
|---|---|
| `reporte-semestral` | Reporte semestral |
| `agenda-numerologica-2026` | Agenda Numerológica 2026 Digital PDF |
| `planeador-numerologico-2026` | Planeador Numerológico 2026 Digital PDF |

Se piden por el **mismo** endpoint `POST /reports/generate`. Si el PDF aún no se
ha subido al servidor, responde **404 `pdf_no_disponible`**.

---

## 4. Referencia de la API

### `POST /reports/generate`

**Headers**

| Header | Valor |
|---|---|
| `Content-Type` | `application/json` |
| `X-Signature` | HMAC-SHA256 (hex) del **cuerpo crudo** con `WEBHOOK_SECRET` |

**Body** (solo se aceptan estos campos — enviar campos extra da error 422)

```jsonc
{
  "order_id": "ORD-1001",            // requerido — id del pedido en tu tienda
  "report": "reporte-quien-soy",     // requerido — clave del catálogo
  "person": {
    "name": "Juan Pedro Martinez",   // requerido
    "birth_date": "1991-11-20"       // requerido — formato ISO YYYY-MM-DD
  },
  "partner": {                       // requerido SOLO en reportes de pareja
    "name": "Ana Belen de los Santos",
    "birth_date": "1991-04-21"
  }
}
```

Reglas:
- `birth_date` debe ser una fecha ISO válida `YYYY-MM-DD`.
- No envíes campos que no estén en el esquema (validación estricta → 422).

**Respuesta `200`**

```json
{
  "ok": true,
  "report": "reporte-quien-soy",
  "order_id": "ORD-1001",
  "url": "https://<servicio>.up.railway.app/files/<hash>/reporte-quien-soy.pdf",
  "path": "/files/<hash>/reporte-quien-soy.pdf"
}
```

**Errores**

| Código | `error` | Causa | Qué hacer |
|---|---|---|---|
| 401 | `firma_invalida` | HMAC no coincide | Revisar secreto y que firmes el cuerpo exacto |
| 422 | `payload_invalido` | Falta campo / fecha inválida / campo extra | Corregir el payload (no reintentar igual) |
| 400 | `reporte_desconocido` | `report` no está en el catálogo | Revisar el mapeo producto→clave |
| 400 | `parametros_faltantes` | Falta `partner` (pareja) o `person` (generado) | Enviar el campo faltante |
| 404 | `pdf_no_disponible` | Reporte estático cuyo PDF aún no se subió | Subir el PDF a `assets/static/` y redeployar |
| 500 | `generacion_fallida` | Error interno al render | Reintentar con backoff; si persiste, avisar |

### Otros endpoints
- `GET /health` → `{ "status": "ok" }` (para monitoreo).
- `GET /reports` → `{ "reports": [...16 claves...] }`.
- `GET /files/<hash>/<clave>.pdf` → descarga del PDF.

---

## 5. Firma HMAC (crítico)

Se firma **exactamente el mismo string** que se envía como cuerpo. Si serializas
el JSON dos veces (una para firmar y otra para enviar) y no son idénticos, la
firma fallará. Firma el `body` una vez y reutilízalo.

```ts
import { createHmac } from "crypto";
const body = JSON.stringify(payload);                 // <- este string exacto
const signature = createHmac("sha256", SECRET).update(body).digest("hex");
// fetch(url, { headers: { "X-Signature": signature }, body })  // <- el MISMO body
```

---

## 6. Integración en Next.js

### 6.1 Cliente reutilizable — `lib/report-generator.ts`

```ts
import "server-only";
import { createHmac } from "crypto";

const GENERATOR_URL = process.env.REPORT_GENERATOR_URL!;
const WEBHOOK_SECRET = process.env.REPORT_WEBHOOK_SECRET!;

export type GeneratedKey =
  | "reporte-quien-soy" | "reporte-quien-soy-extended"
  | "reporte-etapa-de-vida-2022" | "reporte-etapa-de-vida-2023" | "reporte-etapa-de-vida-2026"
  | "horoscopo" | "amor-pareja-ano-personal"
  | "reporte-pareja" | "reporte-pareja-2025" | "reporte-pareja-2023" | "bonus-pareja"
  | "reporte-maestro" | "reporte-herida" | "reporte-antidoto"
  | "reporte-personalidad-pareja" | "reporte-lectura-pareja";

export type StaticKey =
  | "reporte-semestral" | "agenda-numerologica-2026" | "planeador-numerologico-2026";

export type ReportKey = GeneratedKey | StaticKey;

export type GenerateInput = {
  orderId: string;
  report: ReportKey;
  person?: { name: string; birthDate: string };   // requerido en generados; omitir en estáticos
  partner?: { name: string; birthDate: string };
};

export async function generateReport(input: GenerateInput): Promise<{ url: string }> {
  const payload: Record<string, unknown> = {
    order_id: input.orderId,
    report: input.report,
  };
  if (input.person) payload.person = { name: input.person.name, birth_date: input.person.birthDate };
  if (input.partner) payload.partner = { name: input.partner.name, birth_date: input.partner.birthDate };

  const body = JSON.stringify(payload);
  const signature = createHmac("sha256", WEBHOOK_SECRET).update(body).digest("hex");

  const res = await fetch(`${GENERATOR_URL}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Signature": signature },
    body,
    cache: "no-store",
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data?.ok) {
    throw new Error(
      `Generador ${res.status}: ${data?.error ?? "desconocido"} ${JSON.stringify(data?.detail ?? "")}`,
    );
  }
  return { url: data.url as string };
}
```

### 6.2 Mapeo producto → clave de reporte

Define qué reporte corresponde a cada producto de tu catálogo y si necesita pareja.

```ts
// lib/report-catalog.ts
import type { ReportKey } from "./report-generator";

type ProductMap = { report: ReportKey; kind: "generated" | "static"; needsPartner?: boolean };

export const PRODUCT_TO_REPORT: Record<string, ProductMap> = {
  // "<id o slug del producto en tu tienda>": { report, kind, needsPartner? }

  // --- Generados (necesitan datos de la persona) ---
  "quien-soy":                { report: "reporte-quien-soy",           kind: "generated" },
  "quien-soy-extendido":      { report: "reporte-quien-soy-extended",  kind: "generated" },
  "etapa-de-vida":            { report: "reporte-etapa-de-vida-2026",  kind: "generated" },
  "horoscopo":                { report: "horoscopo",                   kind: "generated" },
  "amor":                     { report: "amor-pareja-ano-personal",    kind: "generated" },
  "ano-personal-pareja-2026": { report: "reporte-pareja",              kind: "generated", needsPartner: true },
  "maestro":                  { report: "reporte-maestro",             kind: "generated", needsPartner: true },
  "herida":                   { report: "reporte-herida",              kind: "generated", needsPartner: true },
  "antidoto":                 { report: "reporte-antidoto",            kind: "generated", needsPartner: true },
  "personalidad":             { report: "reporte-personalidad-pareja", kind: "generated", needsPartner: true },
  "lectura-pareja":           { report: "reporte-lectura-pareja",      kind: "generated", needsPartner: true },

  // --- Estáticos (PDF pre-hecho; NO necesitan persona ni pareja) ---
  "semestral":                { report: "reporte-semestral",           kind: "static" },
  "agenda-2026":              { report: "agenda-numerologica-2026",    kind: "static" },
  "planeador-2026":           { report: "planeador-numerologico-2026", kind: "static" },
};
```

> - `needsPartner: true` → el checkout debe **recolectar los datos de la pareja**.
> - `kind: "static"` → producto digital pre-hecho: solo se devuelve su URL (no se
>   envían `person` ni `partner`).

### 6.3 Esquema Drizzle (Neon/Postgres)

```ts
// db/schema.ts
import { pgTable, serial, text, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const generatedReports = pgTable(
  "generated_reports",
  {
    id: serial("id").primaryKey(),
    orderId: text("order_id").notNull(),
    reportKey: text("report_key").notNull(),
    status: text("status").notNull().default("pending"), // pending | ready | error
    url: text("url"),
    error: text("error"),
    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  },
  (t) => ({
    // idempotencia: un registro por (pedido, reporte)
    orderReport: uniqueIndex("generated_reports_order_report_idx").on(t.orderId, t.reportKey),
  }),
);
```

### 6.4 Disparo al confirmarse el pago

Llama esto desde el webhook de tu proveedor de pagos (o el callback de checkout).
Procesa **cada reporte** del pedido:

```ts
// app/api/pagos/confirmado/route.ts
import { generateReport } from "@/lib/report-generator";
import { PRODUCT_TO_REPORT } from "@/lib/report-catalog";
import { db } from "@/db";
import { generatedReports } from "@/db/schema";

type OrderItem = {
  productId: string;
  customer: { name: string; birthDate: string };
  partner?: { name: string; birthDate: string };
};

export async function POST(req: Request) {
  // 1) Verifica ANTES la firma/autenticidad de TU proveedor de pagos.
  const order = (await req.json()) as { id: string; items: OrderItem[] };

  for (const item of order.items) {
    const map = PRODUCT_TO_REPORT[item.productId];
    if (!map) continue; // producto que no es un reporte

    // registra en estado pending (idempotente por índice único)
    await db
      .insert(generatedReports)
      .values({ orderId: order.id, reportKey: map.report, status: "pending" })
      .onConflictDoNothing();

    try {
      const { url } = await generateReport({
        orderId: order.id,
        report: map.report,
        // los estáticos no llevan persona/pareja
        person: map.kind === "generated" ? item.customer : undefined,
        partner: map.needsPartner ? item.partner : undefined,
      });
      await db
        .update(generatedReports)
        .set({ status: "ready", url, updatedAt: new Date() })
        .where(/* eq(orderId) AND eq(reportKey) */ undefined as any);
    } catch (e) {
      await db
        .update(generatedReports)
        .set({ status: "error", error: String(e), updatedAt: new Date() })
        .where(/* eq(orderId) AND eq(reportKey) */ undefined as any);
    }
  }

  return Response.json({ ok: true });
}
```

> Sustituye los `where(...)` por tus condiciones Drizzle reales, p. ej.
> `and(eq(generatedReports.orderId, order.id), eq(generatedReports.reportKey, map.report))`.

### 6.5 No bloquear el checkout (recomendado)

Generar un PDF tarda ~1-3 s. Para no demorar la respuesta al proveedor de pagos:

- **Opción simple (Next.js `after`)**: responde de inmediato y genera después.
  ```ts
  import { after } from "next/server";
  // ...
  after(async () => {
    for (const item of order.items) { /* generateReport + update */ }
  });
  return Response.json({ ok: true });
  ```
- **Opción robusta (cola)**: encola un job (Upstash QStash, Inngest, o un cron
  sobre `generated_reports` en estado `pending`) y procésalo aparte. Es la más
  resistente a fallos y reintentos.

---

## 7. Idempotencia y reintentos

- El generador guarda el PDF en `md5(order_id)/<report>.pdf`. **Reintentar la
  misma combinación sobrescribe el mismo archivo** y devuelve la misma URL: es
  seguro reintentar.
- En la tienda, el índice único `(order_id, report_key)` evita duplicados.
- Reintenta solo ante `500` (o error de red) con backoff (p. ej. 3 intentos:
  2 s, 10 s, 30 s). **No** reintantes ante `422`/`400` (son errores de datos).

---

## 8. Entrega del PDF al cliente

`url` es una descarga directa servida por el generador. Dos opciones:
- **Directa**: muestra/envía la `url` tal cual (la ruta usa `md5(order_id)`, no
  es adivinable, pero cualquiera con el enlace puede descargar).
- **Con control de acceso (recomendado para datos personales)**: guarda la `url`
  en tu BD y sírvela a través de una ruta propia de tu tienda que valide la
  sesión del cliente antes de redirigir/proxyear al PDF.

---

## 9. Pruebas

**Salud y catálogo**
```bash
curl https://<servicio>.up.railway.app/health
curl https://<servicio>.up.railway.app/reports
```

**Generar (firmado) desde una terminal** — usa el script incluido en el repo del
generador:
```bash
GENERATOR_URL=https://<servicio>.up.railway.app \
WEBHOOK_SECRET=<secreto> \
  python scripts/call_example.py reporte-quien-soy
```

**Desde la tienda (local)**: apunta `REPORT_GENERATOR_URL` a la URL de Railway (o
a `http://localhost:8000` si corres el generador local) y dispara el flujo de
pago de prueba.

---

## 10. Checklist de puesta en marcha

- [ ] Generador desplegado en Railway con Volume en `/data` y `PUBLIC_BASE_URL` correcto.
- [ ] `WEBHOOK_SECRET` (Railway) = `REPORT_WEBHOOK_SECRET` (tienda).
- [ ] `PRODUCT_TO_REPORT` cubre todos tus productos-reporte.
- [ ] El checkout recolecta datos de pareja para los reportes que lo requieren.
- [ ] Tabla `generated_reports` migrada en Neon.
- [ ] Disparo al pago implementado (idealmente en segundo plano) con manejo de errores/reintentos.
- [ ] Entrega de la URL al cliente (directa o vía ruta autenticada).
