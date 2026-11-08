# Design

## Context

Lo que hay al cerrar `renombrar-brazos`:

- **Corridas.** Cada variante tiene un único estudio de Optuna: 40 trials, TPE con semilla `SEMILLA_OPTUNA = 0`, que
  también sortea la muestra de optimización (`comun/baseline.py`), y 10 semillas finales. `H3-0.25` y `H3-0.1` usan los
  estudios `U0.25` y `U0.1` de `h1`. `U0.05` existe en `h1`, pero no hay finales de H3 con esa tasa.
- **Reglas comunes** (`control/docs/hipotesis.md`):
  - G al corte N\* = 3.300 (sale de `C` en 201908);
  - Δ apareado por semilla con IC t de 9 g.l.;
  - δ = 0,02 · Ḡ_C = 5,52 M$ (Ḡ_C = 276,10 M$);
  - veredictos gana / no pierde / pierde / indeterminado.
- **Resultados:**
  - H3-0.1: Δ = +4,07, IC [−0,27; 8,41], A = 8,41.
  - H3-0.25: Δ = +4,18, IC [−0,60; 8,96], A = 4,48.
  - Las dos "no pierden".
- **Tiempos del control:** 748 s de Optuna, unos 35 s por final. Optuna en U0.25 / U0.1 / U0.05: 153 / 77 / 67 s.
- **Exploratorios** (los porta y los replica `incorporar-aportes`; acá solo entra el manifiesto de Martín):
  - Martín: 20 configuraciones al azar y 10 muestras del 25 %. La elección de H3 varía con la muestra (−9,9 a
    +8,8 M$), y en 7 de 10 coincide con la del control.
  - Luis: 50 semillas finales con hiperparámetros fijos. Propone `H3-0.05`, el reescalado √(1/r), H4 hard negatives
    y fast-retrain.

## Goals / Non-Goals

**Goals:**
- Medir la suerte de Optuna y meterla en el IC de H3.
- Separar dos explicaciones: (A) la muestra regulariza; (B) el control tuvo mala suerte.
- Probar `H3-0.05` y el reescalado √(1/r) como variantes pre-registradas, con réplicas.
- Dejar una comparación final con dos bloques, A (mismo protocolo) y B (exploratorios), sin números a mano.

**Non-Goals:**
- Réplicas de `U*`, `B*` y `GOSS`: pierden o no aceleran, y las réplicas no cambian eso.
- H4, fast-retrain y el resto de las ideas de Luis: son de `incorporar-aportes`, que usa las réplicas de este
  cambio.
- Otro mes de test.
- Cambiar δ, N\* o el espacio de Optuna.

## Decisions

### D1. Qué es una réplica

En la réplica k, la semilla del sampler TPE y la del sorteo de la muestra de optimización son k. La réplica 0 es la de
hoy. Las semillas finales no cambian.

Se varían juntas porque "la suerte de la optimización" que importa para el tutor incluye las dos. Martín ya aisló el
efecto de la muestra; separarlas acá duplicaría la grilla sin cambiar la respuesta práctica.

Alternativa descartada: variar solo TPE. Subestima la variabilidad real de H3, porque deja fija la muestra, y la
muestra es justamente lo que H3 agrega.

### D2. Nombres y dueños

- **Estudios.**
  - Réplica 0: el nombre de siempre (`C`, `U0.1`).
  - Réplica k ≥ 1: `<estudio>@k`. `@` es válido en nombres de archivo, no lo interpreta el shell sin comillas y se
    lee como "en la réplica k".
- **Dueños de los estudios.**
  - `C@k` es de `control`.
  - `U{r}@k` es de `h3`, no de `h1`. Lo corre este cambio, sirve solo a H3 y así `h1` queda intacto.
  - El registro lo resuelve con una regla: el estudio base `U{r}` es de `h1`, sus réplicas `@k` son de `h3`.
- **Variantes nuevas en `h3`:**

  | variante | método | tasa | estudio | final |
  |---|---|---|---|---|
  | `H3-0.05` | `opt-muestra` | 0,05 | `U0.05` / `U0.05@k` | r = 1 |
  | `H3R-0.1` | `opt-muestra-reescalado` | 0,1 | `U0.1` / `U0.1@k` | r = 1, `min_data_in_leaf` × √10, recortado a [1; 8000] |

  `H3R-0.1` comparte estudios con `H3-0.1`: la diferencia entre las dos es solo el reescalado, apareada por réplica y
  semilla.
