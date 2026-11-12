# Tasks

Requiere `incorporar-aportes` archivado. Convive con `sitio-github-pages` (no toca `reporte-visual`).

## 1. Diseño y predicción (sesión: Opus)

- [ ] 1.1 `control/docs/hipotesis.md`:
  - la ventana del final 201903–201908 con el id 211210;
  - N\* = 3.300 fijo (D3);
  - la lista de 20 semillas en orden (D5);
  - la predicción y la regla de la ronda (D7);
  - las tres adaptaciones del spec de `protocolo-experimental`, con sus ids de Zulip.

  Verificar con un grep que cada adaptación tiene su id y que la regla tiene umbral numérico.
- [ ] 1.2 `control/docs/diseno.md`, el `docs/diseno.md` de cada hipótesis y `sampling_1/docs/diseno.md`:
  - la ronda nueva;
  - la fase 7 (D8) con horas y costo;
  - en `h3` y `h4`, la nota de que `H3` y `H4F` no reoptimizan para el final (211718).

  Anotar 211210 y 211718 en la bitácora de `sampling_1`. Verificar que los enlaces existen.
- [ ] 1.3 Revisión en sesión limpia de hipótesis y diseño con `docs/revision.md` § 1 y § 2, y cierre en la bitácora.
  Ninguna corrida real antes de este cierre.

## 2. Código y migración (sesión: Sonnet)

- [ ] 2.1 `comun/baseline.py`:
  - `MESES_TRAIN_OPT` y `MESES_TRAIN_FINAL` (D1);
  - `MESES_PANEL` con 201907;
  - `N_ESTRELLA = 3300`;
  - `SEMILLAS_FINALES` con 20.

  `comun/datos.py`: etiqueta de 201907 y reconstrucción del panel si falta 201907 (D2). Tests sin datos:
  - con un crudo de juguete, la clase de 201907 sale de 201908 y 201909;
  - un panel sin 201907 se reconstruye.

  Verificar que `pytest` pasa.
- [ ] 2.2 `comun/correr.py`:
  - `optimizar` con `MESES_TRAIN_OPT` y un guard que falla si lee 201907;
  - `final` con `MESES_TRAIN_FINAL`, sin predecir 201908 (`auc_val` y `curva_201908` vacíos);
  - `meses_final` en la fila e id con la ventana (D4).

  `comun/ledger.py`: `meses_final` obligatoria en los finales. Tests:
  - un final sin `meses_final` no se escribe;
  - `optimizar` no lee 201907 ni 201910.

  Verificar que `pytest` pasa.
- [ ] 2.3 `scripts/agregar_meses_final.py --aplicar/--verificar` (D4). Aplicarlo a los ledgers de los cinco experimentos.
  Verificar con `--verificar` que todos los finales previos quedan en `201903-201906` y que el resto de cada archivo no
  cambia.
- [ ] 2.4 `comun/consolidar.py --meses-final` (D3, D4):
  - `corte_control` para la ronda vieja y `N_ESTRELLA` para la nueva;
  - falla si la ronda no tiene `C`.

  Antes de cambiar nada, copiar `apareado.csv` y `replicas.csv` de cada experimento a `ledger/ronda_201903-201906/`.
  Verificar que `consolidar --meses-final 201903-201906` las reproduce byte a byte.
- [ ] 2.5 `comun/reporte.py` rotula la ventana del final y la cantidad de semillas. `scripts/comparar_rondas.py` escribe
  `sampling_1/informe/comparacion_rondas.md` (D9). Verificar con un test sobre ledgers sintéticos de dos rondas que la
  tabla no mezcla rondas y muestra los dos δ.
- [ ] 2.6 Smoke en la Mac con `--filas 20000`:
  - panel reconstruido;
  - huellas por columna de 201903–201906, 201908 y 201910 iguales a las del panel viejo (D2);
  - un final de `C` y uno de `H4F-0.05` con dos semillas en una salida temporal, con `meses_final = 201903-201908` y sin
    curva de 201908.

  Verificar las tres cosas en la salida.
- [ ] 2.7 Listas `sampling_1/scripts/fase7_r0.txt` … `fase7_r7.txt` (D8). Verificar con `lanzar_fase.sh --en-seco` que
  cubren las 113 celdas sin repetir, con `--semilla todas`.
- [ ] 2.8 Revisión en sesión limpia del grupo 2 con `docs/revision.md` § 3 y cierre en la bitácora. Crear el tag
  `corridas-v4` (lo pushea Agustina).

## 3. Corridas (VM, todas las lanza Agustina)

- [ ] 3.1 Aplicar `agregar_meses_final.py` a la copia del bucket, subirla y verificarla bajándola de nuevo con
  `--verificar`.
- [ ] 3.2 Verificar la cuota de vCPU y el crédito. Lanzar `fase7_r0` … `fase7_r7` en dos tandas de 4 VMs. Verificar al
  terminar que no quedan VMs encendidas (`gcloud compute instances list`) y anotar horas y costo en la bitácora.
- [ ] 3.3 `python -m comun.consolidar` (ronda vigente) y `--sanity`. Verificar:
  - 113 celdas × 20 semillas;
  - todo en `n2-highmem-8`, con `codigo_sucio = False` y `meses_final = 201903-201908`;
  - `n_estrella = 3300` en todas las tablas.
- [ ] 3.4 Revisión en sesión limpia de las corridas con `docs/revision.md` § 4 y cierre en la bitácora.

## 4. Informes (sesión: Opus)

- [ ] 4.1 `python -m comun.reporte --todos` y `scripts/comparar_rondas.py`. Aplicar la regla de D7 y escribir el
  resultado en la bitácora de `control`. Verificar que `comparacion_rondas.md` tiene las 113 celdas, o una fila por
  variante con réplicas agregadas.
- [ ] 4.2 Actualizar `informe.md` de `h1`–`h4` y de `sampling_1`, el guion y el README a la ronda nueva:
  - § Limitaciones con las tres adaptaciones y sus ids;
  - la tabla de rondas;
  - un párrafo en el README de `validacion_20_semillas`.

  Verificar con `verificar_readme.py`, `verificar_informe_h3.py --informe` y la copia idéntica del bloque A y B desde
  `tabla_resultados.md`.
- [ ] 4.3 Revisión en sesión limpia de la etapa informe con `docs/revision.md` § 5 (incluye "toda adaptación declarada"
  y el escenario de aclaración nueva en Zulip) y cierre en las bitácoras. Correr `comun/tokens.py`.

## Workflow follow-up

- Archivar con `/opsx:archive` cuando las tres revisiones estén cerradas.
- Si el tutor responde que la ventana es 201905–201908, abrir otro cambio: es una ronda más y no cambia este diseño.
