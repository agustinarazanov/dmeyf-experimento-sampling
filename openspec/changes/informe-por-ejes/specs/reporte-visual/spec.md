# Spec Delta

## MODIFIED Requirements

### Requirement: Comparación de todas las variantes en una vista
Resultados (`experimentos/sampling_1/README.md`) SHALL mostrar todas las variantes de todas las hipótesis contra el
control, en una tabla (diferencia apareada con su intervalo, aceleración con su intervalo, veredicto) y en gráficos,
cada uno con la forma que corresponde a su pregunta. Una tabla de Resultados SHALL NOT repetir lo que ya muestra un
gráfico de la misma página: el resumen del bloque A, que da los números del mapa del tradeoff, va plegado debajo del
mapa; la cobertura, las tablas de tiempo igual y las de búsqueda y final van al Anexo. Resultados SHALL ordenarse así:
pregunta e hipótesis general, configuración común, respuesta (con las variantes que valen la pena antes que el resto),
el mapa de ejes (lectura-por-ejes), ¿dónde achicar?, ¿cómo muestrear?, cuánto se puede achicar, qué se hace con el
tiempo ahorrado, cuánto del tiempo es tamaño de datos y qué tan estable es el resultado; después, limitaciones comunes,
conclusiones y qué sigue. Gráficos:
- **mapa del tradeoff:** aceleración A en escala logarítmica contra Δ con su IC, un punto por variante coloreado por
  veredicto, con la zona de «no pierde» (Δ > −δ) sombreada y la línea A = 1;
- **Δ contra tasa:** una línea por familia de variantes con más de una tasa, con su banda de IC y la línea de −δ;
- **desglose del tiempo:** barras apiladas por variante y para el control, con el tiempo de optimización, el de
  entrenamiento final y el de predicción;
- **semillas y réplicas:** la distribución por variante (caja, media y puntos), con el Δ de cada semilla como un
  punto y las réplicas de Optuna distinguidas, para ver la dispersión y no solo el intervalo;
- **grilla de veredictos:** familia contra tasa, cada celda con el color y el texto del veredicto, y vacía si esa
  combinación no se corrió;
- **tiempo igual:** cada variante con su intervalo;
- **ensamble según K y según el tiempo:** la ganancia del ensamble de las primeras K semillas de cada variante contra K y
  contra el tiempo acumulado T_opt + K·T_final, con la ganancia y el tiempo del control como referencia.

El Anexo (`experimentos/sampling_1/anexo.md`) SHALL mostrar, además de las tablas completas, estos gráficos:
- **diferencias entre variantes:** cada par comparado, con su IC;
- **comparación entre rondas:** para cada variante, el Δ de la ronda anterior y el de la vigente unidos por un
  segmento;
- **IC por ronda:** para cada variante, el IC de Δ de la ronda anterior y el de la vigente uno al lado del otro, con −δ
  marcado, para ver cuánto se angosta.

La portada SHALL mostrar el mapa del tradeoff desde el mismo archivo.

La página de cada hipótesis SHALL mostrar su mapa del tradeoff, las curvas de ganancia (ganancia de cada variante y del
control según la cantidad de envíos, con banda P10–P90 entre semillas y el corte N\*) y la curva de diferencia con el
control (ganancia de la variante menos la del control, con la banda entre semillas, la línea de 0 y N\*).

Las figuras SHALL ser vectoriales, guardadas como archivo junto a la página y enlazadas desde ella, con tres
condiciones:
- ninguna etiqueta de variante ni de eje SHALL quedar encima de otra: un rótulo de eje compartido por varios paneles se
  escribe una sola vez para la figura;
- un gráfico sin datos SHALL salir como pendiente, sin fallar;
- cada figura SHALL tener un título que diga qué mirar, no solo qué se grafica.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre la página de una hipótesis
- **THEN** se ve su predicción, el resultado de cada variante y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y las figuras que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos una variante tienen todas sus semillas
- **THEN** Resultados incluye la comparación a tiempo igual (ensamble de K semillas de la variante contra el control),
  con el K usado y el intervalo de cada variante dibujado

#### Scenario: Hipótesis nueva en `sampling_1`
- **WHEN** se registra un experimento nuevo con variantes (por ejemplo `h5`)
- **THEN** Resultados y el Anexo lo incluyen en sus tablas y en cada gráfico sin cambiar el generador

#### Scenario: Ver el tradeoff de un vistazo
- **WHEN** se abre Resultados
- **THEN** antes de las tablas aparece el mapa del tradeoff en cuatro paneles, uno por hipótesis con su color: Δ e IC
  contra la aceleración, el control como referencia y las que valen la pena con su etiqueta en negrita
- **AND** a 1440 px entra en la columna sin etiquetas pisadas

