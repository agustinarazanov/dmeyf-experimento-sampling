# Design

## Context

Motivación: ver `proposal.md` § Why. Estado actual que condiciona el enfoque:

- El sitio es Jekyll + Just the Docs (`_config.yml`, `_sass/custom/custom.scss`, `scripts/sitio.sh` con html-proofer,
  `.github/workflows/pages.yml` con Ruby). La navegación son ~60 entradas `defaults` en `_config.yml`.
- `comun/reporte.py` genera `informe/reporte.html` por experimento (página Jekyll con YAML + HTML y SVG en línea, de
  300 a 750 KB) y `sampling_1/informe/tabla_resultados.md`. `html_tabla()` envuelve cada tabla en
  `<div class='table-wrapper'>`, y el layout del tema (`table_wrappers.html`) vuelve a envolver cada `<table`. De ahí
  el doble recuadro.
- Leen los documentos actuales: `comun/variantes.py:196` (glob `*/docs/diseno.md`, § Variantes y § Dependencias),
  `comun/reporte.py:66` (secciones de `hipotesis.md`), `scripts/verificar_readme.py` y
  `scripts/verificar_informe_h3.py` (números contra `tabla_resultados.md`), `scripts/comparar_rondas.py` (escribe
  `comparacion_rondas.md`), `tests/test_reporte.py:233` y `tests/test_variantes.py:96-128`.
- `comun/tokens.py` lee `docs/bitacora.md`, que no cambia de lugar.
- Los ledgers ya tienen el tiempo por fase (`tiempo_preparacion_s`, `tiempo_optimizacion_s`,
  `tiempo_entrenamiento_s`, `tiempo_lgbtrain_s` en `estudios.csv` y `resultados.csv`). El desglose del tiempo no
  necesita corridas nuevas.
- Está abierto `tiempos-confiables-y-consistencia`, que se aplica en paralelo en la rama `tiempos-confiables` (worktree
  `../experimento-sampling-tiempos`). Nombra `informe.md`, `tabla_resultados.md`, `docs/hipotesis.md`, `docs/diseno.md`
  y `decisiones.md`, y modifica `reporte-visual`.

## Goals / Non-Goals

**Goals:**
- Que los archivos del repo sean las páginas, sin un paso que arme páginas aparte.
- Que el generador sea la única fuente de números y figuras, y que regenerar no pise el texto escrito a mano.
- Dejar la estructura lista para que los números de `tiempos-confiables-y-consistencia` entren regenerando.

**Non-Goals:**
- Cambiar números, veredictos, ledgers o corridas.
- Reescribir la bitácora o el archivo de Zulip para que sean impersonales: quedan fuera del sitio tal como están.
- Gráficos interactivos (hover, zoom). Las figuras siguen siendo SVG estáticos.
- Traducir el sitio o cambiar el idioma.

## Decisions

### D1. Corregir los archivos y no armar un sitio curado aparte

El sitio sigue siendo un espejo del repo, pero el repo pasa a tener ~12 documentos de lectura. Se descartó armar las
páginas en el build a partir de los documentos actuales. Ese camino deja dos fuentes (archivo y página), rompe la
regla de que un enlace relativo funcione igual en GitHub y en el sitio, y no arregla la repetición, que está en los
archivos.

### D2. Mapa de archivos

| hoy | después | en el sitio |
|---|---|---|
| `index.md` | `index.md` (reescrito: pregunta, respuesta corta, mapa del tradeoff, tarjetas) | Inicio |
| `sampling_1/informe/{informe,tabla_resultados,decisiones,comparacion_rondas}.md`, `informe/reporte.html`, `docs/hipotesis.md` | `experimentos/sampling_1/README.md` | Resultados |
| `sampling_1/README.md` (correspondencia de rutas) | `experimentos/sampling_1/docs/rutas.md` | no |
| `sampling_1/docs/{diseno,operacion}.md` | `experimentos/sampling_1/corridas.md` | Cómo medimos › Corridas |
| `sampling_1/informe/guion.md` | `experimentos/sampling_1/docs/guion.md` | no |
| `sampling_1/informe/figuras/` | `experimentos/sampling_1/figuras/` | (imágenes) |
| `control/docs/{hipotesis,diseno}.md`, `control/informe/reporte.html` | `experimentos/control/README.md` | Cómo medimos › Control y reglas |
| `hN/docs/{hipotesis,diseno}.md`, `hN/informe/{informe.md,reporte.html}` | `experimentos/hN/README.md` | Hipótesis › HN |
| `exploratorios/*/README.md`, `h3/sensibilidad_muestra/README.md` | sin cambios | no (enlazados) |
| — | `experimentos/sampling_1/exploratorios/README.md` (nuevo: bloque B) | Cómo medimos › Exploratorios |
| `docs/metodo.md` + `docs/revision.md` | `docs/metodo.md` (reescrito); `revision.md` sin cambios | Cómo trabajamos; revisión no |
| `sitio/{resultados,experimentos,proceso,especificaciones}.md` | `sitio/hipotesis.md`, `sitio/como-medimos.md` | páginas de sección |
| `README.md` raíz | recortado: qué es, enlace al sitio, cómo correr, estructura | no (es la portada en GitHub) |

