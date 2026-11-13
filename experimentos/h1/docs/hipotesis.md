# Hipótesis — h1

Parte de Sampling_1 ([`sampling_1/docs/hipotesis.md`](../../sampling_1/docs/hipotesis.md)). El control, G, Δ, δ, T, A,
N* y los veredictos están en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y no se repiten. Escrito
antes de cualquier corrida real. Los cambios posteriores se anotan en `docs/bitacora.md`.

## H1 — Submuestreo uniforme del train

- **Variable**: tasa r de filas de 201903–201906 tomadas al azar sin distinguir clase, r ∈ {0,5, 0,25, 0,1, 0,05}.
  Optuna se corre de nuevo para cada tasa, sobre una muestra sorteada con la semilla 0 y con el mismo espacio que el
  control. El modelo final se entrena con la misma tasa, sobre una muestra que se vuelve a sortear con cada semilla
  final.
- **Métrica que decide**: el veredicto de cada tasa contra el control.
- **Predicción**: *no pierde* con r = 0,5 y 0,25; *pierde* con r = 0,05. Como predicciones secundarias, que no deciden:
  *pierde* con r = 0,1, y A ≥ 2 con r = 0,25. La predicción en 201908 tiene un costo fijo, por eso la aceleración no es
  4×.
- **Se confirma** si con r = 0,5 y 0,25 la variante *no pierde* y con r = 0,05 *pierde*: hay margen y después hay caída.
- **Se refuta** si con r = 0,5 la variante *pierde* (no hay margen) o si con r = 0,05 *no pierde* (no hay caída dentro de
  la grilla).
- **Ninguna de las dos** en cualquier otro caso, por ejemplo con r = 0,25 *indeterminado* o con r = 0,25 perdiendo
  mientras r = 0,5 no pierde. Se informa como frontera observada la menor r tal que esa tasa y todas las mayores *no
  pierden*.

## Réplicas de H1 (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Escrito el 13-nov-2026, antes de cualquier corrida de la fase 8, y revisado en sesión limpia antes de la primera. Lo de
arriba no se reescribe. Esta sección suma 8 réplicas de optimización a las cuatro tasas de H1 para que entren en la
grilla común (`sampling_1/docs/diseno.md` § Grilla común) con el mismo tratamiento que H3 y H4.

**Origen: se agrega después de ver 201910.** Las réplicas de `U*` se deciden después de ver en 201910 todas las celdas
vecinas (los `U*` de la réplica 0, `H3-*` y `H4O-0.5` con réplicas). Entran las cuatro tasas juntas, con predicción y
regla escritas acá antes de correr, y ninguna se elige ni se descarta por su resultado. El informe lo lista entre las
limitaciones ("Ideas que vienen de mirar el test").

- **Qué se corre.** Estudios `U{r}@k` y 20 semillas finales por réplica, k = 0…7, r ∈ {0,5; 0,25; 0,1; 0,05}. Los
  estudios `U0.25@k`, `U0.1@k` y `U0.05@k` ya existen (los corrió `h3`) y pasan a ser de `h1`; falta `U0.5@k`.
- **Qué se mide.** Ronda 201903–201908 ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda
  201903–201908): 20 semillas finales, N\* = 3.300 y δ = 0,02 · Ḡ_C de esa ronda (5,65 M$). Δ con réplicas e IC de
  Welch como en [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas de optimización. A con una sola
  referencia y T como mediana entre réplicas ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Medición
  de tiempos). El veredicto con réplicas reemplaza al de la réplica 0, como en H3; el de la réplica 0 se sigue
  informando.

### Predicción y regla

- **Predicción.** Con réplicas, `U0.5` *no pierde* y A ≥ 2; `U0.25`, `U0.1` y `U0.05` *pierden*.
- **Se confirma** si `U0.5` *no pierde* con A ≥ 2 y las otras tres *pierden*. **Se refuta** si `U0.5` *pierde* o si
  alguna de las otras tres *no pierde*. **Ninguna de las dos** en otro caso (alguna *indeterminado*, o `U0.5` *no
  pierde* con A < 2).
- **"Vale la pena".** Si `U0.5` sale *indeterminado* o con A < 2, deja la lista de variantes que valen la pena
  (`sampling_1/docs/hipotesis.md` § Respuesta a la pregunta del tutor) y se informa así.
- Las diferencias directas de `U{r}` con `H3-{r}` y con `H4O-{r}` están en
  [`h4/docs/hipotesis.md`](../../h4/docs/hipotesis.md) § Grilla común.
