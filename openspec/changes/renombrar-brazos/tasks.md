# Tasks

## 1. Foto previa y aporte de Luis (sesión: Sonnet)

- [ ] 1.1 Guardar la foto de D5 en `DATOS_DIR/renombre/antes/`: correr `python -m comun.consolidar` y `python -m comun.reporte --todos`, y copiar cada `apareado.csv` y la tabla de resultados de cada `reporte.html` (extraída a CSV con un script); verificar que hay un archivo por experimento y que `git status` sigue limpio salvo la fecha de los reportes
- [ ] 1.2 Mover el aporte de Luis con `git mv` según D6 (`validacion_50_semillas.py`, `resumen.md`) y escribir su `README.md` con autor, fecha, qué corre, las cinco diferencias con el protocolo y el CSV faltante; verificar que `experimentos/Experimentos h3 y h4/` ya no existe, que `git diff -M --stat` muestra los dos archivos como renombres sin cambios de contenido y que `python -m comun.brazos --verificar` sigue pasando

## 2. Código y ledgers (sesión: Sonnet)

- [ ] 2.1 `git mv comun/brazos.py comun/variantes.py` y `tests/test_brazos.py tests/test_variantes.py`; renombrar según D1 en `comun/`, `scripts/` (salvo `separar_ledger.py`, que ya corrió y se deja con alias de lectura), `experimentos/sampling_1/scripts/` y `tests/`, excluyendo `experimentos/h3/sensibilidad_muestra/`; verificar que `python -m pytest` pasa y que `git grep -n -i brazo -- comun scripts tests experimentos/sampling_1/scripts` solo muestra el alias de `comun/ledger.py`, su test y `separar_ledger.py`
- [ ] 2.2 Agregar a `comun/ledger.py` el alias de lectura de D2 y un test que consolida un ledger sintético con cabecera `brazo` y otro con `variante` y obtiene el mismo `apareado.csv`; verificar con `python -m pytest tests/test_ledger.py tests/test_consolidar.py`
- [ ] 2.3 Escribir `scripts/renombrar_columna.py` con `--verificar` (D2) y correrlo sobre `experimentos/{control,h1,h2,h3}/ledger/` (CSV y `hp/*.json`), sin tocar `apareado_previo.csv`; commit separado solo con las cabeceras; verificar que `--verificar` sale con 0 y que `git diff --numstat` da una línea cambiada por CSV
- [ ] 2.4 Smoke test en la Mac: `python -m comun.correr --metodo uniforme --tasa 0.25 --semilla 100003 --etapa optimizar --filas 20000` y un final de `H3-0.25`; verificar que las filas exploratorias tienen columna `variante` y que `python -m comun.variantes --verificar` pasa
- [ ] 2.5 Revisión en sesión limpia del grupo 2 con la lista de código de `docs/revision.md` y cierre en `sampling_1/docs/bitacora.md`

## 3. Docs, informes y specs (sesión: Sonnet)

- [ ] 3.1 Renombrar en `CLAUDE.md`, `docs/metodo.md`, `docs/revision.md`, `plantilla/`, `sampling_1/README.md` (sumar `comun/brazos.py` → `comun/variantes.py` a la correspondencia) y en `docs/` e `informe/` de `control`, `h1`, `h2`, `h3` y `sampling_1` (incluidos `decisiones.md` y `guion.md`), sin tocar bitácoras; verificar con los dos grep de concordancia de Risks / Trade-offs (sin resultados) y con `git diff --word-diff` sobre los `informe.md` sin cambios en números
- [ ] 3.2 Regenerar con `python -m comun.consolidar` y `python -m comun.reporte --todos` y comparar con la foto de 1.1; verificar que los valores de cada `apareado.csv` y de cada tabla de resultados coinciden (diferencia 0) y que el diff de cada `reporte.html` solo tiene "variante" y la fecha
- [ ] 3.3 Anotar el renombre (fecha, commits, qué no se tocó) en la bitácora de cada experimento; verificar que `git grep -n -i brazo` fuera de lo histórico de D3 y del alias da vacío

## 4. README (sesión: Opus)

- [ ] 4.1 Reescribir `README.md` con las secciones de D7; los números se copian de `sampling_1/informe/informe.md` y de los README de los exploratorios, citando la fuente; verificar con un script que cada Δ, IC y A del README coincide con `informe.md` y que todos los enlaces relativos existen
- [ ] 4.2 Revisión en sesión limpia de los grupos 3 y 4 con la lista de informe de `docs/revision.md` (incluye leer el README como alguien que no conoce el repo) y cierre en `sampling_1/docs/bitacora.md`; correr `comun/tokens.py`

## Workflow follow-up

- Archivar con `/opsx:archive renombrar-brazos` antes de aplicar `h3-semillas-optuna`, que usa los nombres nuevos de
  los requisitos.
- Avisar en el tópico `sampling_1` de Zulip a Martín y Luis: el comando pasa a `python -m comun.variantes --verificar`
  y el aporte de Luis cambió de carpeta.
