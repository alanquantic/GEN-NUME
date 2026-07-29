# Propuesta — Módulo de reportes dinámicos con IA

> Rama `feat/reportes-dinamicos`. Documento de propuesta: **no hay código de
> producción todavía**, sólo una prueba de concepto medida (`poc_recetas.py`).

## Decisiones tomadas

| # | Decisión | Estado |
|---|---|---|
| 1 | El reporte de salud se reencuadra como **«Mi energía vital y bienestar»** | ✅ decidido |
| 2 | El pináculo se implementa desde **el libro de Laura**, no desde la web | ✅ decidido — ver [`pinaculo-formulas.md`](pinaculo-formulas.md) |
| 3 | Motor de PDF: **WeasyPrint** (HTML+CSS) para los cinco reportes nuevos | ✅ decidido — ver §5.1 y §5.5 |

**Lo que cambió al aparecer el libro** (`LIBRO FINAL-LAURA de 26 de JULIO.docx`):
el pináculo tiene **24 posiciones, no 19**, y las fórmulas están confirmadas por
el diagrama oficial de la autora. Tres posiciones nuevas afectan a las recetas
(**X** reacción/somatizaciones, **Y** síntesis/misión, **Z** regalo divino), y
apareció un **bug en el código en producción** (§2.2). Todo el detalle en
[`pinaculo-formulas.md`](pinaculo-formulas.md).

**Y lo más importante: el capítulo VIII interpreta las 24 posiciones, una por
una.** Eso cierra casi entera la «petición de autoría» que había identificado:
las trece posiciones que se podían calcular pero no interpretar (K, L, M, N, O,
Q, R, S, T, W, X, Y, Z) **ya tienen texto de Laura**. Se extraen con
`scripts/extract_book.py` y entran en el corpus como una segunda fuente.

---

## 0. Respuesta corta

**Sí, es posible — y el corpus que subiste es mejor de lo que hace falta.**

Pero **no** se hace metiendo la documentación entera en el prompt: son
**3.180.617 caracteres ≈ 795.000 tokens**. Ni cabe cómodamente, ni conviene
(coste, y sobre todo dilución: el modelo mezclaría el significado del 7 con el
del 2).

La forma correcta es al revés: **primero se calculan los números de la persona,
y esos números seleccionan qué trozos exactos del texto de Laura entran en el
prompt.** El resultado son dossiers de **15.000–21.000 tokens** por reporte —
un 97 % menos — compuestos **sólo** de material de la autora relativo a *esa*
persona.

Eso no es RAG con embeddings. Es una búsqueda por clave: `(documento, número) → texto`.
Un diccionario. Determinista, auditable y gratis.

**Medido de verdad** (`docs/reportes-dinamicos/poc_recetas.py`, persona de
ejemplo 20/11/1991):

| Receta | Dossier (chars) | ≈ tokens | Piezas resueltas |
|---|---:|---:|---|
| Quién soy | 83.261 | ~21.000 | 14/14 ✅ |
| Amor | 83.150 | ~21.000 | 10/10 ✅ |
| Trabajo | 83.779 | ~21.000 | 9/9 ✅ |
| Propósito y camino de vida | 60.710 | ~15.000 | 13/13 ✅ |
| Salud / bienestar | 62.474 | ~16.000 | 8/8 ⚠️ (ver §1.3) |

Ninguna receta tiene huecos: todas las piezas existen en el corpus.

---

## 1. Qué hay realmente en el corpus

### 1.1 Volumen y estructura

- **50 documentos** (+ README), 3,18 MB de markdown.
- **37 de 50** tienen la estructura `## Significados por número` →
  `### Número N`. Es decir: **se pueden trocear a máquina, sin ambigüedad**.
- Tamaño medio de un trozo por número: **6.307 caracteres** (~1.600 tokens).
  El mayor: 24.328 (Año Personal, que incluye los binomios).
- Los 13 restantes son documentos de **método** (pináculo, tabla de letras,
  desafíos, sinastría, deudas kármicas…). Esos entran completos o por sección,
  y son los mismos para todo el mundo → **se cachean** (ver §6.2).

Esto es lo que hace viable todo el proyecto. Si el corpus fuera prosa continua
sin marcadores por número, habría que montar embeddings y aceptar recuperación
aproximada. Con esta estructura, la recuperación es **exacta por construcción**.

