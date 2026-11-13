# Design

## Context

La motivación está en `proposal.md`. El estado actual que condiciona el enfoque:

- **Generador.** `comun/reporte.py` escribe bloques entre `<!-- generado:… -->` en las páginas que devuelve
  `destinos(exp)`. Para `sampling_1` escribe `mapa`, `bloque-a`, `bloque-a-completo`, `varianza`, `diferencias`,
  `tiempo-igual` y `figuras` en `sampling_1/README.md`, y `bloque-b` en `exploratorios/README.md`. En `index.md` y
  `sitio/hipotesis/README.md` escribe `tarjetas`. `scripts/comparar_rondas.py` escribe `rondas`. Si falta un marcador,
  falla sin escribir nada.
- **Verificadores.** `scripts/verificar_readme.py` y `scripts/verificar_informe_h3.py` leen `bloque-a-completo` de
  `sampling_1/README.md`. Sus tests están en `tests/test_verificadores.py`.
- **Dependencias.** `comun/variantes.py` lee `## Dependencias` del README de cada experimento, `sampling_1` incluido.
- **Datos para las figuras nuevas.** Ya existen:
  - curvas por semilla en `ledger/curvas/`, que hoy usa `fig_curva_diferencia`;
  - predicciones por semilla en `ledger/predicciones/`, que hoy usa el bootstrap de tiempo igual (`_probs`);
  - tiempos por fase en `estudios.csv` y `resultados.csv`;
  - el ledger de la ronda anterior en `ledger/ronda_201903-201906/`, que hoy usa `fig_rondas`.

  No hace falta correr nada.
- **Gráficos de los compañeros.** Los reportes de los exploratorios son HTML con PNG embebidos en base64: cuatro en
  `validacion_20_semillas/originales/reporte_h{1..4}.html` y cinco en `validacion_50_semillas/reporte_original.html` y
  `resultados/reporte_50_semillas_original.html`. `sensibilidad_muestra` no tiene gráficos, pero sí CSV
  (`08_ganancia_por_semilla.csv`).
- **Sitio.** MkDocs Material 9.8.1 con `navigation.indexes`. El nav tiene etiquetas cortas («H1»…). El CSS limita el
  texto a 75ch, mientras las figuras y las tablas ocupan todo el ancho, así que hay anchos distintos. Hay un solo modo
  de color.
- **Cambio en paralelo.** `tiempos-confiables-y-consistencia` corre en su rama, y sus tareas nombran
  `bloque-a-completo` en `sampling_1/README.md`.

## Goals / Non-Goals

**Goals:**
- Que Inicio cuente el resultado completo en una pantalla y media, y que Resultados se lea de arriba abajo sin tablas
  de consulta en el medio.
- Que los gráficos que hicieron los compañeros aparezcan, y que los datos del experimento tengan sus equivalentes.
- Que todas las páginas tengan una sola columna y un modo oscuro que se recuerda.
- Que lo que hoy pasa (generador, verificadores, `variantes --verificar`, `sitio.sh`) siga en verde después de mover
  bloques.

**Non-Goals:**
- Cambiar números, veredictos, ledgers o corridas.
- Rehacer los gráficos de los exploratorios con su protocolo: se muestran tal como salieron de sus reportes. Lo único
  generado de nuevo para un exploratorio es la figura de `sensibilidad_muestra`, desde su CSV.
- Gráficos interactivos.
- Tocar `tiempos-confiables-y-consistencia`.

## Decisions

### D1. Mapa de páginas y bloques

