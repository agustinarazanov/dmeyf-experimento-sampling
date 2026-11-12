# Design

## Context

Ver proposal.md (Why) y `specs/sitio-informes`.

Estado actual que condiciona el diseño:
- El repo tiene ~4.000 CSV en `experimentos/*/ledger/`, 67 `.py`, logs y JSON. Nada de eso va al sitio.
- Los documentos se enlazan con rutas relativas: 114 enlaces a `.md`, 10 a `.html`, 8 a carpetas, 2 a `.png`, 2 a
  `.json` y 1 a `.txt`. Hoy ninguno está roto en el repo. Ningún `.md` usa `{{` ni `{%`.
- El código lee los documentos por ruta: `comun/tokens.py` y `scripts/etapa.sh` leen `bitacora.md`;
  `comun/{baseline,ledger,reporte,variantes}.py` leen `hipotesis.md`; `comun/{ganancia,ledger,metodos,variantes}.py`
  leen `diseno.md`. Mover esos archivos rompe el código.
- `comun/reporte.py` (`generar_con_tabla`) arma `<!doctype html>…<style>{CSS}</style><body>…`. Las figuras ya van
  embebidas como base64 y los enlaces a otros reportes ya son relativos (`../../<exp>/informe/reporte.html`).
- La Mac de Agustina tiene Ruby 3.4.1, Bundler y Jekyll 3.10.0 instalado global (el del gem `github-pages`).

## Goals / Non-Goals

**Goals:**
- Que la URL de cada página sea la ruta del archivo en el repo. Así los enlaces relativos no se reescriben.
- Que sumar un experimento nuevo cueste unas pocas líneas en `_config.yml`.
- Que el build local y el de CI sean el mismo comando, con la misma verificación de enlaces.

**Non-Goals:**
- URL lindas (`/h3/`). Se descartan, ver D3.
- Tablas generadas desde CSV con `_data/`, diagramas Mermaid y recuadros dentro de los documentos (ver Open Questions).
- Tocar el contenido de los documentos, salvo los enlaces que el build marque.

## Decisions

### D1. Workflow de Actions con Jekyll 4 y `Gemfile`, no el build clásico de Pages

El workflow (`.github/workflows/pages.yml`) corre en cada push a `main` y a mano (`workflow_dispatch`). Hace, en orden:
1. `actions/checkout`;
2. `ruby/setup-ruby` con `bundler-cache`;
3. `actions/configure-pages`, que da la `base_path`;
4. `bundle exec jekyll build --baseurl "<base_path>"`;
5. la verificación de enlaces (D6);
6. `actions/upload-pages-artifact`;
7. `actions/deploy-pages`.

Usa `concurrency: pages` y los permisos `pages: write` e `id-token: write`.

El `Gemfile` pide `jekyll ~> 4.3`, `just-the-docs ~> 0.10` (resuelve 0.12.0) y estos plugins:
- `jekyll-optional-front-matter`: los `.md` sin encabezado se vuelven páginas;
- `jekyll-relative-links`: los enlaces a `.md` apuntan al `.html` generado;
- `jekyll-titles-from-headings`;
- `jekyll-readme-index`, ver D2.

En un grupo `:test` pide `html-proofer ~> 5.0`. El `Gemfile.lock` se commitea con las plataformas `arm64-darwin` y
`x86_64-linux`, esta última para el runner de CI. Ya está hecho (tarea 1.1).

Configuración que la prueba del 12-nov mostró necesaria en `_config.yml`:
- `optional_front_matter: {remove_originals: true}`. Sin eso, el sitio publica además una copia cruda de cada `.md`
  junto a su página.
- `readme_index: {enabled: true, remove_originals: true}`. `jekyll-optional-front-matter` ignora a propósito los
  archivos llamados `README` (y `LICENSE`, `CONTRIBUTING`, …), así que sin este plugin los README de
  `h3/sensibilidad_muestra/` y de los exploratorios no se publican. Con él, cada README pasa a ser el `index.html` de su
  carpeta (URL `experimentos/h3/sensibilidad_muestra/`).