Las carpetas `informe/` desaparecen y las figuras de cada experimento van a `experimentos/<exp>/figuras/`.

### D3. Plantilla del README de una hipótesis

```
# H1 · Submuestreo uniforme del train
<una línea: qué se prueba>
## Idea                (2-4 párrafos + diagrama Mermaid del pipeline, marcando dónde corta)
## Predicción          (fijada el <fecha>, commit <hash>; reglas: enlace a control/README.md)
## Diseño              (### Variantes, ### Grilla, ### Rondas; tabla de variantes que lee comun/variantes.py)
## Dependencias        (lista que lee comun/variantes.py)
## Resultado           <!-- generado:resultado --> tabla + mapa del tradeoff + curvas de diferencia <!-- /generado:resultado -->
## Veredicto           (callout, escrito a mano, sin números que no estén en el bloque generado)
## Limitaciones        (callout, solo las propias)
```

El nombre de cada sección es fijo, porque lo leen `comun/variantes.py`, los verificadores y la revisión.
`plantilla/README.md` reemplaza a `plantilla/docs/{hipotesis,diseno}.md` y `plantilla/informe/`.

### D4. Bloques generados con marcadores

`comun/reporte.py` reemplaza el contenido entre `<!-- generado:<nombre> -->` y `<!-- /generado:<nombre> -->` y deja
el resto del archivo intacto. Si falta un marcador, falla antes de escribir nada en ningún archivo, para que un error no
deje la mitad de los README regenerados. Cada bloque abre con una línea «Generado por `comun/reporte.py` el <fecha>; no
editar».

Bloques por archivo:
- `sampling_1/README.md`: `mapa`, `bloque-a` (resumen + detalle plegable), `bloque-a-completo` (tablas de formato
  estable para los verificadores, plegado), `varianza`, `diferencias`, `tiempo-igual`, `rondas` y `figuras`.
- `sampling_1/exploratorios/README.md`: `bloque-b`.
- `control/README.md`: `estado`.
- `hN/README.md`: `resultado`.
- `index.md` y `sitio/hipotesis.md`: `tarjetas` (una por hipótesis, con el veredicto leído del ledger, para que
  ninguna tarjeta lo copie a mano).

Las tablas con formato salen como HTML dentro del Markdown, con línea en blanco antes y después. El sitio usa
`md_in_html`, y GitHub muestra el HTML sin clases: el veredicto se sigue leyendo porque va en texto. `html_tabla()` deja
de envolver en `.table-wrapper`: el recuadro y el desplazamiento los pone el tema con un solo contenedor.

Se descartó un include en tiempo de build (snippets): GitHub no lo resuelve y el README se vería vacío ahí.

`scripts/comparar_rondas.py` pasa a escribir el bloque `rondas` en lugar de `comparacion_rondas.md`.

### D5. Figuras como archivos SVG

Cada figura se guarda en `experimentos/<exp>/figuras/<nombre>.svg` y el bloque la enlaza con `![título](figuras/…)`.
Con `--figuras` también se guarda el PNG para el video. Se descartó dejar el SVG en línea: GitHub lo elimina y el README
pesaría cientos de KB. Como el SVG se muestra como `<img>`, el texto usa una fuente genérica (`sans-serif`) y los trazos
llevan sus atributos en el archivo, sin CSS de la página. `svg.hashsalt` sigue fijo para que regenerar dé el mismo
archivo.

### D6. Gráficos

Antes de escribir código de gráficos se carga la skill `dataviz`. Formas:

