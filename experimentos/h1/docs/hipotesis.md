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
