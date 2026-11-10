# protocolo-experimental Specification

## Purpose
Define cómo se formula, revisa y documenta cada experimento del repo por etapas del método científico, de modo que cada
decisión quede escrita antes de ejecutarse, cada etapa tenga una revisión que la cierre y cualquier persona pueda agregar
un experimento nuevo sin tocar los existentes.

## Requirements

### Requirement: Un experimento, una carpeta
Cada experimento SHALL vivir en `experimentos/<nombre>/` con la misma estructura (`docs/`, `ledger/`, `informe/`, y
`scripts/` o `src/` solo si los necesita), con un nombre que sea un identificador válido de Python (`h1`, no `h-1`).
Además de `comun/` y de su propia carpeta, SHALL depender solo de los experimentos que declara (ver
`dependencias-entre-experimentos`). El código compartido (datos, baseline, ganancia, ledger, tokens, corredor, métodos,
consolidación, reporte) SHALL vivir en `comun/`.

#### Scenario: Agregar un experimento nuevo
- **WHEN** un integrante copia `plantilla/` a `experimentos/<nombre>/`, completa `docs/hipotesis.md` y registra sus
  variantes
- **THEN** el experimento aparece en el README del repo y sus corridas se registran en su propio `ledger/`. Ningún
  archivo de otro experimento cambia, salvo el registro de variantes en `comun/`

#### Scenario: Cambio en código común
- **WHEN** se modifica algo en `comun/`
- **THEN** el commit lo dice en el mensaje y cada experimento activo anota en su bitácora si lo afecta

### Requirement: Hipótesis escritas antes de ejecutar
El experimento SHALL tener en `docs/hipotesis.md`, antes de la primera corrida real, la pregunta, cada hipótesis con su
predicción cuantitativa y su regla de decisión (qué resultado la confirma y cuál la refuta), y el baseline de control
sin modificar salvo la variable experimental.

#### Scenario: Corrida sin hipótesis aprobada
- **WHEN** se intenta registrar una corrida real en el ledger y `docs/hipotesis.md` no tiene la etapa marcada como
  revisada en `docs/bitacora.md`
- **THEN** la corrida se considera exploratoria y se registra con `etapa = exploracion`, no como evidencia

