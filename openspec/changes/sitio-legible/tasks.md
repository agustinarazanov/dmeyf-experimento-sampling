# Tasks

## 1. Sitio en MkDocs Material (sesión: Sonnet)

- [x] 1.1 Prototipo (D7): `mkdocs.yml` en la raíz con `mkdocs-same-dir`, `exclude_docs`, `nav` de dos páginas
  (`index.md` y `experimentos/h1/`, todavía con su contenido actual) y `requirements-sitio.txt` con versiones fijadas.
  Verificar con `mkdocs build --strict`: no publica nada de lo excluido (`find site -name '*.py' -o -name 'bitacora*'`
  vacío), el índice de la derecha aparece y un enlace relativo roto hace fallar el build. Si `mkdocs-same-dir` no
  funciona, usar el `docs_dir` temporal de D7/Riesgos y anotarlo en la bitácora.
- [x] 1.2 Tema y extensiones de D7 (`navigation.indexes`, `toc.follow`, admonition, superfences con Mermaid, tabbed,
  `md_in_html`, `attr_list`), `site_name: Sampling_1`, y `sitio/estilos.css` portado de `_sass/custom/custom.scss`
  (pill, icbar, td.sig-\*, ic, nota, largo de línea). Verificar en `mkdocs serve`: un callout, un diagrama Mermaid, una
  grilla de tarjetas y una tabla con pills se ven bien. «Sampling_1» entra en una línea a 1280 px y a 390 px.
- [ ] 1.3 `scripts/sitio.sh [serve]` sobre MkDocs, con la búsqueda de nombres de D8 (con lista de excepciones con
  motivo) antes del build. `.github/workflows/pages.yml` con `setup-python` en lugar de Ruby. Verificar: `scripts/sitio.sh`
  pasa local; con «tutor» en una página publicada falla nombrando archivo y línea; el workflow corre en una rama con
  `workflow_dispatch` (sin publicar desde la rama) y termina en verde.
- [ ] 1.4 README raíz § Ver el sitio localmente con el comando nuevo. Verificar corriéndolo tal como está escrito.

## 2. Generador con marcadores y figuras nuevas (sesión: Sonnet; cambio en `comun/`, se anuncia en el commit)

- [ ] 2.1 `comun/reporte.py`: escritura entre marcadores `<!-- generado:… -->` (D4), que falla sin escribir nada si
  falta un marcador y no toca el texto de afuera. Se puede correr por experimento (`--exp h1`), para que el grupo 3
  regenere cada README cuando lo crea. Mientras tanto, los experimentos sin README nuevo siguen con la salida vieja.
  Test nuevo en `tests/test_reporte.py` para los dos casos. Verificar con `pytest tests/test_reporte.py`.
- [ ] 2.2 `html_tabla()` sin `.table-wrapper` propio, y bloque B sin autor (D4, D8). Verificar en `mkdocs serve`: una
  tabla generada tiene un solo recuadro y una sola barra de desplazamiento a 390 px. `grep -c autor` sobre la salida
  del bloque B da 0.
- [ ] 2.3 Figuras como archivos SVG en `experimentos/<exp>/figuras/` más PNG con `--figuras` (D5). Verificar: regenerar
  dos veces da archivos idénticos (`git status` limpio en la segunda) y el SVG se ve en github.com y en el sitio.
- [ ] 2.4 Cargar la skill `dataviz`. Gráficos de D6: mapa del tradeoff, Δ contra tasa con banda, desglose del tiempo,
  semillas y réplicas, grilla de veredictos, rondas (dumbbell) y curva de diferencia por hipótesis, con títulos que
  digan qué mirar, salidos del generador. Se borran `fig_tradeoff`, `fig_tiempo_ganancia_paneles`, `fig_bandas`,
  `fig_replicas` y `fig_varianza`. Verificar con los escenarios de `reporte-visual` § Comparación de todas las variantes:
  ninguna etiqueta encima de otra, «sin datos» sale como pendiente (test con un ledger vacío) y la curva de `U0.05`
  queda por debajo de 0 en N\*.
- [ ] 2.5 Bloques de tarjetas (`index.md`, `sitio/hipotesis.md`) con el veredicto leído del ledger, y
  `scripts/comparar_rondas.py` escribiendo el bloque `rondas`. Verificar regenerando y comparando los veredictos de
  las tarjetas con `apareado.csv`/`replicas.csv`.
- [ ] 2.6 `comun/variantes.py` lee § Variantes y § Dependencias de `experimentos/*/README.md` y falla si queda una
  `docs/diseno.md` con § Dependencias. `tests/test_variantes.py` en la ruta nueva, con el escenario de archivo viejo.
  Verificar con `pytest tests/test_variantes.py` y `python -m comun.variantes --verificar` (se corre en el grupo 3,
  cuando existan los README).
- [ ] 2.7 `scripts/verificar_readme.py` y `scripts/verificar_informe_h3.py` leen el bloque `bloque-a-completo` de
  `sampling_1/README.md`, y el segundo revisa el texto fuera de los marcadores de cada `hN/README.md` (D9). Verificar
  con un número alterado a mano que el verificador falla nombrándolo.
- [ ] 2.8 Revisión en sesión limpia del grupo 2 con `docs/revision.md` § 3, cierre en la bitácora de `sampling_1` y
  `comun/tokens.py`.

## 3. Un README por experimento (sesión: Opus para redactar; un commit por experimento)