### 1.2 Cobertura por tema (recuento real de menciones)

| Tema | Documentos con material fuerte | Veredicto |
|---|---|---|
| **Amor** | `05-*` completo (6 docs, ~1.000 menciones), `numero-espejo` (142) | 🟢 Excelente |
| **Propósito / camino** | `numero-del-alma`, `tu-destino`, `mision-del-numero-personal`, `etapas-y-ciclos`, `realizaciones-y-metas`, `numero-de-la-madurez`, `mi-proyecto-sentido` | 🟢 Excelente |
| **Quién soy** | Todo el bloque `02-*` + `03-*` (pináculo completo + nombre) | 🟢 Excelente |
| **Trabajo** | `talentos-personales-y-profesionales` (74), `ano-personal` (180), `binomios` (113), `tu-destino`, `numero-del-nombre` | 🟢 Bueno |
| **Salud** | Disperso: ~120 menciones en todo el corpus, ninguna sección dedicada | 🔴 **Hueco real** |

### 1.3 El hueco: salud

No existe un documento «Numerología y salud». Lo que hay es material *adyacente*
repartido:

- `mi-sombra-numero-oculto` — «puede darse enfermedades y baja salud desde
  jóvenes», «angustias, fobias, síntomas de enfermedad», adicciones.
- `armonico-y-desarmonico` — la cara en sombra de cada vibración.
- `tabla-de-letras-y-valores` — «salud reducida», «fatiga física» por letra.
- `tarea-no-aprendida-y-ausencias`, `deudas-karmicas` — lo pendiente.
- `como-potencializar-mi-energia` — prácticas de armonización (sólo 2,3 KB).

**✅ Decidido: se reencuadra como «Mi energía vital y bienestar».** Habla de
patrones de desgaste, de la sombra, de dónde se te va la energía y de prácticas
de armonización — que es exactamente lo que el corpus sí dice. Sin diagnóstico,
sin dolencias, sin pronóstico. Cero autoría extra y cero riesgo legal. Lleva
**aviso sanitario explícito** en portada y cierre.

**El libro mejora este reporte más de lo esperado.** La posición **X · Número de
Reacción** (`B + D`) se define ahí como «tus comportamientos, las somatizaciones,
tu postura corporal, tu tono de voz, la forma de moverte e incluso tus posibles
enfermedades». Es lo más cercano a una posición de salud que existe en el método,
y es de la autora. Entra en la receta.

Queda **una petición de autoría opcional** para subir el nivel: 11 fichas (una
por vibración 1–9, 11, 22) de «Bienestar y energía del número N», ~1 página cada
una. No bloquea el lanzamiento; lo mejora.

---

## 2. Arquitectura propuesta

```
  POST /reports/generate-ai
        │  { report: "amor", person: {...}, partner?: {...} }
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. DOMINIO (determinista, sin IA)                           │
  │    Person + Pinnacle → A..S, alma, expresión, nombre,       │
  │    año/mes/día personal, etapas, realizaciones, ausencias,  │
  │    sinastría si hay pareja                                  │
  └─────────────────────────────────────────────────────────────┘
        │  numbers = {"A": 11, "B": 2, "H": 4, "ALMA": 9, ...}
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 2. RECETA (tabla estática por reporte)                      │
  │    [("02-.../numero-espejo", "J"), ("05-.../numero-de-...", │
  │     "PAREJA"), ...]                                          │
  └─────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 3. KB   content/kb/index.json  (generado en build)          │
  │    slug + número → trozo de markdown de Laura, literal      │
  └─────────────────────────────────────────────────────────────┘
        │  dossier ≈ 20k tokens, sólo de ESTA persona
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 4. LLM   claude-opus-5   (system cacheado + dossier)         │
  │    salida JSON validada contra esquema                       │
  └─────────────────────────────────────────────────────────────┘
        │  { titulo, frase_clave, secciones[], tension, plan[] }
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 5. MAQUETA  Jinja2 → HTML+CSS → WeasyPrint → PDF            │
  │    gráficos SVG generados desde `numbers`                    │
  └─────────────────────────────────────────────────────────────┘
```

### 2.1 Por qué NO vector database

La pregunta que resuelve un RAG es *«¿qué texto se parece a esta consulta?»*.
Aquí no hay consulta difusa: **sabemos exactamente qué buscar**, porque lo
acabamos de calcular. Un embedding sólo introduciría la posibilidad de traer el
significado del número equivocado. La recuperación por clave es 100 % precisa,
0 ms, 0 € y se puede revisar a ojo.

