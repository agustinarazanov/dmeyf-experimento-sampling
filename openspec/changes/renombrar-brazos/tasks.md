# Tasks

## 1. Foto previa (sesión: Sonnet)

- [x] 1.1 Guardar la foto de D6 en `DATOS_DIR/renombre/antes/` (consolidar, reporte `--todos`, cada `apareado.csv` y la tabla de resultados de cada `reporte.html` extraída a CSV) y bajar el bucket a `DATOS_DIR/renombre/bucket/`; verificar que hay un archivo por experimento y que `git status` sigue limpio salvo la fecha de los reportes
- [x] 1.2 Comprobar que `comun/tokens.py` no lee "brazo" del contenido de `ledger/sesiones/`; verificar regenerando `tokens.csv` en una copia con "brazo" reemplazado y comparando con el original (sin diferencias)
- [x] 1.3 Revisión en sesión limpia del grupo 1 con la lista de código de `docs/revision.md` y cierre en `sampling_1/docs/bitacora.md`

## 2. Ledgers y código (sesión: Sonnet)

- [x] 2.1 Escribir `scripts/renombrar_columna.py` con `--verificar` (D2) y correrlo sobre todos los `experimentos/*/ledger/` (incluido `apareado_previo.csv`) y sobre la copia del bucket; commit solo con las cabeceras; verificar que `--verificar` sale con 0 y que `git diff --numstat` da una línea cambiada por CSV
- [x] 2.2 `git mv comun/brazos.py comun/variantes.py` y `tests/test_brazos.py tests/test_variantes.py`; renombrar según D1 en `comun/`, `scripts/`, `sampling_1/scripts/` y `tests/`; en `comun/ledger.py`, rechazar una cabecera `brazo` nombrando el archivo, con test; verificar que `python -m pytest` pasa
- [x] 2.3 Renombrar el paquete de Martín según D4 y recalcular las huellas que dependan de archivos modificados; verificar que sus 13 tests pasan y que `python -m experimentos.h3.sensibilidad_muestra.busqueda` (o el generador que use 07) produce un JSON idéntico a `referencia/grilla_06.json`
- [x] 2.4 Smoke test en la Mac: una optimización de `U0.25` y un final de `H3-0.25` con `--filas 20000`; verificar que las filas tienen columna `variante` y que `python -m comun.variantes --verificar` pasa
- [x] 2.5 Subir el bucket renombrado con `gsutil rsync`, volver a bajarlo y correr `scripts/renombrar_columna.py --verificar` sobre esa copia; verificar que sale con 0
- [ ] 2.6 Revisión en sesión limpia del grupo 2 con la lista de código de `docs/revision.md` y cierre en `sampling_1/docs/bitacora.md`

## 3. Texto y specs (sesión: Sonnet)

- [ ] 3.1 Reemplazo de D3 en todo `git ls-files` (bitácoras, `ledger/sesiones/`, `openspec/changes/archive/`, docs, informes, README de cada experimento, `CLAUDE.md`, `plantilla/`); corregir a mano lo que marquen los grep de concordancia; verificar que `git grep -n -i brazo | grep -v renombrar-brazos` solo devuelve líneas de los archivos de D8 y que los grep de concordancia no dan resultados
- [ ] 3.2 Regenerar con `python -m comun.consolidar` y `python -m comun.reporte --todos` y comparar con la foto de 1.1; verificar que los valores de cada `apareado.csv` y de cada tabla coinciden (diferencia 0), que el diff de cada `reporte.html` solo tiene "variante" y la fecha, y que `git diff --word-diff` de los `informe.md` no toca números
- [ ] 3.3 Anotar el renombre (fecha, commits, que la historia de git y `corridas-v1` siguen con "brazo", que un clon viejo no consolida) en la bitácora de cada experimento

## 4. README (sesión: Opus)

- [ ] 4.1 Reescribir `README.md` con las secciones de D7; los números se copian de `sampling_1/informe/informe.md` citando la fuente; verificar con un script que cada Δ, IC y A del README coincide con `informe.md` y que todos los enlaces relativos existen
- [ ] 4.2 Revisión en sesión limpia de los grupos 3 y 4 con la lista de informe de `docs/revision.md` (incluye leer el README como alguien que no conoce el repo) y cierre en `sampling_1/docs/bitacora.md`; correr `comun/tokens.py`

## Workflow follow-up

- Archivar con `/opsx:archive renombrar-brazos` antes de aplicar `h3-semillas-optuna`.
