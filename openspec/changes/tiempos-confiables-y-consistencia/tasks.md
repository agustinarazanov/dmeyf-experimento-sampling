# Tasks

Requiere la ronda 201903–201908 consolidada (`final-con-julio-agosto`). `Experimentos guion.md`, en la raíz, queda fuera.

Qué puede ir en paralelo:
- Después de cerrar 1.5: el grupo 2 (código de corridas), el grupo 3 (código del reporte), 4.1 (correcciones de texto
  que no dependen de números nuevos) y 4.2 (primera respuesta al tutor). 2 y 3 tocan archivos distintos de `comun/` y
  pueden ir en dos sesiones, cada una en su rama; 3.5 a 3.7 leen del registro lo que deja 2.2, así que esperan a esa
  tarea.
- En el grupo 5: las 9 VMs a la vez (17 si la cuota alcanza).
- En el grupo 6: los informes de `h1`, `h2`, `h3` y `h4` (6.2), cada uno en su sesión; el conjunto va después.

## 1. Predicciones y diseño (sesión: Opus)

- [ ] 1.1 `control/docs/hipotesis.md` § Medición de tiempos (13-nov):
  - la regla nueva de A (D1, D2), con el motivo: la regla vieja usaba dos referencias de T_C. El texto viejo de
    § Métricas y reglas comunes no se reescribe;
  - la definición de A_fijo(r), del cociente entre recetas y del CV entre repeticiones, con la predicción y la regla de
    D5;
  - la calibración por máquina, con la predicción y la regla de D6;
  - el CV entre semillas dentro de una VM recalculado del ledger de la ronda, con el comando que lo da;
  - que la medición y la calibración son exploratorias y no cambian veredictos.

  Las predicciones las confirma o ajusta Agustina.
- [ ] 1.2 Predicciones de la grilla (D13), cada una en una sección nueva con fecha, escrita antes de cualquier corrida y
  con la declaración de que la variante se agrega después de ver 201910:
  - `h1/docs/hipotesis.md` § Réplicas de H1;
  - `h2/docs/hipotesis.md` § Réplicas de H2 y `B0.05`;
  - `h3/docs/hipotesis.md` § `H3-0.5`;
  - `h4/docs/hipotesis.md` § Grilla común: `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, las cuatro `H4P`, los pares de D12 y los
    cuatro contrastes principales. § Comparaciones múltiples suma los 17 contrastes.

  Las predicciones las confirma o ajusta Agustina.
- [ ] 1.3 Diseño:
  - `h1`–`h4/docs/diseno.md`: variantes, estudios y grilla nuevos de cada una; en `h3` y `h1`, el cambio de dueño de
    `U{r}@k` (D10) y `## Dependencias`;
  - `sampling_1/docs/diseno.md`: la fase 8 (D15) con listas, horas y costo, y la tabla de la grilla común (D8);
  - `sampling_1/docs/hipotesis.md` § Pregunta: la grilla común y los pares directos (D12).
- [ ] 1.4 Anotar en la bitácora de `sampling_1` el mensaje del tutor (Zulip 212124, 12-nov), la revisión del 13-nov que
  originó este cambio y la ampliación a la grilla común.
- [ ] 1.5 Revisión en sesión limpia de 1.1–1.4 con `docs/revision.md` § 1 y § 2, y cierre en la bitácora. Ninguna
  corrida antes de este cierre.

## 2. Código de corridas (sesión: Sonnet)

- [ ] 2.1 Dueño de `U{r}@k` (D10), en un commit propio:
  - `comun/variantes.py`: `dueno_estudio` y `dueno_variante` sin el caso especial de `h3`;
  - un script que mueve de `h3/ledger` a `h1/ledger` los 21 estudios `U0.25@k`, `U0.1@k` y `U0.05@k`, sin cambiar ids
    ni contenido;
  - verificar el invariante: `python -m comun.consolidar` de `h3` y `h4` da las mismas tablas antes y después;
  - `python -m comun.variantes --verificar` y `pytest`.
