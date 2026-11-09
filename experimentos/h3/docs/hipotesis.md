# Hipótesis — h3

Parte de Sampling_1 ([`sampling_1/docs/hipotesis.md`](../../sampling_1/docs/hipotesis.md)). El control, G, Δ, δ, T, A,
N* y los veredictos están en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y no se repiten. Escrito
antes de cualquier corrida real. Los cambios posteriores se anotan en `docs/bitacora.md`.

## H3 — Optimizar sobre una muestra, entrenar con todo

- **Variable**: tasa de la muestra uniforme sobre la que corre Optuna, r_opt ∈ {0,1, 0,25}. La muestra de optimización
  se sortea con la semilla 0. El modelo final se entrena con r = 1 y con los hiperparámetros tal como salen de la
  muestra, sin reescalar `min_data_in_leaf`.
- **Métrica que decide**: el veredicto de cada r_opt contra el control.
- **Predicción**: *no pierde* con ambas tasas. Como predicción secundaria, que no decide: A ≥ 2 con r_opt = 0,25 y
  A ≥ 4 con r_opt = 0,1.
- **Se confirma** si con r_opt = 0,25 *no pierde*.
- **Se refuta** si con r_opt = 0,25 *pierde*.
- **Ninguna de las dos** si con r_opt = 0,25 sale *indeterminado*.
- **Riesgo conocido**: el `min_data_in_leaf` que se elige sobre la muestra queda chico para el train completo. Si eso
  hace perder a r_opt = 0,1, el reescalado se propone como trabajo futuro y no como una variante nueva. (El 8-nov el
  reescalado entró como variante pre-registrada, `H3R-0.1`, en § H3 con réplicas.)

## H3 con réplicas de optimización (cambio `h3-semillas-optuna`, 8-nov-2026)

Escrito el 8-nov-2026, antes de cualquier corrida con réplicas, y revisado en sesión limpia antes de la primera. Lo de
arriba es la hipótesis de la réplica 0 y no cambia; su veredicto (las dos tasas *no pierden*) sigue siendo el de
entonces. Esta sección suma réplicas de la optimización para medir la suerte de Optuna, que el IC anterior no veía.

### Qué queda fijo

- **δ = 5,52 M$** (δ = 0,02 · Ḡ_C con Ḡ_C = 276,10 M$, la media del control en la réplica 0) y **N\* = 3.300** quedan
  fijos en estos valores: no se recalculan con las réplicas nuevas de `C`.
- **R = 8 réplicas** (k = 0…7) queda cerrado: no se agregan réplicas después de mirar resultados, aunque el IC quede
  ancho. El porqué de 8 está en [`docs/diseno.md`](diseno.md) § Grilla con réplicas.
- El espacio de Optuna, los 40 trials, las 10 semillas finales y los veredictos son los de
  [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md).

### Qué es una réplica y cómo se mide

- **Réplica k**: la semilla del sampler TPE y la del sorteo de la muestra de optimización valen k. La réplica 0 es la ya
  corrida. Las semillas finales son las 10 de siempre en todas las réplicas.
- **Ḡ_{v,k}**: media de G en las semillas finales de la variante v en la réplica k.
- **Δ con réplicas**: media_k Ḡ_{v,k} − media_k Ḡ_{C,k}, con IC 95% de Welch entre las réplicas de cada uno (sin
  aparear por k: la réplica k de `C` y la de H3 no comparten datos). El veredicto se toma de este Δ con las reglas
  comunes (*gana* / *no pierde* / *pierde* / *indeterminado*) y δ = 5,52 M$.
- **Descomposición de la varianza** de G de cada variante: var_entre(Ḡ_{v,k}) + media_k var_dentro, con la suma de
  cuadrados exacta. Se informa; no decide ningún veredicto.

### Predicciones y reglas

1. **H3 con réplicas** (`H3-0.1` y `H3-0.25`).
   - **Predicción**: las dos *no pierden* con réplicas: cota inferior del IC de Welch de Δ con réplicas ≥ −5,52 M$.
   - **Se confirma** la respuesta al tutor (el tradeoff vale la pena) si las dos cumplen esa regla.
   - **Se corrige** la conclusión del informe si alguna sale *pierde* (media de Δ con réplicas < −5,52 M$) o
     *indeterminado* (cota inferior < −5,52 M$ y media ≥ −5,52 M$).
2. **A contra B** (el mecanismo), sobre `H3-0.1`:
   - **Apoya (A), la muestra regulariza**: Δ con réplicas *gana* (cota inferior del IC de Welch > 0 M$) **y** la
     mediana de `feature_fraction` entre las 8 réplicas es menor en `H3-0.1` (estudios `U0.1`, `U0.1@k`) que en `C`
     (estudios `C`, `C@k`).
   - **Apoya (B), el control tuvo mala suerte**: el IC de Welch de Δ con réplicas contiene a 0 M$ (cota inferior ≤ 0 y
     cota superior ≥ 0) **y** Ḡ_{C,0} queda debajo de la mediana de las 8 Ḡ_{C,k}.
   - **Cualquier otro resultado**: "mecanismo sin resolver". La respuesta práctica sale de la regla 1.
3. **`H3-0.05`** (nueva: Optuna sobre la muestra del 5 %, estudios `U0.05` / `U0.05@k`, final con r = 1).
   - **Predicción**: *no pierde* con réplicas (cota inferior del IC de Welch de Δ con réplicas ≥ −5,52 M$) **y** A ≥ 8,
     con A = T(`C`) / T(`H3-0.05`) y la T de cada una como mediana entre sus 8 réplicas.
   - **Se confirma** si se cumplen las dos condiciones; **se refuta** si sale *pierde* (media de Δ con réplicas
     < −5,52 M$) o A < 8; si no, *indeterminado*.
4. **`H3R-0.1`** (nueva: los estudios de `H3-0.1` con `min_data_in_leaf` × √(1/r) = × √10 en el final, recortado a
   [1; 8000]). Se mide la diferencia D = G(`H3R-0.1`) − G(`H3-0.1`), apareada por semilla dentro de cada réplica (80
   pares); se toma la media de D por réplica y el IC t 95% entre las 8 réplicas (7 g.l.).
   - **Mejora** si la cota inferior del IC de D es > 0 M$.
   - **Empeora** si la cota superior del IC de D es < 0 M$.
   - **No cambia** en cualquier otro caso.
   - **Predicción**: *mejora* (el riesgo conocido de § H3: el `min_data_in_leaf` de la muestra queda chico para el
     train completo). Además, `H3R-0.1` recibe su propio veredicto con réplicas contra `C`, con la regla 1.

### Limitaciones previstas de las réplicas

- Si el desvío entre réplicas es mayor que el previsto (unos 4 M$), el IC de Welch queda ancho y H3 puede salir
  *indeterminado*. Eso también es un resultado: la ventaja de H3 no se distingue de la suerte de Optuna.
- Los tiempos vienen de VMs `n2-highmem-8` distintas; por eso T es la mediana entre réplicas.

## Limitaciones previstas

- H1 y H3 comparten el estudio de Optuna en r = 0,25 y 0,1 (`docs/diseno.md` § Estudios compartidos), así que
  Δ(U0.25) y Δ(H3-0.25) tienen la misma suerte de optimización y no son evidencia independiente entre sí.
- `H3R-0.1` y `H3-0.1` comparten todos sus estudios; su diferencia aísla el reescalado y no es evidencia independiente
  sobre H3.
