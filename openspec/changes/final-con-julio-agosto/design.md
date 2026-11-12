# Design

## Context

El motivo está en `proposal.md`. Estado actual del código:

- `comun/baseline.py` tiene una sola lista de meses de entrenamiento, `MESES_TRAIN = 201903–201906`, que usan
  `optimizar` y `final` (`comun/correr.py:177` y `:263`). `MESES_PANEL` no incluye 201907. La etiqueta se calcula solo
  para train, validación y test (`comun/datos.py:105`).
- El final predice validación (201908) y test (201910). Guarda las dos curvas, y `consolidar` fija N\* con la media de las
  curvas de 201908 de los `C` (`comun/ledger.py:103`). δ sale de la ganancia media del control en 201910.
- `--semilla todas` devuelve las 10 de `SEMILLAS_FINALES`. El id de un final es
  `<estudio>_<método>_<tasa>_<semilla>_final_<commit>`, y `existe_fila` saltea lo que ya tiene fila.
- Los ledgers viven en el repo y en el bucket. Las VMs los sincronizan con `gsutil` (`scripts/vm.sh`).
- Los finales actuales son 113 celdas (variante × réplica) y 1.130 corridas. Suman ~7,5 h en `n2-highmem-8`. La cuota
  global permite 4 VMs a la vez.

## Goals / Non-Goals

**Goals:**
- Una ronda nueva de finales, con train del final 201903–201908 y 20 semillas, para todas las celdas que hoy tienen
  finales, sin tocar estudios ni hiperparámetros.
- Una sola variante con estudio nuevo, `H4O-0.5` (D11).
- ΔAUC en test al lado de Δ de ganancia en todas las tablas (D10).
- Que la ronda anterior se pueda seguir consolidando y comparar con la nueva.

**Non-Goals:**
- Volver a optimizar las variantes que ya tienen estudio, o cambiar el espacio de búsqueda.
- Volver a correr los exploratorios (Luis 50 semillas, Martín, Luis 20 semillas). Quedan con su protocolo y su
  advertencia.
- Ventana corrida 201905–201908. Si el tutor dice que es esa, es otro cambio.
- Tocar el requisito de `reporte-visual` que cambia `sitio-github-pages` («Legible sin servidor y compartible»). Este
  cambio solo modifica «Comparación limpia en dos bloques»; el que se archive segundo sincroniza el spec completo.
- Un veredicto por AUC. La regla escrita antes de correr decide por ganancia (D10).

## Decisions

### D1. Dos listas de meses, no una

`baseline.py` separa `MESES_TRAIN_OPT` (201903–201906) de `MESES_TRAIN_FINAL` (201903–201908). `MESES_TRAIN` desaparece y
cada uso se reemplaza por la lista que corresponde. Así un uso nuevo no puede tomar la ventana equivocada sin decirlo.

`optimizar` conserva el guard actual sobre 201910 y suma otro: no lee 201907.

*Alternativa:* un flag `--meses-final` en el CLI. Se descarta porque abre la puerta a correr rondas mezcladas desde una
lista de tareas. La ventana es una constante del baseline y queda registrada en el ledger (D4).

### D2. Panel con 201907

`MESES_PANEL` suma 201907 y la consulta de la etiqueta incluye los meses de train del final. La ventana de lags ya corre
sobre todo 201901–201910 antes de filtrar (comentario en `datos.py`), así que los otros meses no deberían cambiar.

`asegurar_panel` reconstruye el panel si no tiene filas de 201907, como pide el spec. Una tarea verifica, con huellas por
columna (las de `panel_luis.comparar`), que 201903–201906, 201908 y 201910 dan igual que en el panel viejo.

### D3. N\* fijo en 3.300

`baseline.N_ESTRELLA = 3300`, con el comentario de dónde sale: la ronda anterior, en validación. `consolidar` usa
`corte_control` solo para la ronda 201903–201906 (así la reproduce) y la constante para la ronda nueva.

Los finales nuevos no predicen 201908. `auc_val` y `curva_201908` quedan vacíos, porque esa predicción sería dentro de la
muestra. δ se recalcula con la regla de siempre sobre los `C` de la ronda nueva.

