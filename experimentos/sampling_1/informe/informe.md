# Informe — Sampling_1: velocidad contra ganancia

Comisión lunes: Agustina Razanov, Martín López, Luis María Laguinge. Tutor: Joaquín I. Aramendía. Los bloques A y B de
§ Resultados se copian de [`tabla_resultados.md`](tabla_resultados.md), que genera
`python -m comun.reporte --experimento sampling_1` desde los ledgers (`apareado.csv` y `replicas.csv` de `control`, `h1`,
`h2`, `h3` y `h4`; `ledger/apareado_previo.csv` es la copia anterior a la separación, que cita por línea
`informe/decisiones.md`); la tabla de rondas, de [`comparacion_rondas.md`](comparacion_rondas.md), que genera
`python scripts/comparar_rondas.py`. Las figuras están en `informe/reporte.html` e `informe/figuras/`. El informe de cada
hipótesis está en [`h1`](../../h1/informe/informe.md), [`h2`](../../h2/informe/informe.md),
[`h3`](../../h3/informe/informe.md) y [`h4`](../../h4/informe/informe.md); acá va la comparación y lo que es común.

## Hipótesis

Pregunta del tutor (Zulip 208986): ¿vale la pena el tradeoff entre velocidad y pérdida de performance? Sobre el baseline
de Bolaños (208135) medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 con menos filas, sin cambiar la
proporción de clases (eso lo estudia Sampling_2).