| gráfico | forma | reemplaza | fuente |
|---|---|---|---|
| mapa del tradeoff | dispersión, x = A (log), y = Δ con IC, zona Δ > −δ sombreada, etiquetas sin solaparse | `fig_tiempo_ganancia_paneles`, `fig_tradeoff` (filas Δ + barras A) | `apareado.csv`, `replicas.csv` |
| Δ contra tasa | líneas por familia con banda de IC, x = tasa (log) | `fig_fraccion` (se mantiene, con banda) | ídem |
| desglose del tiempo | barras apiladas verticales, optimización / final / predicción | nuevo | `estudios.csv`, `resultados.csv` (`tiempo_*_s`) |
| semillas y réplicas | puntos por semilla (jitter), réplicas con otro marcador | `fig_replicas`, `fig_varianza` (la sd queda en la tabla de varianza) | `resultados.csv`, `replicas.csv` |
| grilla de veredictos | celdas familia × tasa con color y texto | nuevo (reemplaza la tabla de cobertura en prosa) | registro + veredictos |
| tiempo igual | intervalo por variante | `fig_tiempo_igual_ic` (se mantiene) | bootstrap existente |
| diferencias | intervalo por par | `fig_diferencias` (se mantiene) | ídem |
| rondas | dumbbell anterior → vigente | nuevo | `ronda_201903-201906/` + vigente |
| curva de diferencia (por hipótesis) | línea G(variante) − G(C) contra envíos, banda entre semillas, 0 y N\* | `fig_bandas` | `curvas/` |

Colores: los de veredicto quedan como están (`#2e8b57`, `#c0392b`, `#b8860b`). Las familias usan una paleta categórica
validada con la skill. El título de cada figura dice qué mirar (por ejemplo, «Achicar solo la optimización no pierde y
acelera hasta 11×»), y como los números cambian con la ronda, el título sale del generador y no se escribe a mano.

Los nombres de los PNG cambian. El guion (`sampling_1/docs/guion.md`) se actualiza con los nombres nuevos.

### D7. MkDocs Material

- `mkdocs.yml` en la raíz, con el plugin `mkdocs-same-dir` para usar la raíz del repo como `docs_dir`, `exclude_docs`
  (estilo gitignore) para lo que no se publica, y `nav` explícito con las ~12 páginas.
- Tema: `navigation.indexes` (páginas de sección), `toc.follow` (índice a la derecha que sigue la lectura),
  `navigation.top`, `search.highlight`, `content.tabs.link`; `site_name: Sampling_1`.
- Extensiones: `admonition`, `pymdownx.details`, `pymdownx.superfences` con fence `mermaid`, `pymdownx.tabbed`,
  `attr_list`, `md_in_html`, `tables`, `toc` con `permalink`.
- Callouts: `!!! success "Veredicto"`, `!!! warning "Limitación"`, `!!! info "Predicción"`. En GitHub se ven como
  texto indentado. Se acepta, porque el contenido se lee igual.
- Tarjetas: `<div class="grid cards" markdown>` de Material.
- Estilos: `sitio/estilos.css` porta de `custom.scss` lo que sigue haciendo falta (`.pill`, `.icbar`, `td.sig-*`,
  `.ic`, `.nota`, largo de línea de ~75ch). Se borra lo que el tema ya resuelve (ancho, tarjetas).
- Enlaces: `validation.links` en `warn` y `mkdocs build --strict`. Un enlace a un archivo excluido (bitácora, spec) da
  advertencia y hace fallar el build, así que esos enlaces van como URL absoluta a GitHub. html-proofer deja de usarse.
- Versiones fijadas en `requirements-sitio.txt` (`mkdocs-material`, `mkdocs-same-dir`), aparte de
  `requirements.txt` para no mezclar el entorno de corridas.
- CI: `actions/setup-python` + `pip install -r requirements-sitio.txt` + `scripts/sitio.sh` + `upload-pages-artifact`
  + `deploy-pages`. La fuente de Pages ya es Actions, así que no hace falta cambiar nada en la configuración del repo.
- `scripts/sitio.sh [serve]` sigue siendo el único comando, local y en CI. `--baseurl` desaparece, porque MkDocs usa
  `site_url`.

Alternativas: seguir con Just the Docs + tocbot + Mermaid a mano (menos cambio, pero el índice, las pestañas y las
tarjetas serían código propio), o Quarto (muy bueno para informes, pero suma otra herramienta y otro lenguaje de
plantillas). Material sumó modo mantenimiento a fines de 2025. Para un sitio con horizonte de semanas alcanza, y su
configuración es compatible con su sucesor (Zensical).

### D8. Redacción impersonal, verificada

`scripts/sitio.sh` corre, antes del build, una búsqueda sin distinguir mayúsculas sobre las páginas publicadas (las
del `nav`) y el README raíz, con la lista `tutor|bolaños|aramend|agustina|martín|luis|laguinge|razanov|lópez|autor`. Si
encuentra algo, falla y nombra archivo y línea. Reglas de reemplazo: «baseline de Bolaños» → «baseline», «pregunta del
tutor» → «pregunta del experimento», «aporte de Luis/Martín» → «exploratorio» con su nombre de carpeta, «Agustina corrió»
→ voz impersonal o se borra. Los ids de Zulip quedan como cita. `exploratorio.json` conserva `autor` (lo pide
`protocolo-experimental`), pero el generador no lo muestra.

