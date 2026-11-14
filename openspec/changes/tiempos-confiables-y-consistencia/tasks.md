# Tasks

Requiere la ronda 201903–201908 consolidada (`final-con-julio-agosto`, archivado el 13-nov). `Experimentos guion.md`, en
la raíz, queda fuera. Los números de línea y las rutas de informes que citan las tareas son los de hoy: las frases se
buscan por su texto.

Dónde se trabaja (design § Restricciones):
- **Grupos 1, 2 y 5: en la rama `tiempos-confiables`**, en un worktree aparte, mientras `sitio-legible` se aplica en
  `main`.
- **Grupos 3, 4 y 6: en `main`, después de la unión** (grupo 2b).

Qué puede ir en paralelo:
- Dentro de la rama, después de 2.1: 2.2 a 2.7.
- En el grupo 5: cuatro carriles de VMs a la vez.
- Después de la unión: el grupo 3 y 4.1; y en el grupo 6, los informes de `h1`, `h2`, `h3` y `h4` (6.2), cada uno en su
  sesión.

## 1. Predicciones y diseño (sesión: Opus)

- [x] 1.1 `control/docs/hipotesis.md` § Medición de tiempos (13-nov):
  - la regla nueva de A y de su intervalo (D1, D2), con el motivo: la regla vieja usaba dos referencias de T_C. El texto
    viejo de § Métricas y reglas comunes no se reescribe;
  - la definición de A_fijo(r), del cociente entre recetas y del CV entre repeticiones, qué se cronometra, y la
    predicción y la regla de D5;
  - la calibración por máquina y sus dos anclas, con la predicción y la regla de D6, y que cada ancla es una sola
    medición;
  - el CV entre semillas dentro de una VM, con el comando que lo da del ledger de la ronda;
  - que la medición y la calibración son exploratorias y no cambian veredictos.

  Las predicciones las confirma o ajusta Agustina.
- [x] 1.2 Predicciones de la grilla (D13), cada una en una sección nueva con fecha, escrita antes de cualquier corrida y
  con la declaración de que la variante se agrega después de ver 201910:
  - `h1/docs/hipotesis.md` § Réplicas de H1;
  - `h2/docs/hipotesis.md` § Réplicas de H2 y `B0.05`;
  - `h3/docs/hipotesis.md` § `H3-0.5`;
  - `h4/docs/hipotesis.md` § Grilla común: `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, las cuatro `H4P`, los pares de D12 con lo
    que aísla cada uno y lo que no (filas y peso), y los cuatro contrastes principales. § Comparaciones múltiples suma
    los 17 contrastes, los 9 veredictos nuevos y los 8 que se vuelven a decidir.

  Las predicciones las confirma o ajusta Agustina.
- [x] 1.3 Diseño:
  - `h1`–`h4/docs/diseno.md`: variantes, estudios y grilla nuevos de cada una, y `## Dependencias` después del cambio de
    dueño de `U{r}@k` (D10): `h3` lee todos los `U{r}` de `h1`, y `h4` deja de declarar `h3`;
  - `sampling_1/docs/diseno.md`: la fase 8 (D15) con listas, carriles, horas y costo, y la tabla de la grilla común
    (D8);
  - `sampling_1/docs/hipotesis.md` § Pregunta: la grilla común y los pares directos (D12).
- [x] 1.4 Anotar en la bitácora de `sampling_1` el mensaje del tutor (Zulip 212124, 12-nov), la revisión del 13-nov que
  originó este cambio, la ampliación a la grilla común y las dos revisiones en sesión limpia de la propuesta (13-nov,
  incorporadas).
- [x] 1.5 Revisión en sesión limpia de 1.1–1.4 con `docs/revision.md` § 1 y § 2, y cierre en la bitácora. Ninguna
  corrida antes de este cierre.

## 2. Código de corridas (sesión: Sonnet)

