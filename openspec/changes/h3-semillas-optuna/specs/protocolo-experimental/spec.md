## ADDED Requirements

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

#### Scenario: Aporte de Luis
- **WHEN** se lee `experimentos/sampling_1/exploratorios/validacion_50_semillas/exploratorio.json`
- **THEN** su advertencia dice que las 50 semillas varían solo la semilla final y que las variantes se eligieron mirando
  201910, y el reporte de `sampling_1` lo muestra en el bloque B

#### Scenario: Idea de un exploratorio que se confirma
- **WHEN** el grupo quiere confirmar el reescalado √(1/r) que propuso un exploratorio
- **THEN** se registra la variante `H3R-0.1`, su predicción se escribe en `h3/docs/hipotesis.md` antes de correr y su
  resultado va al bloque A

#### Scenario: Manifiesto incompleto
- **WHEN** a un `exploratorio.json` le falta la advertencia o el protocolo
- **THEN** `python -m comun.variantes --verificar` falla nombrando la carpeta y el campo