- *Alternativa: build clásico desde la rama, con el gem `github-pages`.* Sin workflow, pero queda en Jekyll 3.10, con
  plugins limitados a una lista blanca, el tema por `remote_theme` y sin un paso donde fallar por enlaces rotos (que la
  spec pide). Descartada.
- *Jekyll 3.10 global en la Mac:* no molesta, porque `bundle exec` usa la versión del `Gemfile.lock`. La primera vez
  hay que correr `bundle install`.

### D2. Fuente en la raíz del repo, con `exclude` por carpeta y extensión

El sitio se construye desde la raíz porque el contenido vive en `experimentos/`, `docs/` y `openspec/specs/`, y la
regla de una carpeta por experimento no se toca. `_config.yml` excluye:
- carpetas: `comun`, `scripts`, `tests`, `plantilla`, `openspec/changes`, `experimentos/*/ledger`,
  `experimentos/*/scripts`, `experimentos/*/src`, `vendor`. `.claude/` y `.github/` ya quedan fuera por empezar con
  punto;
- archivos: `CLAUDE.md`, `README.md` (la portada es `index.md`, ver D5), `requirements.txt`, `Gemfile`,
  `Gemfile.lock`;
- extensiones: `"*.py"`, `"*.sh"`, `"*.csv"`, `"*.log"`, `"*.jsonl"`, `"*.json"`, `"*.txt"`, `"*.gitkeep"`.

**Sin barra final en los patrones con `*`.** Jekyll compara cada entrada con `File.fnmatch`, y
`experimentos/*/ledger/` no coincide con la carpeta `experimentos/h1/ledger`. En la prueba se publicaron los ~4.000
CSV y `_site/` pesó 2 GB; sin la barra pesa 6 MB. Las rutas sin `*` funcionan con o sin barra, pero van sin barra por
uniformidad. Verificación: `du -sh _site` en el orden de MB y el `find` de la tarea 1.2 vacío.

Lo que no tiene encabezado y no es `.md` se copia tal cual. Así quedan publicados, por ejemplo, los PNG de `figuras/` y
los HTML originales de los exploratorios de Luis, que sus README enlazan.

- *Alternativa: un paso del workflow que copie una lista blanca a `sitio/` y construya ahí.* Es más explícita, pero
  duplica rutas: cada documento nuevo es una línea más en la lista, y la vista local tendría que copiar igual. Descartada.

### D3. URL = ruta del archivo; navegación por `defaults` en `_config.yml`

No se usan `permalink` propios. `jekyll-relative-links` resuelve los enlaces a `.md`, pero no los enlaces a `.html`
(`reporte.html`, `../../h1/informe/reporte.html`). Con URL lindas, esos enlaces se romperían o habría que reescribirlos
en los documentos y en `reporte.py`. Con URL iguales a la ruta, cada enlace relativo que hoy funciona en github.com
funciona en el sitio.

La navegación de Just the Docs (`title`, `parent`, `grand_parent`, `nav_order`, `nav_exclude`) se asigna con
`defaults:`, con `scope.path` de cada archivo (o un glob donde alcance):

```
Inicio                            index.md
Resultados                        sitio/resultados.md
  Informe conjunto                experimentos/sampling_1/informe/informe.md
  Reporte conjunto                experimentos/sampling_1/informe/reporte.html
  Tabla de resultados             .../tabla_resultados.md
  Decisiones / Guion              .../decisiones.md, guion.md
Experimentos                      sitio/experimentos.md
  Control                         experimentos/control/informe/reporte.html  (no tiene informe.md)
    Hipótesis / Diseño            experimentos/control/docs/*.md
  H1 ... H4                       experimentos/hN/informe/informe.md
    Reporte / Hipótesis / Diseño  experimentos/hN/informe/reporte.html, docs/*.md
    (h3) Sensibilidad de muestra  experimentos/h3/sensibilidad_muestra/README.md
  Exploratorios                   experimentos/sampling_1/exploratorios/*/README.md
  Sampling_1: hipótesis/diseño    experimentos/sampling_1/docs/{hipotesis,diseno,operacion}.md
Método                            docs/metodo.md
  Revisión                        docs/revision.md
Proceso                           sitio/proceso.md
  Bitácora de <exp>               experimentos/*/docs/bitacora.md
Especificaciones                  sitio/especificaciones.md
  <capacidad>                     openspec/specs/*/spec.md
```

