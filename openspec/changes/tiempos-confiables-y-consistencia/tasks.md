# Tasks

Requiere la ronda 201903–201908 consolidada (`final-con-julio-agosto`). `Experimentos guion.md`, en la raíz, queda fuera.

## 1. Predicciones y diseño (sesión: Opus)

- [ ] 1.1 `control/docs/hipotesis.md` § Medición a hiperparámetros fijos (13-nov):
  - la definición de A_fijo(r) y del CV entre repeticiones;
  - la predicción y la regla de D5, confirmadas o ajustadas por Agustina;
  - que es exploratoria y no cambia veredictos.

  En la misma sección, la regla nueva de A (D1, D2), con el motivo: la regla vieja usaba dos referencias de T_C. El
  texto viejo de § Métricas y reglas comunes no se reescribe.
- [ ] 1.2 `h1/docs/hipotesis.md` § Réplicas de U0.5: la predicción y la regla de D6, escritas antes de cualquier
  corrida. `h1/docs/diseno.md`: la fase 8 con horas y costo.
- [ ] 1.3 Anotar en la bitácora de `sampling_1` el mensaje del tutor (13-nov, con el id de Zulip) y la revisión que
  originó este cambio.
- [ ] 1.4 Revisión en sesión limpia de 1.1–1.3 con `docs/revision.md` § 1 y § 2, y cierre en la bitácora. Ninguna
  corrida antes de este cierre.

## 2. Código (sesión: Sonnet)

- [ ] 2.1 `comun/reporte.py`, A con una sola referencia (D1):
  - T_C mediana entre réplicas para todas las filas del bloque A;
  - la nota `AVISO_A` actualizada, que también dice que el tiempo igual de la réplica 0 sigue con T_C de la réplica 0
    (D3).

  Test en `pytest`: A × T(variante) es igual para todas las filas.
- [ ] 2.2 `comun/reporte.py`, rango de A (D2):
  - una columna nueva al final de la tabla de `tabla_resultados.md`;
  - en el HTML, debajo de A, en letra chica;
  - en el gráfico de tradeoff, como barra horizontal sobre A.

  Tests para una variante con réplicas y otra sin.
- [ ] 2.3 `scripts/comparar_rondas.py`: sacar la fila del control y agregar la nota sobre `H4O-0.5` (D7).
- [ ] 2.4 `experimentos/sampling_1/scripts/tiempos_hp_fijos.py` (D4):
  - importa solo de `comun/`;
  - orden aleatorizado con semilla fija;
  - una fila por medición en `experimentos/sampling_1/ledger/tiempos_hp_fijos.csv`;
  - se niega a correr fuera de `n2-highmem-8` salvo con `--prueba`.

  Smoke test local con `--prueba`, 1 juego de hiperparámetros, 2 tasas, 1 repetición y datos reducidos. El CSV de prueba
  no se commitea.
- [ ] 2.5 `comun/variantes.py`: `U0.5` con `replicas=True` (D6). `python -m comun.variantes --verificar`. Escribir
  `experimentos/sampling_1/scripts/fase8.txt`, con optimizar y finales de `U0.5@1…7` a 20 semillas, más la medición
  de 2.4.
- [ ] 2.6 `comun/reporte.py`: sección de la medición a hiperparámetros fijos en el informe conjunto.
  - Por r: A_fijo con su mediana y su rango entre juegos de hiperparámetros, al lado del A del bloque A de la variante U.
  - El CV entre repeticiones.

  Si el CSV no existe, la sección sale como pendiente.
- [ ] 2.7 Revisión en sesión limpia del código con `docs/revision.md` § 3. Commit que anuncia el cambio en `comun/`.

## 3. Corridas (VM a pedido, la lanza Agustina)

- [ ] 3.1 Verificar el crédito y lanzar una VM `n2-highmem-8` a pedido con `fase8.txt`. Al terminar, verificar que no
  queda ninguna VM encendida y anotar horas y costo en la bitácora.
