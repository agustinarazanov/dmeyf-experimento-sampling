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
mantiene la ganancia y acelera. Cinco variantes, todas con 8 réplicas de optimización (k = 0…7) y 20 semillas finales:

| variante | búsqueda (Optuna) | final |
|---|---|---|
| `H4H-0.1` | todas las bajas + 10 % de CONTINUA sorteado dentro del pozo de negativos difíciles de la sonda | completo |
| `H4U-0.1` | todas las bajas + 10 % de CONTINUA sorteado entre todas | completo |
| `H4F-0.05` | como `H3-0.05` | todas las bajas + 50 % de CONTINUA, peso 2 |
| `H4F-0.25` | como `H3-0.25` | todas las bajas + 50 % de CONTINUA, peso 2 |
| `H4O-0.5` | todas las bajas + 50 % de CONTINUA, peso 2 (la receta del final) | todas las bajas + 50 % de CONTINUA, peso 2 |

Las cuatro primeras vienen del aporte de Luis María Laguinge, que las eligió mirando 201910 (§ Limitaciones). `H4O-0.5`
se agregó en el cambio `final-con-julio-agosto` por el pedido del tutor de reoptimizar siempre que cambia el dataset
("siempre OP", Zulip 211718), no por mirar 201910. Texto completo, predicciones y reglas pre-registradas en
[`docs/hipotesis.md`](../docs/hipotesis.md); variantes, sonda y dependencias en [`docs/diseno.md`](../docs/diseno.md).

### Ronda 201903–201908

Todos los números son de la ronda vigente: el final entrena con 201903–201908 y se evalúa en test (201910) con 20
semillas; Optuna no cambia (train 201903–201906, validación 201908) y los estudios se reusan, salvo `F0.5@k`, nuevo. La
ronda anterior (final 201903–201906, 10 semillas) está en
[`comparacion_rondas.md`](../../sampling_1/informe/comparacion_rondas.md). Los apartamientos del baseline, con su id y su
justificación, están en [`docs/diseno.md`](../docs/diseno.md) y en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Apartamientos del baseline: el veredicto por ganancia
con el AUC al lado (Zulip 208135), la ventana del final (Zulip 211210) y, para `H4F-*`, buscar sobre otra muestra que
la del final (Zulip 211718), que `H4O-0.5` pone a prueba.

## Resultados

8 réplicas × 20 semillas en las cinco variantes. Ḡ_C con réplicas = 281,78 M$; δ = 5,65 M$ y N* = 3.300 quedan fijos.
Filas copiadas de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md) (formato del reporte, punto
decimal), con `H3-0.05` y `H3-0.25` para la regla 3:

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | ΔAUC en 201910 [IC] | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| H4F-0.05 | H4 | 283.19 (R=8) | 4.18 [1.11; 7.25] | 1.41 [-1.58; 4.40] (R=8) | -0.0019 [-0.0041; +0.0003] (R=8) | 80 | 12.50 | 4.63 [0.77; 8.50] (R=8) | 9.29 [1.53; 18.04] | no pierde (con réplicas (8)) |
| H4H-0.1 | H4 | 270.37 (R=8) | -9.19 [-12.06; -6.31] | -11.41 [-15.80; -7.03] (R=8) | -0.0045 [-0.0062; -0.0028] (R=8) | 126 | 7.93 | -5.68 [-10.71; -0.65] (R=8) | -8.72 [-17.99; 0.44] | pierde (con réplicas (8)) |
| H4F-0.25 | H4 | 283.04 (R=8) | 1.04 [-2.02; 4.11] | 1.26 [-1.42; 3.94] (R=8) | -0.0002 [-0.0013; +0.0009] (R=8) | 210 | 4.77 | 4.91 [2.09; 7.73] (R=8) | 2.39 [-4.62; 10.01] | no pierde (con réplicas (8)) |
| H4U-0.1 | H4 | 273.76 (R=8) | -7.70 [-10.81; -4.59] | -8.02 [-11.52; -4.53] (R=8) | -0.0037 [-0.0054; -0.0021] (R=8) | 293 | 3.41 | 3.95 [-1.40; 9.29] (R=8) | 2.91 [-7.54; 14.25] | pierde (con réplicas (8)) |
| H4O-0.5 | H4 | 280.44 (R=8) | -0.71 [-3.83; 2.40] | -1.33 [-4.27; 1.60] (R=8) | +0.0004 [-0.0007; +0.0015] (R=8) | 434 | 2.31 | 4.08 [0.49; 7.67] (R=8) | 4.34 [-3.79; 12.60] | no pierde (con réplicas (8)) |
| H3-0.05 | H3 | 283.86 (R=8) | 5.22 [2.96; 7.49] | 2.08 [-0.87; 5.02] (R=8) | -0.0020 [-0.0041; +0.0000] (R=8) | 95 | 10.56 | 4.77 [1.01; 8.53] (R=8) | 7.74 [0.06; 16.23] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 283.20 (R=8) | 4.73 [2.48; 6.98] | 1.42 [-2.82; 5.67] (R=8) | -0.0009 [-0.0021; +0.0004] (R=8) | 229 | 4.38 | 6.15 [3.95; 8.34] (R=8) | 8.85 [1.87; 16.83] | no pierde (con réplicas (8)) |

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| H4F-0.05 | 8 | 160 | 2.80 | 3.96 | 31 % |
| H4F-0.25 | 8 | 160 | 2.15 | 4.43 | 17 % |
| H4H-0.1 | 8 | 160 | 4.91 | 4.83 | 48 % |
| H4O-0.5 | 8 | 160 | 2.69 | 4.50 | 25 % |
| H4U-0.1 | 8 | 160 | 3.65 | 5.57 | 28 % |

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H4H-0.1 - H4U-0.1 | -3.39 [-8.06; 1.28] | 8 | Welch, sin aparear | no cambia |
| H4O-0.5 - H4F-0.05 | -2.74 [-5.69; 0.21] | 8 | Welch, sin aparear | no cambia |