| página | bloques generados | contenido escrito a mano |
|---|---|---|
| `index.md` (Inicio) | `hallazgo-tradeoff`, `hallazgo-tiempo`, `hallazgo-ensamble`, `tarjetas` | pregunta, respuesta, 2–3 líneas por hallazgo, recuadro de limitaciones, botón |
| `sampling_1/README.md` (Resultados) | `mapa`, `grilla`, `desglose`, `bloque-a`, `fraccion`, `ensamble`, `tiempo-igual`, `semillas` | las cuatro preguntas, limitaciones, conclusiones, qué sigue, exploratorios en una línea, dependencias |
| `sampling_1/anexo.md` (Anexo, nuevo) | `bloque-a-completo`, `varianza`, `diferencias`, `ic-rondas`, `rondas` | una línea por sección y el resultado de la predicción de la ronda |
| `sampling_1/exploratorios/README.md` | `bloque-b` (una sección por estudio, con figuras y cifras) | diagrama de motivaciones, texto por estudio |
| `hN/README.md` | `resultado` (suma las curvas de ganancia) | sin cambios |

Hoy el bloque `figuras` tiene tres figuras juntas. Se separa en `grilla`, `desglose` y `fraccion`, para que cada una
quede en la sección de su pregunta.

Resultados, de arriba abajo:
1. Pregunta y respuesta.
2. ¿Qué conviene achicar? Lleva la grilla, el desglose, el bloque A resumen con el detalle plegado y los hallazgos por
   hipótesis.
3. ¿Cuánto se puede achicar? Lleva Δ contra tasa.
4. ¿Qué se hace con el tiempo ahorrado? Lleva el ensamble según el tiempo y el tiempo igual con su tabla plegada.
5. ¿Qué tan estable es? Lleva las cajas por semilla, el resumen de rondas en tres puntos con enlace al Anexo, y AUC y
   ganancia.
6. Limitaciones comunes.
7. Conclusiones.
8. Qué sigue.
9. Exploratorios, en una línea.
10. Dependencias.

Se mudan:
- la predicción conjunta, a `control/README.md` § Predicción, como «Predicción del experimento (1-nov)»;
- el diseño, a `corridas.md` § Protocolo;
- la bibliografía, a `docs/metodo.md` § Bibliografía.

En Resultados, Conclusiones dice si la predicción acertó, y enlaza.

Alternativa descartada: partir Resultados en una página por pregunta. Son más clics, y el escenario «cada resultado en
una sola página» se cumple igual con el Anexo.

### D2. El generador escribe en más de un archivo por experimento

`destinos(exp)` ya devuelve una lista de páginas. Para `sampling_1` suma `anexo.md` e `index.md` con sus bloques. La
validación de marcadores de todas las páginas sigue ocurriendo antes de escribir. `scripts/comparar_rondas.py` pasa a
escribir `rondas` en `anexo.md`. Los verificadores leen `bloque-a-completo` de `anexo.md`.

`verificar_readme.py` revisa además los números escritos a mano de `index.md` y de `sampling_1/README.md` fuera de los
marcadores. Cada número se busca en `bloque-a-completo` y en los títulos de las figuras generadas. Así, el 94 % de la
portada se valida contra el título del desglose.

### D3. Figuras nuevas, equivalentes a las de los exploratorios

Antes de escribir código de gráficos se carga la skill `dataviz`. Las figuras siguen las reglas de `reporte-visual`:
título que dice qué mirar, sin etiquetas pisadas, pendiente sin datos y SVG con `hashsalt` fijo.

| figura | archivo | forma | datos | página |
|---|---|---|---|---|
| ensamble según K y según el tiempo | `ensamble.svg` | dos paneles: G del ensamble de las primeras K semillas contra K, y contra T_opt + K·T_final; una línea por variante que vale la pena más el control; línea vertical en T(C) | `ledger/predicciones/` (como `_probs`) y tiempos | Resultados (pregunta 4), Inicio |
| cajas por semilla | `semillas_replicas.svg` (se amplía) | caja Q1–Q3 con media y puntos por semilla; réplicas con otro marcador | `resultados.csv`, `replicas.csv` | Resultados (pregunta 5) |
| IC por ronda | `ic_rondas.svg` | por variante, dos segmentos de IC (ronda anterior gris, vigente color), −δ punteado | ledger de la ronda anterior y vigente | Anexo |
| curvas de ganancia | `curvas_<H>.svg` | paneles por variante; G contra envíos con banda P10–P90 de la variante y del control, mediana punteada del control, N\* | `ledger/curvas/` | página de cada hipótesis |
| sensibilidad de la muestra | `exploratorios/figuras/sensibilidad_muestra.svg` | Δ de ganancia por muestra (puntos con su mediana), en M$ | `08_ganancia_por_semilla.csv` | Exploratorios |

