# Design

## Context

Motivación: proposal.md § Why. Estado actual que condiciona el enfoque:

- Las variantes se registran en `comun/variantes.py` (`Variante.metodo` identifica la familia; `FILAS_GRILLA` y
  `FUERA_DE_GRILLA` ya describen cómo muestrea cada una en texto). No hay un dato que diga dónde corta ni cómo elige
  filas en una forma que el generador pueda agrupar.
- El bloque `resultado` de cada hipótesis (`bloques_hipotesis`) arma su tabla con `tabla_variantes(ctx, fin, ap)`,
  que lee la réplica 0. La figura del tradeoff de la misma página ya usa el agregado con réplicas (`_agregador`), igual
  que las tarjetas: el desacuerdo está solo en la tabla y en el primer recuadro de veredicto, escrito a mano.
- `protocolo-experimental` prohíbe cambiar la sección Predicción después de la primera corrida. Las predicciones de
  H1–H4 tienen subtítulos con fecha y nombre de cambio, y se quedan así.
- `verificar_readme` exige que cada número escrito a mano en Resultados esté en el bloque `bloque-a-completo` del
  Anexo; `verificar_informe_h3` hace lo mismo con las páginas de hipótesis.
- Entrega del video el 23-nov: el cambio tiene que cerrarse antes de grabar, sin corridas nuevas.

## Goals / Non-Goals

**Goals:**
- Un solo dato de ejes por familia, usado por el mapa de Resultados y por la verificación.
- Que cada variante muestre el mismo veredicto en todas las páginas.
- Páginas que se lean como informe final, con el historial accesible pero fuera del cuerpo.

**Non-Goals:**
- Cambiar el cálculo de Δ, A, IC o veredictos.
- Rediseñar el tema del sitio o las figuras existentes, salvo el rótulo del eje x del tradeoff.
- Reescribir las secciones Predicción o la bitácora.

## Decisions

### D1. Ejes por `metodo`, en el registro
`EJES: dict[str, tuple[str, str]]` en `comun/variantes.py`, de `metodo` a (dónde, cómo), con los valores de la spec
`lectura-por-ejes`. `verificar` falla si un `metodo` usado por alguna variante no está en `EJES`.
- *Alternativa:* un campo nuevo en `Variante`. Repetiría el mismo par en cada tasa y en cada réplica, y una variante
  nueva podría declarar ejes distintos que otra de su familia.
- *Alternativa:* deducirlo de `FILAS_GRILLA`. Deja afuera las familias fuera de la grilla (H3K, H4H, GOSS).

### D2. Mapa de ejes como tabla HTML generada, no figura
Bloque `ejes` en Resultados: filas dónde (`todo`, `lightgbm`, `busqueda`, `final`) y columnas cómo. Cada celda lista
«familia (HN): k de n valen la pena», con el color de la hipótesis como borde, igual que la grilla de veredictos. Es una
tabla de ubicación: no repite Δ ni A del mapa del tradeoff, así que no choca con la regla de no repetir gráficos.
- *Alternativa:* una figura nueva. Una tabla de 4 × 5 con texto se lee mejor en HTML, se busca con la búsqueda del
  sitio y no hay que cuidar que las etiquetas no se pisen.

### D3. Orden de Resultados

```
Resultados
├─ Pregunta e hipótesis general            (a mano; ya existe)
├─ Configuración común                     (a mano; ya existe)
├─ Respuesta                               recuadro + «valen la pena» (H3 y final con bajas) + mapa del tradeoff
│                                          + resumen plegado (bloque-a)
├─ Cómo leer las hipótesis: dos ejes       bloque `ejes` + dos líneas
├─ ¿Dónde achicar?                         desglose del tiempo; H1 vs H3 (par U−H3: lo que pierde es el final);
│                                          H2 (dentro de LightGBM no llega a 2×); final con bajas (H4F, H4O)
├─ ¿Cómo muestrear?                        par H4O−U (tabla actual de § ¿Importa qué filas…?); H4P−H3;
│                                          H4H, H4U (búsqueda informada pierde); extensiones de H3 (K, R, L)
├─ ¿Cuánto se puede achicar?               fracción
├─ ¿Qué se hace con el tiempo ahorrado?    ensamble, tiempo igual
├─ ¿Cuánto del tiempo es tamaño de datos?  A a hiperparámetros fijos
├─ ¿Qué tan estable es?                    semillas y réplicas, rondas, AUC
├─ Limitaciones comunes / Conclusiones / Qué sigue / Exploratorios
```

Los bullets por hipótesis de hoy (§ ¿Qué conviene achicar?) se reparten entre los dos ejes; cada veredicto se dice una
vez. La grilla de veredictos va en § ¿Cómo muestrear?, porque sus filas son formas de muestrear.

### D4. Páginas de hipótesis