Cada tarea: listar antes cada sección de los archivos viejos con su destino o el motivo para descartarla (en la
bitácora del experimento), escribir el README con la plantilla de D3, aplicar las reglas de redacción de D8, regenerar,
borrar los archivos fundidos y correr `python -m comun.variantes --verificar`, `pytest` y `scripts/sitio.sh`.

- [ ] 3.1 `plantilla/README.md` con las secciones de D3 y los marcadores vacíos. Se borran `plantilla/docs/{hipotesis,diseno}.md`
  y `plantilla/informe/`. Verificar copiando la plantilla a una carpeta temporal: `comun.variantes --verificar` acepta
  la estructura.
- [ ] 3.2 `experimentos/control/README.md`: baseline, reglas (G, Δ, δ, T, A, N\*, veredictos), regla de veredicto como
  diagrama Mermaid, línea de tiempo de meses (train / validación 201908 / test 201910), apartamientos con sus ids de
  Zulip, bloque `estado`. Verificar que todo lo de `control/docs/{hipotesis,diseno}.md` tiene destino.
- [ ] 3.3 `experimentos/h1/README.md` (Idea con diagrama del pipeline, Predicción con fecha y commit del
  `hipotesis.md` original, Diseño, Dependencias, Resultado generado, Veredicto, Limitaciones). Verificar con
  `verificar_informe_h3.py --informe experimentos/h1/README.md`.
- [ ] 3.4 `experimentos/h2/README.md`, igual que 3.3.
- [ ] 3.5 `experimentos/h3/README.md`, igual que 3.3, con la dependencia de `h1` en Limitaciones.
- [ ] 3.6 `experimentos/h4/README.md`, igual que 3.3, declarando en Predicción que las variantes salieron de mirar
  201910.
- [ ] 3.7 `experimentos/sampling_1/README.md` (Resultados): pregunta, respuesta, comparación entre hipótesis, a tiempo
  igual, limitaciones comunes, conclusiones y qué sigue, con los bloques de D4. Se funden `informe.md`,
  `tabla_resultados.md`, `decisiones.md`, `comparacion_rondas.md` y `docs/hipotesis.md`, y desaparece
  `sampling_1/informe/`. La tabla de rutas pasa a `docs/rutas.md` y el guion a `docs/guion.md`, con los nombres nuevos de
  los PNG. Verificar con `python -m scripts.verificar_readme` y con que el bloque A tenga las mismas filas y valores que
  el `tabla_resultados.md` anterior (`git show HEAD~:…`).
- [ ] 3.8 `experimentos/sampling_1/corridas.md` (de `docs/diseno.md` y `docs/operacion.md`, con el reparto por máquina
  y por fase) y `experimentos/sampling_1/exploratorios/README.md` (bloque B, una sección por estudio, enlaces a los
  README de cada exploratorio en GitHub). Verificar que la tabla con texto de exploratorios ya no existe y que
  `comun.variantes --verificar` pasa.
- [ ] 3.9 `index.md` (pregunta, respuesta en ≤ 3 líneas, mapa del tradeoff, tarjetas), `sitio/hipotesis.md`,
  `sitio/como-medimos.md` y `docs/metodo.md` (Cómo trabajamos: método, § Agregar una hipótesis con la estructura
  nueva y enlaces a GitHub a bitácoras, specs, `docs/revision.md` y guion). Se borran los `sitio/*.md` viejos.
  Verificar con el escenario «Llegar a una bitácora».
- [ ] 3.10 README raíz recortado (qué es, enlace al sitio, cómo correr, estructura) e impersonal; `CLAUDE.md` con el mapa de
  archivos nuevo. Verificar con `python -m scripts.verificar_readme` y con la búsqueda de nombres de D8.

## 4. Limpieza e integración (sesión: Sonnet)

- [ ] 4.1 Borrar `_config.yml`, `_sass/`, `Gemfile`, `Gemfile.lock`, `_site/`, los `reporte.html` y las carpetas
  `informe/` que queden. Verificar que `git grep -nE "informe/(informe|reporte|tabla_resultados)|docs/(hipotesis|diseno)\.md"`
  no tiene resultados fuera de `openspec/changes/archive/`, la bitácora y los scripts de una sola vez de D9.
- [ ] 4.2 Integración: `pytest`, `python -m comun.variantes --verificar`, `python -m scripts.verificar_readme`,
  `verificar_informe_h3.py` sobre los cuatro README de hipótesis y `scripts/sitio.sh`, todo en verde. Recorrer el sitio en
  `mkdocs serve` contra los escenarios de `sitio-informes`: ~12 páginas en la barra, índice a la derecha, cada
  resultado en una sola página, sin nombres y sin doble recuadro.
- [ ] 4.3 Revisión en sesión limpia (Opus) con `docs/revision.md` § 5, cierre en la bitácora de `sampling_1` y
  `comun/tokens.py`. El push lo decide Agustina. Después del push, verificar en el sitio publicado los escenarios
  «Primera visita del tutor» y «Teléfono».

## Workflow follow-up

- Archivar `sitio-legible` después de la revisión 4.3 y antes de archivar `tiempos-confiables-y-consistencia`, que
  después une `main` en su rama (no se modifica desde acá). En el
  archivo, actualizar el `## Purpose` de `openspec/specs/sitio-informes/spec.md` y de `reporte-visual` para que no
  nombren al tutor.
- Al entrar los números de `tiempos-confiables-y-consistencia`, regenerar con `comun/reporte.py`. Solo cambian los
  bloques generados, y los textos de Veredicto y Conclusiones se revisan a mano.