El ensamble según K se calcula con las mismas probabilidades y el mismo corte N\* que el tiempo igual, sin bootstrap. Se
dibuja solo para las variantes que valen la pena (A ≥ 2, *no pierde*) más el control, para que las líneas se lean. La
leyenda va al costado, no encima.

### D4. Gráficos originales de los exploratorios

Un script de una sola vez, `scripts/extraer_figuras_exploratorios.py`, decodifica los PNG embebidos y los guarda en
`<estudio>/figuras/<nombre>.png`. El nombre sale del `alt` o del título previo. El script es determinista: correrlo dos
veces da los mismos bytes. Cada `exploratorio.json` suma:

```json
"figuras": [{"archivo": "figuras/contraccion_ic.png", "leyenda": "Reporte original (50 semillas, hiperparámetros fijos): IC de Δ con 10 y con 50 semillas"}],
"tablas": [{"csv": "...", "columnas": [{"columna": "g_201908", "etiqueta": "G en 201908", "escala": 1e-6, "unidad": "M$"}]}]
```

Las columnas como texto (formato viejo) siguen valiendo, para no romper un manifiesto que no se actualice.
`comun/variantes.py --verificar` falla si una figura declarada no existe. En `sensibilidad_muestra` la figura se declara
con `"csv"` y `"columna"` en lugar de `"archivo"`, y la genera el bloque B. La leyenda dice de qué reporte o de qué CSV
sale la figura, no quién la hizo. La lista blanca de `mkdocs.yml` suma `!/experimentos/**/figuras/**` para las figuras
de los estudios.

### D5. Diagramas (Mermaid, escritos a mano)

- **Exploratorios:** `sensibilidad_muestra` lleva a R = 8 réplicas; `validacion_50_semillas` lleva a H4 y a las
  extensiones de H3; `validacion_20_semillas` lleva a la ronda vigente con 20 semillas. Se aclara que ninguno decide un
  veredicto.
- **Corridas:**
  - línea de tiempo de las fases 1 a 7 con sus fechas (`gantt` o `timeline`);
  - recorrido de una corrida: `lanzar_fase.sh`, VM, bucket, `gsutil rsync`, ledger, `comun/reporte.py` y páginas;
  - la tabla de fases queda con columnas cortas (fase, fecha, tag, VMs, carga) y lo que corrió cada fase pasa a una
    lista debajo.
- **Cómo trabajamos:**
  - etapas (hipótesis, diseño, código, corridas, análisis, informe), con la revisión en sesión limpia en cada
    compuerta y el modelo de cada una;
  - una etapa sin supervisión: `etapas.sh`, `etapa.sh`, aplicar, revisar, y `bloqueo.txt` o `en_curso.txt`;
  - los pasos de § Agregar una hipótesis como diagrama, antes de la lista.

Mermaid se adapta solo al modo oscuro de Material.

### D6. Una columna y modo oscuro

- **Columna:** `.md-content__inner` tiene un ancho máximo fijo (~36rem, unos 85–90 caracteres de texto; se ajusta
  midiendo), y todo lo de adentro ocupa el 100 %: párrafos, figuras, código, recuadros y plegables. Se quitan los topes
  de 75ch y la regla `calc(89ch …)` de los recuadros. Una tabla más ancha se desplaza en su recuadro. En el teléfono las
  figuras siguen con su ancho mínimo y su desplazamiento propio. Las líneas de código publicadas se cortan a mano en el
  texto, porque no se usa ajuste automático, que rompe los comandos.
