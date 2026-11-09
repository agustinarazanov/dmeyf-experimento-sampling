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
variante `H3-0.05` y el reescalado de `min_data_in_leaf` (`H3R-0.1`). Texto completo y reglas pre-registradas en
[`docs/hipotesis.md`](../docs/hipotesis.md) § H3 con réplicas; variantes y dependencias en `docs/diseno.md`.

## Resultados de la réplica 0

N* = 3.300 envíos (de 201908), Ḡ_C = 276,10 M$, δ = 5,52 M$, 10 semillas en común. Es el veredicto pre-registrado en
§ H3 de `docs/hipotesis.md` y no cambia.

| variante | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| H3-0.1 | 4,07 | [−0,27; 8,41] | 8,41 | no pierde | sí |
| H3-0.25 | 4,18 | [−0,60; 8,96] | 4,48 | no pierde | sí |

- **H3, confirmada en la réplica 0**: las dos tasas no pierden y aceleran 4,48 y 8,41 veces. Ninguna *gana*: las cotas
  inferiores son negativas, aunque la media de Δ es positiva.
- Ese IC solo ve la semilla final: el estudio de Optuna es uno por variante, así que la suerte de la optimización
  quedaba adentro de Δ sin medir. Las réplicas de abajo la miden.

## Resultados con réplicas

8 réplicas × 10 semillas en las 5 variantes (`C` y las cuatro de H3). Ḡ_C con réplicas = 275,92 M$; δ = 5,52 M$ y
N* = 3.300 quedan fijos. Filas copiadas de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md)
(formato del reporte, punto decimal):

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|
| H3-0.05 | H3 | 277.79 (R=8) | 3.74 [1.77; 5.71] | 1.87 [-1.02; 4.76] (R=8) | 83 | 11.82 | 1.97 [-2.83; 6.76] (R=8) | 2.75 [-5.17; 12.54] | no pierde (con réplicas (8)) |
| H3R-0.1 | H3 | 277.68 (R=8) | 3.30 [0.65; 5.95] | 1.76 [-1.21; 4.73] (R=8) | 117 | 8.34 | 3.34 [-0.14; 6.82] (R=8) | 8.14 [-1.32; 18.48] | no pierde (con réplicas (8)) |
| H3-0.1 | H3 | 278.22 (R=8) | 4.07 [-0.27; 8.41] | 2.30 [-0.88; 5.47] (R=8) | 118 | 8.30 | 4.03 [0.78; 7.27] (R=8) | 4.38 [-3.96; 13.42] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 277.74 (R=8) | 4.18 [-0.60; 8.96] | 1.81 [-1.78; 5.41] (R=8) | 216 | 4.53 | 1.83 [-1.91; 5.57] (R=8) | 3.46 [-4.29; 11.77] | no pierde (con réplicas (8)) |

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| C | 8 | 80 | 2.53 | 4.25 | 25 % |
| H3-0.05 | 8 | 80 | 2.84 | 3.96 | 33 % |
| H3-0.1 | 8 | 80 | 3.30 | 4.00 | 38 % |
| H3-0.25 | 8 | 80 | 3.93 | 4.60 | 40 % |
| H3R-0.1 | 8 | 80 | 2.99 | 3.81 | 35 % |

| diferencia | Δ [IC t entre réplicas] (M$) | réplicas | veredicto |
|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.54 [-1.88; 0.81] | 8 | no cambia |

### Veredictos con las reglas de D4

Las reglas se aplican tal como quedaron escritas en [`docs/hipotesis.md`](../docs/hipotesis.md) § Predicciones y reglas,
antes de las corridas.

1. **H3 con réplicas: confirmada.** `H3-0.1` y `H3-0.25` *no pierden* con réplicas: las cotas inferiores del IC de Welch
   (−0,88 y −1,78 M$) quedan por encima de −5,52 M$. La respuesta al tutor se sostiene: el tradeoff vale la pena. Con
   réplicas, Δ baja de 4,07 a 2,30 M$ en `H3-0.1` y de 4,18 a 1,81 M$ en `H3-0.25`: cerca de la mitad de la ventaja
   de la réplica 0 era suerte de Optuna.
