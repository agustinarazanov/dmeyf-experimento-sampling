# Tasks

## 1. Sitio y generador (sesión: Sonnet; cambio en `comun/`, se anuncia en el commit)

- [x] 1.1 `mkdocs.yml`:
  - `nav` sin etiquetas en las páginas (D7), Resultados como sección con `anexo.md` de hija;
  - lista blanca con `anexo.md` y `!/experimentos/**/figuras/**`;
  - `site_name: Sampling_1 · DMEyF 2026`;
  - `theme.palette` claro/oscuro con `toggle` y `media` (D6).

  Verificar con `mkdocs build` y el HTML de `site/`: la barra dice «H4 · Muestras informadas por clase» y «Control y
  reglas», y el encabezado tiene el botón de modo.
- [x] 1.2 `sitio/estilos.css`:
  - una columna (D6): sin topes de 75ch ni `calc(89ch …)`, todo al 100 % de `.md-content__inner`;
  - colores de veredicto, pills e IC en variables, con valores para `slate`;
  - figuras con fondo blanco, borde redondeado y margen en oscuro;
  - encabezado más alto en el teléfono (D7b, con `sitio/overrides/partials/header.html`).

  El orquestador verifica con capturas a 1440 y 390 px, en claro y en oscuro.
- [x] 1.3 `comun/reporte.py`, `scripts/comparar_rondas.py` y los verificadores:
  - `experimentos/sampling_1/anexo.md` con los marcadores `bloque-a-completo`, `varianza`, `diferencias`, `ic-rondas` y
    `rondas`, que salen de `sampling_1/README.md`;
  - el bloque `figuras` se separa en `grilla`, `desglose` y `fraccion`;
  - `index.md` suma `hallazgo-tradeoff`, `hallazgo-tiempo` y `hallazgo-ensamble`;
  - `comparar_rondas.py` escribe en `anexo.md`;
  - `verificar_readme.py` y `verificar_informe_h3.py` leen `bloque-a-completo` de `anexo.md`, y `verificar_readme.py`
    también revisa los números escritos a mano en `index.md` y `sampling_1/README.md` (D2).

  Mientras el grupo 2 no reescriba Resultados, sus secciones quedan en su orden actual, con los marcadores nuevos donde
  estaban los viejos. Verificar con `pytest tests/test_reporte.py tests/test_verificadores.py`, con
  `python -m comun.reporte --todos` dos veces (la segunda sin cambios), con `python -m scripts.verificar_readme` y con
  que las tablas completas del Anexo coinciden con las de `git show HEAD~:experimentos/sampling_1/README.md`.
- [x] 1.4 Cargar la skill `dataviz`. Figuras nuevas de D3:
  - ensamble según K y según el tiempo;
  - cajas por semilla, dentro de `semillas_replicas`;
  - IC por ronda;
  - curvas de ganancia por hipótesis, que suman al bloque `resultado` de cada `hN/README.md`.

  Cada una lleva su título generado, sale pendiente sin datos y tiene un test. Verificar con
  `pytest tests/test_reporte.py`, con regenerar dos veces sin cambios en los SVG, y con un test que comprueba que el
  ensamble de K = 20 del control coincide con «ensamble de 20 semillas del control» del bloque `tiempo-igual`.
- [x] 1.5 `scripts/extraer_figuras_exploratorios.py` (de una sola vez, determinista) guarda los nueve PNG de los reportes
  HTML en `<estudio>/figuras/`. Los tres `exploratorio.json` suman `figuras` con su leyenda (sin autor) y columnas con
  `etiqueta`, `escala` y `unidad` (D4). `sensibilidad_muestra` declara una figura generada desde su CSV. Verificar con
  correr el script dos veces sin cambios en `git status`, y con `python -m comun.variantes --verificar`, que falla si se
  borra una figura declarada (test en `tests/test_variantes.py`).
