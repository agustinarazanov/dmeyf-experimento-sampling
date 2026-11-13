# Hipótesis — h2

Parte de Sampling_1 ([`sampling_1/docs/hipotesis.md`](../../sampling_1/docs/hipotesis.md)). El control, G, Δ, δ, T, A,
N* y los veredictos están en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y no se repiten. Escrito
antes de cualquier corrida real. Los cambios posteriores se anotan en `docs/bitacora.md`.

## H2 — Muestrear dentro de LightGBM

- **Variable**: `bagging_fraction` fijo en f ∈ {0,5, 0,25, 0,1}, con `bagging_freq = 1`. Cada árbol ve una fracción f
  distinta de las filas, pero el modelo usa todas.
- **Adaptación declarada del baseline**: en estas variantes `bagging_fraction` es la variable experimental, así que sale
  del espacio de Optuna; los otros cuatro hiperparámetros se siguen optimizando con los mismos rangos.
- **Métrica que decide**: el veredicto de cada f contra el control.
- **Predicción**: *no pierde* con las tres fracciones, también con f = 0,1, donde H1 predice que el muestreo previo
  pierde. Como predicción secundaria, que no decide: A ≥ 1,5 con f = 0,1, porque el `Dataset` completo se construye
  igual.
- **Se confirma** si con f = 0,1 *no pierde*.
- **Se refuta** si con f = 0,1 *pierde*.
- **Ninguna de las dos** si con f = 0,1 sale *indeterminado*.
- **Lectura conjunta con H1, descriptiva**: en la curva tiempo-ganancia de todas las variantes se mira si los puntos de
  `bagging` quedan por encima de los de `uniforme` al mismo tiempo. No es una prueba, porque `uniforme` sigue
  optimizando `bagging_fraction` y no tiene la misma fracción efectiva por iteración.
- **Variante descriptiva `goss`** (`top_rate = 0,2`, `other_rate = 0,1`, sin bagging porque LightGBM no lo admite): se
  reporta su veredicto contra el control, pero no decide H2. A partir de la iteración 1/`learning_rate` usa un 30% de
  filas por iteración; antes no muestrea. También cambia la mezcla de clases de cada árbol, porque se queda con los
  casos de gradiente alto.

## Limitaciones previstas

- `goss` cambia la mezcla de clases por iteración y queda fuera de la evidencia. Además, si Optuna elige
  `learning_rate` cerca de 0,01, las 100 iteraciones caen antes de 1/`learning_rate` y GOSS nunca muestrea; se
  informa el `learning_rate` elegido.

## Réplicas de H2 y `B0.05` (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Escrito el 13-nov-2026, antes de cualquier corrida de la fase 8, y revisado en sesión limpia antes de la primera. Lo de
arriba no se reescribe. Esta sección suma 8 réplicas de optimización a `B0.5`, `B0.25`, `B0.1` y `GOSS`, y una fracción
nueva, `B0.05`, para que H2 tenga las cuatro tasas de la grilla común (`sampling_1/docs/diseno.md` § Grilla común).

**Origen: se agrega después de ver 201910.** Las réplicas y `B0.05` se deciden después de ver en 201910 todas las celdas
vecinas. Entran todas juntas, con predicción y regla escritas acá antes de correr, y ninguna se elige ni se descarta por
su resultado. El informe lo lista entre las limitaciones ("Ideas que vienen de mirar el test").

- **Qué se corre.** `B0.05`: `bagging_fraction` fijo en 0,05 con `bagging_freq = 1`, fuera del espacio de Optuna como
  las otras `B`. Estudios `B{f}@k` y `GOSS@k` y 20 semillas finales por réplica, k = 0…7 (k = 0 solo falta para
  `B0.05`).
- **Qué se mide.** Ronda 201903–201908 ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda
  201903–201908): 20 semillas finales, N\* = 3.300 y δ = 0,02 · Ḡ_C de esa ronda (5,65 M$). Δ con réplicas e IC de
  Welch como en [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas de optimización. A con una sola
  referencia y T como mediana entre réplicas ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Medición
  de tiempos). El veredicto con réplicas reemplaza al de la réplica 0; el de la réplica 0 se sigue informando.

### Predicción y regla

- **Predicción.** Con réplicas, `B0.5` y `B0.25` *no pierden* con A < 2; `B0.1` y `B0.05` *pierden*. O sea, ninguna `B`
  vale la pena (*no pierde* y A ≥ 2). Con la regla de A de una sola referencia, en la réplica 0 `B0.1` ya tiene A = 2,31
  y `B0.25`, 1,54.
- **Se confirma** si se cumplen las cuatro partes. **Se refuta** si alguna `B` vale la pena, o si `B0.5` o `B0.25`
  *pierde*. **Ninguna de las dos** en otro caso (alguna *indeterminado*, o `B0.1` o `B0.05` *no pierde* con A < 2).
- La regla de H2 de arriba (sobre `B0.1`) se vuelve a decidir con el Δ con réplicas y se informa al lado del veredicto de
  la réplica 0.
- **`GOSS`** recibe réplicas y se informa sin regla, como hasta ahora.
- **H2 no entra en los pares directos** de la grilla común: `bagging_fraction` sale del espacio de Optuna en las `B`, así
  que la comparación con `U*` sigue siendo descriptiva (§ H2, lectura conjunta con H1). La tabla de cobertura la muestra
  al lado.
