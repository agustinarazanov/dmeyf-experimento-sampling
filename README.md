# Sampling_1 — velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026 (comisión lunes): ¿vale la pena el tradeoff entre velocidad y pérdida de performance al
entrenar u optimizar con menos filas? Un experimento por carpeta en `experimentos/`.

## Experimentos

| experimento | qué es | pregunta | estado |
|---|---|---|---|
| [`control`](experimentos/control/) | el control `C` (y su réplica `C-rep`) y las reglas comunes (G, Δ, δ, T, A, N\*, veredictos) | ¿cuál es el punto de comparación de todas las hipótesis? | informe |
| [`h1`](experimentos/h1/) | submuestreo uniforme del train | ¿cuánto se gana en tiempo y se pierde en ganancia con r ∈ {0,5, 0,25, 0,1, 0,05}? | informe |
| [`h2`](experimentos/h2/) | bagging y GOSS | ¿alcanza con submuestrear dentro de LightGBM? | informe |
| [`h3`](experimentos/h3/) | optimizar con muestra y entrenar completo | ¿se puede optimizar rápido y entrenar con todo? (reusa los estudios de `h1`) | informe |
| [`sampling_1`](experimentos/sampling_1/) | el experimento conjunto: compara a `h1`–`h3` contra `control`, informe y video | ¿vale la pena el tradeoff velocidad-performance? | informe |

Para agregar una hipótesis (`h4`, …): `docs/metodo.md` § Agregar una hipótesis. Cada experimento declara en
`## Dependencias` de su `docs/diseno.md` de quién lee (`control` como mínimo) y no toca carpetas ni ledgers ajenos.
El método de trabajo está en `docs/metodo.md`. Los experimentos de `sampling_1` antes del renombre (`sampling-velocidad`)
están en `experimentos/sampling_1/README.md` § Correspondencia de rutas.

## Estructura

- `comun/`: datos (panel con lags y deltas), baseline, ganancia, ledger, registro de brazos (`brazos.py`), muestreo,
  métodos, `correr.py`, `consolidar.py`, `reporte.py` y registro de tokens. Lo usan todos los experimentos; un cambio
  acá se anuncia en el commit.
- `experimentos/<nombre>/`: `docs/` (hipótesis, diseño, bitácora), `ledger/` e `informe/`; `sampling_1` además tiene
  `src/` y `scripts/` propios (fases de las VMs).
- `plantilla/`: la estructura vacía de un experimento.
- `docs/`: `metodo.md` y `revision.md`, compartidos.
- `scripts/`: `vm.sh`, `etapa.sh`, `etapas.sh` y `separar_ledger.py`, para cualquier experimento o cambio.
- `openspec/`: planes de cambio (proposal, specs, design, tasks).

Los datos no están en el repo. Viven en `DATOS_DIR` (por defecto `~/datos/experimentos-dmeyf`).

## Correr en la Mac (smoke test)

Necesita Python 3.14 (pyenv `facultad`) y `libomp` para LightGBM. Todo se corre desde la **raíz del repo**:

```bash
brew install libomp
pip install -r requirements.txt
python -m comun.datos --filas 20000
python -m comun.correr --metodo uniforme --tasa 0.25 --semilla 100003 --etapa optimizar --filas 20000
python -m comun.consolidar --experimento h1       # o sin argumento, para todos
python -m comun.reporte --experimento h1          # o --todos
python -m comun.brazos --verificar                # dependencias, ciclos y qué se rompe si falta una carpeta
python -m pytest
```

`comun.correr` escribe la fila en el ledger del dueño del brazo (`comun/brazos.py`) y lee y escribe los hiperparámetros
en el del dueño del estudio. Las corridas en la Mac son exploratorias (`etapa = exploracion`) y no entran en los
resultados.

## Correr en la VM

Todas las corridas que cuentan van en `n2-highmem-8` spot, desde el template del curso, con el commit del tag
`corridas-v1`:

```bash
scripts/vm.sh <lista-de-configuraciones>
```

`vm.sh` crea la VM, copia el repo, instala dependencias, lanza las corridas con `nohup`, sube los `ledger/` de cada
experimento al bucket y borra la VM. El reparto por persona está en `experimentos/sampling_1/docs/diseno.md` § Reparto y
fases, y la operación paso a paso en `experimentos/sampling_1/docs/operacion.md`.
