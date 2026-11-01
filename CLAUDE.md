# experimento-sampling — mapa y reglas

Repo de experimentos de DMEyF 2026: **una carpeta por experimento** en `experimentos/<nombre>/` (docs, src,
scripts, ledger, informe), lo compartido en `comun/`, `plantilla/` para empezar uno nuevo, `docs/` con el método y las
listas de revisión. El primero es `experimentos/sampling-velocidad/`, el experimento **Sampling_1** (comisión lunes): Agustina Razanov, Martín López, Luis María Laguinge; tutor
Joaquín I. Aramendía; tópico Zulip `Experimentos - Lunes > sampling_1`. Pregunta del tutor (1-nov): ¿vale la pena el
tradeoff entre velocidad y pérdida de performance? Sampling_2 hace undersampling de la clase mayoritaria; **nosotros
aislamos la velocidad sin tocar la proporción de clases**.

**Todo el plan está en `openspec/changes/experimento-sampling-velocidad/`** (proposal, specs, design, tasks). Leer
`design.md` antes que nada; `tasks.md` dice qué sigue y con qué modelo. Avanzar con `/opsx:apply
experimento-sampling-velocidad`. Cada experimento importa solo de `comun/` y de su carpeta; un cambio en `comun/` se anuncia en el
commit.

## Reglas de trabajo (son parte del experimento, se miden)

- **Una sesión por etapa** (hipótesis, diseño, código, corridas, análisis, informe, revisión). Al cerrar una etapa:
  anotar en la bitácora del experimento, correr `comun/tokens.py` cuando exista, `/clear`.
- **Modelo por etapa**: diseño, hipótesis y revisiones con Opus; código, tablas y tareas mecánicas con Sonnet. Fable solo
  si una decisión de diseño lo amerita.
- **Salidas largas a archivo, nunca al chat.** Leer con `head`, `tail` o un resumen. Subagentes solo para búsquedas.
- **Lo repetido va a scripts.** Las corridas las hace la VM, no una conversación.
- **Revisión en sesión limpia**: la lista de cada compuerta está en `docs/revision.md`; revisa una sesión nueva sin
  contexto (o un subagente `general-purpose`, que arranca vacío) o un integrante distinto.
- **Commitear sin pedir permiso**, en cualquier sesión (interactiva o headless), al cerrar una tarea o un grupo, con
  mensaje descriptivo y sin `Co-Authored-By` ni pie de Claude. El push y los tags de corridas los decide Agustina salvo
  que una tarea lo pida. Nada del dataset en el repo.

## Hechos que no están en el código

- Baseline oficial (Bolaños, 28-oct, Zulip 208135): solo 2019; train 201903–201906 completo; positivo BAJA+1 ∪ BAJA+2;
  lags y deltas 2; Optuna sobre `num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction`,
  `bagging_fraction` con `bagging_freq ≥ 1`, resto defaults; validación 201908 por AUC; test 201910 solo al final;
  201911–201912 no se usan. Entrega: video grupal (hipótesis, diseño, limitaciones, resultados, conclusiones).
- Dataset: `https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_02_crudo.csv.gz` (201901–202108).
  Datos fuera del repo, en `DATOS_DIR` (default `~/datos/experimentos-dmeyf`).
- Cómputo: VMs spot `n2-highmem-8` desde el template del curso, una por persona, borrar al terminar. Trial de Google
  Cloud de US$ 300 a 90 días; verificar fecha de alta y cuota de vCPU antes de la fase 1.
- Entorno: pyenv `facultad` (Python 3.14). En la Mac LightGBM necesita `brew install libomp`.
- Código reutilizable: `../competencia-2/src/fe_panel.py` (lags y deltas en DuckDB) y `competencia.py` (ganancia,
  curvas). Se copia lo necesario; no se importa ese repo.
- Archivo de Zulip: `../zulip/` (Postgres `zulip` en Docker; `PYENV_VERSION=zulip python main.py` lo actualiza).
- Línea de base de tokens (octubre 2026, sesiones en `dmeyf2026`): ~400.000 tokens de contexto por turno, 2.509
  turnos, ≈ US$ 694 a precio de API. Objetivo: < 100.000 por turno. La sesión de planificación de este repo fue la
  `08a28c05-6f60-44ea-af46-c4d51105c4b7` del proyecto `dmeyf2026` (1-nov); contarla como etapa `planificacion`.
