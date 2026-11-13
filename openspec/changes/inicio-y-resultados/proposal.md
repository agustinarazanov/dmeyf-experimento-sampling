# Proposal

## Why

Inicio es demasiado corto: tiene la pregunta, la respuesta, el mapa del tradeoff y las tarjetas, pero no dice por qué la
respuesta es esa. Por ejemplo, no dice que en el control la optimización es el 94 % del tiempo. Resultados, en cambio,
tiene 419 líneas con unas 12 tablas y 8 figuras, y mezcla tres lecturas:
- lo que hay que leer: respuesta, comparación, a tiempo igual, limitaciones y conclusiones;
- tablas de consulta: el bloque A completo para los verificadores, la varianza, las diferencias entre variantes y las
  rondas;
- método: predicción conjunta, diseño y bibliografía.

La respuesta y las conclusiones quedan separadas por unas 350 líneas. Además, la página se ve despareja: el texto va a
75ch, mientras que figuras, tablas, recuadros y plegables usan anchos distintos. Algunas líneas de código se cortan, y la
barra lateral nombra las hipótesis solo como «H1»…«H4». La entrega del video es el 23-nov y el sitio es lo que se
muestra.

## What Changes

- **Inicio pasa a ser un resumen ejecutivo** que se lee sin ir a Resultados:
  - pregunta y respuesta;
  - tres hallazgos, cada uno con su figura y 2 o 3 líneas: el mapa del tradeoff (qué vale la pena), el desglose del
    tiempo (por qué alcanza con achicar la optimización) y la comparación a tiempo igual (qué se hace con el tiempo
    ahorrado);
  - un recuadro con las tres limitaciones principales;
  - las tarjetas de hipótesis y el enlace a Resultados.

  Las figuras salen de bloques generados, con el título y los números de la ronda vigente.
- **Resultados se ordena por pregunta**, cada sección con su texto, su figura y el detalle plegado:
  - qué conviene achicar;
  - cuánto se puede achicar;
  - qué se hace con el tiempo ahorrado;
  - qué tan estable es el resultado entre semillas, réplicas y rondas.

  Después vienen las limitaciones comunes, las conclusiones y qué sigue. Conclusiones queda inmediatamente después de los
  hallazgos.
- **Página nueva «Anexo»** (`experimentos/sampling_1/anexo.md`), hija de Resultados en la barra lateral. Lleva el bloque
  A completo, la varianza entre réplicas y entre semillas, las diferencias entre variantes y la comparación entre
  rondas, con su figura y su texto. **BREAKING** para los verificadores y `scripts/comparar_rondas.py`: el bloque
  `bloque-a-completo` y el bloque `rondas` pasan de `sampling_1/README.md` a `sampling_1/anexo.md`.
- **Lo que no es resultado sale de Resultados:**
  - la predicción conjunta pasa a «Control y reglas» (`control/README.md`);
  - el diseño (protocolo de las corridas) pasa a «Corridas»;
  - la bibliografía pasa a «Cómo trabajamos» (`docs/metodo.md`).

  `## Dependencias` queda al final de Resultados, porque la lee `comun/variantes.py`.
- **Las figuras se pueden repetir entre páginas**, porque son el mismo SVG generado. Números y tablas siguen en un solo
  lugar: la tabla resumen del bloque A en Resultados y las tablas completas en el Anexo. Los números que Inicio escribe a
  mano los verifica `scripts/verificar_readme.py`, contra `bloque-a-completo`.
- **Barra lateral con el título de cada página**, por ejemplo «H4: Muestras informadas por clase» en lugar de «H4».
- **Un solo ancho de columna** para texto, figuras, código, recuadros y plegables. Una tabla más ancha que la columna se
  desplaza dentro de su recuadro. Reemplaza la regla vigente: texto a 75ch, y tablas y figuras sin tope.
- **Bloques de código que entran en la columna**: los comentarios largos de `corridas.md` y `docs/metodo.md` se cortan
  en varias líneas. Se borra § Devoluciones del curso de `corridas.md`.
- **Exploratorios, más amigable.** Hoy la página es texto más una lista de medianas de columnas crudas (por ejemplo,
  `g_201908: mediana 201,850,000`). Pasa a tener:
  - un diagrama de qué motivó cada estudio en el experimento: las réplicas de Optuna, H4 y las extensiones de H3, y la
    ronda de 20 semillas;
  - una sección por estudio con la pregunta en un recuadro, el protocolo, qué mostró, sus figuras, la advertencia en un
    recuadro y las cifras en una tabla numérica legible (M$ y etiquetas en lugar de nombres de columna), plegada;
  - **los gráficos de los compañeros:**
    - los nueve que están embebidos en los reportes HTML de `validacion_50_semillas` y `validacion_20_semillas`:
      contracción del IC con 10 y 50 semillas, ganancia del ensamble según K y dentro de 15 minutos, dispersión de las 50
      semillas, curvas con banda P10–P90 y bandas por hipótesis. Se extraen como archivos y se muestran con una
      leyenda que dice de qué reporte salen y qué protocolo tienen;
    - de `sensibilidad_muestra`, que no tiene gráficos, una figura generada desde su CSV.

  Los manifiestos `exploratorio.json` declaran sus figuras y la etiqueta y la escala de cada cifra. Sigue sin mostrarse
  el autor.
