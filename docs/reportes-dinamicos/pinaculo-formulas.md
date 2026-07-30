# El Pináculo — especificación de cálculo

**Fuente:** *LIBRO FINAL-LAURA de 26 de JULIO.docx*, capítulos IV–VII, y el
diagrama oficial de fórmulas ([`pinaculo-diagrama-oficial.png`](pinaculo-diagrama-oficial.png),
extraído del propio libro).

Esta es la especificación autoritativa para implementar `app/domain/pinnacle.py`.
Sustituye a lo que se dedujo de la web: el libro tiene **24 posiciones**, no 19.

---

## 1. Las 24 posiciones

### Datos de partida

| Pos. | Nombre | Cálculo |
|---|---|---|
| **A** | Número del Karma — *«¿Quién no pude SER?»* | Mes de nacimiento |
| **B** | Número Personal — *«Mi nuevo YO»* | Día de nacimiento |
| **C** | Número de Vida Pasada — *«¿Quién fui?»* | Año de nacimiento |
| **D** | Número de Personalidad — *«¿Quién pretendo ser?»* | `A + B + C` ⚠️ *ver §3* |

### Ser Superior — realizaciones (triángulo ascendente)

| Pos. | Nombre | Cálculo |
|---|---|---|
| **E** | 1.ª Etapa · Aprendizaje — *«El programa»* | `A + B` |
| **F** | 2.ª Etapa · Aplicación — *«El encuentro con el Maestro»* | `B + C` |
| **G** | 3.ª Etapa · Consolidación — *«El Antídoto»* | `E + F` |
| **H** | 4.ª Etapa · Destino — *«La elevación del Yo»* | `A + C` ⚠️ *ver §3* |
| **I** | Inconsciente Positivo — *el sexto sentido* | `E + F + G` |
| **J** | Número del Espejo — *la pareja* | `H + D` |

### Ser Inferior — desafíos y sombra (triángulo descendente)

| Pos. | Nombre | Cálculo |
|---|---|---|
| **K** | 1.er Desafío — *el contrato heredado del clan* | `A − B` |
| **L** | 2.º Desafío — *confrontación con los mandatos* | `B − C` |
| **M** | 3.er Desafío — *la individuación* | `K − L` |
| **N** | 4.º Desafío — *la realización interna* | `A − C` |
| **O** | Inconsciente Negativo — *frenos invisibles* | `K + L + M` |
| **P** | Número de la Sombra | `D + O` |
| **Q** | Súper Oculto — *«nos la enseñaron papá y mamá»* (lo imperdonable) | `K + M` |
| **R** | Súper Oculto — *«la desarrollamos nosotros»* (lo inconfesable) | `L + M` |
| **S** | Súper Oculto — *«nuestra arma secreta»* (lo impensable) | `Q + R` |

Los desafíos se emparejan con las realizaciones: **E vs K · F vs L · G vs M · H vs N**.

### Posiciones exteriores

| Pos. | Nombre | Cálculo |
|---|---|---|
| **T** | Números Ausentes — *la energía fuera de control* | Escala 1–9 que no aparece en el pináculo · *ver §5* |
| **W** | Número de la Triplicidad — *sombra emocional* | Suma de 3 vibraciones iguales del Ser Inferior · *ver §4* |
| **X** | Número de Reacción — *personalidad energética ante el mundo* | `B + D` |
| **Y** | Número de Síntesis — *confirmación de la Misión de Vida* | `A + B + C + D + X` |
| **Z** | Regalo Divino — *poder espiritual innato* | Suma de los **2 últimos dígitos del año** · *ver §6* |

---

## 2. Reducción

Reducción teosófica hasta un solo dígito, **excepto 11 y 22**, que se conservan
por ser números maestros.

**Números kármicos.** Si en el paso previo a la reducción final aparece 13, 14,
16 o 19, el resultado se marca con asterisco y se anota como deuda kármica:

```
13 → 4*    14 → 5*    16 → 7*    19 → 1*
```

Se sigue operando con el dígito base (4, 5, 7, 1); el asterisco es información
de interpretación, no un valor distinto. **Hay que conservarlo en el modelo de
datos** — alimenta directamente el material de `06-otros-calculos/deudas-karmicas.md`.

---

## 3. Regla de comprobación (sólo D y H)

Se aplica **únicamente si el resultado de D o de H es 2, 4, 11 o 22**. Con
cualquier otra vibración no hace falta.

