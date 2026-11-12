# Design

## Context

- **Generador.** `comun/reporte.py` arma cada `reporte.html` como página Jekyll, con estas piezas:
  - matplotlib (backend Agg);
  - la función `png()`, que embebe base64 y con `--figuras` guarda archivos;
  - `html_tabla()`, que solo colorea celdas de veredicto con `td.pierde`, `td.ok` y `td.ind`;
  - `markdown_resultados()`, que escribe `tabla_resultados.md`.
- **Tema.** just-the-docs fija `$content-width: 50rem`. Los estilos propios del sitio están en
  `_sass/custom/custom.scss`.
- **Determinismo.** `tests/test_reporte.py::test_dos_veces_da_lo_mismo` exige el mismo archivo en dos corridas salvo la
  fecha. Hoy se logra con `metadata={"Software": None}` en el PNG.
- **Verificadores.** `scripts/verificar_readme.py` lee `tabla_resultados.md`. Los `informe.md` copian sus bloques
  línea por línea.
- **Datos para los gráficos nuevos.** El dict `a` de `calcular_bloque_a` ya trae Δ, IC, A, T, réplicas, tiempo igual
  y bootstrap. `rep` trae la ganancia por réplica. `varianza()` y `pares_replicas()` traen F y G. No hace falta leer
  nada nuevo del ledger.

## Goals / Non-Goals

**Goals:**
- que cada gráfico salga de las mismas estructuras que ya alimentan las tablas, sin cálculos paralelos;
- que el HTML sea más simple sin tocar la fuente auditable (`tabla_resultados.md`).

**Non-Goals:**
- JavaScript, tooltips o gráficos interactivos;
- modo oscuro;
- tocar el layout del tema más allá del ancho;
- rehacer las bandas de curvas por hipótesis (solo pasan a SVG).

## Decisions

### D1. SVG embebido en línea, con salida determinista
`png()` pasa a ser `figura()`, que hace `savefig(format="svg")` y embebe el SVG en el HTML. Para que la salida sea
siempre la misma:
- `rcParams["svg.hashsalt"]` va fijo;
- `metadata={"Date": None, "Creator": None}`;
- `svg.fonttype = "none"`, así el texto queda como texto: más liviano, buscable y nítido.

Con `--figuras` se sigue guardando un PNG a 200 dpi para el video y el `informe.md`.

La alternativa era un PNG a 2x o 3x. Pesa más y sigue sin escalar; el SVG con unas 20 variantes pesa decenas de KB.

### D2. Un gráfico, una función, y todos leen `a`
Funciones nuevas:
- `fig_tradeoff`, el gráfico A;
- `fig_fraccion`, el B;
- `fig_tiempo_ganancia_paneles`, el C, que reemplaza a `fig_tiempo_ganancia_replicas` en el reporte conjunto;
- `fig_tiempo_igual_ic`, el D;
- `fig_replicas`, el E;
- `fig_varianza`, el F, rehecho con barras;
- `fig_diferencias`, el G.

Cada una recibe `ctx` y `a` (o `rep`) y devuelve el fragmento HTML, o `<p class='pend'>` si no hay datos.

En el gráfico B, la fracción es `Variante.tasa` y la familia es `Variante.metodo`, ambos del registro de
`comun/variantes.py`; no se parsean nombres. Entran las familias con dos tasas o más.

Los reportes por hipótesis usan `fig_tradeoff` filtrado a sus variantes.

### D3. El tradeoff (A) como dos paneles con el eje Y compartido
```
           Δ vs control (M$)                    A (x)
U0.05   |---*---|        :    |          #############
H3-0.1          :   |--*-|    |          ########
           -δ   0                          2 (umbral A_VALE)
```
- Eje Y: las variantes agrupadas por hipótesis, en el mismo orden que la tabla.
- Panel izquierdo: puntos con IC (de réplicas si existe, si no de la réplica 0), coloreados por veredicto, con líneas
  en 0 y en −δ.
- Panel derecho: barras de A con una línea en `A_VALE`.

Los colores de veredicto son los mismos de `custom.scss`, con un tono más saturado para las marcas. La hipótesis va en
la etiqueta del eje, no en el color, para que no compitan dos codificaciones de color.

