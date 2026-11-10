# Informe — H4: muestras informadas por clase

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md); las réplicas, Ḡ_{v,k} y Δ con réplicas, en
[`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas. Los números salen de `ledger/replicas.csv`,
`control/ledger/replicas.csv` y [`sampling_1/informe/tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md);
las figuras, de [`reporte.html`](reporte.html).
`python -m scripts.verificar_informe_h3 --informe experimentos/h4/informe/informe.md` comprueba que cada número de este
informe sale de esas fuentes.

## Hipótesis

H4: conservar **todas las bajas** en la muestra que acelera el pipeline (en la búsqueda de Optuna o en el modelo final)
mantiene la ganancia y acelera. Cuatro variantes, todas con 8 réplicas de optimización (k = 0…7) y 10 semillas finales:

| variante | búsqueda (Optuna) | final |
|---|---|---|
| `H4H-0.1` | todas las bajas + 10 % de CONTINUA sorteado dentro del pozo de negativos difíciles de la sonda | completo |
| `H4U-0.1` | todas las bajas + 10 % de CONTINUA sorteado entre todas | completo |
| `H4F-0.05` | como `H3-0.05` | todas las bajas + 50 % de CONTINUA, peso 2 |
| `H4F-0.25` | como `H3-0.25` | todas las bajas + 50 % de CONTINUA, peso 2 |

Las variantes vienen del aporte de Luis María Laguinge, que las eligió mirando 201910 (§ Limitaciones). Texto completo,
predicciones y reglas pre-registradas en [`docs/hipotesis.md`](../docs/hipotesis.md); variantes, sonda y dependencias
en [`docs/diseno.md`](../docs/diseno.md).

## Resultados

8 réplicas × 10 semillas en las cuatro variantes. Ḡ_C con réplicas = 275,92 M$; δ = 5,52 M$ y N* = 3.300 quedan fijos.
Filas copiadas de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md) (formato del reporte, punto
decimal), con `H3-0.05` y `H3-0.25` para la regla 3:

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|
| H4F-0.05 | H4 | 277.78 (R=8) | 4.40 [-0.07; 8.87] | 1.86 [-0.83; 4.54] (R=8) | 74 | 13.17 | 3.89 [0.35; 7.43] (R=8) | 7.18 [-1.33; 17.27] | no pierde (con réplicas (8)) |
| H4H-0.1 | H4 | 267.31 (R=8) | -3.30 [-7.38; 0.78] | -8.61 [-12.78; -4.43] (R=8) | 117 | 8.35 | -4.63 [-8.07; -1.20] (R=8) | -4.12 [-13.09; 4.95] | pierde (con réplicas (8)) |
| H4F-0.25 | H4 | 277.31 (R=8) | 3.52 [-1.66; 8.70] | 1.39 [-1.87; 4.65] (R=8) | 204 | 4.81 | 3.07 [-0.09; 6.23] (R=8) | 5.73 [-2.86; 14.96] | no pierde (con réplicas (8)) |
| H4U-0.1 | H4 | 270.38 (R=8) | -2.42 [-7.11; 2.27] | -5.54 [-8.94; -2.14] (R=8) | 275 | 3.56 | 3.34 [0.77; 5.91] (R=8) | 2.72 [-7.70; 13.21] | pierde (con réplicas (8)) |
| H3-0.05 | H3 | 277.79 (R=8) | 3.74 [1.77; 5.71] | 1.87 [-1.02; 4.76] (R=8) | 83 | 11.82 | 1.97 [-2.83; 6.76] (R=8) | 2.75 [-5.17; 12.54] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 277.74 (R=8) | 4.18 [-0.60; 8.96] | 1.81 [-1.78; 5.41] (R=8) | 216 | 4.53 | 1.83 [-1.91; 5.57] (R=8) | 3.46 [-4.29; 11.77] | no pierde (con réplicas (8)) |

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| H4F-0.05 | 8 | 80 | 2.48 | 4.02 | 25 % |
| H4F-0.25 | 8 | 80 | 3.43 | 4.58 | 34 % |
| H4H-0.1 | 8 | 80 | 4.71 | 4.70 | 49 % |
| H4U-0.1 | 8 | 80 | 3.64 | 4.91 | 34 % |

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H4H-0.1 - H4U-0.1 | -3.07 [-7.61; 1.47] | 8 | Welch, sin aparear | no cambia |

### Veredictos con las reglas pre-registradas

Las reglas se aplican tal como quedaron escritas en [`docs/hipotesis.md`](../docs/hipotesis.md) § Predicciones y reglas,
antes de las corridas.

1. **Búsqueda informada: refutada.** Las dos variantes *pierden* con réplicas: la media de Δ con réplicas queda debajo
   de −5,52 M$ en `H4H-0.1` (−8,61 M$, IC [−12,78; −4,43]) y en `H4U-0.1` (−5,54 M$, IC [−8,94; −2,14]). En
   `H4U-0.1` la media queda apenas debajo del umbral, pero la regla no tiene margen: es *pierde*. Optimizar sobre una
   muestra con todas las bajas y el 10 % de CONTINUA rinde peor que optimizar sobre una muestra uniforme del 10 %
   (`H3-0.1`, Δ con réplicas 2,30 M$). Una explicación posible, que no se probó, es que la proporción de clases
   distorsionada en la búsqueda lleva a hiperparámetros que no sirven para el train completo.