- [x] 2.1 Dueño de `U{r}@k` (D10), en un commit propio y sin ninguna VM viva en el proyecto:
  - guardar antes las tablas de `python -m comun.consolidar` de `h1`, `h3` y `h4` y de `python -m comun.reporte` de
    `h3`, `h4` y `sampling_1`;
  - `comun/variantes.py`: `dueno_estudio`, `dueno_variante` e `implicitas` sin el caso especial de `h3`;
  - `comun/reporte.py`: `cargar_replicas` lee los estudios del dueño de cada estudio;
  - `tests/test_variantes.py` y `tests/test_replicas.py`: el dueño nuevo;
  - `## Dependencias` de `h3/docs/diseno.md` y `h4/docs/diseno.md`;
  - un script que mueve de `h3/ledger` a `h1/ledger` los 21 estudios `U0.25@k`, `U0.1@k` y `U0.05@k` (hp, `corridas/` y
    `estudios.csv`), sin cambiar ids ni contenido, en el repo y en el bucket, con `--en-seco` y `--deshacer`. No mueve
    `exploracion/`;
  - correrlo en el repo y verificar el invariante contra las tablas guardadas: las únicas diferencias son las dos
    esperadas de D10 (`h1` gana 21 filas de optimización; el reporte de `h4` pasa a mostrar T y A con réplicas en
    `H4F-*`). Anotarlas en la bitácora con los valores de antes y de después;
  - correrlo en el bucket con los cinco pasos de D10, primero con `--en-seco`. El listado de lo movido va a la
    bitácora;
  - `python -m comun.variantes --verificar` y `pytest`.