Las páginas de sección (`sitio/*.md`) son nuevas, cortas, y solo dicen qué hay en la sección.

La sección se llama «Experimentos» y no «Hipótesis», porque cada experimento tiene una página hija «Hipótesis» y Just
the Docs resuelve `parent` por título: un mismo título en dos niveles confunde la jerarquía.

Defaults:
- global (`path: ""`): `layout: default`;
- `render_with_liquid: false` solo para `experimentos`, `docs` y `openspec`, en tres entradas de `defaults`. Ningún
  documento usa Liquid, y una tabla con `{{` no debe romper el build.

**No va en el default global.** Los estilos del tema (`assets/css/just-the-docs-*.scss`) son páginas con Liquid
(`{% include css/just-the-docs.scss.liquid %}`), y con Liquid apagado Sass falla («expected end of rule»).
`index.md` y `sitio/*.md` quedan con Liquid encendido.

- *Alternativa: un plugin Ruby (`_plugins/`) que derive la navegación de la ruta.* Sumar un experimento quedaría
  automático, pero es otro lenguaje para mantener por cinco entradas de YAML por experimento. Descartada. El paso
  manual se documenta en `docs/metodo.md`.
- *Mover o renombrar:* solo `docs/` → `metodo/` podría aclarar algo, y no hace falta. No se mueve nada en este cambio.

### D4. `reporte.py` emite una página del sitio

`generar_con_tabla` devuelve:
- un encabezado YAML mínimo (`---\nrender_with_liquid: false\n---\n`). El título y la navegación vienen de D3, así el
  generador no conoce el sitio;
- el `cuerpo` actual, sin `<!doctype>`, `<html>`, `<head>`, `<title>` ni `<style>`.

`CSS` sale de `reporte.py`: las reglas de veredicto (`td.pierde`, `td.ok`, `td.ind`), `.pend` e `img{max-width:100%}`
pasan a `_sass/custom/custom.scss`. Las reglas genéricas (tabla, `code`, `details`) las cubre el tema. El `<h1>` y el
pie «Generado … · commit …» quedan, y los enlaces relativos de «Otros reportes» no cambian.

`tests/test_reporte.py` suma dos verificaciones: que la salida empieza con `---` y que no contiene `<html` ni `<style`.
Las verificaciones de contenido existentes (`pendiente`, `<table>`, `sin_fecha`) siguen igual.

Para cumplir el escenario «mismos números», antes de regenerar se guardan las tablas de los seis reportes, con el
mismo método que `scripts/foto_renombre.py`. Después se comparan celda por celda.

- *Alternativa: un `<iframe>` del HTML autónomo dentro de una página.* Tendría scroll doble y la búsqueda no lo indexa.
  Descartada en la exploración.

### D5. Portada `index.md` nueva; el README de la raíz sigue siendo para el repo

`index.md` tiene `title: Inicio` y `nav_order: 1`, y contiene:
- la pregunta del tutor;
- integrantes, tutor y comisión;
- un recuadro (`{: .conclusion }`, definido en `callouts:` de `_config.yml`) con la respuesta corta, tomada del informe
  conjunto sin números nuevos;
- un botón al informe conjunto;
- enlaces a la tabla de resultados, a Experimentos y a Método.

El `README.md` de la raíz explica cómo correr el repo y queda excluido. La portada lo enlaza en github.com, y el README
suma un enlace al sitio y la sección «Ver el sitio localmente».

### D6. Verificación con `html-proofer`, el mismo script local y en CI