- [x] 1.6 Bloque B (`comun/reporte.py`), una sección por estudio:
  - la pregunta en `!!! question`;
  - el protocolo;
  - las figuras con su leyenda;
  - las cifras en una tabla numérica con etiqueta y unidad, plegada;
  - la advertencia en `!!! warning`.

  Las columnas declaradas como texto siguen funcionando. Verificar con `pytest tests/test_reporte.py` (exploratorio sin
  CSV, bloque B sin autor, columna con escala) y con `mkdocs build`: las imágenes de los estudios resuelven en `site/`.
- [x] 1.7 Revisión en sesión limpia del grupo 1 con `docs/revision.md` § 3, cierre en la bitácora de `sampling_1` y
  `comun/tokens.py`.
- [x] 1.8 Tablas de resultado (D9), en `comun/reporte.py` y los verificadores:
  - el bloque `resultado` de cada `hN/README.md` va sin columna «hipótesis»;
  - sin columna «semillas» cuando todas las filas tienen las mismas, con la línea debajo de la tabla;
  - semillas ganadas como barrita de proporción con su número;
  - encabezados «aceleración (×)», «ganancia contra el control» y «vale la pena (no pierde y ≥ 2×)», también en el
    bloque A completo del Anexo, con los verificadores leyendo los nuevos.

  Verificar con el escenario «Tabla de una hipótesis sin redundancias», con `pytest` (incluye un test con semillas
  distintas: la columna vuelve) y con los dos verificadores.
- [x] 1.9 Figuras (D10, D14):
  - `tradeoff.svg` en dos paneles con una fila por variante;
  - `ANCHO` menor;
  - las curvas contra clientes contactados siempre en dos columnas de paneles;
  - «envíos» pasa a «clientes contactados» en ejes, títulos y textos del generador.

  Verificar con los escenarios «Ver el tradeoff de un vistazo» y «Clientes contactados» (sobre el texto generado), con
  `pytest tests/test_reporte.py` y con regenerar dos veces sin cambios.
- [x] 1.10 Barras laterales (D13). **La hace el orquestador; una sesión headless no la toca ni la marca.** Verificar con
  el escenario «Barras laterales parejas» en capturas a 1440 px en claro y en oscuro.
- [x] 1.12 Resultados por hipótesis (D16, junto con 1.9 porque comparten las figuras):
  - un color por hipótesis en `comun/reporte.py`, validado con la skill `dataviz`;
  - el veredicto, en el marcador;
  - paneles de 2 × 2 por hipótesis en `tradeoff`, `semillas_replicas`, `fraccion` y `tiempo_igual`; las barras
    (`desglose_tiempo`) y la matriz (`grilla_veredictos`) no cambian de forma;
  - el bloque A de Resultados en pestañas («Valen la pena», H1 a H4), y el Anexo entero.

  Verificar con el escenario «Resultados entra en la pantalla» (alto medido en `site/`), con `pytest
  tests/test_reporte.py`, regenerando dos veces sin cambios y con los dos verificadores.
- [x] 1.11 Revisión en sesión limpia de 1.8, 1.9 y 1.12 con `docs/revision.md` § 3 y `python -m scripts.medir_sitio` (tope de 800 px de D16), cierre en la bitácora de `sampling_1`.
  Quedan dos ✗ abiertos que necesitan una decisión humana, en `sampling_1/ledger/sesiones/bloqueo.txt`: la pestaña
  «Valen la pena» mide 1031 px (más que el tope de 800) y regenerar no siempre da lo mismo en «tiempo igual, réplicas».
  Decididos el 13-nov: tareas 1.13 a 1.16.
- [x] 1.13 Primera pestaña del bloque A de Resultados: «Lo mejor de cada hipótesis» en lugar de «Valen la pena» (D16).
  Verificar con `python -m scripts.medir_sitio --pagina experimentos/sampling_1/` sin problemas y con los dos
  verificadores.
