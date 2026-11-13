# Proposal

## Why

El sitio publica la estructura de archivos del repo en lugar de contar el experimento. Tiene unas 45 páginas: cada
hipótesis aparece repartida en informe, reporte, hipótesis y diseño, y los mismos números figuran en hasta tres lugares
(informe conjunto, reporte conjunto, tabla de resultados). Además, decisiones, guion, README e inicio repiten las
conclusiones. Para encontrar un resultado hay que elegir entre «Informe conjunto», «Reporte conjunto» y «Comparación de
rondas». El texto nombra personas («tutor», «Bolaños», autores, quién corrió qué). Los gráficos son casi todos barras
y segmentos horizontales que responden solo «¿cuánto vale Δ?», sin mostrar el tradeoff. Las tablas generadas salen
con doble borde, el título no entra en la barra lateral y no hay un índice de la página actual. El problema está en
los archivos del repo, no solo en el sitio, así que se corrige en los archivos: menos archivos, cada dato en un solo
lugar, y un sitio que los muestra tal cual.

## What Changes

- **BREAKING** Un `README.md` por experimento (`control`, `h1`–`h4`) reemplaza `docs/hipotesis.md`, `docs/diseno.md`,
  `informe/informe.md` e `informe/reporte.html`. Cada uno tiene las secciones Idea, Predicción, Diseño, Dependencias,
  Resultado, Veredicto y Limitaciones. `docs/bitacora.md` y `ledger/` quedan como están. La predicción sigue fijada
  antes de correr, y la fecha la prueba el historial de git de esa sección.
- **BREAKING** `experimentos/sampling_1/README.md` pasa a ser la única página de resultados. Junta el informe conjunto,
  el reporte conjunto, `tabla_resultados.md`, `decisiones.md` y `comparacion_rondas.md`, que dejan de existir como
  archivos aparte. La tabla de correspondencia de rutas viejas pasa a `sampling_1/docs/rutas.md`.
- El generador (`comun/reporte.py`) escribe tablas y figuras **dentro** de cada README, entre marcadores
  `<!-- generado:… -->`, en lugar de producir `reporte.html` y `tabla_resultados.md`. Ningún número se copia a mano.
  Las figuras pasan a ser archivos SVG (y PNG para el video) enlazados desde el README.
- Gráficos nuevos, cada uno ligado a una pregunta: mapa del tradeoff (aceleración contra Δ, con la zona «no pierde»
  sombreada), Δ contra tasa por familia, desglose del tiempo (optimización / final / predicción), puntos por semilla y
  réplica, curva de diferencia contra el control, grilla de veredictos y comparación entre rondas. Además, cada
  hipótesis tiene un diagrama del pipeline que muestra dónde corta, y hay una línea de tiempo de meses.
- El sitio pasa de Jekyll + Just the Docs a **MkDocs Material**: índice de la página a la derecha, título corto
  («Sampling_1»), callouts, pestañas, tarjetas y diagramas Mermaid. Se publica con GitHub Actions, y
  `mkdocs build --strict` verifica los enlaces. Se borran `_config.yml`, `_sass/`, `Gemfile*` y el uso de Ruby.
- Navegación de ~12 páginas: Inicio · Resultados · Hipótesis (H1–H4) · Cómo medimos (control y reglas, corridas,
  exploratorios) · Cómo trabajamos. Las páginas padre solo tienen tarjetas hacia sus hijas.
- **BREAKING** Bitácoras, specs, `docs/revision.md`, el guion del video y los README de cada exploratorio
  quedan en el repo pero fuera del sitio. «Cómo trabajamos» los enlaza en GitHub.
- Redacción impersonal en todo lo publicado y en el README raíz: sin «tutor», «Bolaños», autores, nombres de
  integrantes ni reparto de tareas. «Baseline de Bolaños» pasa a ser «baseline», y el bloque B del reporte deja de mostrar
  el autor.
- Se corrige el doble recuadro de las tablas generadas.
- `plantilla/`, `docs/metodo.md` § Agregar una hipótesis, `comun/variantes.py` (lee § Dependencias y § Variantes),
  los verificadores y los tests pasan a la estructura de un README por experimento.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `sitio-informes`: contenido publicado (sin bitácoras, specs ni Zulip), navegación nueva, portada sin personas,
  README de cada carpeta como su página, verificación de enlaces con MkDocs, índice de la página, redacción impersonal
  y cada dato en un solo lugar.
- `reporte-visual`: el reporte se escribe dentro del README de cada experimento en lugar de `reporte.html` y
  `tabla_resultados.md`, el informe por hipótesis queda unificado en ese README, cambia el conjunto de gráficos, el
  bloque B sale sin autor y las figuras pasan a archivos vectoriales enlazados.
- `protocolo-experimental`: estructura de la carpeta de un experimento (README + `docs/bitacora.md`), hipótesis y
  diseño como secciones del README, reparto entre máquinas y no entre personas, y comunicación con el curso sin nombrar
  personas.
- `dependencias-entre-experimentos`: la sección `## Dependencias` pasa de `docs/diseno.md` al README del experimento.

## Impact

- **Documentos**: `index.md`, `README.md` raíz, `experimentos/*/README.md` (nuevos o reescritos),
  `experimentos/*/docs/{hipotesis,diseno}.md` e `experimentos/*/informe/` (se borran y se funden),
  `experimentos/sampling_1/docs/{hipotesis,diseno,operacion}.md` (se funden en Resultados y Corridas), `docs/metodo.md`
  y `plantilla/`.
- **Código**: `comun/reporte.py` (salida en marcadores, figuras nuevas, sin doble envoltorio, sin autor),
  `comun/variantes.py` (ruta de § Variantes y § Dependencias), `scripts/comparar_rondas.py` (escribe en el marcador),
  `scripts/verificar_readme.py`, `scripts/verificar_informe_h3.py`, `scripts/concordar_d3.py` (rutas),
  `tests/test_reporte.py` y `tests/test_variantes.py`. Si un cambio toca `comun/`, se anuncia en el commit.
- **Sitio y CI**: `mkdocs.yml` y `requirements-sitio.txt` nuevos, `.github/workflows/pages.yml` (Python en lugar de
  Ruby), `scripts/sitio.sh` reescrito sobre MkDocs. Se borran `_config.yml`, `_sass/`, `Gemfile`, `Gemfile.lock` y
  `_site/`.
- **Cambio en curso**: `tiempos-confiables-y-consistencia` se aplica en paralelo en su rama y no se toca desde acá:
  une `main` cuando este se archiva y se adapta solo a la estructura nueva.
- **Sin cambios**: ledgers, corridas, números y veredictos. `comun/tokens.py` sigue leyendo `docs/bitacora.md`.
