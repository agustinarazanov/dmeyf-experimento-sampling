# Tasks

Requiere `renombrar-brazos` y `h3-semillas-optuna` archivados.

## 1. Hipótesis y diseño (sesión: Opus)

- [x] 1.1 Crear `experimentos/h4/` desde `plantilla/`, con `docs/hipotesis.md` (H4, predicciones y reglas de D4, la declaración de que las ideas vienen de mirar 201910, los contrastes principales y la nota de comparaciones múltiples) y `docs/diseno.md` (variantes y estudios de D3, sonda, grilla, `## Dependencias`: control, h1, h3); verificar con un grep que cada regla tiene umbral numérico y métrica
- [x] 1.2 Sumar a `h3/docs/hipotesis.md` y `h3/docs/diseno.md` las extensiones de D4 y las variantes `H3R-0.25`, `H3L-0.25`, `H3L-0.1` y `H3K-0.1` con su estudio `K0.1`, declarando que vienen del aporte de Luis; actualizar `sampling_1/docs/hipotesis.md` y `diseno.md` a cuatro hipótesis; verificar que los enlaces existen
- [x] 1.3 Revisión en sesión limpia de la etapa hipótesis y diseño con la lista de `docs/revision.md`, cierre en las bitácoras de `h3` y `h4`. Ninguna corrida real antes de este cierre

## 2. Métodos y variantes (sesión: Sonnet)

- [x] 2.1 `comun/muestreo.py` y `comun/metodos.py`: muestra por cliente, muestra de búsqueda por clase (uniforme y difícil, con la sonda de la spec), final submuestreado con peso 1/f y reescalados `raiz` y `lineal`; tests sin datos (todo cliente entero o ausente, misma cantidad de positivos y negativos en `H4H` y `H4U`, peso que restituye la proporción, recorte a [1; 8000]); verificar que `pytest` pasa
- [x] 2.2 `comun/variantes.py`: las 8 variantes de D3, los estudios `K0.1` (h3), `NH0.1` y `NU0.1` (h4) con sus `@k`, y el experimento `h4`; `comun/correr.py` suma el tiempo de la sonda a la optimización; verificar que `python -m comun.variantes --verificar` pasa con las dependencias de D3 y un smoke en la Mac (`--filas 20000`) de una optimización de `NH0.1` en la réplica 2 y un final de `H4F-0.05`
- [x] 2.3 Listas `sampling_1/scripts/fase6_r<k>.txt` (k = 0…7) según D6; verificar con `--en-seco` que cubren las 8 variantes × 8 réplicas y los 24 estudios nuevos sin repetir
- [x] 2.4 Revisión en sesión limpia del grupo 2 con la lista de código de `docs/revision.md` y cierre en la bitácora

## 3. Migración del aporte de Luis (sesión: Sonnet)

- [x] 3.1 Crear el paquete de D1 en `experimentos/sampling_1/exploratorios/validacion_50_semillas/`: portar `estrategias.py`, `validacion.py` y `hp_original.json` desde el commit `9e1889e`, sin cambios de lógica en lo portado; sacar Colab, Drive y `FACTOR_VM`; usar `comun.datos`, `comun.ganancia` y `DATOS_DIR`; `git mv` del resumen a `resumen_original.md` y `git rm` del script original; verificar que `experimentos/Experimentos h3 y h4/` ya no existe y que el paquete importa solo de `comun/` y de su carpeta (grep)
- [x] 3.2 Reconstrucciones de D2 marcadas como tales en código y README: CSV por estrategia y semilla (G, ganancia máxima y AUC en 201908 y G y AUC en 201910), `presupuesto.py` (900 s, semillas extendidas) y `--agregar` con el ranking y la curva según K en 201908 (D9); tests sin datos (ningún orden, máximo ni K se calcula sobre 201910: test con datos sintéticos donde 201908 y 201910 ordenan distinto) (semillas 50 + extendidas con la fórmula de Luis, `--hp original` y `--hp ledger` iguales en `C` y `U*`, K del presupuesto con tiempos sintéticos); verificar que `pytest` pasa
- [x] 3.3 `README.md` (autor, fecha, commit de origen, protocolo, diferencias con el nuestro, qué se portó y qué se reconstruyó, tabla reportado/reproducido vacía) y `exploratorio.json`; listas `sampling_1/scripts/fase6_luis_<estrategia>.txt`; verificar que `comun.variantes --verificar` acepta el manifiesto y que `--en-seco` imprime las 9 VMs
- [x] 3.4 Smoke en la Mac de una estrategia con 2 semillas sobre `--filas 20000` y `--agregar`; verificar que se escriben el CSV y el HTML
- [x] 3.5 Revisión en sesión limpia del grupo 3 con la lista de código y cierre en la bitácora; crear el tag `corridas-v3` (lo pushea Agustina)