#### Scenario: Resultados entra en la pantalla
- **WHEN** se recorre Resultados a 1440 × 900
- **THEN** ninguna figura ni tabla mide más de 800 px de alto
- **AND** cada hipótesis tiene el mismo color en todas las figuras
- **AND** el bloque A está en pestañas, con «Lo mejor de cada hipótesis» abierta (una fila por hipótesis), mientras
  el Anexo tiene la tabla entera

#### Scenario: Regenerar con las predicciones fuera del repo
- **WHEN** se corre `python -m comun.reporte --todos` tres veces seguidas con las predicciones en `DATOS_DIR`
- **THEN** las tres dan el mismo resultado y `git status` no cambia
- **AND** una fila del ledger con la ruta vieja de predicciones se resuelve igual si el archivo está solo en el repo

#### Scenario: Tabla de una hipótesis sin redundancias
- **WHEN** se lee el bloque `resultado` de `h3/README.md` y todas sus variantes tienen 20 semillas
- **THEN** no hay columnas «hipótesis» ni «semillas», una línea debajo dice que todas tienen 20 semillas por réplica,
  la columna R dice cuántas réplicas tiene cada variante, y los encabezados dicen «aceleración (×)», «ganancia contra
  el control» y «vale la pena (no pierde y ≥ 2×)»; las semillas ganadas por semilla están en la tabla de réplica 0 del
  Anexo

#### Scenario: Clientes contactados
- **WHEN** se busca «envíos» en el sitio generado
- **THEN** no aparece; N\* se lee como «clientes contactados»

#### Scenario: Por qué H3 es rápida
- **WHEN** se mira el desglose del tiempo
- **THEN** se ve que en el control la optimización es la mayor parte del tiempo y que H3 la achica sin achicar el
  entrenamiento final

#### Scenario: Conclusiones cerca de la respuesta
- **WHEN** se lee Resultados de arriba abajo
- **THEN** después de las secciones por eje y de las preguntas de tiempo y estabilidad vienen las limitaciones comunes
  y las conclusiones, sin tablas de consulta en el medio

#### Scenario: Qué hacer con el tiempo ahorrado
- **WHEN** se mira el ensamble según el tiempo en Resultados
- **THEN** se ve, para cada variante que vale la pena, cuánta ganancia suma ensamblar semillas hasta gastar el tiempo
  del control, y dónde queda el control

#### Scenario: IC más angosto con más semillas
- **WHEN** se mira el IC por ronda en el Anexo
- **THEN** cada variante muestra los dos intervalos, y se ve que el de la ronda vigente (20 semillas) es más angosto
  salvo donde decide la suerte de Optuna

#### Scenario: Dónde se pierde
- **WHEN** se abre la página de H1
- **THEN** la curva de diferencia de `U0.05` queda por debajo de 0 alrededor de N\*, con la banda entre semillas

#### Scenario: Figura nítida a cualquier ancho
- **WHEN** se abre una página con figuras en una pantalla ancha
- **THEN** las figuras se ven nítidas al ancho del contenido
- **AND** con `--figuras` además quedan guardadas como PNG para el video

#### Scenario: Gráfico sin datos
- **WHEN** ninguna variante tiene réplicas
- **THEN** el gráfico de semillas y réplicas muestra solo las semillas, y el resto de las figuras se genera

#### Scenario: Gráfico sin ronda anterior
- **WHEN** una variante solo existe en la ronda vigente
- **THEN** en la comparación entre rondas del Anexo aparece con un solo punto y sin segmento

## ADDED Requirements

### Requirement: Tabla de cada hipótesis con réplicas
El bloque `resultado` de cada hipótesis SHALL mostrar la misma regla de veredicto que Resultados: Δ con réplicas y su
IC, aceleración con su IC y veredicto con réplicas, más las columnas propias de la página (G media, ΔAUC, T mediana,
vale la pena). La tabla de la réplica 0 de cada hipótesis (Δ y semillas ganadas por semilla) SHALL ir al Anexo, en un
bloque generado por hipótesis. Una variante sin réplicas SHALL mostrar los valores de la réplica 0 con la nota al pie de
siempre.

#### Scenario: `U0.5` en la página de H1
- **WHEN** se abre la página de H1
- **THEN** la tabla dice que `U0.5` es *indeterminado* con Δ = −3,64 [−6,58; −0,71] M$, igual que en Resultados, y su Δ
  de la réplica 0 (−1,38) está solo en el Anexo

#### Scenario: Mismo veredicto en todas las páginas
- **WHEN** se compara el veredicto de cada variante en su página, en Resultados, en el Anexo y en la tarjeta de la portada
- **THEN** es el mismo en las cuatro
