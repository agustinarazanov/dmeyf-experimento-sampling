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

## Comparaciones múltiples

Entre `h4` y las extensiones de `h3` (`h3/docs/hipotesis.md` § Extensiones del aporte de Luis) hay más de diez
contrastes, sin corrección por comparaciones múltiples: con un 5 % de error por contraste, alguno puede salir
significativo por azar. El informe lo declara. La respuesta al tutor se apoya solo en los **contrastes principales**,
fijados acá antes de correr:

- `H3-0.1` contra `C`, con réplicas (de `h3-semillas-optuna`);
- `H4H-0.1` contra `C`, con réplicas (regla 1);
- `H4F-0.05` contra `C`, con réplicas y a tiempo igual (regla 3).

El resto de los contrastes se informa como secundario.

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
