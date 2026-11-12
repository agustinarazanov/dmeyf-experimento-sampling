# Proposal

## Why

Los reportes del sitio se leen mal:
- casi todo está en texto y en tablas de 10 a 12 columnas;
- el reporte conjunto tiene solo seis figuras, y en la de tiempo contra ganancia las etiquetas se pisan;
- en escritorio la columna de contenido queda fija en 50rem y el resto de la pantalla queda vacío;
- algunas celdas son párrafos enteros: el bloque B llega a ~1.700 caracteres por fila, y las celdas tipo
  `277.79 (R=8)`, `pierde (réplica 0)` o `no aplica (K<2)` repiten notas.

Antes del video conviene que la respuesta a la pregunta del tutor (¿vale la pena el tradeoff entre velocidad y pérdida de
performance?) se vea en un gráfico, y que las tablas marquen lo que importa.

## What Changes

- **Más gráficos en el reporte, estáticos, generados por `comun/reporte.py` desde el ledger:**
  - A: el tradeoff por variante, con Δ e IC a la izquierda y aceleración A a la derecha, coloreado por veredicto;
  - B: Δ contra fracción de muestra, una línea por familia (U, H3, H3L, H3R, H4F);
  - C: tiempo contra ganancia rehecho, un panel por hipótesis, para que no se pisen las etiquetas;
  - D: tiempo igual con sus intervalos (réplicas y bootstrap de clientes);
  - E: las réplicas de cada variante como puntos, junto a las del control;
  - F: varianza, con barras de sd entre réplicas y sd entre semillas;
  - G: diferencias entre variantes, como gráfico de intervalos.
- **Figuras en SVG embebido** en lugar de PNG, para que se vean nítidas a cualquier ancho. Con `--figuras` se siguen
  guardando PNG para el video.
- **Página a lo ancho:**
  - en escritorio el contenido ocupa todo el ancho disponible;
  - el texto corrido queda limitado a ~75 caracteres por línea;
  - tablas y figuras usan todo el ancho, con desplazamiento horizontal propio en pantallas chicas.
- **Tablas simples en el HTML:**
  - el bloque A se divide en un resumen (variante, hipótesis, Δ, A, veredicto) y un detalle plegable con el resto;
  - una columna `R` para las réplicas;
  - el IC va en una segunda línea, chica y gris;
  - `—` con nota al pie en lugar de textos repetidos;
  - el veredicto va como etiqueta (*pill*);
  - el bloque B va como tarjetas, una por exploratorio.
- **Resaltado de resultados en las tablas numéricas:**
  - etiqueta de color por veredicto;
  - Δ en negrita cuando su IC no cruza 0, con color según el signo;
  - una barra mini del IC dentro de la celda de Δ;
  - en negrita el mejor de cada columna clave entre las variantes que no pierden: la mayor A y el mayor Δ.
- **`tabla_resultados.md` no cambia en el bloque A ni en las tablas de varianza y diferencias.** Sigue siendo la fuente
  auditable que copia `informe.md` y que lee `scripts/verificar_readme.py`. Solo su bloque B pasa de tabla a una lista
  por estudio, con los mismos datos.
- Los reportes por hipótesis (`h1`…`h4`, `control`) toman el mismo formato de tabla y de figuras.

Fuera de alcance:
- gráficos interactivos o bibliotecas de JavaScript;
- reescribir las tablas escritas a mano en los `informe.md` de `h3` y `h4`;
- cambiar números, veredictos o la forma de calcularlos.

## Capabilities

### New Capabilities
<!-- ninguna -->

### Modified Capabilities
- `reporte-visual`:
  - «Comparación de todas las variantes en una vista» suma los gráficos A–G y pide figuras vectoriales;
  - «Comparación limpia en dos bloques» separa el resumen del detalle en el HTML y pasa el bloque B a tarjetas;
  - se agregan «Página a lo ancho» y «Resultados resaltados»;
  - el invariante numérico pasa a ser que `tabla_resultados.md` no cambia. «Página del sitio, compartible» (de
    `sitio-github-pages`) no se toca; ver design.md, D7.

## Impact

- **`comun/reporte.py` (cambio en `comun/`, se anuncia en el commit):**
  - funciones de figura nuevas;
  - salida SVG;
  - `html_tabla` con clases de resaltado;
  - el bloque A del HTML dividido en resumen y detalle;
  - el bloque B en tarjetas.
- **`tests/test_reporte.py`:** tests nuevos para el SVG determinista, el resaltado y el resumen y detalle; los que
  comparan tablas pasan a comparar contra `tabla_resultados.md`.
- **`_sass/custom/`:** ancho del contenido, límite del texto, etiquetas, barras de IC y tarjetas.
- **`experimentos/sampling_1/informe/informe.md`:** cambia la copia del bloque B. Puede embeber figuras de `figuras/`.
- **Reportes regenerados:** los seis `reporte.html` y `tabla_resultados.md`.
- **Dependencias con otros cambios:**
  - `sitio-github-pages` (completo, sin archivar) se archiva antes, para que el requisito «Página del sitio, compartible»
    ya esté en `openspec/specs/`;
  - `final-con-julio-agosto` ya hizo sus cambios a `reporte.py` (2.5). Su 4.1 regenerará los reportes con el formato
    nuevo, así que este cambio no toca su ronda ni sus números.