- [x] 1.14 Predicciones fuera del repo (D18), solo código:
  - `comun/correr.py` escribe las predicciones nuevas en `DATOS_DIR/ledger/<exp>/predicciones/`;
  - la ruta del ledger (`predicciones_201910`) no cambia: una función de `comun/rutas.py` la resuelve, primero en
    `DATOS_DIR` y, si no está, en la ruta vieja del repo;
  - `comun/reporte.py` y quien lea predicciones usan esa función;
  - `scripts/vm.sh` baja y sube las predicciones desde y hacia `DATOS_DIR`.

  No mueve archivos (eso es 1.15). Verificar con `pytest` (un test por cada lado de la resolución: en `DATOS_DIR` y en
  la ruta vieja) y con `python -m comun.reporte --todos` sin cambios en `git status`.
- [x] 1.15 Mover `experimentos/*/ledger/predicciones/` a `DATOS_DIR` (D18). **La hace el orquestador; una sesión
  headless no la toca ni la marca.** Verificar con `python -m comun.reporte --todos` tres veces sin cambios en
  `git status` y con `experimentos/*/ledger/predicciones/` vacío.
- [x] 1.16 Revisión en sesión limpia de 1.13 y 1.14 con `docs/revision.md` § 3, cierre en la bitácora de `sampling_1`.

## 2. Redacción (sesión: Opus; un commit por página)

Cada tarea:
- antes de borrar o mover texto, listar en la bitácora de `sampling_1` cada sección vieja con su destino;
- números escritos a mano solo si están en un bloque generado (D2);
- redacción impersonal, sin «tutor» ni nombres; «A» se escribe «aceleración» (D9) y «envíos», «clientes contactados» (D14);
- correr `python -m scripts.verificar_readme` y `scripts/sitio.sh`.

- [x] 2.1 `experimentos/sampling_1/README.md` (Resultados) en el orden de D1:
  - pregunta y respuesta;
  - las cuatro preguntas, cada una con su texto, sus bloques y el detalle plegado;
  - limitaciones comunes, conclusiones (dicen si la predicción acertó, con enlace), qué sigue, exploratorios en una
    línea y dependencias.

  Se mudan la predicción conjunta a `control/README.md` § Predicción, el diseño a `corridas.md` § Protocolo y la
  bibliografía a `docs/metodo.md`. Verificar con que ninguna tabla de consulta queda entre la respuesta y las
  conclusiones, con `python -m comun.variantes --verificar` (lee § Dependencias) y con `verificar_informe_h3.py`.
- [x] 2.2 `experimentos/sampling_1/anexo.md`: título «Anexo de resultados», una línea por sección, y en Rondas los tres
  resultados de la predicción de la ronda que hoy están en Resultados. Verificar con que el bloque A completo tiene las
  mismas filas que antes del cambio.
- [x] 2.3 `index.md` (Inicio, D8):
  - pregunta y respuesta;
  - tres hallazgos con su bloque y 2–3 líneas;
  - recuadro con tres limitaciones;
  - botón a Resultados y tarjetas.

  Verificar con el escenario «Primera visita del tutor» en el HTML de `site/` y con `verificar_readme` sobre
  `index.md`.
- [x] 2.4 `experimentos/sampling_1/exploratorios/README.md`: diagrama de motivaciones (D5) y una sección por estudio con
  qué mostró, alrededor del bloque B. Verificar con los escenarios «Figuras de un exploratorio» y «Exploratorios» y con
  `scripts/sitio.sh` (sin autor).
- [ ] 2.5 `experimentos/sampling_1/corridas.md`:
  - § Protocolo (viene de Resultados);
  - línea de tiempo de las fases y diagrama del recorrido de una corrida (D5);
  - tabla de fases con columnas cortas y una lista por fase;
  - comentarios de código cortados para que entren en la columna;
  - se borra § Devoluciones del curso.

  Verificar con que ninguna línea de código supera los 80 caracteres y ninguna celda de tabla tiene más de ~60.
