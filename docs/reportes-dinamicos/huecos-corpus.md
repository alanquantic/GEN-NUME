# Huecos de texto del corpus — lo único que falta

> **Fórmulas: no falta ninguna.** Las 33 claves que usan las cinco recetas se
> calculan. Lo que sigue son **textos** que el export de WordPress y el libro no
> traen para ciertas vibraciones. Nada bloquea el arranque — el prompt escribe
> esas secciones más cortas cuando falta el texto — pero tenerlos sube la
> calidad. Ordenados por a cuánta gente afectan.

Frecuencias medidas sobre 18.628 fechas de nacimiento (1955–2005), hoy = 2026.

| Documento | Vibración que falta | Afecta a | Reporte(s) |
|---|---|---|---|
| **La diferencia según el día de nacimiento** | número personal **1** (días 1, 10, 19, 28) | 13 % | ¿Quién soy? |
| **Armónico y Desarmónico** | vibración **1** | 13 % | ¿Quién soy?, Bienestar |
| **Armónico y Desarmónico** | vibración **1** (posición D) | *(igual doc que arriba)* | Bienestar |
| **Número de la Madurez** | madurez **3** | 11 % | Propósito |
| **Binomios Energéticos** | año personal **1** | 11 % | Trabajo |
| **Significado espiritual de los números** | número **4** | 8 % | ¿Quién soy?, Bienestar, Propósito |
| **Súper Ocultos (Q, R, S)** | vibración **0** | ~1 % | ¿Quién soy? |
| **Inconsciente Negativo (O)** | vibración **0** | ~1 % | ¿Quién soy?, Amor |

## Detalle de cada uno

1. **Diferencia por día — el 1.** Falta el texto que distingue a quien nació el
   1, el 10, el 19 o el 28 (todos número personal 1). El resto de días personales
   sí está. *(Hueco del export, ya listado en el README de `new-reports`.)*

2. **Armónico y desarmónico — el 1.** Falta la cara luminosa y en sombra de la
   vibración 1. Se usa en dos sitios (posiciones B y D), así que un mismo texto
   tapa los dos.

3. **Número de la madurez — el 3.** Falta la madurez 3. Del 1 al 22 está todo
   menos ésa.

4. **Binomios energéticos — año personal 1.** Falta el binomio del año personal
   1. *(El documento en sí es enorme; sólo falta esta entrada.)*

5. **Significado espiritual — el 4.** Falta el significado espiritual del número
   4. Es el más transversal: entra en tres reportes.

6. **Los "0" del ser inferior (O y Q).** El libro interpretó estas posiciones a
   partir del 1; el caso "0" (que se da cuando la zona inferior queda plana) no
   lo escribió. Es raro (~1 %) pero real. Si Laura tiene un párrafo de "cuando
   esta posición es 0…", lo añadimos; si no, se queda sin ese trozo.

## Cómo se envía

Cualquiera de estos formatos vale — yo los normalizo al corpus:

- Un párrafo suelto por WhatsApp/correo diciendo a qué documento y número
  corresponde.
- Un enlace al artículo del blog (como los `numero-personal-11-old`).
- Una foto/PDF de la página del libro o de una agenda.

Se meten como **complementos** (igual que hice con los años 8/9/11 del amor):
un fichero en `docs/complementos/` con la cabecera `<!-- extiende: <documento> -->`,
y `build_kb.py` los fusiona sin tocar nada más.

## Lo que NO son huecos (para que no se busquen en vano)

- **Año personal 2 y 22:** no existen matemáticamente. El año personal sólo
  puede ser 1, 3, 4, 5, 6, 7, 8, 9 u 11. No hay que escribirlos.
- **MAESTRO y PROYECTO:** no eran fórmulas que faltaran. «Encuentro con tu
  maestro» = la 2.ª etapa (posición F) y «Proyecto sentido» = la suma de vocales
  (= número del alma). Ya resueltos.

## Dos decisiones — ya resueltas

1. ✅ **E y F se calculan desde las vibraciones** (decisión de Laura). Es el
   valor por defecto del código (`stage_convention="vibration"`).
   Ver [`pinaculo-formulas.md`](pinaculo-formulas.md) §10.

2. ✅ **H muestra ambas como referencia.** Cuando el destino puede elevarse
   (2→11, 4→22), el bloque de números da `H` y `H_POTENCIAL`, y el reporte
   presenta las dos como las dos caras de un mismo camino, sin elegir por la
   persona. Ver [`pinaculo-formulas.md`](pinaculo-formulas.md) §3.
