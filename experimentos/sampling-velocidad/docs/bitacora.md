# Bitácora — Sampling_1

Una entrada por sesión de Claude Code y una por cada cierre de etapa, de la más vieja a la más nueva. La etapa que se
declara acá es la que usa `comun/tokens.py` para clasificar la sesión.

## Formato de cierre de etapa

```
### AAAA-MM-DD — cierre <etapa>
- Sesión: <id de sesión de Claude Code> · modelo: <Opus | Sonnet>
- Revisor: <sesión limpia / subagente general-purpose / integrante>
- Lista: docs/revision.md § <n>; ítems ✓ <k>/<total>
- Hallazgos: <qué encontró la revisión>
- Corregido: <qué se cambió por la revisión>
- Tokens: <turnos> turnos · contexto promedio <n> por turno · ≈ US$ <x> (objetivo < 100.000 por turno)
- Tutor: <id de Zulip y resumen, si hubo devolución>
```

## Entradas

### 2026-11-01 — planificación (sesión previa)
- Sesión: `08a28c05-6f60-44ea-af46-c4d51105c4b7`, que corrió en el proyecto `dmeyf2026` y no en este repo. Se cuenta
  como etapa `planificacion`.
- Produjo `openspec/changes/experimento-sampling-velocidad/` (proposal, specs, design, tasks) y `CLAUDE.md`.

### 2026-11-01 — apertura: etapa hipótesis
- Sesión: `d2e5b603-2b55-42d4-9898-ef129dce5e4b` · modelo: Opus · etapa: **hipotesis**.
- Tareas 1.1 a 1.5 de `tasks.md`: `docs/hipotesis.md`, `docs/revision.md`, esta bitácora y el borrador del post a
  Zulip (`docs/zulip/01_hipotesis.md`).
- Pregunta del tutor tomada de Zulip 208986 (Joaquín Aramendía, 1-nov, `Experimentos - Lunes > sampling_1`).

### 2026-11-01 — cierre hipótesis
- Sesión: `d2e5b603-2b55-42d4-9898-ef129dce5e4b` · modelo: Opus
- Revisor: dos subagentes `general-purpose`, sin contexto, en pasadas sucesivas.
- Lista: docs/revision.md § 1. Primera pasada ✓ 3/10. Segunda pasada ✓ 10/10.
- Hallazgos de la primera pasada:
  - faltaban en el control los rangos de Optuna, las 100 iteraciones y el uso de las semillas;
  - H2 no aislaba una sola variable;
  - H2 y H3 se decidían con dos métricas;
  - había zonas grises entre confirma y refuta;
  - la regla de "un σ_C" era casi trivial con 10 semillas;
  - **el corte de envíos se elegía en 201910**;
  - T se definía distinto según la hipótesis;
  - la condición de tiempo de H2 caía fuera de la grilla.
- Corregido, con decisiones del equipo:
  - no inferioridad con δ = 2% de Ḡ_C (cota inferior del IC ≥ −δ) y un veredicto *indeterminado* con nombre;
  - corte N* elegido en 201908;
  - H2 decidida contra el control, la comparación con `uniforme` como descriptiva y `goss` como brazo descriptivo;
  - T como pipeline completo en todos los brazos;
  - rangos de Optuna propios;
  - D1 y D2 de `design.md` actualizados para coincidir.
  
  Las observaciones menores de la segunda pasada (frontera monótona, muestra de Optuna en H1, origen de δ, arranque de
  GOSS) se aplicaron. Informes: `revision_hipotesis.md` y `revision_hipotesis_2.md` en el scratchpad de la sesión, no
  versionados.
- Tokens: 26 turnos hasta la segunda revisión · contexto promedio 87.648 por turno (máximo 108.724) · 28.831 de salida.
  El objetivo de < 100.000 se cumple. El costo en US$ queda para `comun/tokens.py` (tarea 4.7).
- Tutor: el post `docs/zulip/01_hipotesis.md` está listo y sin enviar, con la consulta sobre la adaptación de H2.
- Pendientes que llegaron del grupo al cierre:
  - Una propuesta de quedarse con el 20% de CONTINUA y el 100% de las BAJA con selección de instancias, y otra con el
    10% de CONTINUA y pesos. Es territorio de Sampling_2. La variante con peso de 10× conserva la proporción efectiva
    en la pérdida y podría ser H4. Hay que decidir si se coordina con Sampling_2 o si se reabre la compuerta.
  - ¿El pipeline de 15 minutos corre todo en GCP, o entrena en GCP y predice en la laptop? Es una decisión de la
    segunda entrega; quedó como limitación en `hipotesis.md`.

### 2026-11-01 — apertura: etapa diseño
- Sesión: `a5afcd58-12ea-4332-9ab8-49822bca2e03` · modelo: Opus · etapa: **diseno**.
- Tarea 2.1: `docs/diseno.md` con 11 brazos, 9 estudios de Optuna (H3 comparte los suyos con `U0.25` y `U0.1`), 110
  finales más 10 de réplica del control, ≈ 6 h de VM (≈ 15 h en el peor caso, ≈ US$ 9) y el reparto por persona.
  D7 de `design.md` se actualizó para que coincida.
- Revisión preliminar con la lista § 2, a cargo de un subagente `general-purpose` sin contexto: ✓ 7/8, con el ítem de
  la devolución del tutor en n/a. No encontró errores aritméticos.
