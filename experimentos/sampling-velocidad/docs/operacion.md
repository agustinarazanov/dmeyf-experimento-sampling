# Operación — Sampling_1

Cómo correr, retomar y consolidar. Todas las rutas son relativas a `experimentos/sampling-velocidad/`, con
`export PYTHONPATH=../..` (la raíz del repo, para ver `comun/`). El diseño y el reparto por persona están en
`docs/diseno.md`.

## Una configuración

```bash
python -m src.correr --metodo uniforme --tasa 0.25 --semilla 0 --etapa optimizar        # estudio U0.25
python -m src.correr --metodo uniforme --tasa 0.25 --semilla todas --etapa final        # brazo U0.25, 10 semillas
python -m src.correr --metodo opt-muestra --tasa 0.25 --semilla todas --etapa final     # brazo H3-0.25
python -m src.correr --metodo uniforme --tasa 1 --semilla todas --etapa final --brazo C-rep --hp ledger/hp/C.json
```

| método | `--tasa` | estudio | brazo |
|---|---|---|---|
| `uniforme` | r | `C` (r = 1) o `U<r>` | igual al estudio |
| `bagging` | f | `B<f>` | igual al estudio |
| `goss` | 1 | `GOSS` | `GOSS` |
| `opt-muestra` | r_opt | el de `uniforme` con la misma tasa | `H3-<r_opt>` |

- `opt-muestra --etapa optimizar` corre el estudio de `uniforme` con esa tasa, que H1 y H3 comparten.
- `--etapa final` usa `ledger/hp/<estudio>.json` salvo que se pase `--hp`. `--semilla todas` son las 10 semillas del
  diseño; una lista con comas también vale. Las que ya tienen fila válida se saltean.
- El estudio de Optuna es un SQLite en `$DATOS_DIR/optuna/`. Si la corrida se corta, el mismo comando retoma los trials
  que faltan. `--tras-trial 'cmd {db}'` corre un comando después de cada trial (la VM lo usa para copiarlo al bucket).

## Qué cuenta y qué no

Una fila es **válida** (`valida = true`) si el árbol estaba limpio (los archivos de `ledger/` no cuentan), no se usó
`--filas` y los trials son 40. Lo demás es exploratorio: va a `ledger/exploracion/` (ignorado por git) y su id lleva
`exp-` y la hora, así que nunca se saltea. `consolidar` solo mira `ledger/corridas/`.

Tiempos de una fila final (`docs/hipotesis.md` § T): `tiempo_entrenamiento_s` es `Dataset` + entrenamiento + predicción
en 201910; `tiempo_lgbtrain_s`, solo `lgb.train`. La predicción de 201908 no entra. En una invocación con varias
semillas, la primera fila lleva además la carga de datos y el panel (`tiempo_preparacion_s`); las otras, solo su muestreo.
En una fila `optimizar`, `tiempo_optimizacion_s` es la suma de la duración de los trials más el armado del `Dataset`.

## Consolidar y graficar

```bash
python -m src.consolidar          # ledger/resultados.csv, reemplazadas.csv, estudios.csv y apareado.csv
python scripts/graficar.py        # bandas de curvas por brazo en informe/figuras/
```

`apareado.csv` trae N* (elegido con el control en 201908), δ, Δ de ganancia por brazo (media, desvío, IC 95%, semillas
ganadas, veredicto), Δ de AUC, T y la aceleración A. Los tiempos solo se comparan con el control si la máquina, la CPU y
los hilos coinciden; si no, la columna `nota` lo dice.

## VM

```bash
PROYECTO=<proyecto-uba> BUCKET=gs://<bucket> scripts/vm.sh configuraciones.txt
```

`vm.sh` crea la VM spot desde `to-064ram-08vcpu` con `n2-highmem-8` e Ice Lake (`docs/diseno.md` § Máquina), copia el repo
en el commit actual, instala `requirements.txt`, corre la lista con `nohup`, sube `ledger/` y los SQLite al bucket,
trae el ledger y **borra la VM** al terminar o fallar. Antes de cada fase:

1. Hacer commit y tag `corridas-v1` (las filas con árbol sucio no cuentan).
2. Armar `configuraciones.txt` con las líneas de la persona (`docs/diseno.md` § Reparto y fases).
3. Si una VM muere, volver a correr el mismo comando: baja el panel y los SQLite del bucket, retoma el estudio y saltea
   las finales que ya tienen fila.
4. Después de traer el ledger: `git add ledger/corridas ledger/curvas ledger/hp`, commit y push; luego `consolidar`.

Smoke de la propia VM: `scripts/vm.sh configuraciones.txt --filas 20000`.