`scripts/sitio.sh` hace:
1. `bundle exec jekyll build`;
2. `bundle exec htmlproofer _site --disable-external --allow-missing-href --ignore-files "/originales/,/reporte_original/"`.

Con `serve`, además corre `bundle exec jekyll serve`. El workflow llama al mismo script con la `base_path` de Pages
(`--swap-urls` para que html-proofer resuelva la base).

Se ignoran los HTML originales de Luis porque son copias históricas y no se editan.

Los enlaces que hoy apuntan a lo que no se publica se reescriben a `https://github.com/agustinarazanov/dmeyf-experimento-sampling/tree/main/…` (carpetas) o
`…/blob/main/…` (archivos):
- las 6 carpetas `experimentos/<exp>/` que enlaza el README de la raíz. El README queda excluido, así que esas no
  cuentan;
- `resultados/` y `originales/` en los README de exploratorios;
- `requirements.txt` y los `.json` de esos README.

Es el único cambio a documentos. Un enlace a GitHub funciona igual en github.com y en el sitio.

## Risks / Trade-offs

- **[Riesgo] `reporte.html` abierto como archivo suelto se ve sin estilo y con el encabezado YAML a la vista.** →
  Aceptado en la exploración. El README documenta `scripts/sitio.sh serve`.
- **[Riesgo] Un experimento nuevo queda fuera de la barra lateral si nadie toca `_config.yml`.** → Just the Docs
  muestra las páginas sin `parent` en el primer nivel, así que no se pierden. El paso queda en `docs/metodo.md`
  § Agregar una hipótesis.
- **[Riesgo] Los enlaces `…/README.md` tienen que llevar a la página índice de la carpeta.** No está verificado que
  `jekyll-relative-links` resuelva un README convertido por `jekyll-readme-index`. → Lo detecta `scripts/sitio.sh`.
  Si falla, el enlace se escribe a la carpeta (`sensibilidad_muestra/`), que funciona en GitHub y en el sitio.
- **[Riesgo] Archivos sin seguimiento en la copia local** (por ejemplo `Experimentos guion.md` en la raíz) salen en el
  build local y no en CI. → Se compara contra CI solo lo commiteado. No se agrega un exclude para archivos ajenos.
- **[Riesgo] `jekyll-relative-links` y `jekyll-optional-front-matter` no son plugins por defecto de Jekyll 4.** → Van
  en el `Gemfile` y en `plugins:`. La tarea 1.x verifica que un `.md` sin encabezado sale como `.html` con el layout.
- **[Riesgo] La bitácora de `sampling_1` (1.223 líneas) es pesada para la búsqueda (`search.json`).** → Just the Docs
  indexa por sección. Si el índice pasa de unos pocos MB, se pone `search_exclude: true` en las bitácoras.
- **[Trade-off] Las URL largas (`/experimentos/h3/informe/informe.html`).** → Se acepta a cambio de no reescribir
  enlaces. Se navega con la barra lateral.
- **[Riesgo] El sitio publica solo lo commiteado.** Un reporte regenerado sin commit no aparece. → Es igual que hoy
  con el repo. No se agrega nada.

## Migration Plan

1. Agustina activa Pages con origen «GitHub Actions» (Settings → Pages, o
   `gh api -X POST repos/agustinarazanov/dmeyf-experimento-sampling/pages -f build_type=workflow`).
2. Se pushea `main`. El primer run publica.
3. **Rollback:** desactivar Pages o revertir el commit del workflow. Para volver al reporte autónomo, revertir el
   commit de `comun/reporte.py` y regenerar. No hay datos que migrar.

## Open Questions

- **Recuadros dentro de los documentos.** La sintaxis de Just the Docs (`{: .note }`) se ve como texto en github.com.
  Las alertas GFM (`> [!IMPORTANT]`) se ven bien en GitHub, pero en Jekyll necesitan un plugin extra. Se decide en un
  cambio posterior. En este, los recuadros van solo en la portada y en las páginas de sección.
- **Tablas desde `_data/`** (por ejemplo `tabla_resultados` leída del CSV del ledger) quedan para después.
