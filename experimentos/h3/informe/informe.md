# Informe — H3: optimizar sobre una muestra, entrenar con todo

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md). Los números de la réplica 0 salen de `ledger/apareado.csv`;
los de las réplicas, de `ledger/replicas.csv`, `control/ledger/replicas.csv` y
[`sampling_1/informe/tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md). Las figuras están en
[`reporte.html`](reporte.html). `python -m scripts.verificar_informe_h3` comprueba que cada número de este informe sale
de esas fuentes.

## Hipótesis

H3: optimizar con Optuna sobre una muestra uniforme (r_opt = 0,25 o 0,1) y entrenar el final con todo no pierde. Con el
cambio `h3-semillas-optuna` se suman 8 réplicas de la optimización (k = 0…7, semilla de TPE y de la muestra = k), la
variante `H3-0.05` y el reescalado de `min_data_in_leaf` (`H3R-0.1`). Con el cambio `incorporar-aportes` se suman cuatro
variantes del aporte de Luis (§ Extensiones del aporte de Luis). Texto completo y reglas pre-registradas en
[`docs/hipotesis.md`](../docs/hipotesis.md) § H3 con réplicas y § Extensiones del aporte de Luis; variantes y
dependencias en `docs/diseno.md`.

### Ronda 201903–201908

Todos los números de este informe son de la ronda vigente (cambio `final-con-julio-agosto`): el modelo final entrena con
201903–201908 y se evalúa en test (201910) con 20 semillas finales; Optuna no cambia (train 201903–201906, validación
201908) y los estudios se reusan. La ronda anterior (final 201903–201906, 10 semillas) y la comparación de veredictos
entre las dos están en [`comparacion_rondas.md`](../../sampling_1/informe/comparacion_rondas.md). Los apartamientos del
baseline tienen su id y su justificación en [`docs/diseno.md`](../docs/diseno.md) § Ronda 201903–201908 y en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Apartamientos del baseline:

- el veredicto sale de la ganancia y no del AUC (Zulip 208135): la regla está escrita en pesos; el AUC en test va al
  lado (ΔAUC);
- el final entrena con 201903–201908 (Zulip 211210);
- `H3` no reoptimiza para el final aunque el tutor pidió "siempre OP" (Zulip 211718): optimizar sobre una muestra y
  entrenar con otra cosa *es* la hipótesis.

## Resultados de la réplica 0

N* = 3.300 envíos (fijo), Ḡ_C = 282,48 M$, δ = 5,65 M$, 20 semillas en común. Es el veredicto pre-registrado en
§ H3 de `docs/hipotesis.md`.

| variante | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| H3-0.1 | 1,26 | [−1,95; 4,48] | 8,04 | no pierde | sí |
| H3-0.25 | 4,73 | [2,48; 6,98] | 4,37 | gana | sí |

- **H3, confirmada en la réplica 0**: las dos tasas no pierden y aceleran 4,37 y 8,04 veces; `H3-0.25` además *gana*.
- Ese IC solo ve la semilla final: el estudio de Optuna es uno por variante, así que la suerte de la optimización
  queda adentro de Δ sin medir. Las réplicas de abajo la miden.

## Resultados con réplicas

8 réplicas × 20 semillas en las 5 variantes (`C` y las cuatro de H3). Ḡ_C con réplicas = 281,78 M$; δ = 5,65 M$ y
N* = 3.300 quedan fijos. Filas copiadas de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md)
(formato del reporte, punto decimal):

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | ΔAUC en 201910 [IC] | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| H3-0.05 | H3 | 283.86 (R=8) | 5.22 [2.96; 7.49] | 2.08 [-0.87; 5.02] (R=8) | -0.0020 [-0.0041; +0.0000] (R=8) | 95 | 10.56 | 4.77 [1.01; 8.53] (R=8) | 7.74 [0.06; 16.23] | no pierde (con réplicas (8)) |
| H3-0.1 | H3 | 283.49 (R=8) | 1.26 [-1.95; 4.48] | 1.71 [-1.07; 4.49] (R=8) | -0.0017 [-0.0030; -0.0003] (R=8) | 129 | 7.76 | 5.46 [2.93; 7.98] (R=8) | 6.04 [-2.37; 15.30] | no pierde (con réplicas (8)) |
| H3R-0.1 | H3 | 283.37 (R=8) | 0.82 [-1.79; 3.44] | 1.59 [-1.80; 4.98] (R=8) | -0.0008 [-0.0023; +0.0006] (R=8) | 130 | 7.71 | 5.87 [4.27; 7.47] (R=8) | 5.06 [-2.15; 13.31] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 283.20 (R=8) | 4.73 [2.48; 6.98] | 1.42 [-2.82; 5.67] (R=8) | -0.0009 [-0.0021; +0.0004] (R=8) | 229 | 4.38 | 6.15 [3.95; 8.34] (R=8) | 8.85 [1.87; 16.83] | no pierde (con réplicas (8)) |

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| C | 8 | 160 | 2.78 | 4.53 | 25 % |
| H3-0.05 | 8 | 160 | 2.71 | 3.75 | 32 % |
| H3-0.1 | 8 | 160 | 2.38 | 3.94 | 24 % |
| H3-0.25 | 8 | 160 | 4.72 | 4.45 | 50 % |
| H3R-0.1 | 8 | 160 | 3.48 | 3.57 | 46 % |

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.12 [-1.95; 1.71] | 8 | t, apareado | no cambia |

### Veredictos con las reglas de D4

Las reglas se aplican tal como quedaron escritas en [`docs/hipotesis.md`](../docs/hipotesis.md) § Predicciones y reglas,
antes de las corridas, con el δ de la ronda (5,65 M$).

1. **H3 con réplicas: confirmada.** `H3-0.1` y `H3-0.25` *no pierden* con réplicas: las cotas inferiores del IC de Welch
   (−1,07 y −2,82 M$) quedan por encima de −5,65 M$. La respuesta al tutor se sostiene: el tradeoff vale la pena. Con
   réplicas, Δ pasa de 4,73 a 1,42 M$ en `H3-0.25` (la réplica 0 había salido arriba de la media) y de 1,26 a 1,71 M$
   en `H3-0.1` (había salido abajo): la suerte de Optuna mueve Δ en los dos sentidos.
2. **A contra B: mecanismo sin resolver.** En `H3-0.1`, el IC de Δ con réplicas, [−1,07; 4,49] M$, contiene a 0, pero
   Ḡ_{C,0} = 282,48 M$ queda arriba de la mediana de las 8 Ḡ_{C,k}, 282,40 M$, así que (B) no se cumple. (A) tampoco:
   Δ con réplicas no *gana* (cota inferior −1,07 < 0), aunque la mediana de `feature_fraction` sí es menor en `H3-0.1`
   (0,518) que en `C` (0,641). En la ronda anterior la regla daba (B) por poco; con el final de seis meses la réplica 0
   de `C` queda casi en la mediana. Con los datos no se distingue una ventaja de H3 sobre el control: H3 *no pierde*,
   pero no se puede decir que regularice.
3. **`H3-0.05`: confirmada.** *No pierde* con réplicas (cota inferior −0,87 ≥ −5,65 M$) y A = 10,56 ≥ 8, con T como
   mediana entre réplicas (95 s en `H3-0.05`). En la réplica 0 sale *gana* ([2,96; 7,49] M$); con réplicas ya no.
4. **`H3R-0.1`: no cambia.** La diferencia apareada `H3R-0.1` − `H3-0.1` es −0,12 M$ con IC t entre réplicas
   [−1,95; 1,71] (7 g.l.): la cota inferior no pasa 0 y la superior no queda debajo de 0. La predicción (*mejora*) no se
   cumple: reescalar `min_data_in_leaf` × √10 no mueve la ganancia. Con su propio veredicto contra `C`, `H3R-0.1` *no
   pierde* (cota inferior −1,80 M$).

**AUC y ganancia.** El veredicto es el de ganancia (Zulip 208135, § Ronda 201903–201908). Las cuatro variantes de la
tabla tienen ΔAUC negativo con Δ de ganancia positivo: van en direcciones distintas. En `H3-0.1` la diferencia de AUC
es distinguible de 0 (−0,0017, IC [−0,0030; −0,0003]) mientras Δ de ganancia es 1,71 M$ con IC que contiene a 0. El
AUC mide el orden de todos los clientes; G solo los 3.300 de arriba, así que un modelo puede ordenar algo peor en
general y quedar igual o mejor en la cabeza.

### ¿Alcanzan 50 semillas finales?

No, si hay un solo estudio de Optuna. La descomposición de la varianza de G (suma de cuadrados exacta) da que entre el
24 % (`H3-0.1`) y el 50 % (`H3-0.25`) de la varianza de una corrida es suerte de Optuna (sd entre réplicas de 2,38 a
4,72 M$; 25 % en `C`). Más semillas finales achican solo la otra parte: con un estudio, la parte de Optuna es el 77 %
(`C`) a 91 % (`H3-0.25`) de la varianza de Ḡ con 10 semillas y el 94 % a 98 % con 50. El desvío de Ḡ con un estudio
baja apenas, de 2,96 a 2,67 M$ en `C` al pasar de 10 a 50 semillas. Pasar de 10 a 20 semillas en esta ronda angostó
el IC por semilla pero no el de réplicas (tabla de rondas). Para medir Δ hace falta repetir la optimización, no solo
el final.

## Extensiones del aporte de Luis (`incorporar-aportes`)

Cuatro variantes del aporte de Luis María Laguinge, con reglas escritas antes de correr en
[`docs/hipotesis.md`](../docs/hipotesis.md) § Extensiones del aporte de Luis: el reescalado √(1/r) en r = 0,25
(`H3R-0.25`), el lineal 1/r en r = 0,25 y 0,1 (`H3L-0.25`, `H3L-0.1`) y la búsqueda sobre el 10 % de los clientes con
todas sus filas (`H3K-0.1`, estudios `K0.1` / `K0.1@k`). Las cuatro con 8 réplicas × 20 semillas. Salen de mirar
201910 (§ Limitaciones). Filas copiadas de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md):

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | ΔAUC en 201910 [IC] | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| H3K-0.1 | H3 | 281.57 (R=8) | 0.44 [-1.91; 2.79] | -0.21 [-5.05; 4.63] (R=8) | -0.0033 [-0.0050; -0.0017] (R=8) | 126 | 7.98 | 3.95 [-1.58; 9.47] (R=8) | 4.24 [-6.33; 15.40] | no pierde (con réplicas (8)) |
| H3L-0.1 | H3 | 281.92 (R=8) | -1.43 [-4.02; 1.16] | 0.14 [-3.30; 3.57] (R=8) | -0.0005 [-0.0020; +0.0010] (R=8) | 130 | 7.73 | 2.98 [0.05; 5.92] (R=8) | 1.76 [-7.26; 10.72] | no pierde (con réplicas (8)) |
| H3L-0.25 | H3 | 283.00 (R=8) | 1.32 [-1.36; 4.00] | 1.22 [-1.59; 4.03] (R=8) | +0.0004 [-0.0008; +0.0016] (R=8) | 222 | 4.51 | 5.46 [0.83; 10.08] (R=8) | 9.00 [2.14; 16.83] | no pierde (con réplicas (8)) |
| H3R-0.25 | H3 | 283.72 (R=8) | 2.04 [-0.81; 4.88] | 1.95 [-0.85; 4.74] (R=8) | +0.0000 [-0.0011; +0.0011] (R=8) | 225 | 4.46 | 5.32 [2.93; 7.71] (R=8) | 6.65 [-0.28; 14.19] | no pierde (con réplicas (8)) |

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| H3K-0.1 | 8 | 160 | 5.51 | 4.31 | 58 % |
| H3L-0.1 | 8 | 160 | 3.55 | 3.58 | 47 % |
| H3L-0.25 | 8 | 160 | 2.45 | 3.90 | 26 % |
| H3R-0.25 | 8 | 160 | 2.41 | 3.68 | 28 % |

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H3R-0.25 - H3L-0.25 | 0.72 [-0.90; 2.35] | 8 | t, apareado | no cambia |
| H3R-0.1 - H3L-0.1 | 1.45 [0.65; 2.25] | 8 | t, apareado | mejora |
| H3R-0.25 - H3-0.25 | 0.52 [-1.59; 2.64] | 8 | t, apareado | no cambia |
| H3K-0.1 - H3-0.1 | -1.93 [-6.68; 2.83] | 8 | Welch, sin aparear | no cambia |

En la tabla de diferencias, "mejora" quiere decir que la primera variante supera a la segunda (cota inferior > 0).

### Veredictos con las reglas pre-registradas

5. **Raíz contra lineal: gana la raíz en r = 0,1; no cambia en r = 0,25.** `H3R-0.1` − `H3L-0.1` = 1,45 M$, IC t entre
   réplicas [0,65; 2,25] (7 g.l.): la cota inferior es > 0. `H3R-0.25` − `H3L-0.25` = 0,72 M$, IC [−0,90; 2,35]:
   contiene a 0. La predicción (gana la raíz con las dos tasas, lo que reportaba Luis) se cumple solo en r = 0,1, igual
   que en la ronda anterior. La raíz no es mejor que no reescalar (reglas 4 y 6).
6. **Raíz contra nada en r = 0,25: no cambia.** `H3R-0.25` − `H3-0.25` = 0,52 M$, IC [−1,59; 2,64]. La predicción
   (*mejora*) no se cumple, igual que con `H3R-0.1` en r = 0,1 (regla 4).
7. **Por cliente: no cambia.** D_K = −1,93 M$, IC de Welch [−6,68; 2,83]. La predicción (*empeora*, lo que reportaba
   Luis) no se cumple. `H3K-0.1` es la variante con más varianza entre réplicas (58 %, sd 5,51 M$); una explicación
   posible, que no se probó, es que sortear clientes enteros hace más distinta una muestra de otra que sortear filas.
8. **Contra `C`, cada una *no pierde* con réplicas**: cotas inferiores del IC de Welch −0,85 (`H3R-0.25`), −1,59
   (`H3L-0.25`), −3,30 (`H3L-0.1`) y −5,05 M$ (`H3K-0.1`), todas ≥ −5,65 M$. No cambia el veredicto de H3, que es el de
   la regla 1.

`H3K-0.1` es la única extensión con ΔAUC distinguible de 0 (−0,0033, IC [−0,0050; −0,0017]) y su Δ de ganancia
(−0,21 M$) casi no se mueve: ordena peor en general sin perder en la cabeza.

Las reglas 5 a 8 son secundarias: la respuesta al tutor se apoya en los contrastes principales fijados en
[`h4/docs/hipotesis.md`](../../h4/docs/hipotesis.md) § Comparaciones múltiples. La única diferencia que sale distinta de
0 (raíz contra lineal en r = 0,1) es una de las más de diez sin corrección por comparaciones múltiples.

## Limitaciones

Solo lo que no está justificado en el diseño; los apartamientos con id (208135, 211210, 211718) están en § Ronda
201903–201908.

- **Ventana del final en duda.** Si el tutor quería una ventana corrida 201905–201908 en vez de 201903–201908, es otra
  ronda (no corrida).
- **Hiperparámetros de cuatro meses en un final de seis**, sin reescalar `min_data_in_leaf` (absoluto). `H3R` y `H3L`
  muestran que reescalarlo no mejora a no hacerlo en las muestras de búsqueda, pero eso no se probó para el salto de
  cuatro a seis meses.
- **Estudios de `h1`**: la réplica 0 de H3 usa los estudios `U0.25`, `U0.1` y `U0.05` de `h1` (`h1/ledger/hp/`); las
  réplicas `@k` son de `h3`. Δ(H3-0.25) y Δ(U0.25) de la réplica 0 tienen la misma suerte de optimización y no son
  evidencia independiente entre sí. Sin `h1`, H3 no se puede correr ni consolidar.
- `H3R-0.1` y `H3-0.1` comparten todos sus estudios: su diferencia aísla el reescalado y no es evidencia independiente
  sobre H3. Lo mismo vale para `H3R-0.25`, `H3L-0.25` y `H3-0.25`, y para `H3L-0.1`.
- **Test ya mirado.** Las extensiones salen del aporte de Luis, que eligió el reescalado √(1/r) frente al lineal y
  descartó el muestreo por cliente mirando su ganancia en 201910; no hay otro mes de test (consigna, Zulip 208135).
  Entraron todas, con reglas escritas antes de correr, y ninguna se eligió ni se descartó acá por 201910, pero estos
  contrastes no cuentan con un mes de test que no se haya mirado.
- **Comparaciones múltiples.** Con `h4` son más de diez contrastes sin corrección: con un 5 % de error por contraste,
  alguno puede salir significativo por azar. Las reglas 5 a 8 son secundarias.
- 8 réplicas: el IC de Welch quedó lo bastante angosto para decidir *no pierde*, pero no para separar de cero una ventaja
  del tamaño de la medida (1,42 a 2,08 M$). R = 8 quedó cerrado antes de correr y no se agregan réplicas.
- Los tiempos vienen de VMs `n2-highmem-8` distintas; T es la mediana entre réplicas y no se compara entre rondas.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto. El
  bootstrap de clientes de 201910 (tabla de arriba) muestra que el ruido del mes de test es mayor que el de las réplicas.

## Conclusión

Optimizar sobre una muestra del 5 %, 10 % o 25 % y entrenar con todas las filas de 201903–201908 no pierde contra el
control, también cuando se mide la suerte de Optuna con 8 réplicas, y acelera de 4,38 a 10,56 veces. La réplica 0 sola
exagera o achica la ventaja según la suerte del estudio; con réplicas Δ queda entre 1,42 y 2,08 M$ con IC que contiene a
0, y el mecanismo (regulariza o suerte del control) queda sin resolver. El AUC en test baja algo con la muestra aunque la
ganancia no: el veredicto es el de ganancia. El reescalado √(1/r) de `min_data_in_leaf` no cambia contra no reescalar.
De las extensiones del aporte de Luis, todas no pierden contra el control: la raíz no mejora a no reescalar (tampoco en
r = 0,25), le gana a la lineal solo en r = 0,1, y buscar sobre el 10 % de los clientes no cambia contra buscar sobre el
10 % de las filas. Comparación con las otras hipótesis, a tiempo igual y entre rondas: informe conjunto.