Consiste en repetir la suma **con los números enteros**, antes de reducirlos a
vibración, y reducir el total:

- **D:** `reduce(mes + día + año)` — p. ej. `10 + 4 + 1979 = 1993 → 22`
- **H:** `reduce(mes + año)` — p. ej. `12 + 1970 = 1982 → 2`

> No es la suma de los dígitos sueltos, sino la suma de los tres números.
> Con los dígitos, el ejemplo de 10/04/1979 daría 4 y el libro dice 22.
> Verificado contra los cuatro ejemplos del capítulo V (`tests/test_pinnacle.py`).

| Caso | Resolución |
|---|---|
| Coinciden | El resultado se confirma. |
| **D** difiere | **Gana la comprobación.** Ese valor se usa en todos los cálculos posteriores. |
| **H** difiere | **No es automático.** Depende del grado de evolución de la persona: en esta posición se puede elevar 2 → 11 o 4 → 22. |

> **Implicación de producto:** H es el único punto del método que no es
> determinista. Lo implementado: se toma la vibración base y la maestra se
> expone como `h_alternative` («potencial de elevación»), en vez de elegir por
> la persona. Es honesto con el método y evita que el PDF afirme algo que Laura
> deja abierto.
>
> ⚠️ **La elección de H se propaga a J** (`J = H + D`), que es el número de
> pareja. Para 16/07/1968: con H = 4 sale J = 6; con H = 22 sale J = 1. No es
> un detalle menor — es el número que sostiene medio reporte de Amor.

---

## 4. Reglas de la zona inferior

1. **Restas en valor absoluto.** No hay negativos: siempre *vibración mayor −
   vibración menor*.
2. **Los números maestros no se restan.** Antes de restar, reducir a la base:
   `11 → 2`, `22 → 4`.
3. **Triplicidad (W).** Si entre `K, L, M, N, O, P, Q, R, S` hay exactamente
   **3 vibraciones iguales**, se suman y se reduce a un dígito. El resultado
   siempre es **3, 6 o 9** — sirve de comprobación:
   - `1+1+1`, `4+4+4`, `7+7+7` → **3** · necesidad de ser visto y escuchado
   - `2+2+2`, `5+5+5`, `8+8+8` → **6** · necesidad de ser amado y cuidado
   - `3+3+3`, `6+6+6`, `9+9+9` → **9** · necesidad de ser reconocido
4. **Con 4 o más vibraciones iguales la regla NO aplica** y **W queda vacía**.
   Es un «Pináculo Especial», de impacto colectivo. Hay que representarlo como
   tal, no como un fallo de cálculo.

---

## 5. Números ausentes (T)

- Sólo se consideran las vibraciones de la **escala básica 1–9**.
- **Los números maestros nunca cuentan como ausencia** (pueden aparecer o no).
- Se buscan en las 3 zonas del pináculo, **excluyendo X, Y y Z**.
- Lo normal es 1–2 ausencias; hay pináculos especiales con hasta 8.

---

## 6. Regalo Divino (Z)

Suma de los **dos últimos dígitos del año**, reducida a un dígito salvo 11 o 22.

```
1968 → 6 + 8 = 14 → 1 + 4 = 4
```

**Excepción:** el 0 no vale como regalo divino. Si la suma da 0, se toma el
dígito siguiente: `1900 → 0 + 9 = 9`.

---

## 7. Etapas de vida — duración

- **1.ª Etapa (E):** de 0 a `36 − D` años.
- **2.ª, 3.ª y 4.ª (F, G, H):** ciclos exactos de **9 años** cada una.

⚠️ **Si D es 11 o 22 se usa la vibración base** (11→2, 22→4):
`D = 11` → `36 − 2 = 34` años, no `36 − 11 = 25`.

> **Bug detectado en el código actual.** `Person._stages_timeline()` calcula
> `first_stage_length = 36 - reduce_number(day + month + year)`, y `reduce_number`
> devuelve 11 o 22 sin reducir. Para alguien con D maestro la primera etapa sale
> 9 o 22 años más corta de lo que dice el libro, y **todas** las etapas
> posteriores se desplazan. Afecta al reporte `reporte-etapa-de-vida-*` que ya
> está en producción.

**Etapas dobles.** Con D maestro se generan dos líneas de tiempo simultáneas
(la maestra y la base). Laura recomienda empezar por la base. Propuesta: calcular
la base y mencionar la doble línea en el texto, sin duplicar la maquetación.

---