- [ ] 2.2 Variantes y métodos (D8, D9, D12):
  - `comun/metodos.py`: `fast-retrain-opt` con la fracción igual a la tasa de la variante (0,5; 0,25; 0,1; 0,05) y el
    peso 1/f; `H4F-*` sigue con 0,5. El método nuevo de `H4P` (búsqueda de `fast-retrain-opt`, final de `opt-muestra`);
  - `comun/variantes.py`: `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, `H4P-0.5`, `H4P-0.25`, `H4P-0.1`, `H4P-0.05` y
    `B0.05`; estudios `F0.25`, `F0.1`, `F0.05` y `B0.05`; `replicas=True` en `U*`, `B*` y `GOSS`; los pares de D12 con la
    decisión que aísla cada uno y cuáles son principales; la fila de la grilla de cada variante y la lista de celdas que
    no se corren, con su motivo (D11);
  - tests: la réplica 0 de lo que ya existe no cambia (mismo `hash_muestra` e hiperparámetros con `--filas 20000`);
    `H4O-0.1` y `H4P-0.1` comparten estudio; la muestra de `H4O-{f}` tiene todas las bajas y round(f · CONTINUA).

  Smoke test local con `--filas 20000` de una variante nueva de cada fila, en `optimizar` y `final`.
  `python -m comun.variantes --verificar`.
- [ ] 2.3 `experimentos/sampling_1/scripts/tiempos_hp_fijos.py` (D4, D6):
  - importa solo de `comun/`;
  - las dos recetas (al azar y bajas con peso), orden aleatorizado con semilla fija;
  - una fila por medición en `experimentos/sampling_1/ledger/tiempos_hp_fijos.csv`, con el nombre de la instancia;
  - `--calibracion`, que escribe en `experimentos/sampling_1/ledger/calibracion.csv` con la lista y el momento;
  - se niega a correr fuera de `n2-highmem-8` salvo con `--prueba`.

  Smoke test local con `--prueba`, 1 juego de hiperparámetros, 2 tasas, 1 repetición y datos reducidos. Los CSV de
  prueba no se commitean.
- [ ] 2.4 `scripts/vm.sh`: corre la calibración antes y después de la lista y trae los dos CSV con los ledgers.
  Verificar con `--en-seco`.
- [ ] 2.5 Listas de la fase 8 en `experimentos/sampling_1/scripts/` (D15): `fase8_r0` … `fase8_r7` y `fase8_medicion`,
  más las mitades `_a` y `_b` de cada réplica. En cada lista, los estudios van antes que sus finales.
  `scripts/lanzar_fase.sh --en-seco` de todas: 67 estudios y 2.560 finales en total, y ninguna corrida repetida.
- [ ] 2.6 Revisión en sesión limpia de 2.1–2.5 con `docs/revision.md` § 3. Commit que anuncia el cambio en `comun/`.

## 3. Código del reporte (sesión: Sonnet)

- [ ] 3.1 `comun/reporte.py`, A con una sola referencia (D1):
  - T_C mediana entre réplicas para todas las filas del bloque A;
  - la nota `AVISO_A` actualizada, que también dice que el tiempo igual de la réplica 0 sigue con T_C de la réplica 0
    (D3).

  Test en `pytest`: A × T(variante) es igual para todas las filas.
- [ ] 3.2 `comun/reporte.py`, rango de A (D2):
  - una columna nueva al final de la tabla de `tabla_resultados.md`;
  - en el HTML, debajo de A, en letra chica;
  - en el gráfico de tradeoff, como barra horizontal sobre A;
  - en las filas sin réplicas, la nota de que el rango solo mueve el control.

  Tests para una variante con réplicas y otra sin.
- [ ] 3.3 Regenerar `tabla_resultados.md` sin corridas nuevas y verificar el escenario "Tabla de resultados intacta":
  solo cambian A y su rango. Guardar el diff en la bitácora. Esto va antes de consolidar la fase 8.
- [ ] 3.4 `scripts/comparar_rondas.py`: sacar la fila del control y agregar la nota sobre las variantes que solo existen
  en la ronda nueva (D16).
- [ ] 3.5 `comun/reporte.py`, tabla de cobertura (D11), leída del registro que deja 2.2: en el reporte de `sampling_1` y
  en `tabla_resultados.md`. Test con un registro de juguete que tiene una celda sin correr.
- [ ] 3.6 `comun/reporte.py`, comparaciones directas (D12): la tabla "Diferencias entre variantes" suma la columna de
  qué aísla cada par y marca los principales. Un par cuya variante todavía no tiene corridas sale como pendiente.
- [ ] 3.7 `comun/reporte.py`, sección de tiempos del informe conjunto (D4, D6, D7):
  - por r: A_fijo con su mediana y su rango entre juegos de hiperparámetros, al lado del A del bloque A de `U{r}` y de
    `H4O-{r}`; el cociente entre recetas; el CV entre repeticiones;
  - calibración: CV entre VMs y cociente fin/inicio por VM;
  - por variante: mediana de búsqueda, mediana de final y fracción de T que es búsqueda.

  Si un CSV no existe, su parte sale como pendiente.
- [ ] 3.8 Revisión en sesión limpia de 3.1–3.7 con `docs/revision.md` § 3. Commit que anuncia el cambio en `comun/`.
  Si 2 y 3 fueron en ramas separadas, unirlas y correr `pytest` y `--verificar` sobre la unión.

## 4. Texto que no espera a las corridas (sesión: Opus)

- [ ] 4.1 Correcciones de texto que no citan números nuevos (D16):
  - `h4/informe/informe.md:78` y `sampling_1/informe/informe.md:177`: solo el IC de `H4H-0.1` queda entero debajo de
    −δ; `H4U-0.1` pierde por la media.
  - `sampling_1/informe/decisiones.md`: aviso de que es de las fases 1–4. `informe.md:206` deja de enlazarlo para los
    números.
  - `guion.md:18` e `informe.md:196`: el rango de varianza entre réplicas sale de la tabla de varianza (hoy, del 17 al
    58 %).
  - `informe.md:188`: la frase de ΔAUC contra Δ de ganancia se limita a las variantes en que se cumple, como
    `h3/informe/informe.md:76`.
  - `experimentos/sampling_1/README.md:3-4`: agregar `h4`.
  - `informe.md:155-157`: agregar `bandas_H4.png`.
  - `guion.md:12`: "en VMs del mismo tipo", no "en la misma máquina".
  - `h3/informe/informe.md`: una línea que dice que el δ = 5,52 de `h3/docs/hipotesis.md` es de la ronda anterior y
    que la ronda vigente usa 5,65, como ya hace `h4`.
  - `h1/informe/informe.md:11` e `informe.md:23`: redactar H1 como predicción pre-registrada ("predecía que…").

  Verificar con `verificar_readme.py` y `verificar_informe_h3.py --informe`.
- [ ] 4.2 Primera respuesta al tutor (D17): `experimentos/sampling_1/docs/zulip/02_dialogo_h1_h4.md`, que sale de los
  informes vigentes y de las secciones de 1.1–1.3. Agustina la postea.

## 5. Corridas (VMs a pedido, las lanza Agustina)

- [ ] 5.1 Verificar el crédito y la cuota de vCPU. Lanzar `fase8_r0` … `fase8_r7` y `fase8_medicion` a la vez, o las
  mitades `_a` y `_b` si la cuota alcanza para 17 VMs. Al terminar, verificar que no queda ninguna VM encendida y anotar
  horas y costo en la bitácora.
- [ ] 5.2 `python -m comun.consolidar` y `--sanity`. Verificar:
  - 67 estudios nuevos y 2.560 finales nuevos, con 20 semillas en cada celda de variante y réplica;
  - 216 filas en `tiempos_hp_fijos.csv` y 4 por lista en `calibracion.csv`;
  - todo en `n2-highmem-8` con `codigo_sucio = False` y un solo commit.
- [ ] 5.3 Revisión en sesión limpia de las corridas con `docs/revision.md` § 4 y cierre en la bitácora.

## 6. Informes (sesión: Opus)

- [ ] 6.1 `python -m comun.reporte --todos` y `scripts/comparar_rondas.py`. Aplicar las reglas de 1.1 y 1.2 tal como
  quedaron escritas y anotar cada resultado en la bitácora del experimento que corresponde (`control`, `h1`–`h4`).
- [ ] 6.2 Informes por hipótesis, cada uno con sus variantes nuevas, sus veredictos con réplicas, sus limitaciones (el
  origen después de mirar 201910, los contrastes sin corrección) y los A nuevos con su rango:
  - `h1/informe/informe.md`: las cuatro tasas con réplicas; si `U0.5` cambia de veredicto o queda con A < 2, sale de
    "vale la pena";
  - `h2/informe/informe.md`: réplicas y `B0.05`;
  - `h3/informe/informe.md`: `H3-0.5`, y en las líneas 42-43, que esos A eran de la réplica 0 contra el T_C de la
    réplica 0, o reemplazarlos por la regla nueva;
  - `h4/informe/informe.md`: `H4O-*`, `H4P-*`, los cuatro contrastes principales y `H4P-0.1` contra `H4U-0.1`.

  Verificar con `verificar_informe_h3.py --informe` los que lo admiten.
- [ ] 6.3 Informe conjunto, `guion.md` y README raíz:
  - la tabla de cobertura y la de comparaciones directas, copiadas de `tabla_resultados.md`;
  - `informe.md:44`: la cantidad de variantes sale del bloque A, y H3 también reusa los estudios de U0.05;
  - los A nuevos y su rango, y la lista de "vale la pena" actualizada en todos los documentos;
  - un párrafo en § Diseño o § Limitaciones con lo medido: la misma CPU, el CV dentro de la máquina, el CV entre VMs, el
    rango por Optuna y la medición a hiperparámetros fijos;
  - en `informe.md:15`, matizar "sin cambiar la proporción de clases": H4 la cambia, y se dice dónde y cómo; una frase
    sobre el corte N* fijo en `H4F` y `H4O` (D17).

  Verificar con `verificar_readme.py`.
- [ ] 6.4 `docs/metodo.md` § Agregar una hipótesis y `docs/revision.md` § 2: la regla de D14.
- [ ] 6.5 Segunda respuesta al tutor (D17): `experimentos/sampling_1/docs/zulip/03_grilla_y_tiempos.md`, que sale de los
  documentos. Agustina la postea.
- [ ] 6.6 Revisión en sesión limpia del informe con `docs/revision.md` § 5, cierre en las bitácoras y
  `comun/tokens.py`.

## Workflow follow-up

- Archivar `final-con-julio-agosto` antes que este cambio: los dos modifican los mismos requisitos.
- Archivar con `/opsx:archive` cuando estén cerradas las cinco revisiones (1.5, 2.6, 3.8, 5.3 y 6.6).