2. **A contra B: apoya (B)** (la regla pre-registrada "el control tuvo mala suerte"). En `H3-0.1`, el IC de Δ con réplicas, [−0,88; 5,47] M$,
   contiene a 0, y Ḡ_{C,0} = 276,10 M$ queda debajo de la mediana de las 8 Ḡ_{C,k}, 276,49 M$. La condición de (A) no
   se cumple: Δ con réplicas no *gana* (cota inferior −0,88 < 0), aunque la mediana de `feature_fraction` sí es menor en
   `H3-0.1` (0,518) que en `C` (0,641). Con los datos no se distingue una ventaja de H3 sobre el control: H3 *no
   pierde*, pero no se puede decir que regularice. La regla se cumple, pero su nombre se lee de más: Ḡ_{C,0} queda
   debajo de la mediana y arriba de la media de las réplicas de `C` (275,92 M$). Δ se achica porque la réplica 0 de
   `H3-0.1` quedó arriba de su media entre réplicas (278,22 M$), no porque el control haya salido bajo: la suerte de
   la réplica 0 estaba más en H3 que en `C`.
3. **`H3-0.05`: confirmada.** *No pierde* con réplicas (cota inferior −1,02 ≥ −5,52 M$) y A = 11,82 ≥ 8, con T como
   mediana entre réplicas (83 s en `H3-0.05`). En la réplica 0 salía *gana* ([1,77; 5,71] M$); con réplicas ya
   no.
4. **`H3R-0.1`: no cambia.** La diferencia apareada `H3R-0.1` − `H3-0.1` es −0,54 M$ con IC t entre réplicas
   [−1,88; 0,81] (80 pares, 7 g.l.): la cota inferior no pasa 0 y la superior no queda debajo de 0. La predicción
   (*mejora*) no se cumple: reescalar `min_data_in_leaf` × √10 no mueve la ganancia. Con su propio veredicto contra `C`,
   `H3R-0.1` *no pierde* (cota inferior −1,21 M$).

### ¿Alcanzan 50 semillas finales?

No, si hay un solo estudio de Optuna. La descomposición de la varianza de G (suma de cuadrados exacta) da que entre el
25 % (`C`) y el 40 % (`H3-0.25`) de la varianza de una corrida es suerte de Optuna (sd entre réplicas de 2,53 a
3,93 M$). Más semillas finales achican solo la otra parte: con un estudio, la parte de Optuna es el 77 % (`C`) a 87 %
(`H3-0.25`) de la varianza de Ḡ con 10 semillas y el 94 % a 97 % con 50. El desvío de Ḡ con un estudio baja apenas, de
2,69 a 2,43 M$ en `C` al pasar de 10 a 50 semillas. Para medir Δ hace falta repetir la optimización, no solo el final.

## Limitaciones

- **Estudios de `h1`**: la réplica 0 de H3 usa los estudios `U0.25`, `U0.1` y `U0.05` de `h1` (`h1/ledger/hp/`); las
  réplicas `@k` son de `h3`. Δ(H3-0.25) y Δ(U0.25) de la réplica 0 tienen la misma suerte de optimización y no son
  evidencia independiente entre sí. Sin `h1`, H3 no se puede correr ni consolidar.
- `H3R-0.1` y `H3-0.1` comparten todos sus estudios: su diferencia aísla el reescalado y no es evidencia independiente
  sobre H3.
- 8 réplicas: el IC de Welch quedó lo bastante angosto para decidir *no pierde*, pero no para separar de cero una ventaja
  del tamaño de la medida (1,76 a 2,30 M$). R = 8 quedó cerrado antes de correr y no se agregan réplicas.
- Los tiempos vienen de VMs `n2-highmem-8` distintas; T es la mediana entre réplicas.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto. El
  bootstrap de clientes de 201910 (tabla de arriba) muestra que el ruido del mes de test es mayor que el de las réplicas.

## Conclusión

Optimizar sobre una muestra del 5 %, 10 % o 25 % y entrenar con todas las filas no pierde contra el control, también
cuando se mide la suerte de Optuna con 8 réplicas, y acelera de 4,53 a 11,82 veces. La ventaja que mostraba la réplica 0
se achica a la mitad con réplicas y su IC contiene a 0: la regla da (B), aunque la suerte de la réplica 0 estaba más en H3 que en el control; no hay evidencia de que
la muestra regularice. El reescalado de `min_data_in_leaf` no cambia nada. Comparación con las otras hipótesis y a tiempo
igual: informe conjunto.