- [ ] 3.2 `python -m comun.consolidar` y `--sanity`. Verificar:
  - 7 estudios `U0.5@k` con 20 finales cada uno y 120 filas en `tiempos_hp_fijos.csv`;
  - todo en `n2-highmem-8` con `codigo_sucio = False`.
- [ ] 3.3 Revisión en sesión limpia de las corridas con `docs/revision.md` § 4 y cierre en la bitácora.

## 4. Informes (sesión: Opus)

- [ ] 4.1 `python -m comun.reporte --todos` y `scripts/comparar_rondas.py`. Aplicar las reglas de 1.1 y 1.2 y escribir
  el resultado en las bitácoras de `control` y `h1`. Verificar el escenario "Tabla de resultados intacta" (versión de este cambio) sobre el estado previo
  a las corridas de U0.5, o explicar en la bitácora qué más cambió con ellas.
- [ ] 4.2 Correcciones de texto (D7), cada una contra `tabla_resultados.md` regenerada:
  - `h4/informe/informe.md:78` y `sampling_1/informe/informe.md:177`: solo el IC de `H4H-0.1` queda entero debajo de
    −δ; `H4U-0.1` pierde por la media.
  - `sampling_1/informe/decisiones.md`: aviso de que es de las fases 1–4. `informe.md:206` deja de enlazarlo para los
    números.
  - `informe.md:44`: la cantidad de variantes sale del bloque A, y H3 también reusa los estudios de U0.05.
  - `guion.md:18` e `informe.md:196`: el rango de varianza entre réplicas sale de la tabla de varianza (hoy, del 17 al
    58 %).
  - `informe.md:188`: la frase de ΔAUC contra Δ de ganancia se limita a las variantes en que se cumple, como
    `h3/informe/informe.md:76`.
  - `experimentos/sampling_1/README.md:3-4`: agregar `h4`.
  - `h3/informe/informe.md:42-43`: decir que esos A son de la réplica 0 contra el T_C de la réplica 0, o reemplazarlos
    por la regla nueva.
  - `informe.md:155-157`: agregar `bandas_H4.png`.
  - `guion.md:12`: "en VMs del mismo tipo", no "en la misma máquina".
  - `h3/informe/informe.md`: una línea que dice que el δ = 5,52 de `h3/docs/hipotesis.md` es de la ronda anterior y
    que la ronda vigente usa 5,65, como ya hace `h4`.
  - `h1/informe/informe.md:11` e `informe.md:23`: redactar H1 como predicción pre-registrada ("predecía que…").
- [ ] 4.3 Tiempos en los informes:
  - los A nuevos y su rango en `informe.md`, los informes de `h1`–`h4`, `guion.md` y el README raíz;
  - un párrafo en § Diseño o § Limitaciones con lo medido: la misma CPU, el CV de máquina, el rango por Optuna y la
    medición a hiperparámetros fijos;
  - si U0.5 cambia de veredicto o queda con A < 2, actualizar la lista de "vale la pena" en todos los documentos.

  Verificar con `verificar_readme.py` y `verificar_informe_h3.py --informe`.
- [ ] 4.4 Respuesta al tutor (D8):
  - en `informe.md:15`, matizar "sin cambiar la proporción de clases": H4 la cambia, y se dice dónde y cómo;
  - una frase sobre el corte N* fijo en `H4F`;
  - el borrador `experimentos/sampling_1/docs/zulip/02_tiempos_y_undersampling.md`, que sale de los documentos.

  Agustina lo postea.
- [ ] 4.5 Revisión en sesión limpia del informe con `docs/revision.md` § 5, cierre en las bitácoras y
  `comun/tokens.py`.

## Workflow follow-up

- Archivar con `/opsx:archive` cuando estén cerradas las cuatro revisiones (1.4, 2.7, 3.3 y 4.5).