- **Gráficos equivalentes a los de los exploratorios, con los datos del experimento.** El generador suma cuatro formas
  que los reportes de los exploratorios usaban y el sitio no tiene:
  - **IC por ronda**: para cada variante, el IC de Δ de la ronda anterior y el de la vigente uno al lado del otro. Muestra
    cuánto se angosta con 20 semillas y con réplicas, y va al Anexo.
  - **Ensamble según K y según el tiempo**: la ganancia del ensamble de K semillas, por variante, contra K y contra el
    tiempo acumulado T_opt + K·T_final, con la línea del tiempo del control. Muestra qué se hace con el tiempo ahorrado y
    va a Resultados y a Inicio.
  - **Cajas por semilla**: la distribución de la ganancia de cada variante (caja, media y puntos) junto al control. Se
    suma al gráfico de semillas y réplicas.
  - **Curvas de ganancia por hipótesis**: la ganancia contra los envíos de cada variante y del control, con banda
    P10–P90 entre semillas y el corte N\*. Va a la página de cada hipótesis, junto a la curva de diferencia.
- **Corridas y Cómo trabajamos, con diagramas y secciones.** Corridas suma una línea de tiempo de las fases, un diagrama
  del recorrido de una corrida (VM, bucket, ledger, generador y páginas) y una sección o un ítem por fase. Hoy la tabla de
  fases lleva párrafos dentro de las celdas. Cómo trabajamos suma un diagrama de las etapas con sus compuertas de
  revisión, otro de cómo corre una etapa sin supervisión (aplicar, revisar, bloqueo) y otro de los pasos para agregar una
  hipótesis.
- **Encabezado** «Sampling_1 · DMEyF 2026»: en una línea en escritorio y, en el teléfono, en un encabezado más alto, con
  las dos partes en dos líneas.
- **Modo oscuro** con un botón en el encabezado, que el sitio recuerda entre visitas (lo trae el tema). Los colores
  propios (veredictos en tablas y pills, barras de IC) tienen su versión oscura, y las figuras se leen sobre fondo
  oscuro.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `sitio-informes`:
  - la portada como resumen ejecutivo con tres hallazgos;
  - el contenido publicado y la navegación suman el Anexo, y la barra lateral usa los títulos de las páginas;
  - en «Cada dato en un solo lugar», las figuras se pueden repetir y los números de la portada se verifican;
  - «Páginas de sección como índice» exceptúa a Resultados, que tiene contenido y una hija;
  - «Páginas con estructura visual» suma los diagramas de Corridas, Cómo trabajamos y Exploratorios;
  - «Encabezado que entra» pasa a «Sampling_1 · DMEyF 2026», con un encabezado más alto en el teléfono;
  - requerimiento nuevo de modo oscuro recordado.
- `reporte-visual`:
  - las tablas completas, la varianza, las diferencias y las rondas pasan a `sampling_1/anexo.md`;
  - Resultados se ordena por pregunta;
  - Inicio lleva tres figuras generadas;
  - el generador escribe también en páginas del experimento que no son su README;
  - «Página a lo ancho» pasa a un ancho único de columna;
  - el bloque B lleva figuras, un diagrama y cifras con etiqueta y escala;
  - cuatro gráficos nuevos: IC por ronda, ensamble según K y según el tiempo, cajas por semilla y curvas de ganancia
    por hipótesis.
- `protocolo-experimental`: el manifiesto `exploratorio.json` puede declarar figuras (archivo y leyenda) y la etiqueta y
  la escala de cada cifra.

## Impact

- **Documentos**: `index.md`, `experimentos/sampling_1/README.md` (reescrito), `experimentos/sampling_1/anexo.md`
  (nuevo), `experimentos/control/README.md` (§ Predicción conjunta), `experimentos/sampling_1/corridas.md`
  (§ Protocolo y comentarios de código), `docs/metodo.md` (§ Bibliografía y comentarios de código),
  `experimentos/sampling_1/docs/guion.md` (si cita secciones que se mudan).
- **Código**: `comun/reporte.py` (destinos y bloques nuevos: `hallazgo-*` en `index.md`; los de `anexo.md`),
  `scripts/comparar_rondas.py`, `scripts/verificar_readme.py` (lee `anexo.md` y revisa también `index.md`),
  `scripts/verificar_informe_h3.py`, `tests/test_reporte.py` y `tests/test_verificadores.py`. Un cambio en `comun/` se
  anuncia en el commit.
- **Sitio**: `mkdocs.yml` (nav con títulos y Anexo, lista blanca, paleta clara y oscura) y `sitio/estilos.css` (ancho
  único y colores oscuros).
- **Exploratorios**: `experimentos/sampling_1/exploratorios/README.md` (reescrito), los tres `exploratorio.json`
  (figuras, etiquetas y escalas), PNG extraídos de los reportes HTML en `<estudio>/figuras/` (por un script de una sola
  vez, reproducible), `comun/variantes.py` (valida los campos nuevos del manifiesto).
- **Sin cambios**: ledgers, números y veredictos. Las figuras existentes conservan su nombre de archivo; hay cuatro
  nuevas.
- **Cambio en curso**: `tiempos-confiables-y-consistencia` (en su rama) nombra `bloque-a-completo` en
  `sampling_1/README.md`. Al unir `main` en su rama, esas referencias pasan a `anexo.md`. Desde acá no se modifica.