### Veredictos con las reglas pre-registradas

Las reglas se aplican tal como quedaron escritas en [`docs/hipotesis.md`](../docs/hipotesis.md) § Predicciones y reglas
y § `H4O-0.5`, antes de las corridas, con el δ de la ronda (5,65 M$; las reglas 1 a 3 se escribieron con el de la ronda
anterior, y la regla de δ dice que su valor sale del control de cada ronda).

1. **Búsqueda informada: refutada.** Las dos variantes *pierden* con réplicas: la media de Δ con réplicas queda debajo
   de −5,65 M$ en `H4H-0.1` (−11,41 M$, IC [−15,80; −7,03]) y en `H4U-0.1` (−8,02 M$, IC [−11,52; −4,53]). En esta
   ronda los dos IC enteros quedan debajo de −δ. Optimizar sobre una muestra con todas las bajas y el 10 % de CONTINUA
   rinde peor que optimizar sobre una muestra uniforme del 10 % (`H3-0.1`, Δ con réplicas 1,71 M$). Una explicación
   posible, que no se probó, es que la proporción de clases distorsionada en la búsqueda lleva a hiperparámetros que no
   sirven para el train completo.
2. **Difícil contra uniforme: no cambia.** D_HU = −3,39 M$, IC de Welch [−8,06; 1,28]: la cota inferior no pasa 0 y la
   superior no queda debajo de 0. La predicción (*ayuda*, lo que reportaba Luis) no se cumple; si algo, la media va en
   contra. La regla no decide la respuesta de H4: explica que elegir negativos difíciles no rescata a la búsqueda
   informada.
3. **Fast-retrain.**
   - **`H4F-0.05`: confirmada.** (a) *No pierde*: cota inferior del IC de Welch −1,58 ≥ −5,65 M$. (b) A = 12,50 >
     10,56 de `H3-0.05` (T mediana 80 s contra 95 s). (c) A tiempo igual *gana*: IC t entre réplicas [0,77; 8,50] M$,
     con cota inferior > 0.
   - **`H4F-0.25`: confirmada.** (a) cota inferior −1,42 ≥ −5,65 M$; (b) A = 4,77 > 4,38 de `H3-0.25`; (c) IC t a
     tiempo igual [2,09; 7,73] M$, con cota inferior > 0. En la ronda anterior (c) no se cumplía y quedaba
     *indeterminado*.
4. **`H4O-0.5` contra `C`: confirmada.** *No pierde*: cota inferior del IC de Welch de Δ con réplicas −4,27 ≥ −5,65 M$
   (Δ = −1,33 M$).
5. **Reoptimizar sobre el set del final: no cambia (confirmada).** D_OF = −2,74 M$, IC de Welch [−5,69; 0,21]: contiene
   a 0. Buscar sobre la receta del final, como pide el "siempre OP" (211718), no mejora a buscar sobre el 5 % uniforme; si
   algo, la media va en contra. Y cuesta: A(`H4O-0.5`) = 2,31 contra A(`H4F-0.05`) = 12,50 (T mediana 434 s contra
   80 s). Es la respuesta a 211718 para `H4F`: con los hiperparámetros elegidos sobre una muestra uniforme el final con
   otra receta no pierde nada medible.

La regla 1 da la respuesta de la búsqueda y la 3, la del final; no hay un veredicto único (`docs/hipotesis.md`). Con los
contrastes principales fijados de antemano: `H4H-0.1` contra `C` *pierde*, y `H4F-0.05` contra `C` *no pierde* con
réplicas y *gana* a tiempo igual. Las reglas 4 y 5 son secundarias.

