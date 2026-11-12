# Tasks

Requiere `sitio-github-pages` archivado (D7). Cambia la presentación, no los cálculos. Cada grupo deja los tests
pasando: `python -m pytest tests/test_reporte.py`.

## 1. Preparación

- [ ] 1.1 Archivar `sitio-github-pages` con `/opsx:archive`. Verificar que `openspec/specs/reporte-visual/spec.md` tiene
  «Página del sitio, compartible» y que `openspec validate reporte-graficos-y-ancho` pasa.
- [ ] 1.2 Guardar una foto de la salida actual en el scratchpad, no en el repo: `tabla_resultados.md` y los seis
  `reporte.html`, regenerados con `python -m comun.reporte --todos`. Verificar que la regeneración no cambia el repo
  (`git status` limpio en `informe/`, salvo la fecha).

## 2. Figuras en SVG (D1)

- [ ] 2.1 Cambiar `png()` por `figura()` en `comun/reporte.py`:
  - SVG embebido en línea, con `svg.hashsalt` fijo, `svg.fonttype="none"` y sin `Date` ni `Creator`;
  - con `--figuras`, PNG a 200 dpi.

  Verificar con `test_dos_veces_da_lo_mismo` y con un test nuevo que el reporte no tenga `data:image/png` y tenga
  `<svg`.
- [ ] 2.2 Actualizar el docstring del módulo (PNG base64 → SVG). Verificar con `grep -n "base64" comun/reporte.py`: no
  quedan menciones a figuras PNG embebidas.

## 3. Gráficos nuevos (D2–D4)

- [ ] 3.1 `fig_tradeoff`: Δ e IC por veredicto a la izquierda y A en barras con la línea `A_VALE` a la derecha. Va
  primero en `html_resultados` y en cada reporte por hipótesis. Test: una variante por fila y el título presente en
  `sampling_1` y en `h1`.
- [ ] 3.2 `fig_fraccion`: Δ contra `tasa`, una línea por `metodo` con dos tasas o más. Test: si se cambia el registro
  con `monkeypatch` para que ninguna familia tenga dos tasas, sale `pendiente` sin error.
- [ ] 3.3 `fig_tiempo_ganancia_paneles`: un panel por hipótesis, control en cada uno, etiquetas desplazadas para no
  pisarse (D4). Reemplaza la figura vieja en el reporte conjunto. Test: dos etiquetas con el mismo (x, y) quedan
  separadas en la salida del desplazador.
- [ ] 3.4 `fig_tiempo_igual_ic`: el tiempo igual con los dos intervalos (réplicas y bootstrap), cada uno con su marca.
  Verificar a ojo en la vista previa que los IC coinciden con la columna de la tabla para `H3-0.1`.
- [ ] 3.5 `fig_replicas`, `fig_varianza` (barras) y `fig_diferencias` (gráfico de intervalos), debajo de su tabla.
  Test: con `rep` vacío, los tres salen `pendiente` y el reporte se genera.

## 4. Tablas simples (D5)

- [ ] 4.1 Celdas estructuradas en `html_tabla`: valor, IC en `<span class="ic">` y clases. Cada tabla generada se
  envuelve en `.table-wrapper`. Verificar que los tests existentes siguen pasando.
- [ ] 4.2 `celdas_resumen()`: bloque A del HTML con a lo sumo seis columnas visibles, columna `R`, `—` con nota al pie,
  y el resto dentro de `<details>`. Test del escenario «Resumen corto».
- [ ] 4.3 Bloque B en tarjetas en el HTML y en lista por estudio en `tabla_resultados.md`. El exploratorio sin CSV
  sigue saliendo pendiente con el nombre del archivo; ajustar
  `test_exploratorio_sin_csv_sale_pendiente_con_el_nombre_del_archivo`.
- [ ] 4.4 Recopiar el bloque B de `tabla_resultados.md` en `experimentos/sampling_1/informe/informe.md`. Verificar:
  - el bloque A, la varianza y las diferencias de `tabla_resultados.md` son idénticos a la foto de 1.2 (`diff`);
  - `python -m scripts.verificar_readme` pasa;
  - las líneas copiadas en `informe.md` coinciden con la tabla.

## 5. Resaltado (D8)

- [ ] 5.1 Clases `sig-pos`/`sig-neg`, `mejor` y `pill` en el generador, y la barra del IC con escala común por columna
  y marca de 0. Tests:
  - `U0.05` lleva `sig-neg`;
  - una sola celda `mejor` por columna;
  - dos corridas, mismas clases.
- [ ] 5.2 Los estilos en `_sass/custom/custom.scss`: `.pill`, `.ic`, `.icbar`, `.sig-*`, `.mejor` y `.tarjetas`, con
  los mismos colores de veredicto que hoy. Las reglas viejas `td.pierde`, `td.ok` y `td.ind` quedan para las tablas
  que todavía las usan. Verificar en la vista previa local que se ven la etiqueta y la barra.

## 6. Ancho de página (D6)

- [ ] 6.1 `_sass/custom/setup.scss` con `$content-width` liberado, y en `custom.scss` el tope de ~75ch para el texto
  corrido. Verificar con `scripts/sitio.sh serve` a 390, 1280 y 1920 px:
  - a 1920, figuras y tablas llegan al borde y los párrafos no;
  - a 390, la página no se desplaza en horizontal;
  - el build del sitio pasa con la verificación de enlaces.

## 7. Integración y cierre

- [ ] 7.1 `python -m comun.reporte --todos --figuras`. Verificar:
  - `python -m pytest`;
  - `python -m comun.variantes --verificar`;
  - `python -m scripts.verificar_readme`;
  - el build del sitio;
  - el diff de `tabla_resultados.md` contra 1.2 solo cambia el bloque B.

  Commitear anunciando el cambio en `comun/`.
- [ ] 7.2 Revisión en sesión limpia según `docs/revision.md`. Anotar el cierre en la bitácora de `sampling_1` y correr
  `comun/tokens.py`.

## Workflow follow-up

- Archivar `reporte-graficos-y-ancho` con `/opsx:archive` después de la revisión. Si el escenario «Mismos números
  después del cambio de formato» choca con el delta, quitarlo en ese momento (D7).
