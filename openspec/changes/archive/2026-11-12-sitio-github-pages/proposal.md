# Proposal

## Why

El grupo y el tutor (Joaquín I. Aramendía) no tienen un lugar cómodo para leer el experimento:
- github.com muestra cada `reporte.html` como código fuente;
- la página de cada `informe.md` enlaza a `reporte.html`, y ese enlace lleva al código fuente;
- hipótesis, diseño, informes, método y bitácoras están repartidos en ~45 archivos sin un índice de lectura.

Con cuatro hipótesis cerradas y el video por delante, conviene una sola dirección
(`agustinarazanov.github.io/dmeyf-experimento-sampling/`) donde se lea todo navegando: conclusión, evidencia y proceso.

## What Changes

- **Sitio Jekyll publicado en GitHub Pages** con el tema Just the Docs: barra lateral, búsqueda, índice por página y
  recuadros (*callouts*). Se construye desde la raíz del repo con un workflow de GitHub Actions en cada push a `main`.
- **Qué se publica:**
  - informes, tabla de resultados, decisiones y guion;
  - hipótesis y diseño de cada experimento;
  - `docs/metodo.md` y `docs/revision.md`;
  - los README que enlazan los informes;
  - las bitácoras, en una sección «Proceso» al final de la barra lateral, porque el proceso es parte del experimento;
  - las specs de `openspec/specs/`.
- **Qué no se publica:** código, tests, scripts, plantilla, `.claude/` y los cambios de OpenSpec (activos y archivados).
- **Navegación sin mover archivos:** el título, la sección y el orden de cada página se definen en `_config.yml` por
  ruta. Las URL son las rutas del repo, así los enlaces relativos que ya funcionan en github.com funcionan igual en el
  sitio. Mover o renombrar queda permitido cuando sea barato; cada movimiento es una tarea con su grep.
- **Portada:** resumen corto con la respuesta a la pregunta del tutor, que lleva primero al informe conjunto de
  `sampling_1`.
- **BREAKING (`comun/reporte.py`, cambio en `comun/`):** `reporte.html` pasa a ser una página del sitio (encabezado
  YAML + cuerpo HTML, sin `<html>`, `<head>` ni CSS propio), con barra lateral y búsqueda. Deja de verse bien abierto
  como archivo suelto en el navegador; para verlo localmente está `bundle exec jekyll serve`.
- **Enlaces verificados en el build:** si hay un enlace interno roto, el workflow falla y no publica.
- Se agrega al método (`docs/metodo.md`, § Agregar una hipótesis) el paso de sumar el experimento nuevo al sitio.

Fuera de alcance: tablas leídas de los CSV del ledger con `_data/` (queda para un cambio posterior); dominio propio;
traducir o reescribir los documentos.

## Capabilities

### New Capabilities
- `sitio-informes`: el sitio público que reúne los documentos del repo para leerlos navegando: qué se publica, cómo se
  ordena, portada, verificación de enlaces y publicación automática.

### Modified Capabilities
- `reporte-visual`: «Legible sin servidor y compartible» cambia. El reporte deja de ser un HTML autónomo y pasa a ser
  una página del sitio, con las figuras todavía embebidas, sin dependencias fuera del sitio y regenerable igual que
  antes. Los enlaces a los otros reportes pasan a ser enlaces dentro del sitio.

## Impact

- **Archivos nuevos en la raíz:**
  - `_config.yml`;
  - `Gemfile` y `Gemfile.lock`;
  - `index.md` (la portada);
  - `.github/workflows/pages.yml`;
  - `_sass/custom/`, para los colores de veredicto del reporte;
  - `.gitignore`, que suma `_site/` y `.jekyll-cache/`.
- **`comun/reporte.py` y `tests/test_reporte.py`:** cambia la forma de la salida; los números, las tablas y las
  figuras quedan iguales. Se anuncia en el commit por ser `comun/`.
- **Los seis `reporte.html` regenerados.** Cambia el envoltorio y no el contenido, y se verifica comparando las
  tablas antes y después.
- **Documentos `.md`:** solo se tocan los enlaces que el build marque como rotos, por ejemplo los enlaces a carpetas,
  que en el sitio no tienen página. El contenido no cambia.
- **GitHub:** hay que activar Pages con origen «GitHub Actions» en la configuración del repo. Lo hace Agustina, igual
  que el push.
- **Dependencias:** Ruby y Bundler, ya instalados en la Mac de Agustina; en CI los instala el workflow. Python no
  suma nada.
