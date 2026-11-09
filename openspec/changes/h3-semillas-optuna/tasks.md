# Tasks

Requiere `renombrar-brazos` archivado.

## 1. Hipótesis y diseño (sesión: Opus)

- [x] 1.1 Escribir en `h3/docs/hipotesis.md` las predicciones y reglas de D4, citando δ = 5,52 M$ y N\* = 3.300 como fijos y R = 8 como cerrado, y en `h3/docs/diseno.md` las variantes `H3-0.05` y `H3R-0.1`, la grilla de D3, la regla de dueños de `U{r}@k` y `## Dependencias` actualizada; verificar con un grep que cada regla tiene umbral numérico y métrica
- [x] 1.2 Anotar en `control/docs/diseno.md` y en su bitácora las réplicas `C@1…7` (qué cambia: nada de lo ya corrido); actualizar `sampling_1/docs/diseno.md` § Reparto y fases con la ejecución de D3 (todo lo corre Agustina, una VM por réplica); verificar que los enlaces existen
- [x] 1.3 Revisión en sesión limpia de la etapa hipótesis y diseño con la lista de `docs/revision.md`, cierre en `h3/docs/bitacora.md`. Ninguna corrida real antes de este cierre

## 2. Código (sesión: Sonnet)

- [x] 2.1 `comun/baseline.py` y `comun/correr.py`: `--replica k`, con semillas TPE y de muestra = k, el estudio `<estudio>@k` y el `id` con `@k` solo si k ≥ 1 (D1, D2); verificar con el smoke de la Mac (`--filas 20000`) que la réplica 0 de `C` y de `U0.1` da los mismos hp y `hash_muestra` que en `main`, y que `--replica 3` de `H3-0.1` escribe en `h3/ledger/hp/U0.1@3.json` sin tocar `h1/`
- [x] 2.2 `comun/variantes.py` y `comun/metodos.py`: variantes `H3-0.05` y `H3R-0.1` (reescalado × √(1/r) recortado a [1; 8000]), marca de qué variantes admiten réplicas y la regla de dueños de `@k`; tests de la regla, del reescalado y de una réplica no habilitada (falla nombrándola); verificar que `pytest` y `python -m comun.variantes --verificar` pasan
- [x] 2.3 `comun/ledger.py` y `comun/consolidar.py`: columna `replica_opt` (ausente = 0), clave con réplica y `ledger/replicas.csv` con Δ con réplicas, IC de Welch, n de réplicas y semillas, y descomposición de varianza (D5); tests con un ledger sintético de 3 réplicas (suma de cuadrados exacta, réplicas incompletas, variante de una réplica sin fila); verificar que consolidar el ledger real da los mismos `apareado.csv` que antes
- [x] 2.4 Diferencia apareada `H3R-0.1` − `H3-0.1` por réplica y semilla (D4, D5) en `h3/ledger/replicas.csv`; test con datos sintéticos
- [x] 2.5 Listas `sampling_1/scripts/fase5_r<k>.txt` (k = 1…7) y `fase5_r0.txt` según D3, y un `scripts/lanzar_fase.sh` que lanza varias listas en VMs paralelas tras verificar la cuota de vCPU N2; verificar con `--en-seco` que cada lista imprime sus corridas y destinos y que la suma cubre las 37 celdas y los 28 estudios nuevos sin repetir
- [x] 2.6 Revisión en sesión limpia del grupo 2 con la lista de código de `docs/revision.md`, cierre en la bitácora; crear el tag `corridas-v2` (lo pushea Agustina)

## 3. Corridas (VM, cada persona su lista)

- [ ] 3.1 Verificar la cuota de vCPU N2 y el crédito del trial, y lanzar las 8 listas de `fase5_*` en paralelo desde `corridas-v2`; verificar al terminar que el ledger del bucket tiene las filas esperadas de cada lista y que `gcloud compute instances list` no muestra VMs encendidas
- [ ] 3.2 Consolidar todo (`python -m comun.consolidar`) y verificar que hay 8 réplicas × 10 semillas en las 5 variantes, que las corridas son todas `n2-highmem-8` y `codigo_sucio = False` y que ninguna fila quedó `valida = False` sin explicación; anotar en la bitácora tiempos reales contra los de D3
- [ ] 3.3 Revisión en sesión limpia de resultados con la lista de `docs/revision.md` y cierre en la bitácora

## 4. Comparación limpia (sesión: Sonnet)

- [ ] 4.1 `exploratorio.json` de `h3/sensibilidad_muestra/` (archivo nuevo, sin tocar los que tienen huella); validación de campos en `comun.variantes --verificar`; verificar que `sha256sum` de los archivos de Martín coincide con su `procedencia.json` y que un manifiesto sin advertencia hace fallar el `--verificar`
- [ ] 4.2 `comun/reporte.py`: bloques A y B, tiempo igual con IC entre réplicas y bootstrap de clientes (D6), figura de tiempo contra ganancia con barras de réplicas, figura de descomposición de varianza y `informe/tabla_resultados.md`; tests de exploratorio sin CSV (pendiente), variante de una réplica (nota) y bootstrap idéntico en dos corridas; verificar que `python -m comun.reporte --todos` corre dos veces con diferencia solo en la fecha
- [ ] 4.3 Revisión en sesión limpia del grupo 4 con la lista de código y cierre en la bitácora

## 5. Análisis e informe (sesión: Opus)

- [ ] 5.1 Aplicar las reglas de D4 tal como quedaron escritas en 1.1: veredicto con réplicas de cada H3, A contra B y efecto del reescalado; escribirlo en `h3/informe/informe.md` (con la tabla que genera el reporte y la descomposición de varianza como respuesta a "¿alcanzan 50 semillas finales?"); verificar con un script que cada número del informe coincide con `replicas.csv` y `tabla_resultados.md`
- [ ] 5.2 Actualizar `sampling_1/informe/informe.md` (Resultados con los dos bloques, Conclusiones, Limitaciones, Qué sigue con H4) y `guion.md`; en el README de la raíz, que la sección de resultados apunte a la comparación nueva; verificar que los enlaces existen y que el README no tiene números que no estén en `tabla_resultados.md`
- [ ] 5.3 Revisión en sesión limpia de la etapa informe con la lista de `docs/revision.md`, cierre en las bitácoras de `h3` y `sampling_1`, y `comun/tokens.py`

## Workflow follow-up

- Archivar con `/opsx:archive h3-semillas-optuna`.
- Seguir con `incorporar-aportes`, que reusa los estudios `@k` de este cambio para H4 y las variantes de Luis.
