# Tasks

No requiere corridas ni datos. Cada grupo es una sesión (Sonnet salvo que diga otra cosa) y se commitea al cerrar.

## 1. Esqueleto del sitio (sesión: Sonnet)

- [x] 1.1 Crear `Gemfile` (D1: `jekyll ~> 4.3`, `just-the-docs`, `jekyll-optional-front-matter`, `jekyll-relative-links`, `jekyll-titles-from-headings`, `jekyll-readme-index`; `html-proofer` en el grupo `:test`), correr `bundle install` y commitear `Gemfile.lock` con la plataforma `x86_64-linux`; sumar `_site/`, `.jekyll-cache/`, `.sass-cache/`, `vendor/` y `.bundle/` a `.gitignore`; verificar que `bundle exec jekyll -v` imprime 4.x (hecho el 12-nov: Jekyll 4.4.1, Just the Docs 0.12.0)
- [x] 1.2 Crear `_config.yml` con el tema, `plugins:`, `exclude:` de D2, `optional_front_matter.remove_originals`, `readme_index` (D1), defaults de D3 (`layout: default` global; `render_with_liquid: false` solo en `experimentos`, `docs` y `openspec`), `search_enabled`, `callouts:` (`conclusion`, `limitacion`) y `aux_links` al repo; verificar con `bundle exec jekyll build` que `_site/` tiene `experimentos/h3/docs/hipotesis.html` con el layout del tema y que `find _site -name '*.py' -o -name '*.csv' -o -path '*openspec/changes*' -o -path '*ledger*'` no devuelve nada, que no hay `.md` crudos en `_site/` (`find _site -name '*.md'` vacío), que existen `_site/experimentos/h3/sensibilidad_muestra/index.html` y los `index.html` de los exploratorios, y que `du -sh _site` da del orden de MB (con 2 GB los excludes con barra final no están andando, ver D2)
- [x] 1.3 Crear `scripts/sitio.sh` (D6: build + `htmlproofer` con `--disable-external` y los `--ignore-files` de los originales de Luis; subcomando `serve`; acepta `--baseurl`); verificar que corre y listar en la bitácora de `sampling_1` los enlaces rotos que informa (se arreglan en 3.3)

## 2. Reporte como página del sitio (sesión: Sonnet; cambio en `comun/`)

- [x] 2.1 Foto previa: guardar las tablas de los seis `reporte.html` actuales en el scratchpad (mismo método que `scripts/foto_renombre.py`); verificar que hay seis archivos con las tablas
- [x] 2.2 `comun/reporte.py` (D4): `generar_con_tabla` devuelve el encabezado YAML mínimo más `cuerpo`, sin `<!doctype>`, `<html>`, `<head>`, `<title>` ni `<style>`; quitar `CSS` y pasar las reglas de veredicto, `.pend` e `img` a `_sass/custom/custom.scss`; actualizar el docstring y la ayuda; sumar a `tests/test_reporte.py` que la salida empieza con `---` y no contiene `<html` ni `<style`; verificar que `pytest` pasa
- [x] 2.3 Regenerar `python -m comun.reporte --todos` y comparar las tablas con la foto de 2.1; verificar diferencia 0 en todas las celdas salvo la fecha de generación, y que en `scripts/sitio.sh serve` las celdas de veredicto del reporte de `sampling_1` salen coloreadas; commitear con «Cambio en comun/: reporte.py emite una página Jekyll»

## 3. Navegación, portada y enlaces (sesión: Sonnet; la portada la revisa Opus en 5.1)

- [x] 3.1 Defaults de navegación en `_config.yml` según el árbol de D3 (title, parent, grand_parent, nav_order; bitácoras bajo «Proceso», specs bajo «Especificaciones») y las páginas de sección `sitio/{resultados,experimentos,proceso,especificaciones}.md`; verificar en `scripts/sitio.sh serve` que cada documento de la lista de la spec aparece una sola vez en la barra lateral, en su sección, y que buscar «GOSS» devuelve páginas de H2
- [x] 3.2 `index.md` (D5): pregunta del tutor, integrantes, tutor y comisión, recuadro `conclusion` con la respuesta tomada de `experimentos/sampling_1/informe/informe.md` § Conclusiones sin números nuevos, botón al informe conjunto y enlaces a tabla, Experimentos, Método y al README en github.com; verificar con un grep que cada número de la portada aparece en `tabla_resultados.md` o en el informe conjunto
- [x] 3.3 Reescribir a URL de github.com (`tree/main` o `blob/main`) solo los enlaces que `scripts/sitio.sh` marcó en 1.3 (carpetas `resultados/`, `originales/`, `requirements.txt`, los `.json`); verificar que `scripts/sitio.sh` termina sin enlaces rotos y que `scripts/verificar_readme.py` sigue sin ✗
- [x] 3.4 `README.md` de la raíz: enlace al sitio y sección «Ver el sitio localmente» (`bundle install`, `scripts/sitio.sh serve`); `docs/metodo.md` § Agregar una hipótesis: paso de sumar el experimento a los defaults de `_config.yml` con un ejemplo; verificar que los comandos documentados corren tal cual

## 4. Publicación (sesión: Sonnet)

- [x] 4.1 `.github/workflows/pages.yml` (D1): push a `main` y `workflow_dispatch`, `concurrency: pages`, permisos `pages: write` e `id-token: write`, `ruby/setup-ruby` con `bundler-cache`, `configure-pages`, `scripts/sitio.sh --baseurl <base_path>`, `upload-pages-artifact`, `deploy-pages`; verificar con `actionlint` si está instalado (si no, revisar a ojo contra la doc de `deploy-pages`) y localmente `scripts/sitio.sh --baseurl /dmeyf-experimento-sampling` sin enlaces rotos
- [ ] 4.2 Sumar `"sitio-github-pages"` a `ETAPA_DE_GRUPO_POR_CAMBIO` de `comun/tokens.py` (`1`–`4`: `codigo`, `5`: `informe`) con su test en `tests/test_tokens.py`; verificar que `pytest` pasa y anunciar el cambio en `comun/` en el commit

## 5. Revisión y puesta en línea

- [ ] 5.1 Revisión en sesión limpia (Opus o subagente `general-purpose`) con `docs/revision.md` § 3 (código) para `reporte.py`, `sitio.sh` y el workflow, y § 5 (informe) para la portada; cierre en la bitácora de `sampling_1` y `comun/tokens.py`; verificar que no quedan ✗ abiertos
- [ ] 5.2 Pushear `main` (lo hace Agustina; Pages ya está activado con origen «GitHub Actions» desde el 12-nov); verificar que el run del workflow termina en verde, que la portada abre en `https://agustinarazanov.github.io/dmeyf-experimento-sampling/` y que desde el informe de h1 el enlace `reporte.html` abre el reporte dentro del sitio

## Workflow follow-up

- Archivar con `/opsx:archive sitio-github-pages` cuando 5.2 esté hecho.
