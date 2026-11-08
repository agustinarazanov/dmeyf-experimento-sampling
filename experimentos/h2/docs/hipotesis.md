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
