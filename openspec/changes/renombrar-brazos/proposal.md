# Proposal

## Why

"Brazo" (de *arm*, en ensayos clínicos) no se entiende sin explicarlo, y el informe y el video se los contamos a gente que
no lo usa: el tutor, el resto de la comisión y los dos integrantes que sumaron trabajo esta semana (Martín con
`h3/sensibilidad_muestra`, Luis con su script de 50 semillas, que ya dice "estrategia"). Antes de sumar las corridas de
`h3-semillas-optuna` y la comparación limpia de todos los resultados conviene tener un solo nombre, claro, en todo el repo.
Elegimos **variante** ("la variante H3-0.1"): es neutro y no choca con nada (Martín usa "configuración" para un juego de
hiperparámetros, así que esa queda descartada). También aprovechamos el cambio para reescribir el README, que hoy
describe el repo y no lo que encontramos, y para ordenar el aporte de Luis, que quedó en una carpeta con espacios fuera
del método.

## What Changes

- **BREAKING** `comun/brazos.py` pasa a `comun/variantes.py` (`Variante`, `VARIANTES`, `variante()`, `dueno_variante()`),
  y `python -m comun.brazos --verificar` pasa a `python -m comun.variantes --verificar`. No queda un módulo `brazos` de
  compatibilidad.
- **BREAKING** La columna `brazo` de los ledgers (`resultados.csv`, `reemplazadas.csv`, `apareado.csv`, `estudios.csv`,
  `corridas/*.csv`) y la clave `brazo` de `hp/*.json` pasan a `variante`. Se reescribe solo la cabecera o la clave: los
  valores, los `id` y el orden de las filas no cambian. `comun/ledger.py` acepta todavía `brazo` al leer (el bucket y el tag
  `corridas-v1` lo tienen) y lo traduce.
- Código, tests, docs (`docs/metodo.md`, `docs/revision.md`, `plantilla/`, `CLAUDE.md`), los `docs/` e `informe/` de
  cada experimento y los `reporte.html` regenerados dicen "variante". Los números de los informes y reportes no cambian.
- Lo histórico no se toca: bitácoras (se suma una entrada que anota el renombre), `ledger/sesiones/`, cambios archivados
  de `openspec/` y los archivos con huella de Martín (`h3/sensibilidad_muestra/referencia/` y `resultados/`, que tienen
  sha256 en `procedencia.json`), y `sampling_1/ledger/apareado_previo.csv`, que es la foto de antes de separar las
  hipótesis.
- El aporte de Luis pasa de `experimentos/Experimentos h3 y h4/` a
  `experimentos/sampling_1/exploratorios/validacion_50_semillas/`, con el nombre de archivo corregido
  (`validacion_50_semillas.py`) y un `README.md` que dice qué protocolo usa y en qué se aparta del nuestro. Su contenido
  no cambia.
- El `README.md` de la raíz se reescribe: qué preguntamos, qué encontramos hasta ahora (tabla de resultados por
  variante y la respuesta corta al tutor), el mapa de experimentos, los estudios exploratorios (Martín, Luis) con su
  advertencia, qué sigue (`h3-semillas-optuna`, H4) y cómo correr. Los números salen de `sampling_1/informe/informe.md`,
  no se recalculan.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `protocolo-experimental`: el registro y las hipótesis hablan de variantes.
- `ledger-resultados`: la clave de consolidación y la columna pasan a `variante`; las curvas son por variante.
- `corrida-reproducible`: la fila va al ledger del dueño de la variante.
- `dependencias-entre-experimentos`: el registro es de variantes y estudios.
- `reporte-visual`: la comparación es de todas las variantes.

## Impact

- `comun/` (anunciar en el commit): `brazos.py` → `variantes.py`, `correr.py`, `consolidar.py`, `ledger.py`,
  `metodos.py`, `reporte.py`; `scripts/vm.sh`, `scripts/separar_ledger.py`, `sampling_1/scripts/*.py`; tests.
- Ledgers de `control`, `h1`, `h2`, `h3` y `sampling_1`: cabeceras y claves. El bucket se resincroniza en la próxima
  corrida; mientras tanto el alias de lectura lo cubre.
- Fuera de alcance: corridas nuevas, cambios de resultados, la comparación nueva (es de `h3-semillas-optuna`) y el código
  de Martín, que usa `brazo` como campo de sus propios archivos de corrida (cambiarlo le rompe la lectura de la corrida
  07 que ya hizo).
