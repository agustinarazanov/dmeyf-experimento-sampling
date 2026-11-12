# Tasks

Requiere `sitio-github-pages` archivado (D7). Cambia la presentación, no los cálculos. Cada grupo deja los tests
pasando: `python -m pytest tests/test_reporte.py`.

## 1. Preparación

- [x] 1.1 Archivar `sitio-github-pages` con `/opsx:archive`. Verificar que `openspec/specs/reporte-visual/spec.md` tiene
  «Página del sitio, compartible» y que `openspec validate reporte-graficos-y-ancho` pasa.
- [x] 1.2 Guardar una foto de la salida actual en el scratchpad, no en el repo: `tabla_resultados.md` y los seis
  `reporte.html`, regenerados con `python -m comun.reporte --todos`. Verificar que la regeneración no cambia el repo
  (`git status` limpio en `informe/`, salvo la fecha).

  Hecho con otra foto (12-nov): desde `final-con-julio-agosto` 2.5 el generador lee la ronda `201903-201908`, que
  todavía no tiene las semillas del control (todo sale pendiente), y los reportes commiteados son de antes de 2.5 (sin
  ΔAUC), así que `git status` no queda limpio por razones ajenas a este cambio. La foto es la salida del generador
  vigente con la ronda anterior (`VENTANA=201903-201906`, 10 semillas), verificada determinista en dos corridas; los
  tests nuevos usan esa misma ronda (fixture `ronda_anterior`).

## 2. Figuras en SVG (D1)

- [x] 2.1 Cambiar `png()` por `figura()` en `comun/reporte.py`:
  - SVG embebido en línea, con `svg.hashsalt` fijo, `svg.fonttype="none"` y sin `Date` ni `Creator`;
  - con `--figuras`, PNG a 200 dpi.

  Verificar con `test_dos_veces_da_lo_mismo` y con un test nuevo que el reporte no tenga `data:image/png` y tenga
  `<svg`.
- [x] 2.2 Actualizar el docstring del módulo (PNG base64 → SVG). Verificar con `grep -n "base64" comun/reporte.py`: no
  quedan menciones a figuras PNG embebidas.

## 3. Gráficos nuevos (D2–D4)

- [x] 3.1 `fig_tradeoff`: Δ e IC por veredicto a la izquierda y A en barras con la línea `A_VALE` a la derecha. Va
  primero en `html_resultados` y en cada reporte por hipótesis. Test: una variante por fila y el título presente en
  `sampling_1` y en `h1`.
- [x] 3.2 `fig_fraccion`: Δ contra `tasa`, una línea por `metodo` con dos tasas o más. Test: si se cambia el registro
  con `monkeypatch` para que ninguna familia tenga dos tasas, sale `pendiente` sin error.
- [x] 3.3 `fig_tiempo_ganancia_paneles`: un panel por hipótesis, control en cada uno, etiquetas desplazadas para no
  pisarse (D4). Reemplaza la figura vieja en el reporte conjunto. Test: dos etiquetas con el mismo (x, y) quedan
  separadas en la salida del desplazador.
- [x] 3.4 `fig_tiempo_igual_ic`: el tiempo igual con los dos intervalos (réplicas y bootstrap), cada uno con su marca.
  Verificar a ojo en la vista previa que los IC coinciden con la columna de la tabla para `H3-0.1`.
- [x] 3.5 `fig_replicas`, `fig_varianza` (barras) y `fig_diferencias` (gráfico de intervalos), debajo de su tabla.
  Test: con `rep` vacío, los tres salen `pendiente` y el reporte se genera.

## 4. Tablas simples (D5)

- [x] 4.1 Celdas estructuradas en `html_tabla`: valor, IC en `<span class="ic">` y clases. Cada tabla generada se
  envuelve en `.table-wrapper`. Verificar que los tests existentes siguen pasando.
- [x] 4.2 `celdas_resumen()`: bloque A del HTML con a lo sumo seis columnas visibles, columna `R`, `—` con nota al pie,
  y el resto dentro de `<details>`. Test del escenario «Resumen corto».
- [x] 4.3 Bloque B en tarjetas en el HTML y en lista por estudio en `tabla_resultados.md`. El exploratorio sin CSV
  sigue saliendo pendiente con el nombre del archivo; ajustar
  `test_exploratorio_sin_csv_sale_pendiente_con_el_nombre_del_archivo`.