#### Scenario: Hipótesis con regla de decisión
- **WHEN** se lee cualquier hipótesis del documento
- **THEN** se encuentra una predicción con umbral numérico y la métrica que la decide (por ejemplo, "la ganancia media
  apareada en 201910 no cae más que un desvío entre semillas")

### Requirement: Diseño experimental explícito
El diseño SHALL fijar, en `docs/diseno.md`, la grilla completa (métodos, tasas, semillas, trials de optimización), las
métricas, el procedimiento de comparación apareada por semilla, el tipo de máquina y el reparto de corridas entre las
tres personas.

#### Scenario: Grilla reproducible por cualquier integrante
- **WHEN** un integrante lee `docs/diseno.md` y el ledger
- **THEN** puede identificar qué configuraciones faltan y lanzarlas con el corredor sin consultar a nadie

### Requirement: Revisión que cierra cada etapa
Cada etapa (hipótesis, diseño, código, resultados, informe) SHALL cerrarse con una revisión registrada en
`docs/bitacora.md` que use la lista de `docs/revision.md`, hecha en una sesión limpia (interactiva o la sesión de revisión de `scripts/etapa.sh`) o por otro integrante,
con fecha y hallazgos.

#### Scenario: Etapa cerrada
- **WHEN** la bitácora marca una etapa como revisada
- **THEN** existe una entrada con fecha, quién revisó, qué ítems de la lista se verificaron y qué se corrigió

#### Scenario: Revisión que encuentra un problema
- **WHEN** la revisión de resultados detecta una inconsistencia (por ejemplo, tiempos medidos en máquinas distintas)
- **THEN** las corridas afectadas se marcan como inválidas en el ledger y la etapa no se cierra hasta repetirlas

### Requirement: Lo que necesita a una persona se declara, no se improvisa
Una sesión headless que encuentra una tarea que requiere a una persona (una respuesta del tutor, una decisión de diseño,
un reparto entre personas) SHALL escribir `BLOQUEADO` con el motivo en `ledger/sesiones/bloqueo.txt` y terminar sin marcar la
tarea, y el loop de etapas SHALL detenerse ahí.

#### Scenario: Etapa que necesita una VM
- **WHEN** una tarea requiere una VM
- **THEN** la sesión la usa solo a través del `scripts/vm.sh` del experimento, que la borra al terminar, y verifica
  antes de cerrar que no quedó ninguna VM encendida

#### Scenario: Etapa que necesita al tutor
- **WHEN** una tarea depende de una respuesta del tutor que no llegó
- **THEN** la sesión escribe el bloqueo con el motivo y `scripts/etapa.sh` termina con código 2

### Requirement: Comunicación con el tutor desde los documentos
El post al tópico `sampling_1` y cualquier respuesta posterior SHALL derivarse de `docs/hipotesis.md` y
`docs/diseno.md`, y las devoluciones del tutor SHALL volcarse en la bitácora con la fecha y el id del mensaje de Zulip.

#### Scenario: Devolución del tutor
- **WHEN** el tutor pide un cambio en el diseño
- **THEN** se actualiza el documento, se anota en la bitácora y, si cambia la grilla, se marcan las corridas previas
  como de la versión anterior

### Requirement: El control es un experimento
El control (`C`) y su réplica (`C-rep`) SHALL vivir en `experimentos/control/`, con las reglas comunes de decisión (G,
Δ, δ, T, A, N*, veredictos) en su `docs/hipotesis.md`. Las hipótesis SHALL citar esas reglas en lugar de repetirlas.
Cambiar una regla común SHALL anotarse en la bitácora de `control` y en la de cada experimento que depende de él.

#### Scenario: Leer la regla de decisión de H2
- **WHEN** se abre `experimentos/h2/docs/hipotesis.md`
- **THEN** encuentra su variable, su predicción y su regla de confirmación, y para δ y los veredictos hay una
  referencia a `experimentos/control/docs/hipotesis.md`

### Requirement: Una hipótesis, una carpeta
Cada hipótesis con variantes propias SHALL tener su experimento (`h1`, `h2`, `h3`, …). La comparación entre hipótesis, la
respuesta a la pregunta del tutor y el guion del video SHALL vivir en `experimentos/sampling_1/`, que depende de todos los
demás y del que no depende ninguno.

#### Scenario: Agregar H4
- **WHEN** el integrante que lleva H4 la incorpora
- **THEN** crea `experimentos/h4/` declarando `control` como dependencia, y `sampling_1` la suma a su comparación sin
  que cambie ninguna carpeta `h1`–`h3`

### Requirement: Estudios exploratorios declarados
Un integrante puede sumar un estudio que no sigue el protocolo, ya sea por usar otra grilla, otro entorno o variantes
elegidas mirando el test. Ese estudio SHALL vivir en una carpeta dentro del experimento al que pertenece:
- en el de la hipótesis que estudia;
- o en `sampling_1/exploratorios/` si cruza varias.

La carpeta SHALL tener un `README.md` (quién, cuándo, qué pregunta, qué corre, en qué se aparta del protocolo) y un
`exploratorio.json` con:
- autor y fecha;
- pregunta;
- protocolo, en una línea;
- advertencia, en una línea;
- los CSV de resultados y las columnas que se muestran como cifras principales.

Un exploratorio SHALL quedar fuera del registro de variantes, SHALL NOT escribir en el `ledger/` del experimento y SHALL
NOT cambiar ningún veredicto. Una idea que surja de un exploratorio y se quiera confirmar SHALL volver a correrse como
variante, con hipótesis escrita antes.

#### Scenario: Aporte de Martín
- **WHEN** se lee `experimentos/h3/sensibilidad_muestra/exploratorio.json`
- **THEN** su advertencia dice que las 10 muestras dan solo 4 modelos distintos y que hay un solo 201910, y el reporte
  de `sampling_1` lo muestra en el bloque B

#### Scenario: Idea de un exploratorio que se confirma
- **WHEN** el grupo quiere confirmar el reescalado √(1/r) que propuso un exploratorio
- **THEN** se registra la variante `H3R-0.1`, su predicción se escribe en `h3/docs/hipotesis.md` antes de correr y su
  resultado va al bloque A

#### Scenario: Manifiesto incompleto
- **WHEN** a un `exploratorio.json` le falta la advertencia o el protocolo
- **THEN** `python -m comun.variantes --verificar` falla nombrando la carpeta y el campo

### Requirement: Un aporte se incorpora replicándolo
Un aporte que llega de fuera del método se incorpora como estudio exploratorio, en un paquete que corre desde la raíz con
`python -m` sobre `comun/` y `DATOS_DIR`, sin rutas personales ni entornos externos.

Su `README.md` SHALL tener una tabla con estas columnas:
- cada número que reportó su autor;
- el número reproducido en `n2-highmem-8`;
- la diferencia;
- la explicación de cualquier diferencia que no sea cero.

Lo que el autor reportó sin código SHALL reconstruirse a partir de su descripción, marcarse como **reconstruido** en
el README y en el código, y dejar escrita la interpretación elegida cuando la descripción admite más de una.

#### Scenario: Número reproducido distinto del reportado
- **WHEN** la ganancia media de una estrategia de Luis reproducida en la VM difiere de la de su resumen
- **THEN** la tabla muestra las dos y la diferencia, y el README explica la causa (otro panel, otra cantidad de hilos,
  tiempos calibrados contra medidos) o dice que no se encontró

#### Scenario: Pieza sin código
- **WHEN** el resumen describe un resultado (por ejemplo, la búsqueda con hard negatives) cuyo código no está en el
  aporte
- **THEN** existe una reconstrucción marcada como tal, con la interpretación elegida escrita, y sus números van en la
  tabla con la etiqueta "reconstruido"

#### Scenario: Replicación byte a byte
- **WHEN** el aporte trae sus salidas con sha256, como `h3/sensibilidad_muestra/resultados/procedencia.json`
- **THEN** la replicación compara las huellas de las salidas nuevas con las registradas, y la tabla dice "idéntico" o
  muestra la primera diferencia

### Requirement: Ideas que vienen de mirar el test
Una variante que se registra a partir de un resultado ya visto en 201910 SHALL declararlo en su `docs/hipotesis.md`, y
el informe de su experimento y el de `sampling_1` SHALL listarla entre las limitaciones. Su predicción y su regla se
escriben igual que las demás, antes de correr.

#### Scenario: H4 viene del aporte de Luis
- **WHEN** se lee `experimentos/h4/docs/hipotesis.md`
- **THEN** dice que las variantes salieron de estrategias que Luis eligió mirando 201910, y que el resultado de H4 no
  cuenta con un mes de test que no se haya mirado

### Requirement: 201910 solo para la comparación
Como pide la consigna (Zulip 208135), toda elección SHALL hacerse con 201908. Esto vale para las variantes del registro
y para los estudios exploratorios. Una elección es:
- un orden entre estrategias;
- un descarte;
- un corte de envíos;
- una cantidad de semillas para ensamblar;
- un factor de reescalado;
- un "campeón".

201910 SHALL usarse solo para comparar, en una tabla que incluye todas las variantes o estrategias del estudio, y
ningún resultado en 201910 SHALL decidir qué se corre, qué se descarta ni con qué parámetros. 201909, 201911 y 201912 no
SHALL usarse.

#### Scenario: Exploratorio que eligió en test
- **WHEN** se porta un aporte que eligió o descartó estrategias por su resultado en 201910
- **THEN** el paquete portado ordena y clasifica con 201908, muestra 201910 solo en la tabla de comparación con todas las
  estrategias y deja los números originales en una sección de reproducción, separada de sus conclusiones

#### Scenario: Máximo de la curva
- **WHEN** un reporte muestra la ganancia máxima de una curva
- **THEN** la de 201908 puede orientar, y la de 201910 se informa como referencia pero ninguna conclusión se apoya en
  ella; la métrica que decide sigue siendo G al corte N\* fijado en 201908