## 4. Corridas (VM, todas las lanza Agustina)

- [x] 4.1 Verificar la cuota de vCPU N2 y el crédito del trial; lanzar en paralelo las 8 VMs de variantes, las 9 de Luis (`--hp original`) y la de Martín (D5, más la comparación de paneles de D7); verificar al terminar que no quedan VMs encendidas (`gcloud compute instances list`)
- [x] 4.2 Con `NH0.1` ya en el ledger, correr la estrategia 7 de Luis con `--hp ledger`; verificar que no quedan VMs encendidas
- [x] 4.3 Consolidar (`python -m comun.consolidar`); verificar que hay 8 réplicas × 10 semillas en las 8 variantes, todo en `n2-highmem-8` con `codigo_sucio = False`, y anotar tiempos reales contra D6 en la bitácora
- [x] 4.4 `validacion.py --agregar` y `presupuesto.py`; copiar los CSV a `resultados/` con `procedencia.json`; verificar que hay 50 semillas (o K si es mayor) por estrategia
- [x] 4.5 Revisión en sesión limpia de resultados con la lista de `docs/revision.md` y cierre en las bitácoras

## 5. Replicación (sesión: Sonnet)

- [x] 5.1 Martín: comparar los sha256 de las salidas nuevas de 07 y 08 con `sha256_lf` de `procedencia.json` y completar en su README la tabla reportado/reproducido (D5) con las versiones de LightGBM y numpy; verificar que cada fila dice "idéntico", "igual salvo redondeo" o "distinto", con la explicación
- [x] 5.2 Luis: escribir las conclusiones del exploratorio con el ranking en 201908 (D9), y en una sección aparte, "Reproducción del resumen original", completar la tabla reportado/reproducido con cada número de `resumen_original.md` (incluidas las reconstrucciones, con su etiqueta, y los descartes contra las variantes de D3) y el resultado de la comparación de paneles (D7); verificar con un script que cada número de la tabla sale de `resultados/` o de `replicas.csv`
- [x] 5.3 Revisión en sesión limpia del grupo 5 con la lista de resultados y cierre en la bitácora

## 6. Análisis e informes (sesión: Opus)

- [x] 6.1 Aplicar las reglas de D4 tal como quedaron escritas en 1.1 y 1.2; escribir `h4/informe/informe.md` y las extensiones en `h3/informe/informe.md`, con las limitaciones de la spec (test ya mirado, comparaciones múltiples); verificar con un script que cada número coincide con `replicas.csv` y `tabla_resultados.md`
- [x] 6.2 Regenerar `python -m comun.reporte --todos`; actualizar `sampling_1/informe/informe.md` (cuatro hipótesis, bloque B replicado, conclusiones con los contrastes principales), `guion.md` y el README de la raíz (D8); verificar que los enlaces existen y que el README no tiene números que no estén en `tabla_resultados.md`
- [ ] 6.3 Revisión en sesión limpia de la etapa informe con la lista de `docs/revision.md`, cierre en las bitácoras de `h3`, `h4` y `sampling_1`, y `comun/tokens.py`

## Workflow follow-up

- Archivar con `/opsx:archive incorporar-aportes`.