- Corregido por la revisión:
  - **parámetros de ejecución** (`deterministic`, `force_col_wise`, `feature_pre_filter`): declarados como adaptación
    en `hipotesis.md` § Control;
  - **T**: suma de las duraciones de los trials más un `Dataset`, para que no dependa de cortes de la VM spot. Se
    llevó también a `hipotesis.md`;
  - **plataforma de CPU**: fija con `--min-cpu-platform`, y el modelo de CPU queda en el ledger;
  - **reparto**: los finales de `U0.25` y `U0.1` pasan a la VM que corre sus estudios;
  - **g.l.**: n − 1 cuando faltan semillas;
  - **limitaciones nuevas**: estudios compartidos entre H1 y H3, y GOSS cuando `learning_rate` es chico;
  - **paralelo**: Martín no espera la calibración.
- Pendiente para cerrar la etapa: 2.2 (consola GCP: trial, cuota, template, zona, plataforma de CPU, precio spot) y
  2.3 (repo en GitHub). `README.md` y `.gitignore` ya están escritos, sin publicar.

### 2026-11-01 — reorganización del repo (layout D0)
- Sesión: `a5afcd58-12ea-4332-9ab8-49822bca2e03` · modelo: Opus · etapa: **diseno**.
- Pedido de la sesión de planificación (`dmeyf2026`), confirmado por Agustina. El repo tiene ahora una carpeta por
  experimento: `comun/`, `experimentos/sampling-velocidad/`, `plantilla/` y `docs/` en la raíz. La decisión es D0 de
  `design.md`.
- Se movieron `hipotesis.md`, `diseno.md`, esta bitácora y `zulip/` a `experimentos/sampling-velocidad/docs/`.
  `docs/revision.md` queda en la raíz, compartido, y se creó `docs/metodo.md`.
- `tasks.md`: las rutas quedaron alineadas con D0 y se agregó la tarea 2.0. Las tareas 1.x y 2.1 conservan su contenido;
  solo cambió dónde viven. `scripts/tokens.py` pasa a ser `comun/tokens.py`.

### 2026-11-01 — tareas 2.2 y 2.3
- **2.2, GCP**: no hay un template `n2-highmem-8`. La VM se crea desde `to-064ram-08vcpu`, sobrescribiendo la máquina
  con `n2-highmem-8` y fijando `--min-cpu-platform="Intel Ice Lake"`, en `northamerica-northeast2-b`.
  - Prueba: `prueba-sampling-n2` se creó con Ice Lake y spot, y se borró junto con su disco (19:19 a 19:21).
  - Cuotas: `CPUS_ALL_REGIONS` 32 y `N2_CPUS` 100 en la región.
  - Trial: alta el 11-oct, confirmada por Agustina; vence el 9-ene-2027.
  - Detalle en `docs/diseno.md` § Máquina.
- **2.3, repo**: es privado, en `agustinarazanov/dmeyf-experimento-sampling`. El prefijo `dmeyf` lo pidió Agustina para
  los repos de la materia; el nombre no admite `/`. Por decisión de Agustina, no se mandaron invitaciones a Martín y
  Luis. El README no menciona el dataset y `.gitignore` excluye los datos.

### 2026-11-01 — cierre diseño
- Sesión: `a5afcd58-12ea-4332-9ab8-49822bca2e03` · modelo: Opus
- Revisor: subagente `general-purpose` sin contexto. Pasó dos veces: la preliminar (ver la apertura) y esta final.
- Lista: docs/revision.md § 2. Pasada final ✓ 7/7 aplicables; el ítem del tutor es n/a. Al recalcular, coincidieron
  todos los números.
- Hallazgos de la pasada final:
  - **bloqueante**: la réplica del control chocaba con la regla de saltear las corridas que ya tienen fila;
  - **bloqueante**: el template borra la VM spot con su disco, y el SQLite de Optuna no funciona sobre gcsfuse;
  - **menores**: el proyecto del template y de las cuotas no estaba nombrado; faltaba la verificación de Ice Lake en
    las zonas `-a` y `-c`; quedaban pendientes de Martín y Luis sin listar; la bitácora decía US$ 8 y el diseño US$ 9.
- Corregido:
  - la réplica pasa a ser un brazo propio, `C-rep`;
  - el SQLite es local y se copia al bucket después de cada trial; el panel y las filas del ledger también se suben,
    y una VM nueva los baja;
  - quedaron nombrados el proyecto y las zonas, con la lista de pendientes de Martín y Luis antes de la fase 1;
  - US$ 9 en los dos documentos.
  - La carga más baja de Luis queda como margen para reintentos.
- Tokens: 61 turnos · contexto promedio 125.991 por turno (máximo 165.868) · 59.180 de salida. **No se cumple el
  objetivo** de < 100.000. Pesaron la reorganización del repo a mitad de etapa, que reabrió `tasks.md` con
  `/opsx:update`, y la configuración de `gcloud` y `gh` en la misma sesión. El costo en US$ queda para
  `comun/tokens.py` (tarea 4.7).
- Tutor: sin devolución. El post `zulip/01_hipotesis.md` sigue sin enviar.

### 2026-11-01 — apertura: etapa código
- Sesión: `457cc09a-a528-48c5-849e-322b3261b914` · modelo: Sonnet · etapa: **codigo**.
- Tareas 3.1 a 4.7 de `tasks.md`: `comun/` (datos, baseline, ganancia, ledger, tokens), `src/` (muestreo, métodos,
  correr, consolidar), `scripts/` (vm.sh, graficar.py) y `docs/operacion.md`.