- [x] 2.2 Variantes y métodos (D8, D9, D12):
  - `comun/metodos.py` y `comun/correr.py`: `fast-retrain-opt` con la fracción igual a la tasa de la variante y peso
    1/f, separado de `fast-retrain`, que sigue en 0,5; `pesos` recibe la tasa; `validar` acepta las cuatro tasas; el
    método nuevo `clase-peso` de `H4P`, que optimiza como `fast-retrain-opt` (y no como `uniforme`) y entrena el final
    como `opt-muestra`;
  - `comun/variantes.py`: `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, `H4P-0.5`, `H4P-0.25`, `H4P-0.1`, `H4P-0.05` y
    `B0.05`; estudios `F0.25`, `F0.1`, `F0.05` y `B0.05`; `replicas=True` en `U*`, `B*` y `GOSS`; los pares de D12 con la
    decisión que aísla cada uno y cuáles son principales; la fila de la grilla de cada variante y la lista de celdas que
    no se corren, con su motivo (D11);
  - tests: la réplica 0 de lo que ya existe no cambia (mismo `hash_muestra` e hiperparámetros con `--filas 20000`, en
    `H4O-0.5`, `H4F-0.05` y `H4U-0.1`); `H4O-0.1` y `H4P-0.1` comparten el estudio `F0.1`; una línea `clase-peso 0.1 0
    optimizar` corre `F0.1` y no `U0.1`; la muestra de `H4O-{f}` tiene todas las bajas y round(f · CONTINUA); la muestra
    de búsqueda de `H4P-0.1` es la de `H4U-0.1`.

  Smoke test local con `--filas 20000` de una variante nueva de cada fila, en `optimizar` y `final`.
  `python -m comun.variantes --verificar`.
- [x] 2.3 Pares entre experimentos (D12): `python -m comun.consolidar` sin `--experimento` arma al final
  `experimentos/sampling_1/ledger/pares.csv` desde los `resultados.csv` de todos los dueños, y `--experimento sampling_1`
  lo arma solo. Usa la cuenta de `ledger.replicas` y guarda las filas de entrenamiento de cada lado. Una réplica entra
  solo si tiene las 20 semillas en los dos lados.
  Tests: un par declarado al que le falta un lado sale como pendiente, con el nombre de la variante que falta; un par
  declarado que no aparece hace fallar el test; los pares de un solo experimento dan lo mismo que en su `replicas.csv`;
  una réplica incompleta no entra y el par dice cuántas usó.
- [x] 2.4 `experimentos/sampling_1/scripts/tiempos_hp_fijos.py` (D4, D6):
  - importa solo de `comun/`;
  - las dos recetas (al azar y bajas con peso), orden aleatorizado con semilla fija;
  - cronometra por separado el `Dataset`, el entrenamiento y la predicción; el tiempo de la medición es entrenamiento
    más predicción, igual que la duración de un trial de Optuna;
  - un archivo por medición en `experimentos/sampling_1/ledger/tiempos/hp_fijos/`, con filas, instancia y versiones de
    LightGBM, numpy y Optuna; al relanzar saltea las mediciones que ya tienen archivo;
  - `--anclas`: en la VM, lee de los `.db` de `C` y `C@1…7` la duración del mejor trial y la deja en
    `tiempos/anclas_trials.csv`;
  - `--calibracion <lista> <momento>`: el trial de calibración (misma semilla que el original) y el final viejo
    (cronometrado como un final del corredor), en
    `experimentos/sampling_1/ledger/tiempos/calibracion_<lista>_<momento>.csv`, sin escribir en el ledger de `control`;
  - `--consolidar`: arma `tiempos_hp_fijos.csv` y `calibracion.csv`, y suma las anclas (`anclas_trials.csv`, y el tiempo
    del final viejo en el ledger de la fase 7 y en `C-rep`);
  - se niega a correr fuera de `n2-highmem-8` salvo con `--prueba`.

  Smoke test local con `--prueba`, 1 juego de hiperparámetros, 2 tasas, 1 repetición y datos reducidos. Los archivos de
  prueba no se commitean.
- [x] 2.5 `scripts/vm.sh` y versiones:
  - corre la calibración antes y después de la lista, y sube al bucket una vez más después de la calibración del final;
  - `requirements.txt` con las versiones exactas que instala una VM de prueba;
  - `scripts/lanzar_carriles.sh`: reparte listas en carriles y lanza las de cada carril una tras otra, con `--en-seco`.

  Verificar con `--en-seco` que la carpeta `tiempos/` sube al bucket y vuelve a la Mac, y que dos listas no escriben el
  mismo archivo.
- [x] 2.6 Listas de la fase 8 en `experimentos/sampling_1/scripts/` (D15): `fase8_r0_a` … `fase8_r7_a` (h1, h3 y h4),
  `fase8_r0_b` … `fase8_r7_b` (h2) y `fase8_medicion`, con las líneas `@ experimentos.sampling_1.scripts.tiempos_hp_fijos`
  de la medición y de las anclas.
  En cada lista, los estudios van antes que sus finales, y ninguna `_a` lee un estudio de una `_b`.
  `scripts/lanzar_fase.sh --en-seco` de todas: 67 estudios y 2.560 finales en total, y ninguna corrida repetida.
- [x] 2.7 `comun/consolidar.py --sanity`: un chequeo de la fase 8, leído del registro: 8 réplicas por 20 semillas en
  cada variante del bloque A, y ningún estudio con dueño `h1` en `h3/ledger/corridas`.
- [x] 2.8 Revisión en sesión limpia de 2.1–2.7 con `docs/revision.md` § 3. Commit que anuncia el cambio en `comun/`.

## 2b. Unión con `main` (después del grupo 5 y de que `sitio-legible` esté archivado)

- [ ] 2b.1 Unir `main` en la rama `tiempos-confiables` y resolver los conflictos esperados (design § Restricciones):
  `comun/variantes.py`, `tests/test_variantes.py`, `cargar_replicas` y las secciones nuevas de hipótesis y diseño, que
  pasan al README de cada experimento con su fecha original.
- [ ] 2b.2 `pytest`, `python -m comun.variantes --verificar`, `python -m comun.consolidar --sanity` y el verificador de
  enlaces del sitio sobre la unión. Unir la rama a `main`.
- [ ] 2b.3 Actualizar con `/opsx:update` las rutas de los grupos 3, 4 y 6 de este cambio a la estructura que dejó
  `sitio-legible`, y los deltas de `reporte-visual` y `dependencias-entre-experimentos` contra las specs ya archivadas
  de aquel. Revisión corta del resultado en sesión limpia.

## 3. Código del reporte (sesión: Sonnet)

- [ ] 3.1 `comun/reporte.py`, A con una sola referencia (D1):
  - la mediana de T_C se calcula una vez, sobre todas las réplicas del control, y se usa en todas las filas del bloque A;
  - la nota `AVISO_A` actualizada, que también dice que el tiempo igual de la réplica 0 sigue con T_C de la réplica 0
    (D3).

  Test en `pytest`: A × T(variante) es igual para todas las filas, también con una variante de réplicas incompletas.
- [ ] 3.2 `comun/reporte.py`, intervalo de A (D2):
  - bootstrap por percentiles del cociente de medianas, con semilla fija;
  - una columna nueva al final de la tabla de `tabla_resultados.md`;
  - en el HTML, debajo de A, en letra chica;
  - en el gráfico de tradeoff, como barra horizontal sobre A;
  - en las filas sin réplicas, la nota de que el intervalo solo mueve el control; en la del control, `—`;
  - la nota del bloque: qué mide, que una réplica rara lo mueve, y por qué el tiempo igual sigue apareado por k.

  Tests para una variante con réplicas y otra sin, y de que el intervalo no cambia al reordenar las réplicas.
- [ ] 3.3 Regenerar la tabla de resultados solo con las corridas anteriores a la fase 8 (una copia del ledger sin las
  filas nuevas) y verificar el escenario "Tabla de resultados intacta": solo cambian A y su intervalo. Guardar el diff
  en la bitácora.
- [ ] 3.4 `scripts/comparar_rondas.py`: sacar la fila del control y agregar la nota sobre las variantes que solo existen
  en la ronda nueva (D16).
- [ ] 3.5 `comun/reporte.py`, tabla de cobertura (D11), leída del registro que deja 2.2: en el reporte de `sampling_1` y
  en `tabla_resultados.md`. Test con un registro de juguete que tiene una celda sin correr.
- [ ] 3.6 `comun/reporte.py`, comparaciones directas (D12): la tabla "Diferencias entre variantes" lee los pares de
  `replicas.csv` y de `sampling_1/ledger/pares.csv`, suma las columnas de qué aísla cada par y de filas de cada lado, y
  marca los principales. Un par cuya variante todavía no tiene corridas sale como pendiente.
- [ ] 3.7 `comun/reporte.py`, sección de tiempos del informe conjunto (D4, D6, D7):
  - por r: A_fijo con su mediana y su rango entre juegos de hiperparámetros, al lado del A del bloque A de `U{r}` y de
    `H4O-{r}`; el cociente entre recetas con las filas de cada una; el CV entre repeticiones;
  - calibración: CV entre VMs, cociente fin/inicio por VM y cociente contra las dos anclas;
  - por variante: mediana de búsqueda, mediana de final, fracción de T que es búsqueda y mediana de preparación, con la
    nota de que la preparación no entra en T.

  Si un CSV no existe, su parte sale como pendiente.
- [ ] 3.8 Revisión en sesión limpia de 3.1–3.7 con `docs/revision.md` § 3. Commit que anuncia el cambio en `comun/`.

## 4. Texto que no espera a las corridas (sesión: Opus)

- [ ] 4.1 Correcciones de texto que no citan números nuevos (D16):
  - `h4/informe/informe.md` e informe conjunto, donde dicen que los dos IC quedan enteros debajo de −δ: solo el de
    `H4H-0.1`; `H4U-0.1` pierde por la media.
  - `sampling_1/informe/decisiones.md`: aviso de que es de las fases 1–4. El informe conjunto deja de enlazarlo para los
    números (hoy lo enlaza en dos lugares).
  - `guion.md` e informe conjunto, donde dan el rango de varianza entre réplicas: sale de la tabla de varianza (hoy, del
    17 al 58 %).
  - Informe conjunto, la frase de ΔAUC contra Δ de ganancia: se limita a las variantes en que se cumple, como en el
    informe de `h3`.
  - `experimentos/sampling_1/README.md`: agregar `h4`.
  - Informe conjunto, lista de figuras: agregar `bandas_H4.png`.
  - `guion.md`, bloque Diseño: "en VMs del mismo tipo", no "en la misma máquina".
  - `h3/informe/informe.md`: una línea que dice que el δ = 5,52 de `h3/docs/hipotesis.md` es de la ronda anterior y
    que la ronda vigente usa 5,65, como ya hace `h4`.
  - `h1/informe/informe.md` § Hipótesis y la hipótesis H1 en el informe conjunto: redactarla como predicción
    pre-registrada ("predecía que…").

  Verificar con `verificar_readme.py` y `verificar_informe_h3.py --informe`.
- [ ] 4.2 Informe conjunto, sección «Diálogo entre H1 y H4» (D17), con lo que ya se sabe: sale de los informes
  vigentes y de las secciones de 1.1–1.3. No afirma un contraste directo entre H1 y H4: da los dos Δ contra el control y
  dice qué se corrió. Va en voz impersonal y cita la pregunta por su id (Zulip 212124). No se escribe ningún borrador
  de mensaje.

## 5. Corridas (VMs a pedido, las lanza Agustina)

- [x] 5.1 Antes de lanzar:
  - los estudios `U{r}@k` están en `h1` en el repo y en el bucket (2.1), y el commit de la rama que va a correr tiene su
    tag (el push y el tag los decide Agustina);
  - verificar el crédito, la cuota (`CPUS_ALL_REGIONS` = 32) y que no hay ninguna otra VM encendida en el proyecto;
  - `scripts/lanzar_carriles.sh --en-seco` con las 17 listas en cuatro carriles.
- [x] 5.2 Lanzar los cuatro carriles desde el worktree de la rama (D15): en cada uno, primero `fase8_medicion` y las
  `_a`, después las `_b`. Al terminar, verificar que no queda ninguna VM encendida. Anotar en la bitácora qué lista
  corrió a qué hora, los relanzamientos, las horas y el costo. Toda la fase con un solo commit; si hay que corregir algo
  en el medio, se anota y las listas que faltan se relanzan con el commit nuevo.
- [x] 5.3 `python -m comun.consolidar`, `--sanity` y `tiempos_hp_fijos.py --consolidar`. Verificar:
  - 67 estudios nuevos y 2.560 finales nuevos, con 20 semillas en cada celda de variante y réplica;
  - 216 filas en `tiempos_hp_fijos.csv` y, en `calibracion.csv`, las de inicio y de fin de las 17 listas;
  - las filas nuevas de la fase 8, todas en `n2-highmem-8`, con `codigo_sucio = False` y un solo commit;
  - ningún estudio `U{r}@k` volvió a `h3/ledger`;
  - `sampling_1/ledger/pares.csv` tiene los 17 pares, ninguno pendiente.
- [ ] 5.4 Revisión en sesión limpia de las corridas con `docs/revision.md` § 4 y cierre en la bitácora.

## 6. Informes (sesión: Opus)

- [ ] 6.1 `python -m comun.reporte --todos` y `scripts/comparar_rondas.py`. Aplicar las reglas de 1.1 y 1.2 tal como
  quedaron escritas y anotar cada resultado en la bitácora del experimento que corresponde (`control`, `h1`–`h4`).
- [ ] 6.2 Informes por hipótesis, cada uno con sus variantes nuevas, sus veredictos con réplicas, sus limitaciones (el
  origen después de mirar 201910, los contrastes sin corrección, y en `h4` que los pares con bajas mezclan filas,
  cantidad y peso) y los A nuevos con su intervalo:
  - `h1/informe/informe.md`: las cuatro tasas con réplicas; si `U0.5` cambia de veredicto o queda con A < 2, sale de
    "vale la pena";
  - `h2/informe/informe.md`: réplicas y `B0.05`;
  - `h3/informe/informe.md`: `H3-0.5`, y donde cita A de la réplica 0, decir que eran contra el T_C de la réplica 0 o
    reemplazarlos por la regla nueva;
  - `h4/informe/informe.md`: `H4O-*`, `H4P-*`, los cuatro contrastes principales y `H4P-0.1` contra `H4U-0.1`.

  Verificar con `verificar_informe_h3.py --informe` los que lo admiten.
- [ ] 6.3 Informe conjunto, `guion.md` y README raíz:
  - la tabla de cobertura y la de comparaciones directas, copiadas de `tabla_resultados.md`;
  - la cantidad de variantes sale del bloque A, y H3 también reusa los estudios de U0.05;
  - la frase que dice que `U*`, `B*` y `GOSS` no tienen réplicas deja de ser cierta: se reescribe;
  - los A nuevos y su intervalo, y la lista de "vale la pena" actualizada en todos los documentos;
  - un párrafo en § Diseño o § Limitaciones con lo medido: la misma CPU, el CV dentro de la máquina, el CV entre VMs con
    la hora mezclada, las anclas con las fases anteriores, el intervalo de A (Optuna y VM), la medición a
    hiperparámetros fijos y que T no incluye la preparación;
  - donde dice "sin cambiar la proporción de clases": H4 la cambia, y se dice dónde y cómo; una frase sobre el corte N*
    fijo en `H4F` y `H4O`, y otra sobre por qué H2 no entra en los pares (D17).

  Verificar con `verificar_readme.py`.
- [ ] 6.4 `docs/metodo.md` § Agregar una hipótesis y `docs/revision.md` § 2: la regla de D14.
- [ ] 6.5 Informe conjunto, sección «Diálogo entre H1 y H4» (D17), actualizada con la tabla de cobertura, los cuatro
  contrastes principales con las filas de cada lado y la sección de tiempos. No se escribe ningún borrador de mensaje.
- [ ] 6.6 Revisión en sesión limpia del informe con `docs/revision.md` § 5, cierre en las bitácoras y
  `comun/tokens.py`.

## Workflow follow-up

- `sitio-legible` se archiva antes que este cambio: los dos modifican "Comparación limpia en dos bloques".
- Archivar con `/opsx:archive` cuando estén cerradas las cinco revisiones (1.5, 2.8, 3.8, 5.4 y 6.6). Borrar entonces el
  respaldo del bucket (`$BUCKET/respaldo/2026-11-mover-U/`).