> **En espera (12-nov, decisión de Agustina):** 4.4 y 7.1 se hacen después del 4.1 de `final-con-julio-agosto`.
> Con la ronda vigente (`201903-201908`) el generador deja todo pendiente hasta que el control tenga sus semillas, así
> que regenerar antes vaciaría los reportes publicados. La otra sesión avisa al terminar su 4.1. Entonces: regenerar,
> recopiar el bloque B en `informe.md` y verificar 7.1 contra los números nuevos. El invariante del bloque A ya se
> verificó contra la ronda `201903-201906` (ver 1.2).
>
> Retomado el 12-nov tras `final-con-julio-agosto` 4.1–4.3 (0f1e170): esa corrida ya regeneró los reportes con este
> generador y copió el bloque B (lista) en `informe.md`, así que regenerar acá solo cambió la fecha de los HTML.

- [x] 4.4 Recopiar el bloque B de `tabla_resultados.md` en `experimentos/sampling_1/informe/informe.md`. Verificar:
  - el bloque A, la varianza y las diferencias de `tabla_resultados.md` son idénticos a la foto de 1.2 (`diff`);
  - `python -m scripts.verificar_readme` pasa;
  - las líneas copiadas en `informe.md` coinciden con la tabla.

  Con la ronda nueva, la foto de comparación es la salida del generador de 6438a0d (antes de este cambio) sobre la
  misma ronda, en un worktree con los `ledger/predicciones` y `exploracion` enlazados (sin ellos el ensamble sale
  pendiente): el `diff` solo toca el bloque B (línea 81 en adelante). El bloque B de `informe.md` (líneas 208–254) es
  idéntico al de la tabla.

## 5. Resaltado (D8)

- [x] 5.1 Clases `sig-pos`/`sig-neg`, `mejor` y `pill` en el generador, y la barra del IC con escala común por columna
  y marca de 0. Tests:
  - `U0.05` lleva `sig-neg`;
  - una sola celda `mejor` por columna;
  - dos corridas, mismas clases.
- [x] 5.2 Los estilos en `_sass/custom/custom.scss`: `.pill`, `.ic`, `.icbar`, `.sig-*`, `.mejor` y `.tarjetas`, con
  los mismos colores de veredicto que hoy. Las reglas viejas `td.pierde`, `td.ok` y `td.ind` quedan para las tablas
  que todavía las usan. Verificar en la vista previa local que se ven la etiqueta y la barra.

## 6. Ancho de página (D6)

- [x] 6.1 `_sass/custom/setup.scss` con `$content-width` liberado, y en `custom.scss` el tope de ~75ch para el texto
  corrido.

  Cambio respecto de D6: `$content-width` no se toca, porque el tema arma con él los breakpoints `md` y `lg` y el
  centrado (con 100% o un tope en rem la barra lateral dejaría de aparecer). En `custom.scss`, `.main` sin `max-width`
  desde `md` y la barra lateral de ancho fijo desde `lg`. Medido con Chrome headless (12-nov): a 1920 y 1280 figuras y
  tablas llegan al borde de `.main-content` y los párrafos quedan en 756 px; a 390 (en un iframe, porque headless no
  baja de 500) `scrollWidth` = 390, con 5 tablas y 7 figuras desplazándose en su recuadro; build y htmlproofer pasan. Verificar con `scripts/sitio.sh serve` a 390, 1280 y 1920 px:
  - a 1920, figuras y tablas llegan al borde y los párrafos no;
  - a 390, la página no se desplaza en horizontal;
  - el build del sitio pasa con la verificación de enlaces.

## 7. Integración y cierre

- [x] 7.1 `python -m comun.reporte --todos --figuras`. Verificar:
  - `python -m pytest`;
  - `python -m comun.variantes --verificar`;
  - `python -m scripts.verificar_readme`;
  - el build del sitio;
  - el diff de `tabla_resultados.md` contra 1.2 solo cambia el bloque B.

  Commitear anunciando el cambio en `comun/`.

  12-nov: `--figuras` pide un directorio; los PNG fueron al scratchpad. Regeneración en 1 min 19 s. pytest 242 pasan,
  `variantes --verificar`, `verificar_readme` y `scripts/sitio.sh` (build y htmlproofer) pasan; el diff, en 4.4.
- [ ] 7.2 Revisión en sesión limpia según `docs/revision.md`. Anotar el cierre en la bitácora de `sampling_1` y correr
  `comun/tokens.py`.

## Workflow follow-up

- Archivar `reporte-graficos-y-ancho` con `/opsx:archive` después de la revisión. Si el escenario «Mismos números
  después del cambio de formato» choca con el delta, quitarlo en ese momento (D7).
