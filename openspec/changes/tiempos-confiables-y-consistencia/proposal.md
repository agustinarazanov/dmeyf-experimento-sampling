# Proposal

## Why

El tutor pidió (Zulip, 13-nov) "medir tiempos de forma confiable" y preguntó si el undersampling dialoga con H1 y usa los
mismos cortes. Una revisión del repo (13-nov) encontró dos cosas. La primera es que la aceleración A no se calcula igual
en todas las filas. Las variantes sin réplicas (`U*`, `B*`, `GOSS`) dividen por el T de la réplica 0 del control (797 s);
las que tienen réplicas, por la mediana del control (1.002 s). El T del control varía de 682 a 1.264 s entre las 8
réplicas de Optuna, y U0.5 queda con A = 2,25, cerca del umbral A ≥ 2 de "vale la pena". La segunda es una serie de
frases de los informes que contradicen las tablas o quedaron de rondas anteriores.

La máquina no es la fuente del ruido. Todas las corridas usaron la misma CPU, con un trabajo por VM, y el tiempo del
mismo modelo entre semillas varía entre el 1 y el 5 %. El ruido viene de los hiperparámetros que recorre y elige Optuna,
así que lo que se corrige es la definición y el reporte de A, más una medición a hiperparámetros fijos. No hace falta
volver a correr la grilla.

## What Changes

- **A con una sola referencia**: en todas las filas del bloque A, A = mediana de T_C entre réplicas / T de la variante.
  Junto a A va su rango (mínimo y máximo de T_C entre réplicas sobre el T de la variante, o el rango entre réplicas de
  la variante cuando las tiene). Cambian los A de `U*`, `B*` y `GOSS` en `tabla_resultados.md`, los informes y el README.
  Este cambio es deliberado: modifica la regla "tabla de resultados intacta" del spec vigente.
- **Medición a hiperparámetros fijos** (nueva, exploratoria y pre-registrada): con los hiperparámetros de las 8 réplicas
  del control, entrenar sobre r = 1; 0,5; 0,25; 0,1; 0,05 del train 201903–201906, prediciendo 201908 como un trial, con
  repeticiones. Separa la aceleración que da el tamaño de los datos de la que da la elección de Optuna.
- **Réplicas de U0.5**: 7 estudios `U0.5@1…7` con sus finales de la ronda 201903–201908. U0.5 es la única variante que
  vale la pena y no tiene réplicas, y su A está cerca del umbral.
- **Respuesta al tutor**: el informe conjunto deja de decir que no se toca la proporción de clases sin matiz (H4 la
  toca) y justifica el corte fijo N* = 3.300 en `H4F-*`, cuyo final entrena con otra proporción reponderada. El borrador
  de la respuesta sale de los documentos, como pide el protocolo.
- **Correcciones de texto**:
  - **H4U-0.1**: "los dos IC enteros debajo de −δ" (`h4/informe/informe.md:78`, `sampling_1/informe/informe.md:177`).
    El IC de `H4U-0.1` no queda entero debajo de −δ.
  - **`decisiones.md`**: se marca como de la ronda de las fases 1–4 o se actualiza.
  - **"Diez variantes"** (`informe.md:44`): el informe ya tiene 21. Se agrega además que H3 también reusa U0.05.
  - **Rangos de varianza entre réplicas** (`guion.md:18`, `informe.md:196`): el rango real va del 17 al 58 %.
  - **ΔAUC contra Δ de H3** (`informe.md:188`): la frase se generaliza de más.
  - **h4 en el README** de `sampling_1`.
  - **Tabla de rondas**: tiene una fila `C | pendiente` y no explica por qué no está `H4O-0.5`.
  - **A de la réplica 0 en `h3/informe`**: sin explicación.
  - **Figuras**: falta `bandas_H4` en la lista.
  - **"Misma máquina"** en `guion.md`.
  - **δ = 5,52 en H3**: el informe de H3 no avisa que se reemplaza.
  - **Hipótesis de H1** (`h1/informe/informe.md:11`): se redacta como predicción pre-registrada, para que no se lea
    como resultado.
- Fuera de alcance: `Experimentos guion.md` en la raíz, a pedido de Agustina.

## Capabilities

### New Capabilities

- `medicion-tiempos`: cómo se mide y reporta el tiempo de una variante. Incluye la referencia única del control, el
  rango de A y la medición a hiperparámetros fijos que separa el tamaño de los datos de la elección de Optuna.

### Modified Capabilities

- `reporte-visual`: "Comparación limpia en dos bloques" cambia la fuente de T y A, que antes salían de la réplica 0 en
  las filas sin réplicas, agrega el rango de A y admite que el bloque A cambie en este cambio, en lugar de quedar
  idéntico.

## Impact

- **Código**:
  - `comun/reporte.py`, para A y su rango. Es un cambio en `comun/` y se anuncia en el commit.
  - `scripts/comparar_rondas.py`.
  - Un script nuevo de medición a hiperparámetros fijos en `experimentos/sampling_1/scripts/`.
  - El registro de `U0.5@k` en `comun/variantes.py`.
- **Ledger**:
  - `h1/ledger`, con los estudios y finales de `U0.5@k`.
  - Un CSV nuevo con la medición a hiperparámetros fijos.
- **Documentos**:
  - Los informes de `sampling_1`, `h1`, `h3` y `h4`, más `decisiones.md`, `guion.md`, el README de `sampling_1`,
    `tabla_resultados.md`, `comparacion_rondas.md` y las figuras.
  - La predicción pre-registrada en `control/docs/hipotesis.md` y `h1/docs/hipotesis.md`.
- **Cómputo**: una VM `n2-highmem-8` a pedido por unas 2–3 h (réplicas de U0.5 y medición), que Agustina lanza.