### D4. Tiempo contra ganancia (C) en paneles por hipótesis
Un panel por hipótesis con el eje Y compartido, y el control (punto y línea −δ) en cada uno. Con unas 4 a 7 variantes
por panel se pueden etiquetar todas. Para evitar que se pisen, cada etiqueta se corre en vertical cuando choca con la
anterior del mismo panel (orden por y). Esto es determinista y no necesita `adjustText`.

### D5. Tablas del HTML: resumen y detalle sin tocar el markdown
`calcular_bloque_a` sigue igual. Las celdas que ve cada salida son distintas:
- `celdas_bloque_a()` sigue alimentando `tabla_resultados.md`, sin cambios;
- una nueva `celdas_resumen()` arma las celdas para el HTML.

`html_tabla` acepta celdas estructuradas (`valor`, `ic`, `clases`) además de texto. Así el IC va en
`<span class="ic">`, y la barra va en `<span class="icbar" style="--l:..;--r:..;--z:..">`, con la escala común
calculada por columna.

El detalle va en `<details><summary>Detalle del bloque A</summary>…</details>`. El tema ya estiliza `details`.

Bloque B:
- en el HTML, `<div class="tarjetas">` con un `<article>` por exploratorio;
- en el markdown, una lista `### carpeta` con viñetas.

### D6. Ancho y largo de línea con CSS, sin tocar el tema
- En `_sass/custom/setup.scss`, `$content-width: 100%` (o un tope grande, como 120rem, si el tema rompe con 100%). Eso
  libera `.main`.
- En `custom.scss`, `.main-content > p, li, blockquote, dl { max-width: 75ch; }`.
- Tablas y figuras sin tope. El tema ya envuelve las tablas en `.table-wrapper` con `overflow-x: auto`. Las tablas
  generadas por `reporte.py` se envuelven igual, con `<div class="table-wrapper">`.

La alternativa era limitar todo el contenido a ~75ch. Se descartó porque deja otra vez el espacio vacío que motivó el
cambio.

### D7. Invariante numérico y relación con `sitio-github-pages`
El escenario «Mismos números después del cambio de formato» de `sitio-github-pages` comparaba celda por celda el HTML.
Era una garantía de esa migración y deja de aplicar cuando el HTML se simplifica. El invariante vigente pasa a ser
«Tabla de resultados intacta»: `tabla_resultados.md` idéntica, y `verificar_readme` y las copias de los `informe.md`
sin cambios.

Orden de los cambios: primero se archiva `sitio-github-pages`, y este cambio se archiva después. Si al archivar el
escenario viejo queda en conflicto, se lo borra en una edición del delta en ese momento.

### D8. Resaltado: reglas en el generador, colores en el SCSS
El generador asigna clases y el SCSS pone los colores.

| Clase | Regla |
|---|---|
| `sig-pos` / `sig-neg` | el IC excluye 0 |
| `mejor` | máximo de la columna entre las variantes con veredicto «no pierde» |
| `pill pierde\|ok\|ind\|pend` | el veredicto |

Para que nada dependa solo del color, se suman negrita, el signo del número y el texto de la etiqueta.

## Risks / Trade-offs

- [SVG no determinista entre versiones de matplotlib] → El test compara dos corridas en el mismo entorno. Las
  versiones fijadas en `requirements.txt` evitan diferencias entre máquinas.
- [`$content-width: 100%` rompe el cálculo del tema en algún breakpoint] → Probar con `scripts/sitio.sh serve` a 390,
  1280 y 1920 px. Si falla, usar un tope en rem.
- [Más gráficos hacen más larga la página] → El reporte conjunto queda ordenado así: tradeoff, tiempo contra ganancia
  y tiempo igual arriba; réplicas, varianza y diferencias debajo de las tablas que explican; el detalle plegado.
- [`informe.md` de `sampling_1` copia el bloque B en formato tabla] → Se recopia con el formato de lista en la misma
  tarea en que cambia el generador, y se verifica con un diff contra `tabla_resultados.md`.
- [El 4.1 de `final-con-julio-agosto` regenera con números nuevos] → Este cambio no toca cálculos, solo presentación.
  Si su 4.1 corre antes o después, el resultado es el mismo formato con los números de la ronda vigente.

## Migration Plan

1. Archivar `sitio-github-pages`.
2. Implementar, regenerar con `python -m comun.reporte --todos --figuras`, y comparar `tabla_resultados.md` con el
   anterior con `git diff`: solo cambia el bloque B.
3. Hacer la vista previa local en tres anchos.

Rollback: revertir el commit; los reportes se regeneran con el generador anterior.