*Alternativas:*
- Fijar N\* con el mejor trial de Optuna en validación. No se guardaron sus predicciones.
- Un N\* nuevo calculado en test. Viola "201910 solo para comparar".

### D4. Columna `meses_final` y rondas

- `ledger.COLUMNAS` suma `meses_final` (`"201903-201908"` en los finales nuevos, vacío en las filas de optimización).
- El id de un final nuevo lleva la ventana (`..._final-0308_<commit>`). Ningún final nuevo puede chocar con uno viejo,
  aunque coincida el commit.
- Un script `scripts/agregar_meses_final.py --aplicar/--verificar`, con el mismo patrón que `renombrar_columna.py`,
  agrega la columna a los `resultados.csv` y `corridas/*.csv` de los cinco experimentos y del bucket, con
  `201903-201906` en los finales viejos. Comprueba que el resto de cada archivo no cambió.
- `consolidar --meses-final <ventana>` usa por defecto la vigente (`baseline.MESES_TRAIN_FINAL`). Falla si en esa ronda
  falta `C`.
- Antes de consolidar la ronda nueva, `apareado.csv` y `replicas.csv` se copian a `ledger/ronda_201903-201906/`. Una tarea
  comprueba que consolidar con la ventana vieja los reproduce byte a byte.

### D5. 20 semillas

`baseline.SEMILLAS_FINALES` pasa a ser las 10 oficiales seguidas de `[110017 + i·19937 for i in range(10)]`
(110017 … 289450, sin choques con las oficiales). `--semilla todas` devuelve las 20.

El orden importa: "las primeras 10" son las de la ronda anterior. Así, si hiciera falta, se puede reconsolidar la ronda
nueva con 10 y separar el efecto de la ventana del de las semillas. La lista se escribe en `control/docs/diseno.md`
antes de lanzar.

*Alternativa:* usar las semillas que Luis usó en sus 20. No las publicó.

### D6. Hiperparámetros de cuatro meses en un final de seis

Se usan sin cambios, incluido `min_data_in_leaf`, que es absoluto y ahora se aplica sobre ~1,5 veces más filas. Es lo que
pide la consigna (reentrenar), no una variante. Se declara como limitación. Reescalarlo sería una variante nueva, y la
idea ya está en `H3R` y `H3L`.

### D7. Predicción antes de correr

Antes del tag de corridas, `control/docs/hipotesis.md` suma una predicción y una regla para la ronda:
- ningún veredicto cambia de *gana* o *no pierde* a *pierde*, ni al revés;
- el IC por semilla se angosta del orden de √2;
- la predicción y la regla de `H4O-0.5` contra `C` y contra `H4F-0.05` se escriben en `h4/docs/hipotesis.md`
  (tarea 1.1), con umbral numérico, antes del tag;
- con réplicas, el ancho baja menos, porque entre el 33 y el 40 % de la varianza de `H3` es entre réplicas.

Un veredicto que cambie no se descarta: se informa en la tabla de rondas (D9).

### D8. Ejecución

- Listas `experimentos/sampling_1/scripts/fase7_r0.txt` … `fase7_r7.txt`, una por réplica, todas con `--semilla todas`.
  `r0` suma `h1`, `h2` y `C-rep`. Cada lista empieza por el estudio `F0.5@k` y sigue con los finales, `H4O-0.5`
  incluido. Son 121 celdas × 20 = 2.420 finales y 8 estudios.
- Todo sale de un tag nuevo, `corridas-v4`, con 4 VMs a la vez (dos tandas).
- Estimado: ~24 h de cómputo, ~7 h de pared, ≈ US$ 5 en spot.
- Lo lanza Agustina con `scripts/lanzar_fase.sh`. Las sesiones solo usan `--en-seco`.

### D9. Informes

- `comun.reporte` rotula cada tabla con la ventana del final y la cantidad de semillas. Lee la ronda vigente.
- Un script `scripts/comparar_rondas.py` escribe `experimentos/sampling_1/informe/comparacion_rondas.md`: por variante,
  Δ y veredicto en la ronda anterior y en la nueva, sin números a mano.
