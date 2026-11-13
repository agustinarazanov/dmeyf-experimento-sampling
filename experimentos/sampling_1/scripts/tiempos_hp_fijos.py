"""Tiempo de un trial con hiperparámetros fijos y calibración por máquina (`tiempos-confiables-y-consistencia` D4, D6).

    python -m experimentos.sampling_1.scripts.tiempos_hp_fijos                       # las 216 mediciones (VM n2-highmem-8)
    python -m experimentos.sampling_1.scripts.tiempos_hp_fijos --anclas              # duración del mejor trial de C y C@1…7
    python -m experimentos.sampling_1.scripts.tiempos_hp_fijos --calibracion fase8_r3_a inicio
    python -m experimentos.sampling_1.scripts.tiempos_hp_fijos --consolidar          # local: arma los dos CSV
    python -m experimentos.sampling_1.scripts.tiempos_hp_fijos --prueba              # humo local, sin tocar los datos reales

Medición: los 8 juegos de hiperparámetros del control (estudios `C` y `C@1…7`), 3 repeticiones, sobre la muestra al azar en
r ∈ {1; 0,5; 0,25; 0,1; 0,05} y sobre la receta de H4 (todas las bajas + f de CONTINUA con peso 1/f) en f ∈ {0,5; 0,25;
0,1; 0,05}. Cada medición reproduce un trial: muestra con la semilla 1000 + repetición, `Dataset`, `lgb.train` con los
parámetros fijos y los hiperparámetros del juego, y predicción de 201908. Se cronometran por separado el `Dataset`, el
entrenamiento y la predicción; el tiempo de la medición es entrenamiento más predicción, lo que guarda Optuna como duración
de un trial. El orden se aleatoriza con semilla fija y cada medición es un archivo en `ledger/tiempos/hp_fijos/`: al
relanzar se saltean las que ya existen.

Calibración: al empezar y al terminar la lista de una VM, un trial de `C` (réplica 0, r = 1, semilla del trial original,
2 repeticiones) y un final viejo de `C` (primera semilla final, cronometrado como un final del corredor), sin escribir en el
ledger de `control`: `ledger/tiempos/calibracion_<lista>_<momento>.csv`.

Solo corre en `n2-highmem-8` (salvo con `--prueba`). Importa solo de `comun/`.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import socket
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from comun import baseline as bl
from comun import correr, metodos, rutas
from comun import datos as dt

EXP = "sampling_1"
TIPO_DE_MAQUINA = "n2-highmem-8"
TASAS_AZAR = (1.0, 0.5, 0.25, 0.1, 0.05)
TASAS_BAJAS = (0.5, 0.25, 0.1, 0.05)
RECETAS = ("azar", "bajas")
REPETICIONES = 3
SEMILLA_BASE = 1000  # la muestra de la repetición k usa 1000 + k
SEMILLA_ORDEN = 20261113  # orden aleatorio de las mediciones
REPETICIONES_CALIBRACION = 2
SEMILLA_FINAL_CALIBRACION = bl.SEMILLAS_FINALES[0]
JUEGOS = ["C", *[f"C@{k}" for k in range(1, 8)]]  # estudios del control, uno por juego de hiperparámetros
MOMENTOS = ("inicio", "fin")
VENTANA_FASE7 = bl.VENTANA_FINAL


def raiz_tiempos(prueba: bool = False) -> Path:
    led = rutas.ledger(EXP)
    return (led / "exploracion" if prueba else led) / "tiempos"


def versiones() -> dict:
    return {"lightgbm": lgb.__version__, "numpy": np.__version__, "optuna": optuna.__version__}


def entorno() -> dict:
    commit, _ = correr.commit_y_sucio()
    return {"maquina": correr.tipo_de_maquina(), "instancia": socket.gethostname(), "cpu": correr.modelo_de_cpu(),
            "hilos": bl.NUM_THREADS, "commit": commit, **{f"version_{k}": v for k, v in versiones().items()}}


def hp_del_juego(juego: str) -> dict:
    """Los mejores hiperparámetros del estudio `juego` (`C`, `C@1`, …), del ledger de `control`."""
    ruta = rutas.ledger("control") / "hp" / f"{juego}.json"
    if not ruta.exists():
        raise FileNotFoundError(f"falta {ruta}: la medición necesita los hiperparámetros de los estudios del control")
    return json.loads(ruta.read_text())["hp"]


def celdas(juegos: list[str], tasas_azar=TASAS_AZAR, tasas_bajas=TASAS_BAJAS, repeticiones: int = REPETICIONES) -> list[dict]:
    """Todas las mediciones, en el orden aleatorio de semilla fija (`SEMILLA_ORDEN`)."""
    todas = [{"receta": r, "tasa": t, "juego": j, "repeticion": k}
             for r, tasas in (("azar", tasas_azar), ("bajas", tasas_bajas)) for t in tasas for j in juegos
             for k in range(repeticiones)]
    orden = np.random.default_rng(SEMILLA_ORDEN).permutation(len(todas))
    return [todas[i] for i in orden]


def nombre_archivo(c: dict) -> str:
    return f"{c['receta']}_{c['tasa']:g}_{c['juego']}_{c['repeticion']}.csv"


def muestra(receta: str, train: pd.DataFrame, tasa: float, semilla: int):
    """(datos, parámetros de la variante, pesos) de la receta: muestra al azar o bajas + fracción de CONTINUA con peso 1/f."""
    if receta == "azar":
        datos, params, _ = metodos.FUNCIONES_OPT["uniforme"](train, tasa, semilla)
        return datos, params, None
    datos, params, _ = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, tasa, semilla)
    return datos, params, metodos.pesos("fast-retrain-opt", datos, tasa)


def cronometrar(x_tr, y_tr, peso, params: dict, x_pred) -> dict:
    """Los tres tiempos de un trial: `Dataset` (fuera de la duración de Optuna), entrenamiento y predicción."""
    t0 = time.perf_counter()
    dtrain = lgb.Dataset(x_tr, label=y_tr, weight=peso, params={**bl.PARAMS_DATASET, "num_threads": bl.NUM_THREADS},
                         free_raw_data=False)
    dtrain.construct()
    t1 = time.perf_counter()
    modelo = lgb.train(params, dtrain)
    t2 = time.perf_counter()
    modelo.predict(x_pred)
    t3 = time.perf_counter()
    return {"t_dataset_s": t1 - t0, "t_entrenamiento_s": t2 - t1, "t_prediccion_s": t3 - t2, "t_medicion_s": t3 - t1}


def medir(argumentos: argparse.Namespace) -> int:
    """Las mediciones a hiperparámetros fijos que todavía no tienen archivo. Devuelve cuántas hizo."""
    salida = raiz_tiempos(argumentos.prueba) / "hp_fijos"
    salida.mkdir(parents=True, exist_ok=True)
    juegos = JUEGOS[: argumentos.juegos]
    todas = celdas(juegos, TASAS_AZAR[: argumentos.tasas] if argumentos.tasas else TASAS_AZAR,
                   TASAS_BAJAS[: argumentos.tasas] if argumentos.tasas else TASAS_BAJAS, argumentos.repeticiones)
    pendientes = [c for c in todas if not (salida / nombre_archivo(c)).exists()]
    print(f"{len(todas)} mediciones, {len(pendientes)} pendientes")
    if not pendientes:
        return 0
    _, _ = dt.asegurar_panel(argumentos.filas)
    train = dt.cargar_meses(bl.MESES_TRAIN_OPT, argumentos.filas)
    val = dt.cargar_meses([bl.MES_VALIDACION], argumentos.filas)
    cols = dt.columnas_predictoras(train)
    x_va = dt.matriz(val, cols)
    hp = {j: hp_del_juego(j) for j in juegos}
    env = entorno()
    for i, c in enumerate(pendientes, 1):
        semilla = SEMILLA_BASE + c["repeticion"]
        datos, params_variante, peso = muestra(c["receta"], train, c["tasa"], semilla)
        x_tr, y_tr = dt.matriz(datos, cols), datos[dt.Y].to_numpy()
        params = {**bl.PARAMS_FIJOS, **params_variante, **hp[c["juego"]], "seed": semilla}
        t = cronometrar(x_tr, y_tr, peso, params, x_va)
        fila = {**c, "semilla": semilla, "filas": len(datos), **t, **env, "load_avg": round(os.getloadavg()[0], 2),
                "fecha": datetime.now().isoformat(timespec="seconds")}
        pd.DataFrame([fila]).to_csv(salida / nombre_archivo(c), index=False)
        print(f"[{i}/{len(pendientes)}] {nombre_archivo(c)}: {t['t_medicion_s']:.2f} s ({len(datos)} filas)", flush=True)
    return len(pendientes)


def calibrar(lista: str, momento: str, argumentos: argparse.Namespace) -> Path:
    """Trial de calibración (2 repeticiones) y final viejo de `C` réplica 0; un archivo por lista y momento."""
    if momento not in MOMENTOS:
        raise SystemExit(f"momento inválido: {momento!r} (opciones: {', '.join(MOMENTOS)})")
    destino = raiz_tiempos(argumentos.prueba) / f"calibracion_{lista}_{momento}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    env = {**entorno(), "lista": lista, "momento": momento}
    hp = hp_del_juego("C")
    filas = []
    dt.asegurar_panel(argumentos.filas)
    train = dt.cargar_meses(bl.MESES_TRAIN_OPT, argumentos.filas)
    val = dt.cargar_meses([bl.MES_VALIDACION], argumentos.filas)
    cols = dt.columnas_predictoras(train)
    datos, params_variante, _ = metodos.FUNCIONES_OPT["uniforme"](train, 1.0, bl.SEMILLA_OPTUNA)
    x_tr, y_tr, x_va = dt.matriz(datos, cols), datos[dt.Y].to_numpy(), dt.matriz(val, cols)
    params = {**bl.PARAMS_FIJOS, **params_variante, **hp, "seed": bl.SEMILLA_OPTUNA}  # la semilla del trial original
    for k in range(REPETICIONES_CALIBRACION):
        t = cronometrar(x_tr, y_tr, None, params, x_va)
        filas.append({"tipo": "trial", "repeticion": k, "semilla": bl.SEMILLA_OPTUNA, "filas": len(datos), **t,
                      "t_s": t["t_medicion_s"], **env, "fecha": datetime.now().isoformat(timespec="seconds"),
                      "load_avg": round(os.getloadavg()[0], 2)})
    del train, val, datos, x_tr, y_tr, x_va
    # final viejo: como un final del corredor (`Dataset`, entrenamiento y predicción de 201910; sin la carga de datos)
    train = dt.cargar_meses(bl.MESES_TRAIN_FINAL, argumentos.filas)
    test = dt.cargar_meses([bl.MES_TEST], argumentos.filas)
    cols = dt.columnas_predictoras(train)
    x_te = dt.matriz(test, cols)
    datos, params_variante, _ = metodos.FUNCIONES["uniforme"](train, 1.0, SEMILLA_FINAL_CALIBRACION)
    x_tr, y_tr = dt.matriz(datos, cols), datos[dt.Y].to_numpy()
    params = {**bl.PARAMS_FIJOS, **params_variante, **metodos.ajustar_hp("uniforme", 1.0, hp), "seed": SEMILLA_FINAL_CALIBRACION}
    t = cronometrar(x_tr, y_tr, None, params, x_te)
    filas.append({"tipo": "final", "repeticion": 0, "semilla": SEMILLA_FINAL_CALIBRACION, "filas": len(datos), **t,
                  "t_s": t["t_dataset_s"] + t["t_entrenamiento_s"] + t["t_prediccion_s"], **env,
                  "fecha": datetime.now().isoformat(timespec="seconds"), "load_avg": round(os.getloadavg()[0], 2)})
    pd.DataFrame(filas).to_csv(destino, index=False)
    print(f"{destino}: " + ", ".join(f"{f['tipo']} {f['t_s']:.2f} s" for f in filas))
    return destino


def anclas(argumentos: argparse.Namespace) -> Path:
    """Duración del mejor trial de cada estudio `C`, `C@1…7`, leída de los `.db` de Optuna (en la VM, los baja `vm.sh`)."""
    filas = []
    for juego in JUEGOS:
        db = bl.DATOS_DIR / "optuna" / f"{juego}.db"
        if not db.exists():
            print(f"falta {db}: se saltea {juego}")
            continue
        try:
            estudio = optuna.load_study(study_name=juego, storage=f"sqlite:///{db}")
            mejor = estudio.best_trial
        except KeyError:  # un .db vacío (el de una corrida a medias) no tiene el estudio
            print(f"{db} no tiene el estudio {juego}: se saltea")
            continue
        filas.append({"estudio": juego, "trial": mejor.number, "auc_val": mejor.value,
                      "duracion_s": mejor.user_attrs["duracion_s"], "n_trials": len(estudio.trials)})
    destino = raiz_tiempos(argumentos.prueba) / "anclas_trials.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(destino, index=False)
    print(f"{destino}: {len(filas)} estudios")
    return destino


def _leer_carpeta(patron: str) -> pd.DataFrame:
    archivos = sorted(glob.glob(patron))
    return pd.concat([pd.read_csv(a) for a in archivos], ignore_index=True) if archivos else pd.DataFrame()


def ancla_final(variante: str, semilla: int) -> float:
    """`tiempo_entrenamiento_s` del final de `variante` (réplica 0, ronda vigente) con esa semilla, del ledger de `control`."""
    f = rutas.ledger("control") / "resultados.csv"
    if not f.exists():
        return float("nan")
    r = pd.read_csv(f)
    r = r[(r["etapa"] == "final") & (r["variante"] == variante) & (r["meses_final"] == VENTANA_FASE7)
          & (r["semilla"] == semilla) & (r["replica_opt"].fillna(0) == 0)]
    return float(r["tiempo_entrenamiento_s"].iloc[0]) if len(r) else float("nan")


def consolidar(prueba: bool = False) -> tuple[Path, Path]:
    """`ledger/tiempos_hp_fijos.csv` (las mediciones) y `ledger/calibracion.csv` (con las anclas y sus cocientes)."""
    base = raiz_tiempos(prueba)
    led = base.parent
    hp = _leer_carpeta(str(base / "hp_fijos" / "*.csv"))
    cal = _leer_carpeta(str(base / "calibracion_*.csv"))
    anc = base / "anclas_trials.csv"
    if len(cal):
        trial_c = float("nan")
        if anc.exists():
            a = pd.read_csv(anc)
            if (a["estudio"] == "C").any():
                trial_c = float(a.loc[a["estudio"] == "C", "duracion_s"].iloc[0])
        cal["ancla_trial_s"] = np.where(cal["tipo"] == "trial", trial_c, np.nan)
        cal["ancla_final_fase7_s"] = np.where(cal["tipo"] == "final", ancla_final("C", SEMILLA_FINAL_CALIBRACION), np.nan)
        cal["ancla_final_crep_s"] = np.where(cal["tipo"] == "final", ancla_final("C-rep", SEMILLA_FINAL_CALIBRACION), np.nan)
        cal["cociente_ancla_trial"] = cal["t_s"] / cal["ancla_trial_s"]
        cal["cociente_ancla_fase7"] = cal["t_s"] / cal["ancla_final_fase7_s"]
        cal["cociente_ancla_crep"] = cal["t_s"] / cal["ancla_final_crep_s"]
    salida_hp, salida_cal = led / "tiempos_hp_fijos.csv", led / "calibracion.csv"
    hp.sort_values(["receta", "tasa", "juego", "repeticion"]).to_csv(salida_hp, index=False) if len(hp) else None
    cal.sort_values(["lista", "momento", "tipo", "repeticion"]).to_csv(salida_cal, index=False) if len(cal) else None
    print(f"{salida_hp}: {len(hp)} mediciones; {salida_cal}: {len(cal)} filas")
    if anc.exists():
        print(f"anclas: {anc}")
    return salida_hp, salida_cal


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--anclas", action="store_true", help="deja en tiempos/anclas_trials.csv la duración del mejor trial de C y C@1…7")
    p.add_argument("--calibracion", nargs=2, metavar=("LISTA", "MOMENTO"), help="calibración de la VM: `inicio` o `fin` de la lista")
    p.add_argument("--consolidar", action="store_true", help="local: arma tiempos_hp_fijos.csv y calibracion.csv (con las anclas)")
    p.add_argument("--prueba", action="store_true", help="humo local: 1 juego, 2 tasas, 1 repetición, panel reducido, fuera de la VM")
    p.add_argument("--filas", type=int, help="panel reducido de ~N filas (solo para pruebas)")
    p.add_argument("--juegos", type=int, default=len(JUEGOS), help="solo los primeros N juegos de hiperparámetros")
    p.add_argument("--tasas", type=int, default=0, help="solo las primeras N tasas de cada receta")
    p.add_argument("--repeticiones", type=int, default=REPETICIONES)
    a = p.parse_args(argv)
    if a.prueba:
        a.filas, a.juegos, a.tasas, a.repeticiones = a.filas or 20000, 1, 2, 1
    if a.consolidar:
        consolidar(a.prueba)
        return
    maquina = correr.tipo_de_maquina()
    if maquina != TIPO_DE_MAQUINA and not a.prueba:
        raise SystemExit(f"esto mide tiempos y solo corre en {TIPO_DE_MAQUINA} (acá: {maquina}); para probar, --prueba")
    if a.anclas:
        anclas(a)
    elif a.calibracion:
        calibrar(*a.calibracion, a)
    else:
        medir(a)


if __name__ == "__main__":
    main()