```
HN · título
  una línea: qué eje responde (enlace a Resultados § eje)
  ## Idea            diagrama del pipeline (ya existe)
  ## Predicción      SIN CAMBIOS (byte a byte)
  ## Diseño          estado final: variantes, muestras, grilla; sin subtítulos «(cambio …, fecha)»
  ## Resultado       bloque generado: tabla con réplicas + tradeoff + curvas
  ## Veredicto       un recuadro, con réplicas; una línea por predicción: se cumplió / no
  ## Limitaciones
```

H4 tiene tres partes en Diseño y Veredicto: búsqueda informada (`H4H`, `H4U`), final con bajas (`H4F`, `H4O-0.5`) y
grilla común (`H4O-{r}`, `H4P-{r}`). Así la página se lee por eje sin dejar de ser una hipótesis. Los textos que hoy
explican por qué se agregó algo («La consigna pide reoptimizar…», Zulip 211718) pasan a una frase de Diseño que dice
qué regla del curso aplica, sin presentarlo como respuesta.

### D5. Tabla de hipótesis con réplicas, réplica 0 al Anexo
`tabla_variantes` pasa a leer las filas del agregado (`_agregador`): Δ con réplicas, A con su IC y el veredicto con
réplicas, las mismas celdas que el resumen del bloque A. La columna «semillas ganadas» deja de tener sentido con
réplicas y se reemplaza por R. La tabla de réplica 0 de hoy se mueve tal cual a bloques nuevos del Anexo,
`replica0-h1` a `replica0-h4`, en una sección «Réplica 0 por hipótesis».
- *Alternativa:* mostrar las dos en la página de la hipótesis. Es justo la confusión que se quiere sacar.
- `verificar_informe_h3` busca los números de las páginas de hipótesis en sus fuentes; el veredicto escrito a mano
  pasa a citar los números con réplicas, que están en `bloque-a-completo`.

### D6. Una respuesta, dos páginas
El recuadro «Respuesta» se escribe en Resultados. `scripts/verificar_readme.py` gana una comprobación: el cuerpo del
recuadro `!!! success "Respuesta"` de `index.md` es igual al de Resultados. Se compara en el script y no se genera desde
uno de los dos archivos, porque es texto escrito a mano y los bloques generados son solo para números.

### D7. Títulos de proceso: verificador
`scripts/nombres_sitio.py`, que ya corre en `scripts/sitio.sh`, gana una regla: fuera de `## Predicción` (hasta el
siguiente `## `), un título `#`–`####` de una página publicada no puede tener «cambio», una fecha `\d{1,2}-[a-z]{3}`
o `\d{4}-\d{2}-\d{2}`, «Zulip» ni un nombre entre comillas invertidas que sea un cambio archivado. Así el error vuelve a
aparecer en el build si alguien agrega un título así.

### D8. Corridas
Quedan Protocolo, Máquina, Una configuración, Qué cuenta y qué no, Consolidar y regenerar, VM y Costo. § Fases (con
la grilla común y la fase 8) se mueve a `experimentos/sampling_1/docs/fases.md`, sin cambios de texto, y Corridas lo
enlaza en GitHub. La línea de tiempo de fases se va con él.

### D9. Rótulo del eje x del tradeoff
`fig_tradeoff` usa `fig.supxlabel` una vez, en lugar de `ax.set_xlabel` por panel de la última fila, y deja lugar abajo
para la leyenda. Vale para la figura de Resultados y para las de cada hipótesis (un solo panel: queda igual).

## Risks / Trade-offs

- [Reescribir Veredicto y Diseño puede cambiar números a mano] → `verificar_readme` y `verificar_informe_h3` deben
  pasar, y la tabla de la réplica 0 sigue disponible en el Anexo para lo que se cita de ella.
- [Tocar la sección Predicción por accidente al reordenar] → una tarea compara cada sección Predicción con la de
  `main` antes del cambio (`git show main:…`), byte a byte, antes de commitear cada grupo.
- [La tabla de hipótesis con réplicas pierde «semillas ganadas»] → sigue en la tabla de réplica 0 del Anexo; el
  escenario «Tabla de una hipótesis sin redundancias» de `reporte-visual` se ajusta en este cambio.
- [Los ejes pueden leerse como hipótesis post hoc] → la spec lo prohíbe de forma explícita, y cada conclusión por eje
  cita veredictos y pares registrados antes de correr.
- [Tiempo hasta el 23-nov] → el orden de las tareas deja el sitio coherente después de cada grupo, así que se puede
  cortar después de cualquier grupo y publicar.

## Migration Plan

Un grupo de tareas por commit, con push después de cada uno (regla del repo). Cada grupo deja `scripts/sitio.sh`,
`pytest` y los dos verificadores en verde. Para volver atrás alcanza `git revert` del grupo: no hay datos que migrar.