### 2.2 Lo que falta en el dominio actual

`app/domain/person.py` cubre: número personal (día), año/mes/día/semana
personal, etapas de vida, alma (vocales), expresión (consonantes), desarrollo
profesional, y **toda la sinastría de pareja A–W**.

**No cubre el pináculo individual.** Y no son 19 posiciones sino **24**: el
libro añade `T` (ausencias), `W` (triplicidad), `X` (reacción), `Y` (síntesis /
misión) y `Z` (regalo divino), más las reglas de comprobación, kármicos y
triplicidad. Todas las fórmulas están confirmadas por el diagrama oficial y
especificadas en **[`pinaculo-formulas.md`](pinaculo-formulas.md)**.

> **La fuente es el libro, no la web.** Cotejé las dos con 20/11/1991: la zona
> inferior cuadra al 100 % (D=6, O=Q=R=S=0, P=6), pero **la web devuelve I=1 y
> J=7 y el libro da I=7 y J=1** — parecen intercambiados. Hasta resolverlo, la
> implementación sigue el libro. Conviene revisar el Next.js: si el fallo está
> ahí, hoy está publicando el espejo de pareja de todo el mundo cambiado.

> ⚠️ **Bug en producción.** `Person._stages_timeline()` calcula la primera etapa
> como `36 − reduce(día+mes+año)` sin reducir los maestros a su base. Para
> alguien con D = 11 o 22 la etapa sale 9–18 años corta y **todas** las
> siguientes se desplazan. Afecta a `reporte-etapa-de-vida-*`, que ya se vende.
> Detalle y corrección en [`pinaculo-formulas.md`](pinaculo-formulas.md) §7.

---

## 3. Las cinco recetas

Cada receta es una lista de `(documento, clave_de_número)`. Están escritas y
verificadas en `poc_recetas.py`.

### R1 · ¿Quién soy? — según mi nombre y fecha de nacimiento
`significado-espiritual`[B] · `numero-personal`[B] · `numero-del-karma`[A] ·
`numero-de-vida-pasada`[C] · `numero-de-la-personalidad`[D] · `tu-destino`[H] ·
`numero-del-subconsciente`[I] · `numero-espejo`[J] · `mi-sombra`[P] ·
`armonico-y-desarmonico`[B] · `numero-del-alma`[ALMA] · `numero-del-nombre`[NOMBRE] ·
`expresion-del-alma-y-personalidad`[EXPRESIÓN] · `nombre-activo`[ACTIVO]
→ **~21k tokens · 14 piezas**

### R2 · Numerología en el amor
`numero-espejo`[J] · `numero-personal`[B] · `numero-del-alma`[ALMA] ·
`relacion-entre-numeros`[B] y [J] · `numero-de-pareja`[PAREJA] ·
`el-amor-segun-tu-ano-personal`[AP] · `ciclo-de-vida-de-la-pareja`[AÑO-REL] ·
`almas-gemelas-karmicas-y-dharmicas` (íntegro) · `sinastria-numerologica` (intro)
→ **~21k tokens · 10 piezas**
*Sin pareja funciona igual: describe a la pareja ideal (J) en vez de comparar.*

### R3 · Numerología en el trabajo
`talentos-personales-y-profesionales`[B] y [H] · `tu-destino`[H] ·
`numero-personal`[B] · `expresion-del-alma-y-personalidad`[EXPRESIÓN] ·
`numero-del-nombre`[NOMBRE] · `ano-personal`[AP] · `binomios-energeticos`[AP] ·
`realizaciones-y-metas`[REALIZACIÓN VIGENTE]
→ **~21k tokens · 9 piezas**

### R4 · Mi energía vital y bienestar *(antes «salud» — ver §1.3)*
`significado-espiritual`[B] · `armonico-y-desarmonico`[B] y [D] · `mi-sombra`[P] ·
`tarea-no-aprendida-y-ausencias`[AUSENCIAS] · `como-potencializar-mi-energia` (íntegro) ·
`deudas-karmicas` (íntegro) · `ano-personal`[AP]
→ **~16k tokens · 8 piezas** · ⚠️ aviso sanitario obligatorio