2. **Difícil contra uniforme: no cambia.** D_HU = −3,07 M$, IC de Welch [−7,61; 1,47]: la cota inferior no pasa 0 y la
   superior no queda debajo de 0. La predicción (*ayuda*, lo que reportaba Luis) no se cumple; si algo, la media va en
   contra. La regla no decide la respuesta de H4: explica que elegir negativos difíciles no rescata a la búsqueda
   informada.
3. **Fast-retrain.**
   - **`H4F-0.05`: confirmada.** (a) *No pierde*: cota inferior del IC de Welch −0,83 ≥ −5,52 M$. (b) A = 13,17 >
     11,82 de `H3-0.05` (T mediana 74 s contra 83 s). (c) A tiempo igual *gana*: IC t entre réplicas [0,35; 7,43] M$,
     con cota inferior > 0.
   - **`H4F-0.25`: indeterminado.** Cumple (a), cota inferior −1,87 ≥ −5,52 M$, y (b), A = 4,81 > 4,53 de `H3-0.25`.
     No cumple (c): el IC t a tiempo igual es [−0,09; 6,23] M$, con cota inferior apenas debajo de 0. No *pierde* y A
     supera a la de su H3, así que tampoco se refuta.

La regla 1 da la respuesta de la búsqueda y la 3, la del final; no hay un veredicto único (`docs/hipotesis.md`). Con los
contrastes principales fijados de antemano: `H4H-0.1` contra `C` *pierde*, y `H4F-0.05` contra `C` *no pierde* con
réplicas y *gana* a tiempo igual.

### Lo que no decide

- Δ réplica 0 no anticipaba el resultado: con una sola réplica, `H4H-0.1` y `H4U-0.1` salían con medias de −3,30 y
  −2,42 M$; con 8 réplicas bajan a −8,61 y −5,54 M$. `H4H-0.1` es la variante con más varianza entre réplicas (49 %,
  sd 4,71 M$): la sonda y el sorteo dentro del pozo suman suerte a la de Optuna.
- `H4U-0.1` tiene la T mediana más alta del grupo (275 s, A = 3,56): la búsqueda de `NU0.1` fue la más variable de la
  tanda (`docs/bitacora.md`, 4.3). A tiempo igual sale positivo ([0,77; 5,91] M$) aunque pierda con réplicas: el
  reporte compara el ensamble de las semillas de la variante que entran en el tiempo del control (hasta 10) contra un
  modelo del control, y ensamblar suma ganancia por sí solo. Es secundario y no cambia la regla 1, que no usa el
  tiempo igual.
- La diferencia de `H4F-0.05` con `H3-0.05` es solo el final (comparten estudios): Δ con réplicas casi igual (1,86 y
  1,87 M$) con un final más barato. La ganancia a tiempo igual sale de ahí: más semillas en el mismo tiempo.

## Limitaciones

- **Test ya mirado.** Las cuatro variantes salen de estrategias que Luis eligió o descartó mirando su ganancia en 201910,
  y no hay otro mes de test (consigna, Zulip 208135). Entraron todas juntas, con reglas escritas antes de correr, y
  ninguna se eligió ni se descartó acá por 201910; aun así, el resultado de H4 no cuenta con un mes de test que no se
  haya mirado. En este caso el sesgo esperable (a favor de lo que Luis eligió) no se vio: su elegida, la búsqueda
  difícil, *pierde*.
- **Comparaciones múltiples.** Entre `h4` y las extensiones de `h3` hay más de diez contrastes sin corrección: con un
  5 % de error por contraste, alguno puede salir significativo por azar. Las conclusiones se apoyan en los contrastes
  principales (`H3-0.1`, `H4H-0.1`, `H4F-0.05` contra `C`); el resto es secundario. La *ganancia* a tiempo igual de
  `H4F-0.05` es un contraste principal, pero su cota inferior (0,35 M$) está cerca de 0.
- `H4F-0.05` y `H4F-0.25` comparten los estudios de `H3-0.05` y `H3-0.25`: no son evidencia independiente sobre la
  búsqueda.
- La búsqueda de `H4H-0.1` y `H4U-0.1` cambia la proporción de clases, terreno de Sampling_2; es la excepción declarada
  en `docs/hipotesis.md`. El final de `H4F-*` también la cambia, con el peso 2 restituyendo la proporción ponderada.
- Los tiempos vienen de VMs `n2-highmem-8` distintas; T es la mediana entre réplicas. Un solo año (2019) y un solo mes
  de test (201910); el bootstrap de clientes (tabla de arriba) muestra que el ruido del mes de test es mayor que el de
  las réplicas.

## Conclusión

Conservar todas las bajas **en la búsqueda** no sirve: `H4H-0.1` y `H4U-0.1` pierden contra el control con réplicas, y
elegir los negativos difíciles no cambia nada contra elegirlos al azar. Conservarlas **en el final** sí: `H4F-0.05`
(búsqueda sobre el 5 % uniforme, final con todas las bajas y la mitad de CONTINUA con peso 2) no pierde, acelera
13,17 veces y gana a tiempo igual; `H4F-0.25` no pierde y acelera más que su H3, pero a tiempo igual queda
indeterminado. Lo que Luis reportaba como ganador (la búsqueda difícil) es lo que pierde; su arquitectura de producción
(fast-retrain) es la que se sostiene.