- **Modo oscuro:** `theme.palette` con dos esquemas (`default` y `slate`), cada uno con su `toggle` (icono y
  etiqueta), y `media: "(prefers-color-scheme: …)"` para la primera visita. Material guarda la elección en
  `localStorage` (documentado en «Changing the colors › Color palette toggle»). En `sitio/estilos.css`, los colores de
  veredicto, pills, `.icbar` e `.ic` pasan a variables CSS con valores para `[data-md-color-scheme="slate"]`.
- **Figuras en oscuro:** las figuras conservan su fondo blanco (lo tienen los SVG generados y los PNG de los
  exploratorios), con un borde redondeado y un margen interno. Así se leen igual en los dos modos, sin regenerar.
  Alternativa descartada: fondo transparente y texto con `currentColor`. No funciona en `<img>` y rompería los PNG del
  video.

### D7. Barra lateral con títulos

En `nav` las páginas van sin etiqueta, y MkDocs toma el título de su H1: «H4 · Muestras informadas por clase»,
«Control y reglas», «Anexo de resultados». Las secciones conservan su etiqueta («Hipótesis», «Cómo medimos»).
Resultados se vuelve sección, con `sampling_1/README.md` como índice y `anexo.md` como hija. Con `navigation.indexes`,
el README es el índice. `anexo.md` no se llama README, así que no lo toma por índice.

### D7b. Encabezado

`site_name: Sampling_1 · DMEyF 2026`. En pantallas angostas (menos de 60em, donde Material esconde la barra lateral),
`sitio/estilos.css` sube la altura de `.md-header` (por ejemplo, a 3.6rem) y muestra el título en dos líneas. Para eso,
un override del parcial `header.html` (`theme.custom_dir: sitio/overrides`) envuelve «DMEyF 2026» en un `<span>` que en
escritorio va en línea y en el teléfono pasa a la segunda línea, en letra más chica. Hay que ajustar el desplazamiento
del contenido y del menú lateral (`.md-main`, `.md-sidebar`), que asumen la altura estándar. Alternativa descartada:
achicar la letra hasta que entre en una línea, porque a 390 px se lee mal.

### D8. Inicio sin copiar

El texto de cada hallazgo explica qué mirar y por qué, en 2–3 líneas. Los números que escribe a mano (por ejemplo,
94 %) los valida D2. El recuadro de limitaciones resume tres de las de Resultados («Test ya mirado», «Un mes, un año,
una máquina», «Réplicas solo en parte de las variantes») en una línea cada una, con enlace a Resultados § Limitaciones
comunes.

### D9. Tablas de resultado sin columnas redundantes (agregado el 13-nov)

El bloque `resultado` de cada `hN/README.md` es la tabla que se lee en la página de la hipótesis. No repite lo que ya es
igual en todas sus filas:

- **hipótesis**: no va en la página de una sola hipótesis; sigue en Resultados y en el Anexo, donde hay varias.
- **semillas**: si todas las filas tienen las mismas semillas (hoy 20), la columna no va y una línea debajo de la tabla lo
  dice («Todas las variantes con 20 semillas»). Las 20 semillas, como regla, quedan en Control y reglas. Si una fila
  difiere, la columna vuelve.
- **semillas ganadas**: una barrita de proporción en la celda (ganadas sobre el total, con el número al lado), en lugar de
  «14/20». Se descarta la torta: una torta por fila no se compara entre filas, y las barras alineadas sí.
- **A** pasa a llamarse **aceleración (×)** en todas las tablas y figuras: A es T(C) / T(variante), no AUC, y la letra sola
  se confunde con el AUC de la columna de al lado.
- **veredicto** y **vale la pena** se distinguen desde el encabezado: «ganancia contra el control» (gana, no pierde,
  pierde, indeterminado) y «vale la pena (no pierde y ≥ 2×)».