### R5 · Mi propósito y camino de vida
`significado-espiritual`[B] · `numero-del-alma`[ALMA] · `tu-destino`[H] ·
`mision-del-numero-personal`[B] · `numero-de-la-madurez`[MADUREZ] ·
`reidentificacion-con-tu-yo`[B] · `encuentro-con-tu-maestro`[MAESTRO] ·
`mi-proyecto-sentido`[PROYECTO] · `etapas-y-ciclos`[E1..E4] ·
`realizaciones-y-metas`[REALIZACIÓN]
→ **~15k tokens · 13 piezas**

---

## 4. El prompt

Está escrito, completo y listo para probar:

- [`prompts/sistema.md`](prompts/sistema.md) — voz, reglas de anclaje,
  prohibiciones, esquema de salida. **Es la parte cacheable** (idéntica en cada
  petición del mismo reporte).
- [`prompts/usuario.md`](prompts/usuario.md) — plantilla con los datos, los
  números y el dossier.

### Decisiones de diseño del prompt, y por qué

| Decisión | Motivo |
|---|---|
| **Anclaje duro**: sólo puede afirmar lo que esté en `<material>` | Es el mecanismo antialucinación. El modelo no «sabe numerología» aquí; transcribe e integra a Laura. |
| Los números van **ya calculados** en el prompt, y se le prohíbe recalcular | Los LLM son malos con aritmética y buenos con prosa. Separar las dos cosas elimina la clase de error más embarazosa (un número mal en un PDF de pago). |
| **Salida JSON con esquema** (structured outputs) | La maqueta necesita bloques, no un churro de markdown. Además permite regenerar una sección sola sin rehacer el reporte. |
| **Sección obligatoria «la tensión central»** | Es lo que diferencia un reporte dinámico de cinco horóscopos pegados. El modelo tiene que nombrar la contradicción entre dos números concretos de *esta* persona (p. ej. esencia 2 conciliadora vs. karma 11 exigente). Un reporte estático no puede hacer esto. |
| **Referencias cruzadas obligatorias** entre secciones | Misma razón: coherencia de retrato, no lista de fichas. |
| Longitud **por palabras, por sección** | Control de maquetación. Sin esto, las páginas se descuadran. |
| Prohibiciones explícitas: nada médico, legal, financiero, ni fechas de muerte, embarazo o enfermedad | Riesgo real de producto. |
| Prohibido el relleno («recuerda que eres único y especial») | Es lo que hace que un texto generado se note. |
| `effort: high`, thinking adaptativo | La calidad importa más que 20 s de latencia en un producto de pago. |

---

## 5. Propuesta de diseño de los reportes

### 5.1 Motor: cambiar de fpdf2 a HTML+CSS → WeasyPrint

**Esta es la recomendación técnica de más peso del documento.**

Los 16 reportes actuales funcionan con el modelo heredado del PHP: un `.jpg` de
página completa como fondo + `text(x, y, …)` en coordenadas absolutas de
milímetro. Eso funciona **porque el texto es fijo y ya está calibrado**.

Con texto generado por IA, la longitud varía en cada persona. Con coordenadas
absolutas, un párrafo dos líneas más largo pisa el pie de página. Se puede
forzar al modelo a contar caracteres, pero es pelear contra la herramienta.

**Propuesta:** para *estos cinco* reportes, maquetar con HTML + CSS y renderizar
con **WeasyPrint**:

- Flujo natural: el texto empuja, no se solapa. Nunca.
- `@page`, cabeceras y pies corridos, numeración, índice automático.
- SVG nativo → los gráficos se generan como SVG y entran directos.
- Reutiliza **exactamente** los tokens de diseño de la web (§5.2).
- Python puro. En el `Dockerfile` sólo añade
  `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libgdk-pixbuf-2.0-0`.
  (Descartado Playwright/Chromium: ~400 MB de imagen para lo mismo.)

**Los 16 reportes existentes no se tocan.** Conviven: `registry.py` decide qué
motor usa cada clave. El endpoint, la firma HMAC y el storage no cambian.

### 5.2 Sistema de diseño — heredado de web-nume.vercel.app

Extraje las variables CSS reales del sitio. **Ya tenéis un color por área, y
coincide uno a uno con cuatro de los cinco reportes.** Es un regalo:

| Token del sitio | HSL | Hex | Uso en el PDF |
|---|---|---|---|
| `--primary` | `263 67% 35%` | `#4C1D95` | Marca, títulos · **Quién soy** |
| `--accent` | `46 64% 52%` | `#D3AE36` | Oro: filetes, números destacados, portada |
| `--area-amor` | `330 81% 60%` | `#EC4899` | **Amor** |
| `--area-trabajo` | `217 91% 60%` | `#3B82F6` | **Trabajo** |
| `--area-bienestar` | `160 84% 39%` | `#059669` | **Energía vital y bienestar** |
| `--area-espiritual` | `271 76% 53%` | `#A855F7` | **Propósito y camino de vida** |
| `--background` | `270 60% 98%` | `#FBF9FE` | Fondo de página |
| `--foreground` | `263 35% 18%` | `#2A1E3E` | Texto |
| `--border` | `270 32% 90%` | `#E6DDEE` | Filetes, bordes de tarjeta |
| `--secondary` | `270 100% 96%` | `#F5EBFF` | Fondo de bloques destacados |
| `--gray` | `255 10% 48%` | `#746E87` | Texto secundario, notas al margen |
| `--danger` | `350 80% 55%` | `#E8304F` | Polaridad desarmónica, avisos |

**Tipografía.** El sitio usa Inter en todo. Para papel conviene contraste:

- **Cuerpo:** Inter (o la Open Sans que ya está en `assets/fonts/`) 10,5 pt /
  16 pt de interlínea. Mantiene la continuidad con la web.
- **Display:** el número protagonista y los títulos de sección en **PassionOne**
  (ya es fuente de marca; falta el `.ttf`, está en Google Fonts).
- **Cifras del pináculo:** tabulares, para que la rejilla no baile.

**Retícula.** A4 con margen asimétrico: 22 mm izq · 116 mm de columna de texto ·
**38 mm de margen derecho vivo** para números al margen, la etiqueta de la
posición del pináculo y micro-glosas. Ese margen ancho es lo que hace que un
reporte numerológico parezca un estudio y no un folleto.

### 5.3 Anatomía de un reporte (14 páginas)

| Pág. | Contenido |
|---|---|
| 1 | **Portada.** Nombre, fecha, el número protagonista en enorme (150 pt, en el color del área), la `frase_clave` del modelo. Fondo del color del área al 6 %. |
| 2 | **Tus números.** Ficha: los 8–14 números que alimentan *este* reporte, con etiqueta y valor. Transparencia total sobre de dónde sale todo. |
| 3 | **El gráfico principal** del área a página completa (§5.4). |
| 4 | **Tu retrato** — la síntesis, 250–300 palabras. |
| 5–10 | **Cuerpo**, una sección por página o página y media. Cada una: entradilla en oro, 2–4 párrafos, y un bloque destacado (cita / dato / alerta). |
| 11 | **La tensión central** — página a color pleno del área, texto en blanco. El momento de mayor impacto del reporte. |
| 12 | **Tu plan** — 4–6 prácticas concretas, en tarjetas. |
| 13 | **Tu calendario** — barra del año personal con los meses marcados (sólo en Trabajo y Amor). |
| 14 | **Cierre + aviso legal + CTA** a la tienda / consulta. |

### 5.4 Los siete gráficos (todos SVG, generados en servidor)

Salen de lo que ya existe en el sitio o de datos que el dominio ya calcula.

1. **El Pináculo A–S.** Es el gráfico insignia y ya está en
   `/calculatupinaculo` con las etiquetas correctas («A. Número de Karma — Mi
   tarea pendiente», «J. Número del inconsciente — Mi espejo»…). Rejilla
   piramidal, celdas con el número, etiqueta al margen. → **Quién soy**.
2. **Línea de etapas de vida.** Barra horizontal de 4 tramos con años y edades,
   y un marcador «estás aquí». `Person._stages_timeline()` ya devuelve
   exactamente estos datos. → **Propósito**, **Trabajo**.
3. **Rueda del año personal 1→9.** Círculo de nueve sectores, el actual
   iluminado en el color del área, los demás al 12 %. Da de un vistazo «en qué
   punto del ciclo estás». → **Trabajo**, **Amor**, **Bienestar**.
4. **Balanza armónico ↔ desarmónico.** Barra bipolar por número: a la izquierda
   los rasgos de la polaridad positiva, a la derecha los de la sombra, con el
   número en el fiel. Es la traducción visual directa de
   `armonico-y-desarmonico.md`. → **Bienestar**, **Quién soy**.