- **H1**: submuestrear el train al azar (r = 0,5 a 0,05) no pierde con r ≥ 0,25 y pierde con r = 0,05.
- **H2**: muestrear dentro de LightGBM (`bagging_fraction` fijo en 0,5, 0,25 o 0,1) no pierde ni con 0,1.
- **H3**: optimizar con Optuna sobre una muestra (r_opt = 0,25 o 0,1) y entrenar el final con todo no pierde.
- **H3 con réplicas** (cambio `h3-semillas-optuna`, pre-registrado el 8-nov): con 8 réplicas de la optimización, H3
  sigue sin perder; además se prueba si la ventaja viene de que la muestra regulariza (A) o de que el control tuvo mala
  suerte (B), una tasa más chica (`H3-0.05`) y el reescalado de `min_data_in_leaf` (`H3R-0.1`). Reglas en
  [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas.
- **H4** (cambio `incorporar-aportes`, pre-registrado el 9-nov): conservar **todas las bajas** en la muestra que acelera
  (en la búsqueda de Optuna o en el modelo final) mantiene la ganancia y acelera. Búsqueda con todas las bajas y el 10 %
  de CONTINUA, difícil (`H4H-0.1`) o uniforme (`H4U-0.1`), con final completo; y búsqueda como `H3-0.05` o `H3-0.25` con
  final sobre todas las bajas y la mitad de CONTINUA con peso 2 (fast-retrain, `H4F-0.05` y `H4F-0.25`). Con el cambio
  `final-con-julio-agosto` (pre-registrado el 12-nov) se suma `H4O-0.5`, que optimiza sobre la misma receta del final,
  por el "siempre OP" del tutor (Zulip 211718). Reglas en [`h4/docs/hipotesis.md`](../../h4/docs/hipotesis.md).
- **Extensiones de H3** (`incorporar-aportes`): reescalado √(1/r) en r = 0,25 (`H3R-0.25`), reescalado lineal 1/r
  (`H3L-0.25`, `H3L-0.1`) y búsqueda sobre el 10 % de los clientes (`H3K-0.1`). Reglas en
  [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § Extensiones del aporte de Luis.
- H4 (salvo `H4O-0.5`) y las extensiones vienen del aporte de Luis, que eligió y descartó estrategias **mirando 201910**:
  lo declaran sus hipótesis y va en § Limitaciones. Los **contrastes principales**, fijados antes de correr, son `H3-0.1`,
  `H4H-0.1` y `H4F-0.05` contra el control; el resto es secundario.
- **Ronda 201903–201908** (cambio `final-con-julio-agosto`): predicción escrita antes de correr en
  [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Predicción y regla de la ronda: ningún veredicto cambia
  de lado, el IC por semilla se angosta del orden de √2 y el de réplicas menos.
- Una variante **vale la pena** si no pierde y además es al menos 2 veces más rápida (A ≥ 2).

## Diseño

Diez variantes contra el control, cada una con su Optuna (40 trials, train 201903–201906, AUC en validación, 201908; H3
reusa los estudios de U0.25 y U0.1). Decide la ganancia en test (201910) al corte N* = 3.300 envíos. Δ es la diferencia
contra el control apareada por semilla final, con IC 95% t. Con δ = 2% de la ganancia del control: *no pierde* si la cota
inferior del IC es ≥ −δ, *pierde* si la media es < −δ, *indeterminado* en el resto. T es el tiempo de la optimización más
un modelo final, medido en `n2-highmem-8`. Las fases 1 a 4 corrieron la réplica 0 de cada variante.

La fase 5 suma réplicas de la optimización: en la réplica k = 1…7 la semilla de TPE y la del sorteo de la muestra valen k
(la réplica 0 es la de las fases 1–4). `C`, `H3-0.25`, `H3-0.1`, `H3-0.05` y `H3R-0.1` quedan con 8 réplicas. En esas
variantes Δ con réplicas es la diferencia de las medias entre réplicas con IC de Welch, y su veredicto reemplaza al de la
réplica 0. La fase 6 (`incorporar-aportes`) suma las ocho variantes de H4 y de las extensiones de H3, todas con 8
réplicas, y los estudios `K0.1`, `NH0.1` y `NU0.1` (la sonda de `NH0.1` cuenta en T). En las mismas VMs se replicaron
los aportes de Martín y de Luis (bloque B). Diferencias entre variantes: apareadas por réplica y semilla si comparten
estudios (IC t entre réplicas) y con IC de Welch entre réplicas si no. Detalle en
[`h3/docs/diseno.md`](../../h3/docs/diseno.md) y [`h4/docs/diseno.md`](../../h4/docs/diseno.md).

La fase 7 (`final-con-julio-agosto`, tag `corridas-v4`) es la **ronda vigente**: todos los finales se vuelven a correr
entrenando con 201903–201908 y con 20 semillas (las 10 oficiales y 10 más, en el orden de
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda 201903–201908), sin tocar estudios ni
hiperparámetros, más los 8 estudios `F0.5@k` de `H4O-0.5`: 121 celdas × 20 semillas = 2.420 finales, en 8 VMs (dos tandas de 4). N* queda
fijo en 3.300 (el de la ronda anterior, de validación: los finales nuevos ya vieron 201908) y δ sale de los `C` de la
ronda. La ronda anterior (final 201903–201906, 10 semillas) se sigue pudiendo consolidar y se compara en § Tabla de
rondas. Horas y costo en [`docs/diseno.md`](../docs/diseno.md) y en la bitácora.

**Apartamientos del baseline**, cada uno con su id y su justificación (detalle en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Apartamientos del baseline y en el `docs/diseno.md` de
cada hipótesis):

| apartamiento | id | justificación |
|---|---|---|
| El veredicto sale de la ganancia y no del AUC; ΔAUC en test va al lado en todas las tablas. | Zulip 208135 | La regla se escribió en pesos antes de la primera corrida; un umbral de AUC sería una regla nueva escrita después de ver los AUC. Optuna sí elige por AUC en validación. |
| El final entrena con 201903–201908 (seis meses). | Zulip 211210 | Bolaños confirmó que para el test se reentrena incluyendo 07 y 08. |
| `H3` y `H4F-*` no reoptimizan sobre el set del final. | Zulip 211718 | En `H3` optimizar sobre una muestra y entrenar con todo *es* la hipótesis; para `H4F` se agregó `H4O-0.5`, que sí reoptimiza, como contraste. |

## Resultados

Las cifras de los bloques están en el formato del reporte (punto decimal).

Final entrenado con 201903-201908, 20 semillas por réplica; N* = 3,300 envíos; Ḡ_C (réplica 0) = 282.48 M$; Ḡ_C con réplicas = 281.78 M$ (R=8); ensamble de 20 semillas del control = 286.55 M$.

## Bloque A: mismo protocolo

Ḡ, T y A salen de la réplica 0 en las variantes sin réplicas; en las marcadas (R=n), Ḡ es la media entre réplicas, T la mediana entre réplicas y A = T_C / T con T_C también mediana entre réplicas, así que se comparan con Ḡ_C con réplicas y no con Ḡ_C de la réplica 0.

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | ΔAUC en 201910 [IC] | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| U0.05 | H1 | 252.34 | -30.14 [-34.56; -25.72] | — | -0.0176 [-0.0186; -0.0166] (réplica 0) | 70 | 11.45 | sin réplicas | -13.72 [-26.90; -0.92] | pierde (réplica 0) |
| U0.1 | H1 | 266.20 | -16.28 [-19.83; -12.73] | — | -0.0103 [-0.0111; -0.0095] (réplica 0) | 81 | 9.89 | sin réplicas | -5.82 [-15.73; 3.85] | pierde (réplica 0) |
| U0.25 | H1 | 272.91 | -9.57 [-12.65; -6.49] | — | -0.0055 [-0.0060; -0.0050] (réplica 0) | 164 | 4.87 | sin réplicas | -0.52 [-8.86; 7.54] | pierde (réplica 0) |
| U0.5 | H1 | 281.11 | -1.38 [-3.99; 1.24] | — | -0.0019 [-0.0023; -0.0015] (réplica 0) | 354 | 2.25 | sin réplicas | 5.98 [-1.71; 13.53] | no pierde (réplica 0) |
| B0.1 | H2 | 274.01 | -8.47 [-11.02; -5.92] | — | -0.0088 [-0.0094; -0.0083] (réplica 0) | 434 | 1.84 | sin réplicas | -2.34 [-11.66; 6.44] | pierde (réplica 0) |
| B0.25 | H2 | 283.36 | 0.88 [-1.95; 3.71] | — | -0.0044 [-0.0047; -0.0041] (réplica 0) | 650 | 1.23 | sin réplicas | 3.72 [-6.00; 13.31] | no pierde (réplica 0) |
| B0.5 | H2 | 281.55 | -0.94 [-3.62; 1.75] | — | -0.0012 [-0.0017; -0.0008] (réplica 0) | 1,011 | 0.79 | sin réplicas | no aplica (K<2) | no pierde (réplica 0) |
| GOSS | H2 | 278.46 | -4.01 [-7.03; -1.00] | — | +0.0005 [+0.0003; +0.0008] (réplica 0) | 1,102 | 0.72 | sin réplicas | no aplica (K<2) | indeterminado (réplica 0) |
| H3-0.05 | H3 | 283.86 (R=8) | 5.22 [2.96; 7.49] | 2.08 [-0.87; 5.02] (R=8) | -0.0020 [-0.0041; +0.0000] (R=8) | 95 | 10.56 | 4.77 [1.01; 8.53] (R=8) | 7.74 [0.06; 16.23] | no pierde (con réplicas (8)) |
| H3K-0.1 | H3 | 281.57 (R=8) | 0.44 [-1.91; 2.79] | -0.21 [-5.05; 4.63] (R=8) | -0.0033 [-0.0050; -0.0017] (R=8) | 126 | 7.98 | 3.95 [-1.58; 9.47] (R=8) | 4.24 [-6.33; 15.40] | no pierde (con réplicas (8)) |
| H3-0.1 | H3 | 283.49 (R=8) | 1.26 [-1.95; 4.48] | 1.71 [-1.07; 4.49] (R=8) | -0.0017 [-0.0030; -0.0003] (R=8) | 129 | 7.76 | 5.46 [2.93; 7.98] (R=8) | 6.04 [-2.37; 15.30] | no pierde (con réplicas (8)) |
| H3L-0.1 | H3 | 281.92 (R=8) | -1.43 [-4.02; 1.16] | 0.14 [-3.30; 3.57] (R=8) | -0.0005 [-0.0020; +0.0010] (R=8) | 130 | 7.73 | 2.98 [0.05; 5.92] (R=8) | 1.76 [-7.26; 10.72] | no pierde (con réplicas (8)) |
| H3R-0.1 | H3 | 283.37 (R=8) | 0.82 [-1.79; 3.44] | 1.59 [-1.80; 4.98] (R=8) | -0.0008 [-0.0023; +0.0006] (R=8) | 130 | 7.71 | 5.87 [4.27; 7.47] (R=8) | 5.06 [-2.15; 13.31] | no pierde (con réplicas (8)) |
| H3L-0.25 | H3 | 283.00 (R=8) | 1.32 [-1.36; 4.00] | 1.22 [-1.59; 4.03] (R=8) | +0.0004 [-0.0008; +0.0016] (R=8) | 222 | 4.51 | 5.46 [0.83; 10.08] (R=8) | 9.00 [2.14; 16.83] | no pierde (con réplicas (8)) |
| H3R-0.25 | H3 | 283.72 (R=8) | 2.04 [-0.81; 4.88] | 1.95 [-0.85; 4.74] (R=8) | +0.0000 [-0.0011; +0.0011] (R=8) | 225 | 4.46 | 5.32 [2.93; 7.71] (R=8) | 6.65 [-0.28; 14.19] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 283.20 (R=8) | 4.73 [2.48; 6.98] | 1.42 [-2.82; 5.67] (R=8) | -0.0009 [-0.0021; +0.0004] (R=8) | 229 | 4.38 | 6.15 [3.95; 8.34] (R=8) | 8.85 [1.87; 16.83] | no pierde (con réplicas (8)) |
| H4F-0.05 | H4 | 283.19 (R=8) | 4.18 [1.11; 7.25] | 1.41 [-1.58; 4.40] (R=8) | -0.0019 [-0.0041; +0.0003] (R=8) | 80 | 12.50 | 4.63 [0.77; 8.50] (R=8) | 9.29 [1.53; 18.04] | no pierde (con réplicas (8)) |
| H4H-0.1 | H4 | 270.37 (R=8) | -9.19 [-12.06; -6.31] | -11.41 [-15.80; -7.03] (R=8) | -0.0045 [-0.0062; -0.0028] (R=8) | 126 | 7.93 | -5.68 [-10.71; -0.65] (R=8) | -8.72 [-17.99; 0.44] | pierde (con réplicas (8)) |
| H4F-0.25 | H4 | 283.04 (R=8) | 1.04 [-2.02; 4.11] | 1.26 [-1.42; 3.94] (R=8) | -0.0002 [-0.0013; +0.0009] (R=8) | 210 | 4.77 | 4.91 [2.09; 7.73] (R=8) | 2.39 [-4.62; 10.01] | no pierde (con réplicas (8)) |
| H4U-0.1 | H4 | 273.76 (R=8) | -7.70 [-10.81; -4.59] | -8.02 [-11.52; -4.53] (R=8) | -0.0037 [-0.0054; -0.0021] (R=8) | 293 | 3.41 | 3.95 [-1.40; 9.29] (R=8) | 2.91 [-7.54; 14.25] | pierde (con réplicas (8)) |
| H4O-0.5 | H4 | 280.44 (R=8) | -0.71 [-3.83; 2.40] | -1.33 [-4.27; 1.60] (R=8) | +0.0004 [-0.0007; +0.0015] (R=8) | 434 | 2.31 | 4.08 [0.49; 7.67] (R=8) | 4.34 [-3.79; 12.60] | no pierde (con réplicas (8)) |

Notas:

- `U0.05`: sin réplicas
- `U0.1`: sin réplicas
- `U0.25`: sin réplicas
- `U0.5`: sin réplicas
- `B0.1`: sin réplicas
- `B0.25`: sin réplicas
- `B0.5`: sin réplicas
- `GOSS`: sin réplicas

### Varianza entre réplicas y entre semillas

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| C | 8 | 160 | 2.78 | 4.53 | 25 % |
| H3-0.05 | 8 | 160 | 2.71 | 3.75 | 32 % |
| H3-0.1 | 8 | 160 | 2.38 | 3.94 | 24 % |
| H3-0.25 | 8 | 160 | 4.72 | 4.45 | 50 % |
| H3K-0.1 | 8 | 160 | 5.51 | 4.31 | 58 % |
| H3L-0.1 | 8 | 160 | 3.55 | 3.58 | 47 % |
| H3L-0.25 | 8 | 160 | 2.45 | 3.90 | 26 % |
| H3R-0.1 | 8 | 160 | 3.48 | 3.57 | 46 % |
| H3R-0.25 | 8 | 160 | 2.41 | 3.68 | 28 % |
| H4F-0.05 | 8 | 160 | 2.80 | 3.96 | 31 % |
| H4F-0.25 | 8 | 160 | 2.15 | 4.43 | 17 % |
| H4H-0.1 | 8 | 160 | 4.91 | 4.83 | 48 % |
| H4O-0.5 | 8 | 160 | 2.69 | 4.50 | 25 % |
| H4U-0.1 | 8 | 160 | 3.65 | 5.57 | 28 % |

### Diferencias entre variantes

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.12 [-1.95; 1.71] | 8 | t, apareado | no cambia |
| H3R-0.25 - H3L-0.25 | 0.72 [-0.90; 2.35] | 8 | t, apareado | no cambia |
| H3R-0.1 - H3L-0.1 | 1.45 [0.65; 2.25] | 8 | t, apareado | mejora |
| H3R-0.25 - H3-0.25 | 0.52 [-1.59; 2.64] | 8 | t, apareado | no cambia |
| H3K-0.1 - H3-0.1 | -1.93 [-6.68; 2.83] | 8 | Welch, sin aparear | no cambia |
| H4H-0.1 - H4U-0.1 | -3.39 [-8.06; 1.28] | 8 | Welch, sin aparear | no cambia |
| H4O-0.5 - H4F-0.05 | -2.74 [-5.69; 0.21] | 8 | Welch, sin aparear | no cambia |

### Lectura del bloque A

Las variantes `U*`, `B*` y `GOSS` no tienen réplicas (pierden o no aceleran, y las réplicas no cambian eso).
Figuras: tiempo contra ganancia con el rango entre réplicas y descomposición de la varianza en
[`reporte.html`](reporte.html); bandas de curvas por hipótesis en `figuras/bandas_H1.png`, `bandas_H2.png` y
`bandas_H3.png`.

- **H1, ninguna de las dos** ([`h1`](../../h1/informe/informe.md)): U0.5 *no pierde* y U0.25 ya *pierde*; la frontera
  observada es r = 0,5. La pérdida crece a medida que baja r.
- **H2, refutada** ([`h2`](../../h2/informe/informe.md)): con f = 0,1 pierde y con 0,5 y 0,25 casi no acelera
  (A ≤ 1,23). GOSS es descriptivo y queda *indeterminado*.
- **H3, confirmada también con réplicas** ([`h3`](../../h3/informe/informe.md)): `H3-0.1` y `H3-0.25` no pierden con
  réplicas (cotas inferiores −1,07 y −2,82 M$, contra −δ = −5,65 M$) y aceleran 7,76 y 4,38 veces. La réplica 0 sola
  movía Δ en los dos sentidos: de 4,73 a 1,42 M$ con réplicas en `H3-0.25`, de 1,26 a 1,71 M$ en `H3-0.1`.
- **Mecanismo: sin resolver.** El IC de Δ con réplicas de `H3-0.1` contiene a 0, pero la réplica 0 de `C` (282,48 M$)
  queda arriba de la mediana de sus 8 réplicas (282,40 M$), así que la regla no da (B); tampoco (A), porque H3 no
  *gana*. En la ronda anterior daba (B) por poco. No hay evidencia de que la muestra regularice.
- **`H3-0.05`, confirmada**: no pierde con réplicas y A = 10,56 (≥ 8). En la réplica 0 sale *gana*; con réplicas no.
- **`H3R-0.1`, no cambia**: reescalar `min_data_in_leaf` × √10 da −0,12 M$ [−1,95; 1,71] contra `H3-0.1`.
- **Extensiones de H3** (secundarias; [`h3`](../../h3/informe/informe.md) § Extensiones): las cuatro no pierden contra
  el control. La raíz no mejora a no reescalar tampoco en r = 0,25 (0,52 M$ [−1,59; 2,64]); le gana a la lineal en
  r = 0,1 (1,45 M$ [0,65; 2,25]) y no en r = 0,25 (0,72 M$ [−0,90; 2,35]); buscar sobre el 10 % de los clientes no
  cambia contra el 10 % de las filas (−1,93 M$ [−6,68; 2,83], Welch).
- **H4, búsqueda informada: refutada** ([`h4`](../../h4/informe/informe.md)). `H4H-0.1` y `H4U-0.1` *pierden* con
  réplicas (−11,41 y −8,02 M$, con los IC enteros debajo de −δ). Elegir negativos difíciles en vez de uniformes no
  cambia (−3,39 M$ [−8,06; 1,28], Welch).
- **H4, fast-retrain: confirmada en las dos tasas.** `H4F-0.05` no pierde (1,41 M$ [−1,58; 4,40]), acelera 12,50 veces
  (más que `H3-0.05`, 10,56) y a tiempo igual *gana* (4,63 M$ [0,77; 8,50]). `H4F-0.25` no pierde (1,26 M$
  [−1,42; 3,94]), acelera 4,77 veces (más que `H3-0.25`, 4,38) y a tiempo igual *gana* (4,91 M$ [2,09; 7,73]); en la
  ronda anterior esto último quedaba *indeterminado*.
- **`H4O-0.5`, reoptimizar sobre el set del final** (respuesta a 211718): no pierde contra el control (−1,33 M$
  [−4,27; 1,60]) y no cambia contra `H4F-0.05` (−2,74 M$ [−5,69; 0,21], Welch), con A = 2,31 contra 12,50. Seguir el
  "siempre OP" en fast-retrain cuesta más de 5 veces el tiempo y no suma ganancia medible.
- U0.25 y H3-0.25 comparten el estudio de Optuna de la réplica 0, o sea los mismos hiperparámetros. U0.25 pierde y
  H3-0.25 no, así que en H1 lo que se pierde es por entrenar el final con menos filas, no por optimizar sobre una muestra.
- **Vale la pena** (no pierde y A ≥ 2): las ocho variantes de H3, las de fast-retrain (`H4F-0.05`, `H4F-0.25` y
  `H4O-0.5`) y, en esta ronda, U0.5 (A = 2,25). Ninguna de H2 (las que no pierden, B0.25 y B0.5, tienen A < 2) ni de la
  búsqueda informada de H4, que pierde.
- **AUC y ganancia.** El veredicto es el de ganancia (208135). Las variantes de H3 y `H4F-0.05` tienen ΔAUC negativo con
  Δ de ganancia positivo: en `H3-0.1` la caída de AUC es distinguible de 0 (−0,0017 [−0,0030; −0,0003]) y la ganancia
  no. En GOSS va al revés: ΔAUC positivo y distinguible de 0 (+0,0005) con Δ de ganancia negativo (−4,01 M$). El AUC
  mide el orden de todos los clientes; G, solo los 3.300 de arriba. En H1, B0.1 y la búsqueda informada de H4 las dos
  bajan juntas.
- **¿Alcanzan más semillas finales?** No, con un solo estudio de Optuna: entre el 24 % (`H3-0.1`) y el 58 % (`H3K-0.1`)
  de la varianza de G es suerte de la optimización (25 % en `C`), y esa parte no baja con más semillas finales. Pasar
  de 10 a 20 semillas angostó el IC por semilla pero no el de réplicas (§ Tabla de rondas). Cuentas en el informe de
  [`h3`](../../h3/informe/informe.md) § ¿Alcanzan 50 semillas finales?.
- **A tiempo igual** (`decisiones.md` § A tiempo igual): cada variante gasta el tiempo que le sobra en un ensamble de K
  semillas. Con réplicas, todas las H3 salvo `H3K-0.1` y las tres de fast-retrain quedan arriba del control (por
  ejemplo, `H3-0.1` 5,46 M$ [2,93; 7,98], `H4F-0.05` 4,63 M$ [0,77; 8,50]); `H4U-0.1` tiene IC que contiene a 0 aunque
  pierda con réplicas, porque el ensamble suma ganancia por sí solo, y `H4H-0.1` queda abajo (−5,68 M$
  [−10,71; −0,65]). El bootstrap de clientes de 201910, que mide el ruido del mes de test, da IC de unos ±8 M$ o más. Con
  20 semillas ensamblar el control sí suma (286,55 M$ contra 282,48 M$ de un modelo), así que la ventaja a tiempo igual
  es en buena parte ensamble.

## Bloque B: exploratorios

Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno.

### experimentos/h3/sensibilidad_muestra

- **Autor:** Martín López
- **Pregunta:** ¿Cuánto depende de la muestra la configuración que elige H3?
- **Protocolo:** 20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64, 4 hilos
- **Cifras principales:**
  - 08_ganancia_por_semilla.csv, delta: mediana 0 [-9,900,000; 8,800,000], n = 10
  - 08_ganancia_por_semilla.csv, delta_pct: mediana 0 [-3.622; 3.219], n = 10
  - 07_resumen_por_semilla.csv, delta: mediana 0 [-8.051e-05; 0.002227], n = 10
  - 07_resumen_por_semilla.csv, spearman_seleccion: mediana 0.7752 [0.6647; 0.8165], n = 10
  - 07_resumen_por_semilla.csv, tiempo_busqueda_s: mediana 487 [378; 1,064], n = 10
- **Advertencia:** 10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25

### experimentos/sampling_1/exploratorios/validacion_20_semillas

- **Autor:** Luis María Laguinge
- **Pregunta:** ¿Cambian los veredictos de H1 a H4 si el control y cada variante se evalúan con 20 semillas finales en lugar de 10?
- **Protocolo:** 20 semillas finales por variante (lista no publicada), una búsqueda por estudio, reportes por hipótesis hechos con una versión anterior de comun/reporte.py y editados a mano; sin código ni ledger
- **Cifras principales:**
  - reportado_20_semillas.csv, delta_media: mediana -0.6 [-30.75; 6.38], n = 13
  - reportado_20_semillas.csv, tiempo_s: mediana 175 [70; 786], n = 13
  - comparacion_10_semillas.csv, diferencia_delta: mediana 0.88 [-4.12; 9.68], n = 13
- **Advertencia:** solo los HTML (commits d8f04b2 y ffe5cae): no se puede reproducir; H4_HardNeg usa los hiperparámetros fijos del script de Luis (no es H4H-0.1); los tiempos de h2 no coinciden con los medidos; no cambia ningún veredicto

### experimentos/sampling_1/exploratorios/validacion_50_semillas

- **Autor:** Luis María Laguinge
- **Pregunta:** ¿Con 50 semillas finales, qué estrategias de las hipótesis 3 y 4 ganan al control y cuántas semillas entran en un presupuesto de 900 s?
- **Protocolo:** 9 estrategias con hiperparámetros fijos, 50 semillas finales (10 oficiales + 110017 + i·19937), presupuesto de 900 s; ranking y curva según K en 201908, 201910 solo informado
- **Cifras principales:**
  - resumen_50_semillas_original.csv, g_201908: mediana 201,850,000 [186,450,000; 216,150,000], n = 493
  - resumen_50_semillas_original.csv, gmax_201908: mediana 207,350,000 [196,625,000; 218,075,000], n = 493
  - resumen_50_semillas_original.csv, auc_201908: mediana 0.9274 [0.9236; 0.9311], n = 493
  - resumen_50_semillas_original.csv, g_201910: mediana 278,850,000 [266,750,000; 296,450,000], n = 493
  - resumen_50_semillas_original.csv, auc_201910: mediana 0.9328 [0.9304; 0.9357], n = 493
  - resumen_50_semillas_original.csv, tiempo_s: mediana 19.02 [11.33; 35.72], n = 493
  - ranking_201908_original.csv, puesto_201908: mediana 5 [1; 9], n = 9
  - ranking_201908_original.csv, g_201908: mediana 201,762,698 [196,690,000; 207,856,000], n = 9
  - ranking_201908_original.csv, g_201908_sd: mediana 4,037,318 [3,275,288; 4,559,427], n = 9
  - presupuesto_original.csv, k_presupuesto: mediana 40 [4; 70], n = 9
  - presupuesto_original.csv, ens_k_201908: mediana 205,150,000 [198,550,000; 210,650,000], n = 9
  - presupuesto_original.csv, ens_k_201910: mediana 281,050,000 [278,850,000; 284,350,000], n = 9
- **Advertencia:** origen: commit 9e1889e, script de Colab con su propio panel; el resumen original elige con 201910 (ya mirado) y hay piezas reconstruidas (presupuesto, resumen CSV, H4_Hard); no es una variante ni cambia el veredicto de ninguna hipótesis

### Lectura del bloque B

- **Martín, replicado** ([`h3/sensibilidad_muestra/`](../../h3/sensibilidad_muestra/README.md) § Reproducción en la
  VM): sus pasos 07 y 08 se volvieron a correr en `n2-highmem-8` con otras versiones de Python, LightGBM y numpy, y las
  elecciones, los AUC y las ganancias salieron idénticos; solo cambian los tiempos. Con 10 muestras del 25 %, la
  configuración que elige H3 cambia con la muestra, y la ganancia en 201910 se mueve de −9,9 a +8,8 M$ contra la del
  control (mediana 0; es la columna `delta` de `08_ganancia_por_semilla.csv`, en $; la `delta` de
  `07_resumen_por_semilla.csv` es diferencia de AUC, no de ganancia). Va en la misma dirección que las réplicas: la
  suerte de la optimización pesa tanto como la diferencia que se quiere medir.
- **Luis, replicado** ([`validacion_50_semillas/`](../exploratorios/validacion_50_semillas/README.md)): el script se
  portó al repo, con las piezas sin código reconstruidas y marcadas, y se corrió en `n2-highmem-8` con sus
  hiperparámetros. Ordenadas por G en 201908 (como pide la consigna), el control queda primero y ninguna estrategia lo
  supera; el "campeón" de su resumen, elegido en 201910, no gana en el mes que decide. Al repetir la búsqueda (bloque A)
  la búsqueda difícil pierde y H3 queda en *no pierde*. Su idea de producción, el fast-retrain, es la que se sostiene con
  réplicas (`H4F-0.05`).
- **Luis, 20 semillas** ([`validacion_20_semillas/`](../exploratorios/validacion_20_semillas/README.md)): su pregunta
  (¿cambian los veredictos con 20 semillas?) la contesta ahora la ronda vigente con nuestro protocolo: 20 semillas
  publicadas, con réplicas y desde los ledgers. Ningún veredicto cambia de lado (§ Tabla de rondas).

## Tabla de rondas

Copiada de [`comparacion_rondas.md`](comparacion_rondas.md). Regla escrita antes de correr en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Predicción y regla de la ronda; resultado en la bitácora
de `control`:

- Ronda 201903-201906 (final con 4 meses, 10 semillas, N* de validación): δ = 5.52 M$.
- Ronda 201903-201908 (final con 6 meses, 20 semillas, N* fijo): δ = 5.65 M$.

Δ en M$ al corte N* de cada ronda, con IC 95%.

| variante | Δ réplica 0 201903-201906 | veredicto | Δ con réplicas | veredicto | Δ réplica 0 201903-201908 | veredicto | Δ con réplicas | veredicto | ¿cambia el veredicto? |
|---|---|---|---|---|---|---|---|---|---|
| B0.1 | -7.81 [-12.27; -3.35] | pierde | — | — | -8.47 [-11.02; -5.92] | pierde | — | — | no |
| B0.25 | 0.66 [-2.86; 4.18] | no pierde | — | — | 0.88 [-1.95; 3.71] | no pierde | — | — | no |
| B0.5 | -0.11 [-4.46; 4.24] | no pierde | — | — | -0.94 [-3.62; 1.75] | no pierde | — | — | no |
| C | pendiente | pendiente | — | — | pendiente | pendiente | — | — | pendiente |
| GOSS | 0.55 [-2.60; 3.70] | no pierde | — | — | -4.01 [-7.03; -1.00] | indeterminado | — | — | sí |
| H3-0.05 | 3.74 [1.77; 5.71] | gana | 1.87 [-1.02; 4.76] | no pierde | 5.22 [2.96; 7.49] | gana | 2.08 [-0.87; 5.02] | no pierde | no |
| H3-0.1 | 4.07 [-0.27; 8.41] | no pierde | 2.30 [-0.88; 5.47] | no pierde | 1.26 [-1.95; 4.48] | no pierde | 1.71 [-1.07; 4.49] | no pierde | no |
| H3-0.25 | 4.18 [-0.60; 8.96] | no pierde | 1.81 [-1.78; 5.41] | no pierde | 4.73 [2.48; 6.98] | gana | 1.42 [-2.82; 5.67] | no pierde | sí |
| H3K-0.1 | 5.17 [1.48; 8.86] | gana | 1.28 [-3.42; 5.98] | no pierde | 0.44 [-1.91; 2.79] | no pierde | -0.21 [-5.05; 4.63] | no pierde | sí |
| H3L-0.1 | -1.43 [-3.86; 1.00] | no pierde | -1.46 [-4.73; 1.81] | no pierde | -1.43 [-4.02; 1.16] | no pierde | 0.14 [-3.30; 3.57] | no pierde | no |
| H3L-0.25 | 1.21 [-2.40; 4.82] | no pierde | 0.25 [-2.02; 2.51] | no pierde | 1.32 [-1.36; 4.00] | no pierde | 1.22 [-1.59; 4.03] | no pierde | no |
| H3R-0.1 | 3.30 [0.65; 5.95] | gana | 1.76 [-1.21; 4.73] | no pierde | 0.82 [-1.79; 3.44] | no pierde | 1.59 [-1.80; 4.98] | no pierde | sí |
| H3R-0.25 | 2.97 [-0.20; 6.14] | no pierde | 1.53 [-1.92; 4.97] | no pierde | 2.04 [-0.81; 4.88] | no pierde | 1.95 [-0.85; 4.74] | no pierde | no |
| H4F-0.05 | 4.40 [-0.07; 8.87] | no pierde | 1.86 [-0.83; 4.54] | no pierde | 4.18 [1.11; 7.25] | gana | 1.41 [-1.58; 4.40] | no pierde | sí |
| H4F-0.25 | 3.52 [-1.66; 8.70] | no pierde | 1.39 [-1.87; 4.65] | no pierde | 1.04 [-2.02; 4.11] | no pierde | 1.26 [-1.42; 3.94] | no pierde | no |
| H4H-0.1 | -3.30 [-7.38; 0.78] | indeterminado | -8.61 [-12.78; -4.43] | pierde | -9.19 [-12.06; -6.31] | pierde | -11.41 [-15.80; -7.03] | pierde | sí |
| H4U-0.1 | -2.42 [-7.11; 2.27] | indeterminado | -5.54 [-8.94; -2.14] | pierde | -7.70 [-10.81; -4.59] | pierde | -8.02 [-11.52; -4.53] | pierde | sí |
| U0.05 | -33.77 [-39.84; -27.70] | pierde | — | — | -30.14 [-34.56; -25.72] | pierde | — | — | no |
| U0.1 | -16.94 [-23.35; -10.53] | pierde | — | — | -16.28 [-19.83; -12.73] | pierde | — | — | no |
| U0.25 | -6.38 [-11.21; -1.55] | pierde | — | — | -9.57 [-12.65; -6.49] | pierde | — | — | no |
| U0.5 | -1.32 [-6.77; 4.13] | indeterminado | — | — | -1.38 [-3.99; 1.24] | no pierde | — | — | sí |

- **Veredictos estables: se confirma.** 0 cambios de lado. Cambian 8 veredictos, todos desde o hacia *indeterminado* o
  entre *gana* y *no pierde* (por semilla); con réplicas no cambia ninguno.
- **IC más angosto: se confirma.** La mediana de la razón de anchos del IC por semilla (ronda anterior / nueva) es 1,44,
  dentro de [1,2; 1,9].
- **Con réplicas el ancho baja menos: se confirma.** La mediana de la razón con réplicas es 0,96: con 8 réplicas el IC
  prácticamente no se angosta, porque la suerte de Optuna no depende de las semillas finales.
- T y A no se comparan entre rondas: el final de seis meses es más largo y se midió en otras VMs.

## Limitaciones

Solo lo que no está justificado en § Diseño (los tres apartamientos con id están justificados ahí):

- **Hiperparámetros de cuatro meses en un final de seis.** Se usan sin cambios, incluido `min_data_in_leaf`, que es
  absoluto y ahora se aplica sobre más filas. Reescalarlo sería una variante nueva (la idea está en `H3R` y `H3L`).
- **Test ya mirado.** H4 y las extensiones de H3 salen del aporte de Luis, que eligió y descartó estrategias mirando su
  ganancia en 201910, y no hay otro mes de test (la consigna lo reserva para la comparación). Entraron todas juntas, con
  reglas escritas antes de correr, y ninguna se eligió ni se descartó acá por 201910; aun así, esos resultados no
  cuentan con un mes de test que no se haya mirado.
- **Comparaciones múltiples.** Entre H4 y las extensiones de H3 hay más de diez contrastes sin corrección: con un 5 % de
  error por contraste, alguno puede salir significativo por azar. Las conclusiones se apoyan en los contrastes
  principales fijados antes de correr (`H3-0.1`, `H4H-0.1` y `H4F-0.05` contra el control); el resto es secundario.
- Las limitaciones propias de cada hipótesis (GOSS descriptivo y adaptación de `bagging_fraction` en H2, estudios
  compartidos con `h1` y reescalado en H3, sonda y proporción de clases en H4) están en su informe.
- Solo `C`, las H3 y las H4 tienen réplicas de Optuna. Para `U*`, `B*` y `GOSS`, Δ sigue incluyendo la suerte de una
  sola optimización; como pierden por mucho o no aceleran, no cambia la respuesta (U0.5, que vale la pena por poco, es
  la excepción: su veredicto es de una sola búsqueda).
- 8 réplicas alcanzan para decidir *no pierde*, pero no para separar de 0 una ventaja de 1,42 a 2,08 M$. R = 8 quedó
  cerrado antes de correr, y la tabla de rondas muestra que más semillas finales no angostan ese IC.
- U0.25/H3-0.25 y U0.1/H3-0.1 comparten el estudio de la réplica 0; H3R, H3L y H3 de la misma tasa comparten todos, y
  `H4F-0.05`/`H4F-0.25` comparten los de `H3-0.05`/`H3-0.25`: no son evidencia independiente entre sí.
- H4 cambia la proporción de clases en la búsqueda (o en el final, con peso 2 para restituirla), el terreno de
  Sampling_2; es la excepción declarada en `h4/docs/hipotesis.md`.
- La réplica del control (C-rep) se corrió en otra VM de la misma cuenta, no por otra persona.
- A N* fijo la ganancia se mueve en pasos de 1,1 M$, así que diferencias de uno o dos BAJA+2 no se distinguen del ruido.
- Un solo año (2019) y un solo mes de test (201910): el bootstrap de clientes muestra que el ruido de ese mes es mayor
  que el de las réplicas. Los tiempos valen para `n2-highmem-8` (VMs distintas; T es la mediana entre réplicas) y en
  otra máquina solo se trasladan las aceleraciones relativas.
- `num_iterations = 100` fijo y `force_col_wise`: T(C) no es el tiempo del baseline con la configuración automática.

## Conclusiones

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 5 %, 10 % o 25 % de las filas y entrenar con todas las de 201903–201908 no pierde contra el control, también
cuando se mide la suerte de Optuna con 8 réplicas, y es de 4,38 a 10,56 veces más rápido. Entrenar el final con menos
filas al azar pierde desde r = 0,25 (r = 0,5 no pierde y acelera 2,25 veces), y dentro de LightGBM pierde con f = 0,1.
Por qué: la optimización es lo que domina T (en el control, 748 s de Optuna; `control/ledger/estudios.csv`), y los
hiperparámetros que elige Optuna sobre la muestra sirven para el total.

Lo que las réplicas corrigen es el tamaño de la ventaja: con una sola optimización, H3 puede parecer que le gana al
control o que empata, según la suerte del estudio; con 8 réplicas la diferencia queda entre 1,42 y 2,08 M$ y su IC
contiene a 0. El mecanismo queda sin resolver. La respuesta práctica no cambia (H3 no pierde y acelera), pero no hay que
venderla como una mejora de ganancia. Para comparar variantes con Optuna, más semillas finales no alcanzan: hay que
repetir la optimización; la ronda de 20 semillas lo muestra (el IC por semilla se angosta, el de réplicas no).

Con los tres contrastes principales, fijados antes de correr H4:
- **`H3-0.1` contra el control: no pierde** (1,71 M$ [−1,07; 4,49] con réplicas) y acelera 7,76 veces. Es la respuesta
  de arriba.
- **`H4H-0.1` contra el control: pierde** (−11,41 M$ [−15,80; −7,03]). Achicar la búsqueda conservando todas las bajas
  y recortando CONTINUA rinde peor que achicarla al azar, elijan como se elijan los negativos. La ventaja que reportaba
  el aporte de Luis no se sostiene al repetir la búsqueda.
- **`H4F-0.05` contra el control: no pierde** (1,41 M$ [−1,58; 4,40]), acelera 12,50 veces y **a tiempo igual gana**
  (4,63 M$ [0,77; 8,50]). Achicar también el final, conservando todas las bajas y la mitad de CONTINUA con peso 2,
  agrega velocidad sin perder; con el tiempo que sobra se ensamblan más semillas. Esta variante viene de una idea vista
  en 201910, y reoptimizarla sobre su propio set (`H4O-0.5`) no la mejora.

La respuesta al tutor: vale la pena achicar la optimización (al azar, no informada por clase) y, si además se quiere el
final más rápido, achicar CONTINUA conservando las bajas con peso. Ninguna de las dos es una mejora de ganancia por
modelo, ni en ganancia ni en AUC; la ganancia extra, si la hay, viene de ensamblar con el tiempo ahorrado. Con el final
de seis meses y 20 semillas la respuesta es la misma que con cuatro meses y 10.

## Qué sigue

- Otro mes de test, para separar el ruido de 201910 del efecto de las variantes y para tener uno que no se haya mirado
  al elegir H4 y las extensiones de H3.
- Fast-retrain sobre otras búsquedas (por ejemplo, `H3-0.1`) y con otras fracciones de CONTINUA, con réplicas desde el
  principio: la suerte de la optimización es del mismo orden que las diferencias entre variantes.

## Bibliografía (para postear en Zulip)

- Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS 30. (GOSS)
- Friedman, J. H. (2002). *Stochastic Gradient Boosting*. Computational Statistics & Data Analysis 38(4). (bagging por
  iteración)
- Akiba, T. et al. (2019). *Optuna: A Next-generation Hyperparameter Optimization Framework*. KDD.
- Bergstra, J. et al. (2011). *Algorithms for Hyper-Parameter Optimization*. NeurIPS 24. (TPE)
- Bolaños, baseline oficial del experimento colaborativo, Zulip 208135 (28-oct-2026).