### D9. Verificadores y tests

- `verificar_readme.py` y `verificar_informe_h3.py` leen los números del bloque `bloque-a-completo` de
  `sampling_1/README.md` en lugar de `tabla_resultados.md`. `verificar_informe_h3.py` revisa el texto fuera de los
  marcadores de cada `hN/README.md`, que es la parte escrita a mano.
- `comun/variantes.py` lee § Variantes y § Dependencias de `experimentos/*/README.md`. Si encuentra un
  `docs/diseno.md` con § Dependencias, falla (escenario de `dependencias-entre-experimentos`).
- `tests/test_variantes.py` y `tests/test_reporte.py` pasan a la ruta nueva, y se agrega un test de marcadores
  (regenerar no toca el texto de afuera; un marcador faltante falla sin escribir).
- `scripts/concordar_d3.py`, `reemplazar_d*.py` y otros scripts de una sola vez ya aplicados quedan como están. Son
  historia y no se vuelven a correr.

### D10. Orden respecto de `tiempos-confiables-y-consistencia`

Los dos cambios se aplican en paralelo (decisión de Agustina, 13-nov). Este, en `main`, con los números de la ronda
vigente. `tiempos-confiables-y-consistencia`, en la rama `tiempos-confiables`: predicciones, código de corridas y
corridas. Su reporte y sus informes se hacen después de unir la rama.

Este cambio **no modifica** los artefactos de `tiempos-confiables-y-consistencia`. Cuando este se archive, aquel une
`main` en su rama, resuelve los conflictos y actualiza sus propias rutas, gráficos, tablas y su delta de `reporte-visual`
(su grupo 2b). Este cambio solo tiene que archivarse antes que aquel, porque los dos modifican «Comparación limpia en
dos bloques».

## Risks / Trade-offs

- [`mkdocs-same-dir` no anda con la versión fijada o choca con `exclude_docs`] → La primera tarea es un prototipo de
  dos páginas. Si falla, `scripts/sitio.sh` arma un `docs_dir` temporal con enlaces simbólicos a los archivos del `nav`
  (sin cambiar rutas, así que los enlaces relativos se conservan).
- [Fundir archivos pierde texto que importaba] → Cada fusión se hace por experimento y en un commit propio. Antes de
  borrar, se lista cada sección vieja con su destino o el motivo para descartarla, y la revisión de cierre compara
  contra `git show HEAD~:<archivo>`.
- [Se rompe la prueba de que la predicción es previa] → La sección Predicción cita el commit y la fecha del
  `hipotesis.md` original, y `git log --follow` sobre el README lleva a él. Los archivos viejos siguen en el historial.
- [Los README pierden formato en GitHub (callouts, tarjetas)] → Se acepta, porque el contenido se lee igual. El sitio
  es la vista principal.
- [El README de Resultados queda muy largo] → Bloques plegables (`??? note`) para las tablas completas y el índice a la
  derecha. Si supera ~1.500 líneas, `bloque-a-completo` se mueve a un anexo publicado.
- [Los dos cambios tocan los mismos archivos] → D10. `tiempos-confiables-y-consistencia` trabaja en su rama y une
  `main` cuando este se archiva; los conflictos se resuelven de su lado.
- [La lista de nombres prohibidos da falsos positivos (por ejemplo «Luis» en una cita o «autor» en otra acepción)] → La
  búsqueda admite una lista de excepciones por archivo y línea en `scripts/sitio.sh`, y cada excepción lleva motivo.

## Migration Plan

1. Prototipo de MkDocs (dos páginas) y CI en una rama, comprobando local y en Pages.
2. Generador con marcadores y figuras nuevas sobre los README nuevos, uno por experimento: `control`, `h1`…`h4`,
   `sampling_1`, exploratorios.
3. Borrar los archivos fundidos, Jekyll y Ruby. Verificadores, tests y `mkdocs build --strict` en verde.
4. Revisión en sesión limpia con `docs/revision.md`, y push a criterio de Agustina.
5. Archivar este cambio. `tiempos-confiables-y-consistencia` une `main` en su rama después.

Vuelta atrás: `git revert` de los commits del cambio. El sitio publicado no cambia hasta el push, y si el build nuevo
falla en CI queda la versión anterior.
