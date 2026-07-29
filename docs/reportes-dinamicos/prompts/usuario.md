# Plantilla del mensaje de usuario

El ensamblador (`app/ai/dossier.py`) rellena esta plantilla. Todo lo que va
antes de `<material>` es corto y variable; el `<material>` es el dossier
troceado del corpus.

---

```text
<persona>
Nombre completo: {{nombre}}
Nombre de pila: {{nombre_pila}}
Fecha de nacimiento: {{fecha_larga}}   ({{dia}} / {{mes}} / {{anio}})
Edad hoy: {{edad}} años
Fecha de hoy: {{hoy}}
</persona>

{{#pareja}}
<pareja>
Nombre: {{pareja_nombre}}
Fecha de nacimiento: {{pareja_fecha_larga}}
{{#inicio_relacion}}La relación empezó: {{inicio_relacion}}{{/inicio_relacion}}
</pareja>
{{/pareja}}

<numeros>
Estos valores están calculados y son correctos. Úsalos tal cual.

  B   Número personal (esencia, día de nacimiento) ........ {{B}}
  A   Número del karma (mes de nacimiento) ................ {{A}}
  C   Número de vida pasada (año de nacimiento) ........... {{C}}
  D   Número de la personalidad (la máscara) .............. {{D}}
  H   Número del destino .................................. {{H}}
  I   Número del subconsciente ............................ {{I}}
  J   Número del inconsciente / espejo / pareja ideal ..... {{J}}
  P   Número de sombra (súper oculto) ..................... {{P}}

  ALMA       Número del alma (vocales del nombre) ......... {{ALMA}}
  EXPRESION  Expresión / personalidad (consonantes) ....... {{EXPRESION}}
  NOMBRE     Número del nombre completo ................... {{NOMBRE}}
  ACTIVO     Número del nombre activo ..................... {{ACTIVO}}
  INICIAL    Primera letra del nombre ..................... {{INICIAL}}

  MADUREZ    Número de la madurez ......................... {{MADUREZ}}
  MAESTRO    Encuentro con tu maestro ..................... {{MAESTRO}}
  PROYECTO   Proyecto sentido ............................. {{PROYECTO}}
  AUSENCIAS  Números ausentes del pináculo ................ {{AUSENCIAS}}
  DEUDAS     Deudas kármicas detectadas ................... {{DEUDAS}}

  AP   Año personal {{anio_actual}} ....................... {{AP}}
  AU   Año universal {{anio_actual}} ...................... {{AU}}
  MP   Mes personal ({{mes_actual}}) ...................... {{MP}}
  REALIZACION  Realización vigente ........................ {{REALIZACION}}

  Etapas de vida:
    Etapa 1 · vibración {{E1}} · {{E1_anios}} · {{E1_edades}} años
    Etapa 2 · vibración {{E2}} · {{E2_anios}} · {{E2_edades}} años
    Etapa 3 · vibración {{E3}} · {{E3_anios}} · {{E3_edades}} años
    Etapa 4 · vibración {{E4}} · {{E4_anios}} · {{E4_edades}} años
    Etapa actual: {{ETAPA_ACTUAL}}

{{#pareja}}
  PAREJA     Número de la pareja .......................... {{PAREJA}}
  AÑO-REL    Año personal de la relación .................. {{ANIO_RELACION}}
  Sinastría: A={{S_A}} B={{S_B}} C={{S_C}} D={{S_D}} … W={{S_W}}
{{/pareja}}
</numeros>

<material>
Textos de Laura L. Rodríguez correspondientes exactamente a los números de
arriba. Es tu única fuente. Están sin editar, tal como los escribió.

{{#piezas}}
─────────────────────────────────────────────────────────────────────────
FUENTE: {{doc_titulo}} — vibración {{numero}}   [{{clave}} = {{valor}}]
─────────────────────────────────────────────────────────────────────────
{{texto}}

{{/piezas}}
</material>

Escribe ahora el reporte «{{reporte_titulo}}» para {{nombre_pila}}, siguiendo
tu encargo y devolviendo únicamente el JSON.
```

---

## Notas de implementación

**Orden del dossier.** Las piezas se emiten siempre en el orden de la receta,
que es fijo. Así, dos peticiones del mismo reporte comparten prefijo hasta
`<material>` y el bloque de sistema entra íntegro en la caché.

**Deduplicación.** El corpus contiene párrafos repetidos entre entradas de blog
distintas (el mismo texto aparece hasta 7 veces en algunos ficheros). El
ensamblador quita párrafos duplicados por hash dentro de un mismo dossier.
Ahorra ~5 % — poco, pero también evita que el modelo dé más peso a una idea
sólo porque el export la repitió.

**Claves ausentes.** Si un número no aplica (sin pareja, sin deudas kármicas,
sin ausencias), se omite la línea entera de `<numeros>` en vez de escribir
`null` o `—`. Un hueco explícito invita a rellenarlo; una línea que no está, no.

**Recorte.** Si un dossier superara los ~30k tokens (sólo puede pasar en
Trabajo, por lo grande que es `ano-personal.md`), se recorta por el final de la
pieza más larga respetando límites de párrafo, y se registra en el log qué se
recortó. Nunca truncar en mitad de una frase.

**Llamada** (`app/ai/generate.py`):

```python
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    system=[{"type": "text", "text": SISTEMA[report_key],
             "cache_control": {"type": "ephemeral"}}],
    thinking={"type": "adaptive"},
    output_config={
        "effort": "high",
        "format": {"type": "json_schema", "schema": ESQUEMA[report_key]},
    },
    messages=[{"role": "user", "content": usuario}],
)
```

Con `output_config.format` la salida está garantizada como JSON válido contra
el esquema, así que no hay que parsear a mano ni reintentar por formato. Lo que
sí hay que validar después, en código, es la **regla de anclaje**: que ningún
número citado en el texto esté fuera de `<numeros>`.