- **Ledger.**
  - La columna `replica_opt` es un entero; una fila sin esa columna se lee como 0.
  - El `id` suma `@k` al nombre de la variante solo si k ≥ 1, así los `id` existentes no cambian.
- **Registro.** `comun/variantes.py` marca qué variantes admiten réplicas: `C`, `H3-0.25`, `H3-0.1`, `H3-0.05` y
  `H3R-0.1`.

### D3. Grilla, costo y ejecución

Se corren 8 réplicas (k = 0…7) × 10 semillas finales × 5 variantes. Ya hay 3 de las 40 celdas (k = 0 de `C`, `H3-0.25`
y `H3-0.1`).

| bloque | corridas | tiempo estimado |
|---|---|---|
| Optuna `C@1…7` | 7 × 748 s | 87 min |
| Optuna `U0.25@k`, `U0.1@k`, `U0.05@k` (k = 1…7) | 7 × (153 + 77 + 67) s | 35 min |
| Finales (37 celdas nuevas × 10 semillas) | 370 × ~35 s | 216 min |
| **Total** | | **~5,6 h de VM** |

**Por qué R = 8.** Si el desvío entre réplicas fuera de unos 4 M$ (la escala que sugiere Martín), con 8 contra 8 el
IC de Welch tiene una semiamplitud cercana a ±4,3 M$. Alcanza para decidir "no pierde" con δ = 5,52 si el Δ real
está cerca de 0, y para "gana" si el Δ real pasa los 4,5 M$. Con 5 réplicas la semiamplitud sube a unos ±5,8 y "no
pierde" deja de ser decidible. Con 10 réplicas el costo crece un 30 % para ganar poco.

**Ejecución.** Agustina corre todo, sin repartir entre integrantes:
- una VM `n2-highmem-8` spot por réplica k = 1…7, cada una con las 5 variantes de su réplica;
- una VM más para los finales de `H3-0.05` y `H3R-0.1` en k = 0.

Son 8 VMs (64 vCPU), dentro de la cuota de 200 vCPU N2 de `us-central1`, todas desde el tag `corridas-v2`. Cada VM
tarda unos 47 min y el total de pared queda en ~50 min.

Antes de lanzar se verifican la cuota y el crédito del trial (`CLAUDE.md` § Cómputo). Si la cuota no alcanzara, se
lanzan en tandas.

### D4. Hipótesis pre-registradas (van a `h3/docs/hipotesis.md` antes de correr)

Las reglas usan los veredictos comunes sobre **Δ con réplicas** (D5), con δ y N\* fijos.

- **H3 con réplicas.** `H3-0.1` y `H3-0.25` no pierden con réplicas.
  - Si no pierden, se confirma la respuesta al tutor: el tradeoff vale la pena.
  - Si alguna pasa a pierde o indeterminado, el informe corrige la conclusión.
- **A contra B** (el mecanismo), sobre `H3-0.1`:
  - **Apoya (A):** Δ con réplicas *gana* (cota inferior > 0) **y** la mediana de `feature_fraction` entre réplicas
    es menor en `H3-0.1` que en `C`.
  - **Apoya (B):** el IC de Δ con réplicas contiene a 0 **y** Ḡ de `C` en la réplica 0 queda debajo de la mediana de
    las 8 réplicas de `C`.
  - Cualquier otro resultado: "mecanismo sin resolver". La respuesta práctica sale de la regla anterior.
- **H3-0.05.** No pierde con réplicas y A ≥ 8.
- **H3R-0.1.** Se mide la diferencia `H3R-0.1` − `H3-0.1` apareada por réplica y semilla (80 pares), con IC t por
  réplica (7 g.l.).
  - Mejora si la cota inferior es > 0.
  - Empeora si la cota superior es < 0.
  - Si no, no cambia.

### D5. Estadística

- **Por réplica:** Ḡ_{v,k} es la media de G en las semillas finales de la variante v en la réplica k.
- **Δ con réplicas:** media_k Ḡ_{v,k} − media_k Ḡ_{C,k}.
  - IC de Welch entre las réplicas de cada uno.
  - No se aparea por k: la réplica k de `C` y la de H3 no comparten nada que las correlacione, porque la muestra y el
    sampler corren sobre datos distintos.