**AUC y ganancia.** El veredicto es el de ganancia (Zulip 208135). En `H4F-0.05` van en direcciones distintas: ΔAUC
−0,0019 con Δ de ganancia 1,41 M$; en `H4O-0.5`, al revés: ΔAUC +0,0004 con Δ de ganancia −1,33 M$. En los dos casos
los IC contienen a 0. En `H4H-0.1` y `H4U-0.1` van juntas: las dos bajan (ΔAUC −0,0045 y −0,0037, IC debajo de 0).

### Lo que no decide

- Δ réplica 0 ya anticipaba la búsqueda informada en esta ronda (−9,19 y −7,70 M$), pero con réplicas baja más:
  −11,41 y −8,02 M$. `H4H-0.1` tiene mucha varianza entre réplicas (48 %, sd 4,91 M$): la sonda y el sorteo dentro del
  pozo suman suerte a la de Optuna.
- `H4U-0.1` tiene la T mediana más alta de las cuatro de Luis (293 s, A = 3,41). A tiempo igual su IC contiene a 0
  ([−1,40; 9,29] M$) aunque pierda con réplicas: el reporte compara el ensamble de las semillas de la variante que entran
  en el tiempo del control contra un modelo del control, y ensamblar suma ganancia por sí solo. Es secundario y no cambia
  la regla 1, que no usa el tiempo igual.
- La diferencia de `H4F-0.05` con `H3-0.05` es solo el final (comparten estudios): Δ con réplicas parecido (1,41 y
  2,08 M$) con un final más barato. La ganancia a tiempo igual sale de ahí: más semillas en el mismo tiempo.

## Limitaciones

Solo lo que no está justificado en el diseño; los apartamientos con id (208135, 211210, 211718) están en § Ronda
201903–201908.

- **Hiperparámetros de cuatro meses en un final de seis**, sin reescalar `min_data_in_leaf`. En `H4F-*` y `H4O-0.5` el
  final además usa la mitad de CONTINUA, así que el número de filas del final cambia en los dos sentidos.
- **Test ya mirado.** Las cuatro variantes de Luis salen de estrategias que eligió o descartó mirando su ganancia en
  201910, y no hay otro mes de test (consigna, Zulip 208135). Entraron todas juntas, con reglas escritas antes de correr,
  y ninguna se eligió ni se descartó acá por 201910; aun así, el resultado de H4 no cuenta con un mes de test que no se
  haya mirado. En este caso el sesgo esperable (a favor de lo que Luis eligió) no se vio: su elegida, la búsqueda
  difícil, *pierde*.
- **Comparaciones múltiples.** Entre `h4` y las extensiones de `h3` hay más de diez contrastes sin corrección: con un
  5 % de error por contraste, alguno puede salir significativo por azar. Las conclusiones se apoyan en los contrastes
  principales (`H3-0.1`, `H4H-0.1`, `H4F-0.05` contra `C`); el resto es secundario. La *ganancia* a tiempo igual de
  `H4F-0.05` es un contraste principal, con cota inferior (0,77 M$) cerca de 0.
- `H4F-0.05` y `H4F-0.25` comparten los estudios de `H3-0.05` y `H3-0.25`: no son evidencia independiente sobre la
  búsqueda.
- La búsqueda de `H4H-0.1`, `H4U-0.1` y `H4O-0.5` cambia la proporción de clases, terreno de Sampling_2; es la excepción
  declarada en `docs/hipotesis.md`. El final de `H4F-*` y `H4O-0.5` también la cambia, con el peso 2 restituyendo la
  proporción ponderada.
- Los tiempos vienen de VMs `n2-highmem-8` distintas; T es la mediana entre réplicas y no se compara entre rondas. Un
  solo año (2019) y un solo mes de test (201910); el bootstrap de clientes (tabla de arriba) muestra que el ruido del mes
  de test es mayor que el de las réplicas.

## Conclusión

Conservar todas las bajas **en la búsqueda** no sirve: `H4H-0.1` y `H4U-0.1` pierden contra el control con réplicas, y
elegir los negativos difíciles no cambia nada contra elegirlos al azar. Conservarlas **en el final** sí: `H4F-0.05`
(búsqueda sobre el 5 % uniforme, final con todas las bajas y la mitad de CONTINUA con peso 2) no pierde, acelera 12,50
veces y gana a tiempo igual; con el final de seis meses `H4F-0.25` también cumple las tres condiciones. Reoptimizar
sobre la receta del final (`H4O-0.5`, el "siempre OP" del tutor) no pierde contra el control, pero no mejora a
`H4F-0.05` y es más de 5 veces más lento (T mediana 434 s contra 80 s). Lo que Luis reportaba como ganador (la búsqueda difícil) es lo que pierde; su
arquitectura de producción (fast-retrain) es la que se sostiene.
