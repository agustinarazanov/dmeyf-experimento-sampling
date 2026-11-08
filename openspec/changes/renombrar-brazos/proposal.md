# Proposal

## Why

"Brazo" (de *arm*, en ensayos clínicos) no se entiende sin explicarlo, y el informe y el video se los contamos a gente que
no lo usa: el tutor, el resto de la comisión y los dos integrantes que sumaron trabajo esta semana. Luis, en su script,
ya dice "estrategia". Antes de sumar las corridas de `h3-semillas-optuna`, los aportes de `incorporar-aportes` y la
comparación limpia de todos los resultados, queremos **un solo nombre en todo el repo, sin excepciones**.

Elegimos **variante** ("la variante H3-0.1"): es neutro y no choca con nada. Martín usa "configuración" para un juego
de hiperparámetros, así que esa opción queda descartada. También reescribimos el README, que hoy describe el repo y no
lo que encontramos.

## What Changes

- **BREAKING** `comun/brazos.py` pasa a `comun/variantes.py`, con `Variante`, `VARIANTES`, `variante()` y
  `dueno_variante()`. `python -m comun.brazos --verificar` pasa a `python -m comun.variantes --verificar`.
- **BREAKING** La columna `brazo` pasa a `variante` en todos los ledgers del repo y del bucket:
  - `resultados.csv`, `reemplazadas.csv`, `apareado.csv`, `apareado_previo.csv`, `estudios.csv` y `corridas/*.csv`;
  - la clave `brazo` de `hp/*.json`.

  Se reescribe solo la cabecera o la clave: los valores, los `id` y el orden de las filas no cambian. No queda alias de
  lectura, así que un ledger con `brazo` hace fallar la consolidación con un mensaje que lo nombra.
- **"Variante" en todo el repo, histórico incluido:**
  - código, tests y scripts (`separar_ledger.py` incluido);
  - `CLAUDE.md`, `docs/`, `plantilla/`, el README de cada experimento, sus `docs/` (bitácoras incluidas) e `informe/`,
    y los `reporte.html` regenerados;
  - `ledger/sesiones/`;
  - los cambios archivados en `openspec/changes/archive/`;
  - las specs vigentes;
  - el paquete de Martín, `h3/sensibilidad_muestra/`: código, README, `referencia/grilla_06.json` y su generador. Las
    huellas que dependan de esos archivos se recalculan.

  Lo único que sigue diciendo "brazo" es lo que tiene que nombrarlo para que el renombre se haga y se sostenga:
  - la historia de git y el tag `corridas-v1`, que no se reescriben;
  - los artefactos de este cambio, también una vez archivado;
  - `scripts/renombrar_columna.py`;
  - el rechazo de la columna vieja en `comun/ledger.py`, su test y su requisito en la spec;
  - la entrada de cada bitácora que registra el renombre.
- **Ningún número cambia**, y eso se comprueba contra una foto previa de cada `apareado.csv` y de cada tabla de
  resultados.
- **README de la raíz, reescrito**, con los números copiados de `sampling_1/informe/informe.md`:
  - qué preguntamos y qué encontramos hasta ahora: la tabla por variante y la respuesta corta al tutor;
  - el mapa de experimentos;
  - los aportes de Martín y de Luis y su estado: el de Luis se incorpora en `incorporar-aportes`;
  - qué sigue;
  - cómo correr.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `protocolo-experimental`: el registro y las hipótesis hablan de variantes.
- `ledger-resultados`: la clave de consolidación y la columna pasan a `variante`; las curvas son por variante; un ledger
  con la columna vieja se rechaza.
- `corrida-reproducible`: la fila va al ledger del dueño de la variante.
- `dependencias-entre-experimentos`: el registro es de variantes y estudios.
- `reporte-visual`: la comparación es de todas las variantes.

## Impact

- `comun/` (anunciar en el commit):
  - `brazos.py` → `variantes.py`;
  - `correr.py`, `consolidar.py`, `ledger.py`, `metodos.py`, `reporte.py`;
  - `scripts/`, `sampling_1/scripts/`, tests.
- Todos los ledgers del repo, sus copias en el bucket y todo el texto del repo.
- `h3/sensibilidad_muestra/`: renombre del campo de sus archivos de corrida. Las corridas 07 y 08 que Martín hizo
  antes del renombre dejan de leerse con el código nuevo, pero `incorporar-aportes` las vuelve a correr.
- Fuera de alcance:
  - corridas nuevas y cambios de resultados;
  - mover o portar el aporte de Luis, que es de `incorporar-aportes`;
  - la comparación nueva, que es de `h3-semillas-optuna`.
