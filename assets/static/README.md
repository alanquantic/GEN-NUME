# PDFs estáticos (pre-hechos)

Coloca aquí los PDFs ya creados que se venden tal cual (no se generan). El
servidor los sirve en `/static/<archivo>` y el endpoint `/reports/generate`
devuelve su URL cuando la tienda pide su clave.

## Archivos esperados (nombres EXACTOS)

| Clave (`report`) | `variant` | Archivo a subir aquí |
|---|---|---|
| `reporte-semestral` | — | `reporte-semestral.pdf` |
| `agenda-numerologica-2026` | — | `agenda-numerologica-2026.pdf` |
| `planeador-numerologico-2026` | — | `planeador-numerologico-2026.pdf` |
| `agenda-numerologica-2025` | `verde` | `agenda-numerologica-2025-verde.pdf` |
| `agenda-numerologica-2025` | `azul` | `agenda-numerologica-2025-azul.pdf` |
| `agenda-numerologica-2025` | `naranja` | `agenda-numerologica-2025-naranja.pdf` |
| `agenda-numerologica-2025` | `morado` | `agenda-numerologica-2025-morado.pdf` |

- Si un archivo no está subido, ese producto responde **404 `pdf_no_disponible`**.
- Los `.pdf` de esta carpeta SÍ se versionan (viajan con el deploy). Para
  cambiar el catálogo de estáticos, edita `app/static_reports.py`.
- La URL es la misma para todos los compradores (producto digital idéntico).