5. **Cuadrícula de presencias y ausencias.** 3×3 con los dígitos 1–9; los
   presentes en tu pináculo encendidos, los ausentes apagados y con contorno
   discontinuo. Materializa `tarea-no-aprendida-y-ausencias`. → **Bienestar**,
   **Quién soy**.
6. **Tira del nombre.** Cada letra con su valor debajo; vocales arriba en oro
   (alma), consonantes abajo en violeta (personalidad), y una regleta con la
   letra activa del ciclo de vida del nombre según la edad
   (`get_professional_development()` ya lo resuelve). → **Quién soy**,
   **Trabajo**.
7. **Puente de sinastría.** Dos columnas de números enfrentadas (tú / pareja)
   con líneas de unión codificadas por tipo de relación: natural,
   complementaria, de aprendizaje, de reto. El propio sitio ya usa esa
   taxonomía en `/numerologia-de-pareja`. → **Amor con pareja**.

Extra de bajo coste: **medidor de intensidad** (nueve barritas, N encendidas)
para expresar «tu año vibra 3 sobre 9», reutilizable en cualquier sección.

### 5.5 «¿WeasyPrint es lo más sencillo para el usuario final?»

Conviene separar dos cosas que se confunden fácil:

| | Qué es | Lo ve el usuario |
|---|---|---|
| **Motor** (WeasyPrint vs fpdf2) | Cómo el servidor dibuja el PDF | **No.** Recibe un PDF idéntico en ambos casos |
| **Formato de entrega** (PDF descargable / página web / email) | Cómo le llega | **Sí.** Es lo único que percibe |

El motor es invisible. Elegirlo no empeora ni mejora nada para quien compra: es
una decisión de mantenibilidad. Lo que sí se decide aparte es el formato — y ahí
es donde tu duda tiene fondo, porque **un PDF de 14 páginas en un móvil se lee
regular**, y la mayoría de tus compras van a llegar desde Instagram.

**Y aquí está el argumento fuerte a favor de HTML, que no había puesto encima de
la mesa:** con fpdf2 sólo puedes producir PDF. Con HTML el mismo fichero da
**dos salidas desde una única plantilla**:

1. **PDF descargable** — para guardar, imprimir y regalar. Es el entregable que
   justifica el precio y lo que la gente espera al comprar un «reporte».
2. **Página web privada** con enlace único (`/mi-reporte/<token>`) — responsive,
   se lee bien en el móvil, se abre al instante desde el email, con índice
   lateral y el botón de descargar el PDF arriba. Y como vive en tu dominio,
   permite lo que un PDF no: seguir leyendo donde lo dejaste, compartir una
   sección suelta, y enlazar a la tienda desde dentro.

Mi recomendación de producto: **entregar las dos, con la web por delante**. El
email dice «tu reporte ya está listo» y lleva a la página; el PDF es un botón
dentro. Sale gratis en esfuerzo — es la misma plantilla — y resuelve justo el
problema que te preocupa.

Con el motor actual esa opción ni existe. Por eso el cambio no es sólo
mantenibilidad: **es lo que hace posible la experiencia móvil.**

Riesgos reales de WeasyPrint, para que estén dichos:

- No soporta *container queries* ni JavaScript. Irrelevante aquí: la maqueta usa
  `@page` en milímetros y los gráficos son SVG estático.
- El `Dockerfile` necesita cuatro paquetes de sistema (`libpango`, `libpangoft2`,
  `libharfbuzz`, `libgdk-pixbuf`). Es una línea de `apt-get`.
- Tipografía menos fina que un motor de imprenta profesional. Para un reporte de
  consumo no se nota; si algún día quisierais calidad de imprenta, la salida
  natural es Chromium/Playwright, y **la misma plantilla HTML sirve**. Con fpdf2
  esa puerta está cerrada.

---

## 6. Operación

### 6.1 El contrato de la API tiene que cambiar a asíncrono

La generación tarda **30–90 s** (llamada al modelo + render). El endpoint actual
es síncrono y devuelve la URL en la respuesta. Propuesta:

```
POST /reports/generate-ai   →  202  { job_id, status: "queued" }
GET  /reports/jobs/{job_id} →  200  { status: "done", url: "..." }
```

