# Proposal

## Why

H3 es el único resultado positivo de Sampling_1. Optimizar sobre el 10% de las filas y entrenar con todas da
Δ = +4,07 M$ (IC [−0,27; 8,41]) con 8,4 veces menos tiempo. Pero cada variante corrió **una sola optimización de
Optuna**, y el informe ya lo marca como la limitación principal. Esta semana llegaron dos aportes que hacen que esa
limitación pese más:

- **Martín** (`h3/sensibilidad_muestra`) repitió la búsqueda de H3 con 10 muestras distintas. Solo por la muestra, la
  ganancia del modelo elegido va de −9,9 a +8,8 M$ respecto del control, un rango mayor que nuestro Δ. Además, en 7 de
  10 muestras eligió la misma configuración que el control.
- **Luis** (`experimentos/Experimentos h3 y h4/`, que `incorporar-aportes` porta al repo) corrió 50 semillas finales
  y concluye que todas las H3 "le ganan" al control. Sin embargo, sus 50 semillas varían solo la semilla final con
  hiperparámetros fijos: el intervalo no incluye la suerte de Optuna. Además eligió variantes mirando 201910.

Hay dos explicaciones de la ventaja de H3 que hoy no podemos separar:

- **(A)** La muestra chica empuja a Optuna a hiperparámetros más regularizados (`feature_fraction` 0,18–0,34 contra
  0,985 del control), y eso generaliza mejor.
- **(B)** La única optimización del control cayó en una configuración mala, y H3 parece mejor por eso.

Contestarlo es la respuesta honesta a la pregunta del tutor, y es barato: unas 5,6 horas de VM, que corremos nosotros en VMs paralelas.
También queremos terminar con **una comparación limpia de todos los resultados**, con los exploratorios a la vista pero
separados de lo que se corrió con el protocolo.

## What Changes

- **Réplicas de optimización.** El corredor acepta `--replica k`:
  - la réplica k usa k como semilla del sampler TPE y del sorteo de la muestra;
  - k = 0 es lo que ya existe, sin cambios;
  - los estudios de las réplicas k ≥ 1 se llaman `<estudio>@k`.
- **Grilla nueva**, con 8 réplicas (k = 0…7) y 10 semillas finales por réplica, sobre cinco variantes:
  - `C`;
  - `H3-0.25`, `H3-0.1`;
  - `H3-0.05` (nueva);
  - `H3R-0.1` (nueva): los estudios de `H3-0.1` con `min_data_in_leaf` × √(1/r) en el final, pre-registrada.

  Lo ya corrido es la réplica 0 de `C`, `H3-0.25` y `H3-0.1`.
- **Hipótesis escritas antes de correr.** Antes de la primera corrida, `h3/docs/hipotesis.md` suma predicciones y
  reglas para separar A de B, y para `H3-0.05` y `H3R-0.1`. δ y N\* quedan fijos en los valores actuales.
- **Análisis.**
  - Δ con réplicas: diferencia de medias entre réplicas, con IC de Welch.
  - Descomposición de la varianza: entre réplicas contra entre semillas finales.
  - Comparación a tiempo igual por réplica, con IC entre réplicas, y bootstrap de clientes de 201910 como segunda fuente
    de ruido.
- **Comparación limpia en `sampling_1/informe/reporte.html` e `informe.md`**, en dos bloques:
  - **A. Mismo protocolo:** todas las variantes del registro, con Δ, Δ con réplicas cuando existe, A, tiempo igual con
    intervalo y veredicto.
  - **B. Exploratorios:** cada estudio exploratorio con su protocolo y su advertencia, leído de sus CSV mediante un
    manifiesto. No hay números escritos a mano. Este cambio suma el de Martín, e `incorporar-aportes` suma el de Luis.
- **Estudios exploratorios como figura del método.** Son una carpeta con `README.md` y `exploratorio.json`, no entran
  al registro de variantes y no cambian veredictos. Este cambio agrega el manifiesto de Martín.
- **Informes.** `h3/informe/informe.md` y `sampling_1/informe/informe.md` se actualizan con el veredicto con réplicas
  y la respuesta A/B. El README apunta a la comparación nueva.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `corrida-reproducible`: réplicas de optimización (`--replica k`), con estudios y semillas definidos.
- `ledger-resultados`: la clave suma `replica_opt`. Diferencia con réplicas y descomposición de varianza.
- `reporte-visual`: comparación en dos bloques, tiempo igual con intervalo, estudios exploratorios desde manifiesto.
- `protocolo-experimental`: estudios exploratorios declarados, separados de la evidencia.

## Impact

- `comun/` (anunciar en el commit):
  - `correr.py`: `--replica`;
  - `variantes.py`: `H3-0.05`, `H3R-0.1` y los estudios `@k`;
  - `metodos.py`: el reescalado;
  - `ledger.py` y `consolidar.py`: la columna y la clave;
  - `reporte.py`: los bloques A y B y el tiempo igual con IC.
- Ledgers: estudios `C@k` en `control`, estudios `U{r}@k` y finales en `h3`. `h1` no cambia.
- Cómputo: ~2 h de Optuna y ~3,6 h de finales en `n2-highmem-8` spot. Agustina lanza todas las VMs en paralelo, una por
  réplica: con la cuota de 200 vCPU N2 en `us-central1` entran 7 a la vez, y el total de pared queda en ~50 min.
- Depende de `renombrar-brazos` archivado: usa "variante" y los nombres nuevos de los requisitos.
- Fuera de alcance:
  - H4 (hard negatives, fast-retrain) y el resto de los aportes de Luis y Martín, que son de `incorporar-aportes`;
  - réplicas para `U*`, `B*` y `GOSS`, que ya pierden o no aceleran;
  - meses de test fuera de 201910.
