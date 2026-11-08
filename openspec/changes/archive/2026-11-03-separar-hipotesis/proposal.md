# Proposal

## Why

Hoy las tres hipótesis de Sampling_1 viven juntas en `experimentos/sampling-velocidad/`: un `hipotesis.md`, un ledger y
un informe para todas las variantes. Para leer, revisar o presentar una hipótesis hay que separarla a mano del resto, y una
hipótesis nueva (H4 de un integrante, o las que vengan) no tiene dónde caer sin tocar la carpeta de otro. Queremos una
carpeta y un informe por hipótesis, más un informe conjunto que las compare. Para eso tiene que quedar escrito qué
comparten: el control, los estudios de Optuna que H3 toma de H1 y el corredor.

## What Changes

- **BREAKING** `experimentos/sampling-velocidad/` se reparte en cinco carpetas hermanas:
  - `experimentos/control/`: variantes `C` y `C-rep`, su estudio y sus 10 finales, más las reglas comunes (G, Δ, δ, T, A,
    N*, veredictos).
  - `experimentos/h1/`: `U0.5`, `U0.25`, `U0.1`, `U0.05`. Es dueña de los estudios `U*`.
  - `experimentos/h2/`: `B0.5`, `B0.25`, `B0.1` y `GOSS`.
  - `experimentos/h3/`: `H3-0.25` y `H3-0.1`. Lee los estudios `U0.25` y `U0.1` de `h1`.
  - `experimentos/sampling_1/`: la carpeta actual renombrada con `git mv`. Guarda la comparación entre hipótesis (curva
    tiempo-ganancia, tiempo igual, "vale la pena"), la pregunta, la respuesta al tutor, el guion del video, la bitácora,
    el registro de tokens, las sesiones y la exploración.
- **BREAKING** Un experimento puede depender de otros siempre que lo declare y que no haya ciclos. Se reemplaza la regla
  de "solo `comun/` y su carpeta".
- **BREAKING** El corredor, los métodos, el muestreo, la consolidación y el generador de reportes pasan a `comun/`, junto
  con un registro único que dice a qué experimento pertenece cada variante y cada estudio. La corrida escribe en el ledger
  del experimento dueño de la variante.
- Cada `hN/` y `control/` tiene su `docs/hipotesis.md`, su `docs/diseno.md`, su `ledger/` (filas filtradas del ledger
  actual por `variante`), su `informe/informe.md` y su `informe/reporte.html` generado.
- Los scripts de VM (`vm.sh`, `lanzar_fase.sh`) pasan a `scripts/`, en la raíz, y sincronizan el ledger de cada
  experimento por separado.
- No cambia ningún resultado: no hay corridas nuevas, y los números de cada informe salen iguales a los del informe
  actual.

## Capabilities

### New Capabilities
- `dependencias-entre-experimentos`: cómo un experimento declara de qué otros depende (control, estudios ajenos), cómo
  los lee sin copiarlos y qué pasa al borrar uno.

### Modified Capabilities
- `protocolo-experimental`: "Un experimento, una carpeta" deja de exigir independencia total; el control pasa a ser un
  experimento propio.
- `corrida-reproducible`: el punto de entrada único pasa a `comun/` y escribe en el ledger del dueño de la variante; el
  control vive en `experimentos/control/`.
- `ledger-resultados`: la tabla apareada de cada experimento se arma contra el ledger de `control`.
- `reporte-visual`: un reporte por experimento (su hipótesis, sus variantes contra el control) más el reporte conjunto con
  la comparación entre todas las variantes y a tiempo igual.
- `registro-tokens`: las sesiones previas quedan en `sampling_1`; las nuevas se registran en el experimento de la etapa.

## Impact

- Código: `experimentos/sampling-velocidad/src/*` pasa a `comun/`; `comun/tokens.py` (default `--experimento`);
  `scripts/etapa.sh` y `scripts/etapas.sh` (defaults); `tests/test_consolidar.py` (ruta de import).
- Datos: `ledger/predicciones/` (241 MB, fuera de git) se reparte en disco y en el bucket con el mismo filtro.
- Documentos: `README.md`, `CLAUDE.md`, `docs/metodo.md` y `plantilla/` (sección de dependencias).
- Lo histórico no se reescribe: el cambio archivado, los tags y los commits siguen nombrando `sampling-velocidad`. En
  `sampling_1/` queda una nota con la correspondencia de rutas.