y opcionalmente un webhook de vuelta a la tienda. Firma HMAC igual que ahora.
En la tienda: «Tu reporte se está escribiendo, te llega por email en un par de
minutos» — que además comunica bien que es artesanal, no instantáneo.

### 6.0 Proveedor de IA — Anthropic o Google (Gemini)

El sistema es agnóstico del modelo: el prompt, el dossier, el esquema y la
validación de anclaje son idénticos. Sólo cambia [`app/ai/providers.py`](../../app/ai/providers.py),
que despacha por `AI_PROVIDER`:

| Proveedor | Modelo por defecto | Salida estructurada | Notas |
|---|---|---|---|
| `anthropic` | `claude-opus-5` | `output_config.format` | prompt cacheado, effort |
| `google` | `gemini-2.5-pro` | `response_schema` (subconjunto OpenAPI) | **tier gratuito** con `gemini-2.5-flash` en AI Studio |

El esquema JSON se adapta automáticamente al dialecto de Gemini
(`to_gemini_schema`: quita `additionalProperties`, colapsa el opcional
`anyOf:[null,…]` a `nullable`), y está validado contra el SDK de Google.

Para usar Gemini: `AI_PROVIDER=google` + `GOOGLE_API_KEY=…`. El resto del
sistema no cambia.

### 6.2 Coste por reporte

Con `claude-opus-5` ($5 / $25 por millón de tokens):

| Concepto | Tokens | Coste |
|---|---:|---:|
| Entrada (dossier ~21k + sistema ~4k) | 25.000 | $0,125 |
| Salida (JSON, 14 páginas) | ~8.000 | $0,200 |
| **Total sin optimizar** | | **≈ $0,33** |

Con **prompt caching** sobre el bloque de sistema + los documentos de método
(idénticos en todas las peticiones del mismo reporte, lecturas a 0,1×):
**≈ $0,30**. Con `claude-sonnet-5` bajaría a ~$0,20, pero para un producto de
pago recomiendo Opus: la diferencia son céntimos y el texto es *el producto*.

**Batch API** (50 % de descuento, hasta 24 h) es interesante para
regeneraciones masivas si cambiáis el prompt, no para pedidos en caliente.

### 6.3 Control de calidad

- **Validación dura**: si el JSON no valida contra el esquema, o si aparece en
  el texto un número que no está en `numbers`, se reintenta una vez y si falla
  se avisa. Nunca se entrega un PDF con un número inventado.
- **Cachear el texto por firma** `(reporte, nombre_normalizado, fecha, año)`:
  la misma persona pidiendo dos veces no paga dos generaciones, y el reporte no
  cambia entre descargas — que es lo que la gente espera.
- **Semilla de estilo**: el mismo prompt + los mismos números dan textos muy
  parecidos pero no idénticos. Si quieres reproducibilidad total, guardas el
  JSON generado y regeneras sólo el PDF.

---

## 7. Lo que queda por decidir

*(1 y 3 de la lista original ya están decididos — ver la tabla del principio.)*

1. **¿Se dice que hay IA?** Mi recomendación: **no destacarlo en el producto**,
   pero sí una nota honesta en el pie legal («redactado a partir del método y
   los textos de Laura L. Rodríguez»). Todo el contenido es suyo; el modelo
   selecciona, integra y personaliza. Pero es tu marca y tu llamada.
2. **¿PDF + página web, o sólo PDF?** (§5.5) Recomiendo las dos, con la web por
   delante. Cuesta lo mismo y arregla la lectura en móvil.
3. **Longitud y precio.** He asumido ~14 páginas. Si el producto va a costar
   más, el mismo dossier da para 20–24 sin tocar la arquitectura (sólo más
   secciones en el esquema).
4. **Pareja obligatoria en Amor.** ¿El reporte de amor se vende con y sin
   pareja (dos SKU) o siempre con? Técnicamente ambas funcionan.
5. **Textos por vibración de X, Y, Z y W** — segunda petición de autoría a
   Laura. Las fórmulas están; el significado por número no aparece en el libro
   extraído, y sin él esas posiciones se pueden calcular y dibujar pero no
   interpretar (regla de anclaje).
6. **Elevación de H** (2→11, 4→22): el libro lo deja al criterio del
   consultante. Propongo exponerlo como «potencial» en el texto en vez de
   elegir por la persona.

---

## 8. Plan por fases