- **Diferencias entre variantes que comparten estudios:** `H3R-0.1` contra `H3-0.1` se aparea primero por semilla
  dentro de cada réplica y después se toma la media por réplica, con IC t entre réplicas.
- **Descomposición:** para cada variante, var(G) = var_entre(Ḡ_{v,k}) + media_k var_dentro, con la suma de cuadrados
  exacta.
  - El reporte muestra qué parte de la varianza es suerte de Optuna y qué parte es semilla final.
  - Es la respuesta directa a "¿alcanzan 50 semillas finales?".
- **Lo que no cambia:** el Δ apareado de la réplica 0 se sigue calculando como hasta ahora, para que los números
  previos sigan siendo verificables.

### D6. Tiempo igual con intervalo

- **Por réplica.** El tiempo de la variante en la réplica k (Optuna de esa réplica + media del final) da K_k ≤ 10
  semillas en el presupuesto del control de esa misma réplica. El ensamble de esas K_k semillas se compara con
  Ḡ_{C,k}, y la media entre réplicas lleva IC t.
- **Bootstrap de clientes.** 1.000 remuestreos de clientes de 201910 con reposición, con `default_rng(20261108)`. El
  corte es N\* · n_b / n, redondeado, y se recalcula la diferencia en cada remuestreo. Mide el ruido del mes de test,
  que las réplicas no ven.
- **Variantes de una sola réplica** (`U*`, `B*`): solo el bootstrap.

### D7. Comparación en dos bloques y manifiesto de exploratorios

`comun/reporte.py --experimento sampling_1` arma los dos bloques y `informe.md` § Resultados los copia de una tabla
que genera el mismo comando (`informe/tabla_resultados.md`), así el texto no repite números a mano.

**Bloque A:**
- Columnas: variante, hipótesis, Ḡ, Δ (réplica 0) [IC], Δ con réplicas [IC] (R), T mediana, A, tiempo igual [IC],
  veredicto (fuente).
- Orden: por hipótesis y, dentro de cada una, por A.
- Figuras:
  - tiempo contra ganancia, con barras de rango entre réplicas;
  - descomposición de varianza: barras apiladas por variante con réplicas.

**Bloque B:** una fila por `exploratorio.json` encontrado en `experimentos/*/` y en `experimentos/sampling_1/exploratorios/*/`.

```json
{
  "autor": "Martín López",
  "fecha": "2026-11-04",
  "pregunta": "¿Cuánto depende de la muestra la configuración que elige H3?",
  "protocolo": "20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64",
  "advertencia": "10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25",
  "tablas": [{"csv": "resultados/08_ganancia_por_configuracion.csv", "columnas": ["config", "rol", "ganancia"]}]
}
```

El manifiesto de Luis lo escribe `incorporar-aportes`, cuando porte y corra su script.

`comun.variantes --verificar` valida los campos obligatorios de cada manifiesto.

## Risks / Trade-offs

- **[R = 8 no alcanza]** Si el desvío entre réplicas es mayor que el previsto, el IC queda ancho y H3 puede quedar
  indeterminado. Eso también es un resultado (la ventaja de H3 no se distingue de la suerte de Optuna), y se informa
  así. No se agregan réplicas después de mirar los resultados.
- **[Mirar y volver a elegir]** δ, N\*, R y las reglas quedan escritos en `h3/docs/hipotesis.md` y revisados en sesión
  limpia antes de la primera corrida. El análisis corre una vez sobre el ledger completo.
- **[Tiempos de VMs distintas]** Todas las VMs son `n2-highmem-8`, pero no la misma máquina física. Se registran `cpu` y
  `load_avg`, como ya se hace, y T se informa como mediana entre réplicas. `C-rep` ya mostró que la variación entre
  VMs de la misma familia es chica.
- **[Spot que se cae]** Optuna retoma el estudio desde el SQLite, y los finales saltean las semillas que ya tienen fila.
  Es el mecanismo actual.
- **[Ownership raro de `U{r}@k`]** Que la réplica 0 sea de `h1` y las demás de `h3` es una excepción → regla
  explícita en el registro, test que la cubre y nota en `h3/docs/diseno.md` § Dependencias.
