# Proposal

## Why

El 9-nov, en el hilo del baseline, Luis Suárez preguntó: "Para el test en mes 10, ¿se reentrena incluyendo los meses 07 y
08?". Bolaños respondió "Yes" (Zulip 211210). Hoy el modelo final de cada variante entrena solo con train 201903–201906
(`comun/correr.py:263`) y el panel ni siquiera tiene 201907. La revisión contra la consigna (12-nov) lo marcó como el único
✗: no es el protocolo pedido y no aparece entre las limitaciones.

Hay que volver a correr todos los finales. Aprovechamos esa corrida para pasar de 10 a 20 semillas finales, como propuso
Luis en su aporte de 20 semillas (`sampling_1/exploratorios/validacion_20_semillas`). La lista de semillas se fija antes
de correr.

## What Changes

- **Final con seis meses.** El modelo final entrena con 201903–201908 y se evalúa en test (201910). Agustina eligió los
  seis meses, no una ventana corrida 201905–201908.
- **Optuna no cambia.** Sigue entrenando con train 201903–201906 y eligiendo por AUC en validación (201908). Los estudios
  y los hiperparámetros ya guardados (réplicas `@k` incluidas) se reusan; no se vuelve a optimizar.
- **El panel suma 201907**, con su clase. Para tener la etiqueta de 201908 hacen falta 201909 y 201910 del crudo, que ya se
  leen para los lags; 201909 sigue sin usarse para entrenar, validar ni evaluar.
- **N\* queda fijo en 3.300**, el valor de la ronda anterior, calculado en validación con modelos que no vieron 201908.
  Con el final nuevo, la predicción de 201908 es dentro de la muestra y ya no sirve para fijar el corte. δ sigue la regla
  de `control` (2 % de la ganancia media del control en 201910 al corte N\*) y se recalcula con el control nuevo.
- **20 semillas finales.** Son las 10 oficiales más 10 de la fórmula de Luis, `110017 + i·19937` con i = 0…9. Valen
  para el control y todas las variantes, en todas las réplicas.
- **Se vuelven a correr todos los finales:** `C` y `C-rep` y las variantes de `h1`, `h2`, `h3` y `h4`, más las 8 réplicas
  de `H4O-0.5`. Son 121 celdas (variante × réplica) × 20 semillas.
- **La ronda anterior se conserva.** Sus 10 semillas con el final de 4 meses quedan en el ledger, marcadas con la ventana
  del final, y sus tablas consolidadas se guardan aparte. Nada se pisa.
- **Informes, guion y README** pasan a la ronda nueva y comparan sus veredictos con los de la anterior.
- **AUC además de ganancia.** 208135 dice "métrica auc". Cada tabla muestra ΔAUC en test con su IC (con réplicas
  cuando existen) al lado de Δ de ganancia. El veredicto sigue saliendo de la ganancia, como dice la regla escrita antes
  de correr; el AUC se lee junto a ella.
- **Variante nueva `H4O-0.5`.** El tutor pidió reoptimizar siempre que cambia el dataset (Tschopp, Zulip 211718).
  `H4F` busca sobre una muestra uniforme y entrena con otra receta (todas las bajas + 50 % de CONTINUA con peso 2).
  `H4O-0.5` usa esa misma receta para optimizar y para entrenar, con 8 réplicas (estudio `F0.5`). Se compara con el
  control y con `H4F-0.05`, con predicción escrita antes de correr.
- **Apartamientos justificados no son limitaciones.** Cada apartamiento del baseline o de un tutor se escribe en el
  diseño con su id y su motivo. `H3` no reoptimiza para el final porque esa es la hipótesis. `H4F` contra `H4O` es un
  contraste del experimento. Solo lo que no tiene justificación va a § Limitaciones.
- Consultar al tutor si la ventana es 201903–201908 o 201905–201908 **no** es una tarea del cambio. Si Agustina lo
  pregunta, la respuesta se anota en la bitácora.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `corrida-reproducible`:
  - meses del final (201903–201908) separados de los de optimización (201903–201906);
  - 20 semillas finales;
  - N\* fijo de la ronda anterior;
  - búsqueda sobre el set del final (`H4O-0.5`).
- `ledger-resultados`:
  - columna con la ventana del final;
  - consolidado por ronda, sin mezclar ventanas;
  - la ronda anterior se conserva;
  - ΔAUC con réplicas en `replicas.csv`.
- `protocolo-experimental`: cada apartamiento del baseline o de un tutor se escribe con su id; solo los que no están
  justificados en el diseño son limitaciones.
- `reporte-visual`: el bloque A suma ΔAUC con su IC al lado de Δ de ganancia.

## Impact

- `comun/` (anunciar en el commit):
  - `baseline.py`: meses del final, semillas extra, N\* fijo;
  - `datos.py`: 201907 en el panel; el panel se reconstruye una vez por máquina;
  - `correr.py`: entrena el final con los meses del final, no registra AUC de 201908 como validación;
  - `metodos.py` y `variantes.py`: método y variante `H4O-0.5`, estudio `F0.5` con réplicas;
  - `ledger.py` y `consolidar.py`: ventana del final, N\* fijo, consolidado por ronda;
  - `reporte.py`: rótulos con la ventana y la cantidad de semillas, y la columna de ΔAUC.
- Ledgers de los cinco experimentos: los finales viejos reciben la columna nueva con un script de migración que se
  puede verificar; las tablas de la ronda anterior se copian aparte antes de consolidar.
- Cómputo:
  - los finales actuales suman ~7,5 h en `n2-highmem-8`;
  - con 20 semillas y 6 meses, más los 8 estudios y 160 finales de `H4O-0.5`, el estimado es ~24 h de cómputo, ~7 h
    de pared con 4 VMs (cuota de 32 vCPU) y ≈ US$ 5 en spot;
  - las VMs las lanza Agustina.
- Docs:
  - `control/docs/hipotesis.md` y `diseno.md`;
  - el `docs/diseno.md` de cada hipótesis;
  - los informes de `h1`–`h4` y de `sampling_1`, el guion y el README.
- Convive con `sitio-github-pages`, que también modifica `reporte-visual` pero otro requisito («Legible sin servidor y
  compartible»); este cambio toca «Comparación limpia en dos bloques».