| Fase | Entregable | Depende de |
|---|---|---|
| **1** | ✅ **hecho** — [`app/domain/pinnacle.py`](../../app/domain/pinnacle.py): las 24 posiciones, kármicos, comprobación de D/H, triplicidad, ausencias y las 4 etapas. 27 pruebas en [`tests/test_pinnacle.py`](../../tests/test_pinnacle.py), verificadas contra los ejemplos del libro. Sin regresiones (`smoke_test.py`: 17/17) | — |
| **2** | ✅ **hecho** — [`scripts/extract_book.py`](../../scripts/extract_book.py) saca del libro las 9 secciones de interpretación que faltaban; [`scripts/build_kb.py`](../../scripts/build_kb.py) trocea las dos fuentes en `content/kb/index.json` (59 docs · 514 trozos) y valida las recetas contra **todas** las vibraciones. Recetas en [`app/ai/recipes.py`](../../app/ai/recipes.py) | — |
| **3** | ✅ **hecho** — [`app/ai/numbers.py`](../../app/ai/numbers.py) resuelve toda clave a su valor; [`app/ai/knowledge.py`](../../app/ai/knowledge.py) sirve trozos y deduplica; [`app/ai/dossier.py`](../../app/ai/dossier.py) ensambla `<numeros>`+`<material>`. Inspección sin gastar tokens: `scripts/preview_dossier.py`. 10 pruebas en [`tests/test_dossier.py`](../../tests/test_dossier.py) | 1, 2 |
| **4** | ✅ **hecho** — [`app/ai/prompts.py`](../../app/ai/prompts.py) (sistema + encargos + esquema JSON) y [`app/ai/generate.py`](../../app/ai/generate.py): llamada a `claude-opus-5` con salida estructurada garantizada, prompt cacheado y validación de anclaje. **Modo de prueba sin API** (`--mock`) con respuesta de ejemplo en `content/mock/`; muestra legible en [`muestra-quien-soy.txt`](muestra-quien-soy.txt). Correr real: `ANTHROPIC_API_KEY=… py -3 scripts/generate_report.py <reporte> "<nombre>" <fecha>`. Falta ejecutarlo con la clave real. | 3 |
| **5** | ✅ **hecho** — [`app/pdf/charts.py`](../../app/pdf/charts.py) (5 gráficos SVG desde los números), [`app/pdf/html_report/`](../../app/pdf/html_report/) (plantilla Jinja2 + CSS con `@page` A4 y color de área por reporte) y [`app/pdf/html_renderer.py`](../../app/pdf/html_renderer.py) (JSON+números → HTML → PDF con WeasyPrint). Dockerfile con las libs nativas. Correr: `py -3 scripts/render_report.py <reporte> "<nombre>" <fecha> --mock`. Muestra: [`maqueta-quien-soy.html`](maqueta-quien-soy.html). El PDF se genera en Linux (en Windows WeasyPrint no importa; el HTML sí). | §5.1 |
| **6** | ⏳ **pendiente** — endpoint asíncrono `/reports/generate-ai` + job store, **separado** del `/reports/generate` de los 16 reportes viejos. Es lo que la tienda llamará al pagar. | 4, 5 |
| **7** | Muestras reales de las 5 y revisión con Laura | todo |

La fase 4 es el punto de validación: con relativamente poco trabajo se puede
tener el texto de un reporte real en pantalla y decidir si el resultado merece
seguir.

---

## Anexos

- **[`pinaculo-formulas.md`](pinaculo-formulas.md)** — especificación de cálculo
  de las 24 posiciones, extraída del libro. Es la base de `app/domain/pinnacle.py`.
- [`pinaculo-diagrama-oficial.png`](pinaculo-diagrama-oficial.png) — el diagrama
  de fórmulas de Laura, extraído del `.docx`.
- [`mockup-diseno.html`](mockup-diseno.html) — paleta, tres páginas A4 y los
  siete gráficos. Ábrelo en el navegador.
- [`prompts/sistema.md`](prompts/sistema.md) — prompt de sistema completo
- [`prompts/usuario.md`](prompts/usuario.md) — plantilla de usuario
- [`poc_recetas.py`](poc_recetas.py) — prueba de concepto: trocea el corpus,
  resuelve las 5 recetas y mide el coste. Ejecutar desde `GENERADOR/`:
  `py -3 docs/reportes-dinamicos/poc_recetas.py`
