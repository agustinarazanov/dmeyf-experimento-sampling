# Listas de revisión por compuerta

Revisa una sesión nueva sin contexto (o un subagente `general-purpose`) o un integrante que no ejecutó la etapa. Hay que
marcar cada ítem como ✓, ✗ (con lo que falta) o n/a, y pegar el resultado en `docs/bitacora.md` del experimento. La
etapa no se cierra con un ✗ abierto.

Las listas son las mismas para todos los experimentos. Las rutas son relativas a la carpeta del experimento
(`experimentos/<nombre>/`).

## 1. Hipótesis (`docs/hipotesis.md`)

- [ ] La pregunta es la del tutor y está citada con id de Zulip.
- [ ] El control es el baseline de Bolaños sin cambios y está descrito completo (meses, target, FE, espacio de Optuna,
      validación, test).
- [ ] Cada hipótesis nombra **una sola** variable y sus valores.
- [ ] Cada hipótesis nombra **una sola** métrica que la decide.
- [ ] Cada predicción tiene un umbral numérico.
- [ ] Cada hipótesis dice qué resultado la confirma y qué resultado la refuta, sin zona gris sin nombre.
- [ ] Toda adaptación del baseline está declarada y justificada.
- [ ] Ninguna hipótesis toca la proporción de clases (eso es Sampling_2).
- [ ] La respuesta a "¿vale la pena?" tiene una regla escrita.
- [ ] Se puede decidir todo con 201910 sin haber usado 201910 para elegir nada.

## 2. Diseño (`docs/diseno.md`)

- [ ] La grilla está completa: método × tasa × semilla × etapa, con el total de corridas calculado.
- [ ] Cada variante de `hipotesis.md` aparece en la grilla y no hay variantes que no estén en `hipotesis.md`.
- [ ] El control está apareado por semilla con cada variante (mismas 10 semillas finales).
- [ ] Los trials de Optuna, la semilla de optimización y el espacio de búsqueda son iguales en todas las variantes, salvo
      la adaptación declarada de H2.
- [ ] Los tiempos se miden en un solo tipo de máquina y está nombrado.
- [ ] Las horas de VM y el costo están estimados y entran en el trial.
- [ ] El reparto por persona y por fase está escrito y no deja huecos ni solapes.
- [ ] La devolución del tutor, si llegó, está incorporada con id de Zulip.

## 3. Código (`src/`, `scripts/`)

- [ ] El smoke test con `--filas 20000` corre en la Mac para los cuatro métodos y escribe una fila cada uno.
- [ ] Determinismo: la misma configuración corrida dos veces da el mismo hash de muestra, el mismo AUC y la misma
      ganancia.
- [ ] La etapa `optimizar` no lee 201910 (se verifica en el log de meses leídos).
- [ ] La fila del ledger tiene todas las columnas obligatorias, y si falta una el corredor falla nombrándola.
- [ ] `codigo_sucio` vale verdadero si hay cambios sin commitear.
- [ ] Las filas de train registradas coinciden con r × filas totales, con un margen de ± 0,1%.
- [ ] `consolidar.py` aparea solo las semillas en común (probado con datos sintéticos).
- [ ] `vm.sh` deja la VM borrada al terminar.
- [ ] No hay datos del dataset en el repo.

## 4. Resultados (`ledger/`)

- [ ] Todas las filas finales son del mismo tipo de máquina y del mismo commit por fase.
- [ ] No hay `codigo_sucio` ni `etapa = exploracion` en `resultados.csv`.
- [ ] Las filas de train de cada corrida coinciden con su tasa.
- [ ] El control da AUC y ganancia que se repiten, dentro del ruido, en una segunda corrida independiente (otra persona si la hay; si no, otra VM, y queda anotado como limitación).
- [ ] En las variantes de H2, `bagging_fraction` quedó fijo y no optimizado.
- [ ] Cada variante tiene sus 10 semillas, y si no, está anotado por qué.
- [ ] `apareado.csv` tiene media, desvío, IC 95% y semillas ganadas para cada variante contra su referencia.
- [ ] Las VMs están borradas y el gasto quedó anotado.

## 5. Informe (`informe/`)

- [ ] Cada hipótesis se decide con la regla escrita en `hipotesis.md`, sin reglas nuevas.
- [ ] Cada afirmación cita una fila de `apareado.csv` o una figura de `informe/figuras/`.
- [ ] Las refutaciones y los empates se informan con el mismo peso que las confirmaciones.
- [ ] Las limitaciones incluyen semillas, un solo mes de test y la adaptación de H2.
- [ ] El guion entra en 10 minutos y sigue la estructura de Bolaños: hipótesis, diseño, limitaciones, resultados y
      conclusiones.
- [ ] El guion no explica el baseline.
- [ ] La bibliografía está lista para postear en Zulip.