- [ ] 2.6 `docs/metodo.md` (Cómo trabajamos):
  - diagrama de etapas con compuertas, diagrama de una etapa sin supervisión y diagrama de § Agregar una hipótesis
    (D5);
  - § Bibliografía (viene de Resultados);
  - comentarios de código cortados.

  Verificar con el escenario «Cómo trabajamos» y con que ninguna línea de código supera los 80 caracteres.
- [ ] 2.7 `experimentos/sampling_1/docs/guion.md`: secciones y figuras citadas que se mudaron, y la figura de ensamble
  según el tiempo donde corresponda. `CLAUDE.md` y el README raíz suman `anexo.md` al mapa de archivos. Verificar con
  `python -m scripts.verificar_readme` y con que cada figura que cita el guion existe.
- [ ] 2.7b `control/README.md` y `h1` a `h4/README.md`:
  - Veredicto con un solo recuadro (la conclusión) y Limitaciones sin recuadros, en listas con el nombre en negrita
    (D11; lo mismo en Resultados § Limitaciones comunes);
  - diagramas en `flowchart TB` o en dos filas, con etiquetas cortas (D12);
  - § Variantes con la columna «búsqueda de hiperparámetros» y la línea que explica estudio y réplica (D15);
  - «envíos» pasa a «clientes contactados» en todo el texto escrito a mano (D14).

  Antes, listar en la bitácora cada recuadro con su destino. Verificar con el escenario «Veredicto y limitaciones
  legibles», con `grep -rn envío` vacío en las páginas publicadas, con los dos verificadores y con
  `python -m scripts.medir_sitio --pagina experimentos/control/ experimentos/h1/ experimentos/h2/ experimentos/h3/
  experimentos/h4/` (los diagramas entran en la columna).
- [ ] 2.8 Revisión en sesión limpia del grupo 2 con `docs/revision.md` § 5 (comparando contra
  `git show <commit previo>:experimentos/sampling_1/README.md` que no se perdió texto), cierre en la bitácora de
  `sampling_1` y `comun/tokens.py`.

## 3. Integración (sesión: Sonnet)

- [ ] 3.0 Zoom en las figuras y tablas ordenables y filtrables (D17). **La hace el orquestador; una sesión headless no
  la toca ni la marca.** Verificar en el navegador: ordenar por Δ en las dos direcciones, filtrar «H3», abrir una figura,
  a 1440 y 390 px y en claro y oscuro, y que `mkdocs build` pase con `requirements-sitio.txt`.
- [ ] 3.0b `tradeoff.svg`, panel de H3 (D10, D16): las nueve etiquetas no se pisan (por ejemplo, con las etiquetas en
  una columna al costado y una línea fina a cada punto, o con la región de 4× a 6× ampliada en un recuadro), y la
  leyenda distingue *indeterminado* de *pierde* a simple vista. Verificar con la figura a 1440 px en `site/` y
  regenerando dos veces sin cambios.
- [ ] 3.1 `pytest` entero, `python -m comun.variantes --verificar`, los dos verificadores y `scripts/sitio.sh`, todo en
  verde. `mkdocs build` y `python -m scripts.medir_sitio` sin problemas: ancho único a 1440 px (texto, figura, código,
  recuadro, plegable y diagrama con el ancho de la columna; las tablas más anchas, solo como aviso), ninguna de las
  ~13 páginas desborda a 390 px y Resultados respeta el tope de alto de D16. Las capturas en claro y en oscuro las
  hace el orquestador.
- [ ] 3.2 Revisión en sesión limpia (Opus) del cambio completo contra los escenarios de `sitio-informes` y
  `reporte-visual`, cierre en la bitácora y `comun/tokens.py`.

## Workflow follow-up

- Push a `main` y verificación del sitio publicado en claro y en oscuro, a 1440 y 390 px.
- Archivar `inicio-y-resultados`.
- Anotar en la bitácora, para quien una `main` en la rama de `tiempos-confiables-y-consistencia`, que
  `bloque-a-completo` y `rondas` viven en `sampling_1/anexo.md`.
