## RENAMED Requirements

- FROM: `### Requirement: Comparación de todos los brazos en una vista`
- TO: `### Requirement: Comparación de todas las variantes en una vista`

## MODIFIED Requirements

### Requirement: Reporte regenerable desde el ledger
Cada experimento SHALL tener un comando que genere su `informe/reporte.html` a partir de su ledger, del ledger de los
experimentos de los que depende, de las curvas guardadas y de su `docs/hipotesis.md`, sin números escritos a mano, y que
pueda correrse en cualquier momento con los resultados que haya. Un mismo comando SHALL poder regenerar todos los
reportes del repo.

#### Scenario: Regenerar con resultados parciales
- **WHEN** se genera el reporte y a una variante le faltan semillas o no tiene corridas
- **THEN** la variante aparece como pendiente con lo que tiene, y ninguna sección falla ni muestra un número inventado

#### Scenario: Regenerar dos veces
- **WHEN** se genera el reporte dos veces sin corridas nuevas
- **THEN** el archivo resultante es el mismo salvo la fecha de generación

#### Scenario: Mismos números que antes de separar
- **WHEN** se regeneran los reportes después de separar `sampling-velocidad`
- **THEN** cada Δ, IC, A y veredicto de los reportes de `h1`, `h2`, `h3` y `sampling_1` coincide con la tabla de
  resultados de `informe.md` anterior a la separación

### Requirement: Comparación de todas las variantes en una vista
El reporte de `sampling_1` SHALL mostrar una tabla con todas las variantes de todas las hipótesis contra el control (ganancia
media, diferencia apareada con su intervalo, tiempo, aceleración, veredicto), un gráfico de tiempo contra ganancia con
un punto por variante y el control marcado, y un enlace al reporte de cada hipótesis. El reporte de cada hipótesis SHALL
mostrar las curvas de ganancia (banda entre semillas) de sus variantes junto al control.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre el reporte de una hipótesis
- **THEN** se ve su predicción, la regla, el resultado de cada variante y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y la figura que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos una variante tienen sus 10 semillas
- **THEN** el reporte de `sampling_1` incluye la comparación a tiempo igual (ensamble de K semillas de la variante contra el
  control) con el K usado

#### Scenario: Hipótesis nueva en `sampling_1`
- **WHEN** se registra un experimento nuevo con variantes (por ejemplo `h4`)
- **THEN** el reporte de `sampling_1` lo incluye en la tabla y en el gráfico sin cambiar el generador