El bloque A completo del Anexo conserva todas sus columnas, porque es la tabla de consulta, con los encabezados nuevos.
Los verificadores leen los encabezados nuevos.

### D10. Figura del tradeoff en filas (agregado el 13-nov)

`tradeoff.svg` deja de ser un solo gráfico de dispersión de 12 pulgadas (Δ contra A en escala log, con 21 etiquetas que
se pisan alrededor de 4,5×) y pasa a **cuatro paneles de 2 × 2, uno por hipótesis** (D16):

- en cada panel, Δ con su IC contra la aceleración en escala log, con los ejes compartidos;
- el control como referencia en (1×, 0), la línea de 2× y −δ punteado;
- el color de la hipótesis;
- las variantes que pierden, con el marcador vacío;
- las que valen la pena, con su etiqueta en negrita.

Con 4 a 9 variantes por panel, las etiquetas no se pisan. `ANCHO` baja para que la letra de las figuras no quede más
chica que la del texto al escalar a la columna. El escenario «Ver el tradeoff de un vistazo» cambia en consecuencia.

### D11. Veredicto y Limitaciones sin pila de recuadros (agregado el 13-nov)

En cada `hN/README.md`, en `control/README.md` y en Resultados:

- **Veredicto** lleva un solo recuadro, el de la conclusión, primero. Las reglas o rondas que la sostienen van debajo
  como lista: el resultado en negrita y una o dos líneas.
- **Limitaciones** va sin recuadros: una lista con el nombre de la limitación en negrita y una o dos líneas cada una.

El texto no se pierde, solo cambia de forma (el grupo 2 lo compara contra el commit previo).

### D12. Diagramas que entran en la columna (agregado el 13-nov)

Los diagramas Mermaid de las hipótesis (`flowchart LR` con seis o siete nodos) se escalan hasta que la letra no se lee.
Pasan a `flowchart TB`, o a dos filas, con etiquetas cortas, de modo que a 1440 px el diagrama entre en la columna con
su letra a tamaño de texto.

### D13. Barras laterales (agregado el 13-nov)

Se revierte el «nombre del sitio oculto arriba de la barra lateral» de `sitio/estilos.css`: la barra izquierda vuelve a
mostrar su título. Las dos barras, en escritorio:

- arrancan con el mismo espacio arriba, más chico que el de Material;
- llevan el mismo título (versalitas chicas con una línea debajo) y un recuadro de fondo tenue;
- la página activa y la sección que se lee se marcan con una barrita del color de acento y fondo suave;
- los subniveles van con sangría y una guía vertical.

Los colores salen de las variables del tema, así que valen en los dos modos. Esta tarea la hace el orquestador, con
capturas.

### D14. Vocabulario: clientes contactados (agregado el 13-nov)

«Envíos» viene de la competencia (a cuántos clientes se les manda el estímulo), y en el sitio se lee como si algo se
enviara. Pasa a «clientes contactados»: N\* = 3.300 clientes contactados, ejes «N clientes contactados». Lo cambia el
generador (ejes, títulos y textos de `comun/reporte.py`), y el grupo 2 cambia el texto escrito a mano. Las variables y
columnas de los CSV no cambian.

Los gráficos contra clientes contactados (`curvas_<H>.svg` y la curva de diferencia de cada hipótesis) van **siempre en
dos columnas** de paneles, con las filas que hagan falta, en lugar de `min(n, 3)`.

### D15. Estudios y réplicas, dichos en palabras (agregado el 13-nov)

La tabla de § Variantes de cada hipótesis tiene la columna «estudio (réplica 0 / réplica k ≥ 1)» con valores como
«`U0.25` / `U0.25@k`», que no se entienden sin leer § Estudios y réplicas. Pasa a decirse en palabras:

- la columna se llama «búsqueda de hiperparámetros»;
- una línea antes de la tabla explica la notación: un *estudio* es una búsqueda de Optuna; `U0.25` busca sobre una
  muestra uniforme del 25 % de train; `U0.25@k` es la misma búsqueda repetida con semilla k (las *réplicas*, que miden
  cuánto depende el resultado de la suerte de la búsqueda); la réplica 0 es la búsqueda original.

Los ids no cambian, porque son los del ledger.

### D16. Resultados dividido por hipótesis, con un color por hipótesis (agregado el 13-nov)

Las figuras y tablas de Resultados muestran las 21 variantes a la vez. Al ancho de la columna son más altas que la
pantalla y no se encuentra nada. Tres reglas:

- **Un color por hipótesis**, el mismo en todas las figuras del sitio: control en gris y H1 a H4 con cuatro tonos. Es una
  constante de `comun/reporte.py`, validada con el validador de la skill `dataviz` en claro y en oscuro, porque las
  figuras tienen fondo blanco en los dos modos.
  - El veredicto deja de ser color y pasa al marcador: lleno *no pierde*, vacío *pierde*, con borde punteado
    *indeterminado*. Los nombres de las variantes llevan el color de su hipótesis.
  - Las tablas generadas suman una pastilla de color con el nombre de la hipótesis donde haya columna «hipótesis».
- **Dividir por hipótesis**: los gráficos de puntos con todas las variantes juntas (`tradeoff`, `semillas_replicas`,
  `fraccion`, `tiempo_igual`) pasan a paneles de 2 × 2, uno por hipótesis, con los ejes compartidos para comparar
  entre paneles. El control se repite en cada panel como referencia gris.
- **Se quedan como están** el gráfico de barras (`desglose_tiempo`) y la matriz de veredictos (`grilla_veredictos`):
  se leen bien con todas las variantes (pedido del 13-nov). Solo toman el color de la hipótesis en los nombres, si eso
  no cambia su forma.
- **Tablas en pestañas**: el bloque A de Resultados va en pestañas `pymdownx.tabbed` (ya habilitado): «Lo mejor de
  cada hipótesis» (la primera que se ve), «H1», «H2», «H3» y «H4».
  - «Lo mejor de cada hipótesis» tiene una fila por hipótesis: la variante más rápida entre las que valen la pena o, si
    ninguna vale la pena, la de mayor Δ.
  - Reemplaza a «Valen la pena» (las 12 variantes medían 1031 px, más que el tope; decidido el 13-nov). Las 12 siguen
    en las pestañas de cada hipótesis y en el Anexo. La tabla completa sigue entera en el Anexo.
  Para que la pestaña no rompa el bloque generado, el generador escribe las pestañas dentro del marcador.

Tope: a 1440 × 900, ninguna figura ni tabla de Resultados es más alta que 800 px. Si una no entra con 2 × 2, se parte
en dos figuras (H1–H2 y H3–H4) y no se achica la letra.

### D17. Zoom en las figuras y tablas ordenables (agregado el 13-nov)

Las dos cosas son interactivas, casi gratis y no tocan el generador. Lo demás que es interactivo (gráficos con
leyenda que oculta hipótesis, comparador de dos variantes, explorador del tradeoff con δ y 2× movibles, presupuesto de
tiempo del ensamble) va en un cambio aparte, después de archivar este.

- **Zoom**: plugin `mkdocs-glightbox` (`auto_caption: false`, `zoomable: true`). Un clic en una figura la abre a
  pantalla completa. Se suma a `requirements-sitio.txt` con versión fija (0.5.3), para que lo instale el flujo de
  GitHub Pages. El plugin envuelve cada imagen en `a.glightbox`, así que las reglas de ancho de `sitio/estilos.css`
  (`p > img:only-child`) tienen que cubrir también `p > a.glightbox:only-child > img`.
