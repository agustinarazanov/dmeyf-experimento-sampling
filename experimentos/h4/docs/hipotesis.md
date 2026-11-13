# Hipótesis — h4

Parte de Sampling_1 ([`sampling_1/docs/hipotesis.md`](../../sampling_1/docs/hipotesis.md)). Escrito el 9-nov-2026
(cambio `incorporar-aportes`), antes de cualquier corrida real de sus variantes, y revisado en sesión limpia antes de la
primera. Los cambios posteriores se anotan en `docs/bitacora.md`.

El control, G, Δ, δ, T, A, N* y los veredictos están en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y
no se repiten: se citan. Las réplicas de optimización (réplica k, Ḡ_{v,k}, Δ con réplicas con IC de Welch) y los valores
fijos **δ = 5,52 M$**, **N\* = 3.300** y **R = 8 réplicas** (k = 0…7) son los de
[`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas de optimización; tampoco se repiten ni se
recalculan.

## Pregunta

¿Conviene que la muestra que acelera el pipeline conserve **todas las bajas**? H1 y H3 muestrean filas al azar, así que
la muestra pierde bajas en la misma proporción que CONTINUA. H4 las conserva todas y recorta solo CONTINUA, en la
búsqueda de Optuna o en el modelo final.

## Origen: las variantes salen de mirar 201910

Las cuatro variantes vienen del aporte de Luis María Laguinge (`experimentos/sampling_1/exploratorios/validacion_50_semillas/`, origen en el commit `9e1889e`),
que eligió y descartó estrategias **mirando su ganancia en 201910**: la búsqueda con hard negatives como la de mayor
ganancia (+7,19 M$), la búsqueda con CONTINUA uniforme como descarte (−2,31 M$) y el fast-retrain como la arquitectura
de producción (283,25 M$ contra 276,65 M$ del control a tiempo igual). No sabemos con qué mes fijó el pozo del 35 % ni
el 10 % de CONTINUA; los mantenemos como los dejó.

Por eso **el resultado de H4 no cuenta con un mes de test que no se haya mirado**: 201910 ya influyó en qué se prueba.
Seguimos la consigna (Zulip 208135) y no usamos otro mes. Lo que hacemos para acotar el sesgo:
- las cuatro variantes entran juntas, con predicción y regla escritas acá antes de correr, y ninguna se elige ni se
  descarta por su resultado en 201910;
- los contrastes principales quedan fijados de antemano (§ Comparaciones múltiples);
- el informe de `h4` y el de `sampling_1` listan este origen entre sus limitaciones.

## Variantes

Detalle en [`docs/diseno.md`](diseno.md). Todas con 8 réplicas de optimización y 10 semillas finales.

| variante | búsqueda (Optuna) | final |
|---|---|---|
| `H4H-0.1` | todas las bajas + 10 % de CONTINUA sorteado dentro del pozo de negativos difíciles de la sonda | completo |
| `H4U-0.1` | todas las bajas + 10 % de CONTINUA sorteado entre todas | completo |
| `H4F-0.05` | como `H3-0.05` (estudios `U0.05` / `U0.05@k`) | todas las bajas + 50 % de CONTINUA, peso 2 |
| `H4F-0.25` | como `H3-0.25` (estudios `U0.25` / `U0.25@k`) | todas las bajas + 50 % de CONTINUA, peso 2 |

## H4 — Muestras informadas por clase

- **Variable**: cómo se arma la muestra (búsqueda con todas las bajas y CONTINUA difícil o uniforme; final con todas
  las bajas y la mitad de CONTINUA con peso 2).
- **Métrica que decide**: el veredicto de cada variante con Δ con réplicas contra `C` (reglas comunes, δ = 5,52 M$) y,
  para `H4F-*`, la aceleración A con T como mediana entre las 8 réplicas.
- **Predicción**: conservar todas las bajas en la búsqueda o en el final mantiene la ganancia y acelera.

### Predicciones y reglas

1. **Búsqueda informada** (`H4H-0.1` y `H4U-0.1`).
   - **Predicción**: las dos *no pierden* con réplicas: cota inferior del IC de Welch de Δ con réplicas ≥ −5,52 M$.
   - **Se confirma** si las dos tienen cota inferior del IC de Welch de Δ con réplicas ≥ −5,52 M$.
   - **Se refuta** si alguna sale *pierde*: media de Δ con réplicas < −5,52 M$.
   - **Ninguna de las dos** en otro caso (alguna *indeterminado*: cota inferior < −5,52 M$ y media ≥ −5,52 M$).
2. **Difícil contra uniforme.** D_HU = media_k Ḡ_{`H4H-0.1`,k} − media_k Ḡ_{`H4U-0.1`,k}, con IC 95% de Welch entre las
   8 réplicas de cada una (sin aparear: la réplica k de una y otra no comparten la muestra de búsqueda).
   - **Ayuda** si la cota inferior del IC de D_HU es > 0 M$.
   - **Empeora** si la cota superior del IC de D_HU es < 0 M$.
   - **No cambia** en cualquier otro caso.
   - **Predicción**: *ayuda*, que es lo que reporta Luis.
3. **Fast-retrain** (`H4F-0.05` y `H4F-0.25`). Tres condiciones por variante:
   - (a) *no pierde* con réplicas: cota inferior del IC de Welch de Δ con réplicas ≥ −5,52 M$;
   - (b) acelera más que la H3 de la misma tasa: A(`H4F-0.05`) > A(`H3-0.05`) y A(`H4F-0.25`) > A(`H3-0.25`), con
     A = T(`C`) / T(variante) y cada T como mediana entre sus 8 réplicas;
   - (c) a tiempo igual *gana*: la cota inferior del IC t 95% entre réplicas del tiempo igual (ensamble de K semillas de
     la variante contra la media de `C` en la misma réplica, como lo calcula el reporte de `sampling_1`) es > 0 M$.
   - **Predicción**: las dos cumplen (a), (b) y (c).
   - **Se confirma** para una variante si cumple las tres; **se refuta** si sale *pierde* (media de Δ con réplicas
     < −5,52 M$) o si A no supera a la de su H3; si no, *indeterminado*.

La respuesta de H4 sale de las reglas 1 y 3; la regla 2 explica el mecanismo de la búsqueda y no decide. No hay un
veredicto único que junte las dos: el informe da el de la regla 1 y el de la regla 3 por variante, y la respuesta al
tutor usa los contrastes principales (§ Comparaciones múltiples).

## `H4O-0.5` (cambio `final-con-julio-agosto`, 12-nov-2026)

Escrito antes del tag `corridas-v4` y de cualquier corrida de la variante. Solo existe en la ronda 201903–201908
([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda 201903–201908): 20 semillas finales, N\* = 3.300
y δ = 0,02 · Ḡ_C de los `C` de esa ronda.

**De dónde viene.** El tutor pidió reoptimizar siempre que cambia el dataset (Tschopp, "siempre OP", Zulip 211718).
`H4F-0.05` busca sobre una muestra uniforme del 5 % y entrena con otra receta (todas las bajas + 50 % de CONTINUA con
peso 2), así que no cumple esa indicación. `H4O-0.5` usa la receta del final también para optimizar. La idea viene de
211718, no de mirar 201910: se agrega por la indicación del tutor y entra con su predicción y su regla antes de correr.

- **Variante**: `H4O-0.5`, método `fast-retrain-opt`, 8 réplicas (estudio `F0.5` / `F0.5@k`, k = 0…7).
  - **Búsqueda**: todas las bajas + 50 % de CONTINUA de train 201903–201906, sorteado con la semilla de la réplica, con
    peso 2 en CONTINUA en cada trial. Validación 201908 completa, sin pesos.
  - **Final**: la misma receta sobre 201903–201908 con la semilla final.
  - La tasa 0,5 es la fracción de CONTINUA, no una r de muestra de búsqueda; los hiperparámetros no se reescalan.

### Predicciones y reglas

4. **`H4O-0.5` contra `C`**, con Δ con réplicas (IC de Welch entre las 8 réplicas de cada una).
   - **Predicción**: *no pierde*: cota inferior del IC de Welch de Δ con réplicas ≥ −δ (δ = 0,02 · Ḡ_C de la ronda).
   - **Se confirma** si la cota inferior es ≥ −δ; **se refuta** si sale *pierde* (media de Δ con réplicas < −δ);
     *indeterminado* en otro caso.
5. **Reoptimizar sobre el set del final.** D_OF = media_k Ḡ_{`H4O-0.5`,k} − media_k Ḡ_{`H4F-0.05`,k}, con IC 95% de
   Welch entre las 8 réplicas de cada una (sin aparear: las búsquedas no comparten muestra).
   - **Ayuda** si la cota inferior del IC de D_OF es > 0 M$.
   - **Empeora** si la cota superior del IC de D_OF es < 0 M$.
   - **No cambia** en cualquier otro caso.
   - **Predicción**: *no cambia*. En la ronda anterior `H4F-0.05` ya *no pierde* con réplicas (IC [−0,83; 4,54] M$) y su
     búsqueda sobre el 5 % es de la misma familia que la de `H3`, que tampoco pierde; no esperamos que buscar sobre la
     receta del final mueva la ganancia más que el ruido entre réplicas.
   - Se informa además A(`H4O-0.5`) junto a A(`H4F-0.05`), con T como mediana entre réplicas: buscar sobre más de la mitad
     de las filas cuesta más que sobre el 5 %. A no decide la regla 5; dice cuánto cuesta seguir el "siempre OP".

El contraste `H4O-0.5` contra `H4F-0.05` es un resultado del experimento, no una limitación: el informe de `h4` lo da como
respuesta a 211718. Es secundario (§ Comparaciones múltiples).

## Grilla común (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Escrito el 13-nov-2026, antes de cualquier corrida de estas variantes, y revisado en sesión limpia antes de la primera.
Lo de arriba no se reescribe. Esta sección lleva H4 a la grilla común (`sampling_1/docs/diseno.md` § Grilla común): las
mismas cuatro tasas {0,5; 0,25; 0,1; 0,05} y 8 réplicas en cada forma de muestrear, para que la receta con bajas se pueda
comparar directamente con la muestra al azar de H1 y H3. Ronda 201903–201908
([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda 201903–201908): 20 semillas finales, N\* = 3.300
y δ = 0,02 · Ḡ_C de esa ronda (5,65 M$). Δ con réplicas e IC de Welch como en § `H4O-0.5`; A con una sola referencia y T
como mediana entre réplicas ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Medición de tiempos).

**Origen: se agregan después de ver 201910.** Las variantes nuevas se deciden después de ver en 201910 todas las celdas
vecinas (`H4O-0.5`, `H4U-0.1`, `H3-*`, `U*`). Entran todas juntas, con predicción y regla escritas acá antes de correr, y
ninguna se elige ni se descarta por su resultado. El informe las lista entre las limitaciones ("Ideas que vienen de mirar
el test").

**"Siempre OP" (Zulip 211718).** `H4O-{f}` busca y entrena con la misma receta. `H4P-{f}` busca sobre la receta con bajas
y entrena el final completo: es un apartamiento decidido el 13-nov porque es la hipótesis misma (como H3 y `H4F`), y se
declara con su id en el informe.

### Variantes nuevas

| variante | búsqueda (Optuna) | final | estudio |
|---|---|---|---|
| `H4O-0.25`, `H4O-0.1`, `H4O-0.05` | todas las bajas + f de CONTINUA, peso 1/f | lo mismo, sobre 201903–201908 | `F{f}` / `F{f}@k` |
| `H4P-0.5`, `H4P-0.25`, `H4P-0.1`, `H4P-0.05` | como `H4O-{f}` (comparte su estudio) | completo, sin peso | `F{f}` / `F{f}@k` |

- `H4O-{f}` generaliza `H4O-0.5`: la fracción de CONTINUA pasa a ser la tasa de la variante. Los hiperparámetros no se
  reescalan. `H4F-*` sigue con la mitad de CONTINUA en el final.
- `H4P-{f}` comparte el estudio de `H4O-{f}`, como `H3-{r}` comparte el de `U{r}`; el tiempo del estudio entra en T de
  las dos. La muestra de búsqueda de `H4P-0.1` es la misma que la de `H4U-0.1` (misma función y misma semilla): solo
  cambia el peso.
- La receta con bajas tiene más filas que la muestra al azar de la misma tasa (506.871 filas, 5.312 bajas):

  | tasa | filas al azar | filas con bajas | cociente |
  |---|---|---|---|
  | 0,5 | 253.436 | 256.092 | 1,010 |
  | 0,25 | 126.718 | 130.702 | 1,031 |
  | 0,1 | 50.687 | 55.468 | 1,094 |
  | 0,05 | 25.344 | 30.390 | 1,199 |

### Pares directos

Se declaran en el registro antes de correr. Cada par tiene su IC:
- **Welch, sin aparear** (los lados no comparten estudio): D = media_k Ḡ_{a,k} − media_k Ḡ_{b,k}, IC 95% de Welch entre
  las réplicas de cada lado.
- **t, apareado** (comparten estudio): D = G(a) − G(b) por semilla dentro de cada réplica, media de D por réplica e IC t
  95% entre réplicas (n − 1 g.l.), con el esquema de la regla 4 de [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md).

Una réplica entra en un par solo si tiene las 20 semillas en los dos lados; el par dice con cuántas réplicas se calculó.
Un par al que le falta un lado sale como pendiente, con el nombre de la variante que falta. **Etiquetas**: *mejora* si la
cota inferior del IC de D es > 0 M$, *empeora* si la cota superior es < 0 M$, *no cambia* en otro caso.

| qué aísla | par (a − b) | tasas | IC | qué no aísla |
|---|---|---|---|---|
| conservar las bajas, búsqueda y final (**principal**) | `H4O-{r}` − `U{r}` | 4 | Welch | qué filas quedan, entre 1 y 20 % más filas y el peso 1/f, todo junto |
| conservar las bajas, solo búsqueda | `H4P-{r}` − `H3-{r}` | 4 | Welch | lo mismo, en la búsqueda; el final es completo en los dos lados |
| muestrear también el final, al azar | `U{r}` − `H3-{r}` | 4 | t apareado | nada más: comparten estudio |
| muestrear también el final, con bajas | `H4O-{r}` − `H4P-{r}` | 4 | t apareado | en el final cambian a la vez las filas y el peso |
| el peso en la búsqueda | `H4P-0.1` − `H4U-0.1` | 1 | Welch | nada más: misma muestra de búsqueda, mismo final |

Los pares "conservar las bajas" se comparan a igual tasa de CONTINUA, que es lo que pregunta Zulip 212124, y la tabla
del informe muestra las filas de entrenamiento de cada lado. Los pares entre experimentos (`h4` con `h1` o `h3`, y `h1`
con `h3`) se calculan en `sampling_1`. H2 no entra en los pares (`h2/docs/hipotesis.md` § Réplicas de H2 y `B0.05`).

### Predicciones y reglas

Para los veredictos contra `C` valen las reglas comunes con Δ con réplicas: una predicción *no pierde* se confirma si la
cota inferior del IC es ≥ −δ y se refuta si sale *pierde*; una predicción *pierde* se confirma si la media de Δ es < −δ y
se refuta si sale *no pierde*; *indeterminado* no confirma ni refuta. Para los pares, una predicción se confirma si sale
la etiqueta predicha y se refuta si sale otra.

6. **Conservar las bajas, búsqueda y final** (`H4O-{r}` − `U{r}`, principal).
   - **Predicción**: *no cambia* en 0,5; *mejora* en 0,1 y 0,05, donde la muestra al azar se queda con unas 531 y 266 de
     las 5.312 bajas. En 0,25 no hay predicción firme y se informa.
7. **`H4O-{r}` contra `C`.**
   - **Predicción**: *no pierde* en 0,5 (ya medido, regla 4) y en 0,25; *pierde* en 0,05. En 0,1 se informa sin
     predicción.
8. **`H4P-{r}` contra `C`.**
   - **Predicción**: *no pierde* en las cuatro tasas.
9. **Conservar las bajas, solo búsqueda** (`H4P-{r}` − `H3-{r}`).
   - **Predicción**: *no cambia* en las cuatro tasas.
10. **El peso en la búsqueda** (`H4P-0.1` − `H4U-0.1`).
    - **Predicción**: *mejora*.
    - Si sale *no cambia*, la explicación del informe de H4 (la proporción distorsionada en la búsqueda hace perder a
      `H4U-0.1`) queda sin sostén, y se dice.
11. **Muestrear también el final** (`U{r}` − `H3-{r}` y `H4O-{r}` − `H4P-{r}`): se informan sin predicción.

Cada variante nueva recibe además su A, con su intervalo. A no decide ninguna de las reglas 6 a 11.

## Comparaciones múltiples

Entre `h4` y las extensiones de `h3` (`h3/docs/hipotesis.md` § Extensiones del aporte de Luis) hay más de diez
contrastes, sin corrección por comparaciones múltiples: con un 5 % de error por contraste, alguno puede salir
significativo por azar. El informe lo declara. La respuesta al tutor se apoya solo en los **contrastes principales**,
fijados acá antes de correr:

- `H3-0.1` contra `C`, con réplicas (de `h3-semillas-optuna`);
- `H4H-0.1` contra `C`, con réplicas (regla 1);
- `H4F-0.05` contra `C`, con réplicas y a tiempo igual (regla 3).

El resto de los contrastes se informa como secundario.

*Grilla común (13-nov-2026, cambio `tiempos-confiables-y-consistencia`, antes de correr).* Se suman, sin corrección:
- los **17 contrastes** de los pares directos (§ Grilla común): 4 `H4O-{r}` − `U{r}`, 4 `H4P-{r}` − `H3-{r}`,
  4 `U{r}` − `H3-{r}`, 4 `H4O-{r}` − `H4P-{r}` y `H4P-0.1` − `H4U-0.1`;
- **9 veredictos nuevos** contra `C`, de las variantes nuevas: `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, las cuatro
  `H4P` y `B0.05`;
- los veredictos que **se vuelven a decidir** con réplicas: `U0.5`, `U0.25`, `U0.1`, `U0.05`, `B0.5`, `B0.25`, `B0.1` y
  `GOSS`.

Los contrastes principales de la grilla común son los cuatro `H4O-{r}` − `U{r}`; las conclusiones sobre la grilla se
apoyan en ellos y el resto es secundario. Los tres principales de arriba siguen siéndolo para las variantes de la
ronda anterior.

## Limitaciones previstas

- **Test ya mirado** (§ Origen): las variantes vienen de resultados de Luis en 201910 y no hay otro mes de test.
- **Comparaciones múltiples** sin corrección (§ Comparaciones múltiples).
- `H4F-0.05` y `H4F-0.25` comparten los estudios de `H3-0.05` y `H3-0.25`; su diferencia con ellas es solo el final y
  no son evidencia independiente sobre la búsqueda.
- La sonda que define el pozo de negativos difíciles es parte de `H4H-0.1`: su semilla es la de la réplica, así que su
  suerte entra en el IC, y su tiempo cuenta en T.
- La muestra de búsqueda de `H4H-0.1` y `H4U-0.1` cambia la proporción de clases, así que Optuna ve probabilidades
  descalibradas. El final es completo y G se mide con un corte por cantidad de envíos (N\*), que depende solo del orden;
  en `H4F-*` el peso 2 restituye la proporción ponderada del train.
- **Toca la proporción de clases**, que es el terreno de Sampling_2 (undersampling de la clase mayoritaria). Es la
  excepción declarada a la regla de `sampling_1` (`sampling_1/docs/hipotesis.md` § Pregunta): H4 sigue midiendo
  velocidad, con el final completo (`H4H-0.1`, `H4U-0.1`) o con la proporción ponderada restituida (`H4F-*`), y no
  compara proporciones de clases entre sí.
- *Grilla común (13-nov):* en `H4O-0.05` y `H4P-0.05` el peso de CONTINUA es 20 en la búsqueda (y en el final de
  `H4O-0.05`), con `min_data_in_leaf` sin reescalar. Es parte de la receta y se declara, como en `H4O-0.5`. Los pares
  "conservar las bajas" mezclan qué filas quedan, cuántas y el peso (§ Grilla común).
