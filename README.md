# Sampling_1 — velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026 (comisión lunes): ¿vale la pena el tradeoff entre velocidad y pérdida de performance al
entrenar u optimizar con menos filas? Un experimento por carpeta en `experimentos/`.

## Experimentos

| experimento | pregunta | estado |
|---|---|---|
| [`sampling-velocidad`](experimentos/sampling-velocidad/) | ¿Cuánto tiempo se ahorra y cuánta ganancia se pierde al entrenar u optimizar con menos filas, sin tocar la proporción de clases? | diseño |

Para agregar uno: copiar `plantilla/` a `experimentos/<nombre>/`, completar `docs/hipotesis.md`, abrir la bitácora y
sumarlo a esta tabla. Cada experimento depende solo de `comun/` y de su carpeta. El método de trabajo está en
`docs/metodo.md`.

## Estructura

- `comun/`: datos (panel con lags y deltas), baseline, ganancia, ledger y registro de tokens. Lo usan todos los
  experimentos; un cambio acá se anuncia en el commit.
- `experimentos/<nombre>/`: `docs/` (hipótesis, diseño, bitácora, Zulip), `src/`, `scripts/`, `ledger/` e `informe/`.
- `plantilla/`: la estructura vacía de un experimento.
- `docs/`: `metodo.md` y `revision.md`, compartidos.
- `openspec/`: planes de cambio (proposal, specs, design, tasks).

Los datos no están en el repo. Viven en `DATOS_DIR` (por defecto `~/datos/experimentos-dmeyf`).

## Correr en la Mac (smoke test)

Necesita Python 3.14 (pyenv `facultad`) y `libomp` para LightGBM. Los comandos se corren desde la carpeta del
experimento, con la raíz del repo en `PYTHONPATH`:

```bash
brew install libomp
pip install -r requirements.txt
cd experimentos/sampling-velocidad
export PYTHONPATH=../..
python -m comun.datos --filas 20000
python -m src.correr --metodo uniforme --tasa 0.25 --semilla 100003 --etapa optimizar --filas 20000
```

Las corridas en la Mac son exploratorias (`etapa = exploracion`) y no entran en los resultados.

## Correr en la VM

Todas las corridas que cuentan van en `n2-highmem-8` spot, desde el template del curso, con el commit del tag
`corridas-v1`:

```bash
experimentos/sampling-velocidad/scripts/vm.sh <lista-de-configuraciones>
```

`vm.sh` crea la VM, copia el repo, instala dependencias, lanza las corridas con `nohup`, sube `ledger/corridas/` y
borra la VM. El reparto por persona está en `docs/diseno.md` § Reparto y fases del experimento, y la operación paso a
paso en su `docs/operacion.md`.