- **Tablas**: tablesort 5.3.0 (núcleo y `sorts/tablesort.number`) desde unpkg, en `extra_javascript`, más
  `sitio/tablas.js`, que se suma a la lista blanca. Corre en cada página con `document$.subscribe` de Material:
  - antes de iniciar tablesort pone `data-sort` en cada celda con su primer número, porque los números del sitio llevan
    «−» (U+2212), coma decimal, punto de miles y texto alrededor (IC, «×»);
  - en las tablas de 8 filas o más agrega un campo «Filtrar filas» que oculta las filas sin el texto buscado;
  - ignora las tablas sin `tbody`, porque hay tablas así y en la prueba del 13-nov rompieron el script.
  
  Los encabezados muestran ▲/▼ y el cursor de clic. El campo usa las variables del tema, así que vale en los dos modos.

Lo verifica el orquestador en el navegador: ordenar por Δ en las dos direcciones, filtrar «H3», abrir una figura, a
1440 y 390 px y en claro y oscuro.

### D18. Predicciones fuera del repo (agregado el 13-nov)

Las predicciones de test por semilla (`experimentos/<exp>/ledger/predicciones/*.parquet`, ~10 GB y 4950 archivos)
viven dentro del repo, excluidas de git por `.git/info/exclude`. El repo está en `~/Documents`, que iCloud sincroniza.
En la revisión 1.11, regenerar tres veces dio dos resultados distintos en «tiempo igual, réplicas»: R bajó a 7 o 6 y
apareció un «pendiente». El generador no encontraba por un rato un parquet que sí existía.

- **Dónde quedan:** las predicciones van a `DATOS_DIR/ledger/<exp>/predicciones/`, donde ya están los demás datos
  (`~/datos/experimentos-dmeyf`, fuera de `~/Documents`).
- **El ledger no cambia:** la columna `predicciones_201910` conserva la ruta relativa de siempre. Una función de
  `comun/rutas.py` la resuelve, primero en `DATOS_DIR` y, si no está, en la ruta vieja del repo. Así funciona antes y
  después de mover los archivos, y también en la rama de `tiempos-confiables-y-consistencia` hasta que una `main`.
- **Escritura y VMs:** `comun/correr.py` escribe las nuevas en `DATOS_DIR`, y `scripts/vm.sh` las sincroniza con el
  bucket desde ahí.
- **Quién mueve los archivos:** el orquestador, porque las sesiones headless no pueden mover archivos fuera del repo.
  Es un renombre en el mismo disco.
- **Alternativa descartada:** el sufijo `.nosync` con un enlace simbólico deja los datos dentro del repo, al revés de
  la regla de `CLAUDE.md` («datos fuera del repo, en `DATOS_DIR`»).

## Risks / Trade-offs

- [Unir `main` en la rama de `tiempos-confiables-y-consistencia` choca con `sampling_1/README.md` y con
  `comun/reporte.py`] → Este cambio se archiva antes. La bitácora de `sampling_1` deja anotado qué bloques se mudaron, y
  esa rama regenera después de unir, porque sus números entran solo regenerando.
- [El guion del video cita figuras y secciones] → Los nombres de las figuras existentes no cambian. Una tarea revisa el
  guion y anota las figuras nuevas que conviene mostrar (ensamble según el tiempo).
- [Los PNG de los exploratorios pesan] → Unos 100–300 KB cada uno, nueve en total. Se aceptan, porque están en el repo
  dentro de los HTML.
- [Ancho fijo angosto en pantallas de 1920 px] → Se acepta: queda aire a los costados, y es el pedido. Las tablas anchas
  se desplazan.
- [Los PNG de los exploratorios llevan textos con nombres de estrategia («Campeon», «IdeaC_…»)] → No nombran personas.
  La búsqueda de nombres de `scripts/sitio.sh` revisa el texto, no las imágenes, y la leyenda no dice el autor.
- [Fecha de entrega, 23-nov] → El grupo 1 deja el sitio en verde aunque el texto de Resultados todavía sea el viejo,
  reordenado en lo mínimo. El grupo 2 se puede cortar por página si no alcanza el tiempo.