## 8. Qué cambia respecto a la propuesta inicial

| | Antes (deducido de la web) | Ahora (libro) |
|---|---|---|
| Posiciones | 19 (A–S) | **24** (A–S + T, W, X, Y, Z) |
| Fórmulas | inferidas | **confirmadas por el diagrama oficial** |
| Kármicos | no contemplados | 13/14/16/19 con asterisco |
| Comprobación D/H | no contemplada | regla explícita |
| Triplicidad | no contemplada | W, con excepción de 4+ |
| Etapas | 7 tramos (port del PHP) | **4 etapas**, 1.ª = 36−D |

### Tres posiciones nuevas que cambian las recetas

**X · Número de Reacción** — el libro dice que involucra «tus comportamientos,
las somatizaciones, tu postura corporal, tu tono de voz, la forma de moverte e
incluso tus posibles enfermedades».

> **Es lo más cercano a una posición de salud que existe en todo el método.**
> Entra directamente en la receta de *Mi energía vital y bienestar*, y reduce el
> hueco de contenido que había detectado. Sigue sin haber material por
> vibración para X, pero el marco conceptual ya existe y es de la autora.

**Y · Número de Síntesis** — «confirmación de tu Misión de Vida». Es
literalmente el tema del reporte de *Propósito y camino de vida*: entra en su
receta como sección propia.

**Z · Regalo Divino** — el don que sostiene en la crisis. Cierre natural de
cualquiera de los cinco reportes; encaja especialmente bien en la última sección
antes del plan de acción.

---

## 9. Estado de la implementación

Implementado en **[`app/domain/pinnacle.py`](../../app/domain/pinnacle.py)**,
con 27 pruebas en **[`tests/test_pinnacle.py`](../../tests/test_pinnacle.py)**:

```bash
py -3 tests/test_pinnacle.py
```

Verificado contra todos los ejemplos resueltos del libro (18/10/1981,
10/04/1979, 23/09/2000, 21/12/1970, 16/07/1968, 1900) y contra la web para
20/11/1991. `Pinnacle.to_numbers()` produce ya el bloque `<numeros>` del prompt,
con los asteriscos kármicos incluidos.

**Erratas del libro detectadas** (el código hace lo aritméticamente correcto):

- Regalo Divino, ejemplo de 1968: el libro escribe «6 + 8 = 14 · 1 + 4 = **4**».
  Son 5.

---

## 10. La única cuestión abierta: E y F

El diagrama dice `E = A + B` y `F = B + C` sobre las **vibraciones reducidas**.
El ejemplo resuelto del capítulo VIII las calcula sobre los **números crudos**:
`E = 07 + 16 = 23 → 5`, `F = 16 + 1968 = 1984 → 22`.

Las dos vías son congruentes módulo 9, así que **coinciden siempre salvo cuando
aflora un maestro**. Para 16/07/1968:

| | vibración (diagrama) | raw (libro) |
|---|---|---|
| E | 5* | 5 |
| **F** | **4\*** | **22** |
| G | 9 | 9 |
| I | 9 | 9 |

Sólo F cambia; G e I vuelven a coincidir aguas abajo. Pero F es la **2.ª Etapa
de Realización**, así que la diferencia se ve en el reporte.

**Implementado como conmutador**, sin dar por resuelta la duda:

```python
Pinnacle.from_date(fecha)                             # diagrama (por defecto)
Pinnacle.from_date(fecha, stage_convention="raw")     # ejemplo del libro
```

`py -3 tests/test_pinnacle.py` imprime al final una tabla comparando las dos
convenciones contra el libro. **Pregunta para Laura:** ¿E y F se calculan desde
las vibraciones o desde los números crudos? Basta con que resuelva un pináculo
con maestro en F para saberlo.

---

## 11. Pendiente de confirmar con Laura

1. **Textos por vibración de X, Y, Z y W.** Las fórmulas están; el significado
   por número no aparece en los capítulos extraídos. Sin ellos, esas posiciones
   se pueden calcular y mostrar en el gráfico, pero el modelo no puede
   interpretarlas (regla de anclaje). Es la segunda petición de autoría, junto
   con las fichas de bienestar.
2. **Elevación de H** (§3): ¿lo dejamos como «potencial» en el texto o hay un
   criterio para elegir?
3. **Pináculos especiales** (4+ vibraciones iguales, o 8 ausencias): ¿reciben
   una nota específica en el reporte o se tratan como cualquier otro?