- `informe.md`, el guion y el README pasan a la ronda nueva.
- Los diseños de `control`, `h3` y `h4` escriben cada apartamiento con su id (208135 métrica, 211718 reoptimizar, 211210
  ventana) y su justificación. § Limitaciones lista solo los que quedan sin justificar.
- Un párrafo en el README de `validacion_20_semillas` remite a la ronda nueva, que corre nuestro protocolo con 20
  semillas.

### D10. AUC al lado de la ganancia

`apareado.csv` ya tiene `delta_auc_media` y su IC por semilla. Se agregan:
- en `replicas.csv`, ΔAUC con réplicas (media de AUC en 201910 por réplica, Welch entre réplicas), igual que Δ de
  ganancia;
- en el bloque A y en los reportes por hipótesis, una columna de ΔAUC con su IC;
- en el informe, una frase por hipótesis cuando AUC y ganancia van en direcciones distintas.

El veredicto sigue siendo el de ganancia porque así está escrita la regla, y δ está definido en pesos. Un umbral de
AUC sería una regla nueva escrita después de haber visto los AUC de la ronda anterior.

### D11. `H4O-0.5`

- Método nuevo `fast-retrain-opt`. En `optimizar`, la muestra es la receta de `fast_retrain` (todas las bajas + 50 % de
  CONTINUA) con la semilla de la réplica, y los pesos de `pesos` se aplican al `Dataset` de cada trial. La validación es
  201908 completo, sin pesos.
- En el final, la misma receta sobre 201903–201908 con la semilla final.
- Registro: `Variante("H4O-0.5", "h4", "fast-retrain-opt", 0.5, "F0.5", replicas=True)`, estudio `F0.5` con dueño `h4`.
  `PARES_WELCH` suma `("H4O-0.5", "H4F-0.05")`.
- La tasa 0,5 es la fracción f de CONTINUA, no una r de muestra de búsqueda. `ajustar_hp` no reescala.
- `h4/docs/hipotesis.md` suma la predicción y la regla antes del tag (D7) y declara que la idea viene del "siempre OP" del
  tutor (211718), no de mirar 201910.

*Alternativa:* reoptimizar también `H4F-0.25`. Se descarta: con `F0.5` alcanza para ver si reoptimizar sobre el set del
final cambia algo, y la búsqueda de `H4O` no depende de r.

## Risks / Trade-offs

- **[El panel nuevo cambia meses que no debía]** → Huellas por columna contra el panel viejo (D2) antes del tag. Si algo
  difiere, se frena y se investiga.
- **[Tiempos no comparables entre rondas]** → T y A se comparan solo dentro de una ronda. La tabla de rondas no compara
  tiempos.
- **[δ cambia con el control nuevo]** → Es la regla pre-registrada (δ sale del control), no un ajuste. La tabla de rondas
  muestra los dos δ.
- **[Interrupción de VMs spot]** → `existe_fila` retoma por semilla, igual que en las fases anteriores.
- **[El bucket queda con el formato viejo de ledger]** → La migración de D4 corre también sobre la copia del bucket, y se
  verifica bajándola de nuevo (como en `renombrar-brazos` 2.5).
- **[`H4O-0.5` solo existe en la ronda nueva]** → No entra en la tabla de rondas; su comparación es contra `C` y
  `H4F-0.05` de la misma ronda.
- **[La ventana correcta era 201905–201908]** → Las listas y el código no dependen de que sea 03–08: es una constante y
  una ronda más. Se declara en limitaciones hasta que haya respuesta.

## Migration Plan

1. Código, tests y migración de ledgers (repo y bucket) con `--verificar`.
2. Copias de la ronda anterior y comprobación de que se reproducen.
3. Predicción escrita, smoke `--filas 20000` en la Mac y tag `corridas-v4`.
4. Corridas.
5. Consolidado y reportes.
6. Informes.

Para volver atrás, `consolidar --meses-final 201903-201906` regenera todo lo de la ronda anterior. Ninguna fila se borra.
