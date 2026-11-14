"""Punto de entrada del experimento: una configuración (método, tasa, semilla, etapa) -> filas del ledger.

    python -m comun.correr --metodo uniforme --tasa 0.25 --semilla 0 --etapa optimizar
    python -m comun.correr --metodo uniforme --tasa 0.25 --semilla todas --etapa final
    python -m comun.correr --metodo opt-muestra --tasa 0.1 --etapa optimizar --replica 3

Se corre desde la raíz del repo. La fila va al ledger del experimento dueño de la variante y los hiperparámetros se
guardan y se leen en el ledger del dueño del estudio (`comun/variantes.py`): un final de `H3-0.25` escribe en
`experimentos/h3/ledger/` y lee `experimentos/h1/ledger/hp/U0.25.json`.

Con `--replica k` (k ≥ 1, solo variantes que el registro habilita) el sampler TPE y el sorteo de la muestra de
optimización usan la semilla k y el estudio se llama `<estudio>@k`; las semillas finales no cambian. La réplica 0 es la
optimización de siempre.

`optimizar` corre Optuna (40 trials, AUC en 201908, una semilla) y guarda los mejores hiperparámetros en
`<ledger del estudio>/hp/<estudio>.json`; no carga 201910. `final` entrena con ese JSON sobre 201903-201908 (`MESES_TRAIN_FINAL`) y evalúa en 201910 (curva) para cada
semilla pedida, sin predecir 201908 (`auc_val` y `curva_201908` vacíos) y registrando `meses_final`; saltea las que ya tienen fila válida. Con `--filas N` (o con `--trials` distinto de 40, o con el árbol
sucio) la corrida es exploratoria y va a `<ledger>/exploracion/`, fuera de los resultados.
"""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
import platform
import resource
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import roc_auc_score

from comun import baseline as bl
from comun import variantes
from comun import datos as dt
from comun import ganancia as gn
from comun import ledger as lg
from comun import metodos, muestreo, rutas

log = logging.getLogger("correr")


# --- entorno -------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(rutas.RAIZ), *args], capture_output=True, text=True).stdout.strip()


def commit_y_sucio() -> tuple[str, bool]:
    """Commit corto y si hay cambios sin commitear. Los archivos del ledger no cuentan: cada corrida los agrega.

    En la VM no hay `.git` (vm.sh copia un `git archive` de HEAD, limpio por construcción): el commit llega en
    `COMMIT_REPO`."""
    commit = _git("rev-parse", "--short", "HEAD")
    if not commit:
        return os.environ.get("COMMIT_REPO") or "sin-git", False
    cambios = [l for l in _git("status", "--porcelain", "--untracked-files=all").splitlines() if "/ledger/" not in l]
    return commit, bool(cambios)


def tipo_de_maquina() -> str:
    """`n2-highmem-8` y similares desde el metadata server de GCE; `local` fuera de Google Cloud."""
    try:
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/instance/machine-type",
            headers={"Metadata-Flavor": "Google"},
        )
        with urllib.request.urlopen(req, timeout=0.5) as r:
            return r.read().decode().rsplit("/", 1)[-1]
    except Exception:
        return "local"


def modelo_de_cpu() -> str:
    try:
        for linea in Path("/proc/cpuinfo").read_text().splitlines():
            if linea.startswith("model name"):
                return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    mac = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    return mac or platform.processor() or "desconocida"


def memoria_max_mb() -> float:
    maximo = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(maximo / (1024 * 1024) if sys.platform == "darwin" else maximo / 1024, 1)


def persona() -> str:
    return os.environ.get("PERSONA") or _git("config", "user.name") or getpass.getuser()


# --- utilidades -----------------------------------------------------------------


def auc(y, p) -> float:
    try:
        return float(roc_auc_score(y, p))
    except ValueError:  # un solo valor de clase (solo pasa con muestras de smoke)
        return float("nan")


def semillas_pedidas(texto: str) -> list[int]:
    return bl.SEMILLAS_FINALES if texto == "todas" else [int(s) for s in texto.split(",")]


class Contexto:
    """Lo que cambia entre corrida real y exploratoria: directorios, validez e identificación."""

    def __init__(self, a: argparse.Namespace):
        self.a = a
        self.commit, self.sucio = commit_y_sucio()
        self.explora = bool(a.filas) or a.trials != bl.N_TRIALS
        self.valida = not self.explora and not self.sucio
        self.rel = "exploracion/" if self.explora else ""
        self.etapa = "exploracion" if self.explora else a.etapa
        self.replica = a.replica
        self.semilla_opt = bl.SEMILLA_OPTUNA + self.replica  # sampler TPE y sorteo de la muestra de optimización
        self.metodo = metodos.metodo_optimizacion(a.metodo) if a.etapa == "optimizar" else a.metodo
        self.estudio = variantes.nombre_estudio(metodos.estudio(a.metodo, a.tasa), self.replica)
        self.variante = a.variante or metodos.variante(self.metodo, a.tasa)
        self.dueno = variantes.dueno_variante(self.variante, self.replica)
        self.raiz = rutas.ledger(self.dueno)  # ledger del dueño de la variante: filas y curvas
        self.base = self.raiz / "exploracion" if self.explora else self.raiz
        ledger_estudio = rutas.ledger(variantes.dueno_estudio(self.estudio))  # ledger del dueño del estudio: hp
        self.base_hp = ledger_estudio / "exploracion" if self.explora else ledger_estudio
        sufijo = f"_smoke{a.filas}" if a.filas else ("_exp" if self.explora else "")
        self.db = bl.DATOS_DIR / "optuna" / f"{self.estudio}{sufijo}.db"

    def id(self, semilla: int, etapa: str) -> str:
        if etapa == "final":  # el id del final lleva la ventana de train: nunca choca con uno de otra ronda (D4)
            etapa = f"final-{ventana_corta(bl.MESES_TRAIN_FINAL)}"
        base = f"{variantes.nombre_estudio(self.variante, self.replica)}_{self.metodo}_{self.a.tasa:g}_{semilla}_{etapa}_{self.commit}"
        if self.valida:
            return base
        return f"exp-{base}-{datetime.now():%H%M%S%f}"  # una corrida no válida nunca se saltea

    def fila(self, **kw) -> dict:
        base = {c: None for c in lg.COLUMNAS}
        base.update(
            fecha=datetime.now().isoformat(timespec="seconds"), variante=self.variante, metodo=self.metodo,
            tasa=self.a.tasa, replica_opt=self.replica, etapa=self.etapa, estudio=self.estudio, maquina=tipo_de_maquina(),
            cpu=modelo_de_cpu(), hilos=bl.NUM_THREADS, load_avg=round(os.getloadavg()[0], 2), commit=self.commit,
            codigo_sucio=self.sucio, persona=persona(), valida=self.valida,
        )
        base.update(kw)
        return base

    def ruta_hp(self) -> Path:
        return Path(self.a.hp) if self.a.hp else self.base_hp / "hp" / f"{self.estudio}.json"


def ventana(meses: list[int]) -> str:
    """`201903-201908`: primero y último mes de la ventana de train."""
    return bl.ventana(meses)


def ventana_corta(meses: list[int]) -> str:
    """`0308`: la ventana en el id de un final."""
    return f"{str(meses[0])[4:]}{str(meses[-1])[4:]}"


def _dataset_params() -> dict:
    return {**bl.PARAMS_DATASET, "num_threads": bl.NUM_THREADS}


# --- etapa optimizar --------------------------------------------------------------


def optimizar(cx: Contexto) -> None:
    a = cx.a
    id_ = cx.id(cx.semilla_opt, "optimizar")
    if lg.existe_fila(cx.base / "corridas", id_):
        log.info("ya existe %s: se saltea", id_)
        return
    t0 = time.perf_counter()
    _, t_panel = dt.asegurar_panel(a.filas)
    train = dt.cargar_meses(bl.MESES_TRAIN_OPT, a.filas)
    val = dt.cargar_meses([bl.MES_VALIDACION], a.filas)
    if bl.MES_TEST in dt.MESES_LEIDOS:  # el test no se toca al elegir hiperparámetros
        raise RuntimeError(f"la etapa optimizar leyó {bl.MES_TEST}")
    if 201907 in dt.MESES_LEIDOS:  # 201907 solo entra en el train del final (D1)
        raise RuntimeError("la etapa optimizar leyó 201907")
    cols = dt.columnas_predictoras(train)
    t_sonda = 0.0  # H4H: la sonda que arma el pozo de negativos difíciles cuenta como tiempo de optimización
    if cx.metodo == "clase-dificil":
        pozo, t_sonda = metodos.sonda_pozo(train, cx.semilla_opt)
        datos, params_variante, idx = metodos.clase_dificil(train, a.tasa, cx.semilla_opt, pozo)
    else:
        datos, params_variante, idx = metodos.FUNCIONES_OPT[cx.metodo](train, a.tasa, cx.semilla_opt)
    hash_ = muestreo.hash_muestra(idx, len(train))
    x_tr, y_tr = dt.matriz(datos, cols), datos[dt.Y].to_numpy()
    x_va, y_va = dt.matriz(val, cols), val[dt.Y].to_numpy()
    filas_train = len(datos)
    del train
    t_prep = t_panel + (time.perf_counter() - t0)

    sin_bagging = metodos.sin_bagging_fraction(cx.metodo)
    cx.db.parent.mkdir(parents=True, exist_ok=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        study_name=cx.estudio, storage=f"sqlite:///{cx.db}", direction="maximize", load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=cx.semilla_opt),
    )
    t0 = time.perf_counter()
    dtrain = lgb.Dataset(x_tr, label=y_tr, weight=metodos.pesos(cx.metodo, datos, a.tasa), params=_dataset_params(),
                         free_raw_data=False)  # solo `fast-retrain-opt` lleva pesos; la validación nunca
    dtrain.construct()
    t_dataset = time.perf_counter() - t0
    study.set_user_attr("tiempo_dataset_s", study.user_attrs.get("tiempo_dataset_s", t_dataset))
    study.set_user_attr("tiempo_sonda_s", study.user_attrs.get("tiempo_sonda_s", t_sonda))

    def objetivo(trial: optuna.Trial) -> float:
        hp = bl.sugerir(trial, sin_bagging)
        params = {**bl.PARAMS_FIJOS, **params_variante, **hp, "seed": cx.semilla_opt}
        t = time.perf_counter()
        pred = lgb.train(params, dtrain).predict(x_va)
        trial.set_user_attr("duracion_s", time.perf_counter() - t)
        return auc(y_va, pred)

    def tras_trial(_study, _trial) -> None:
        if a.tras_trial:
            subprocess.run(a.tras_trial.replace("{db}", str(cx.db)), shell=True, check=False)

    hechos = sum(t.state == optuna.trial.TrialState.COMPLETE for t in study.trials)
    log.info("estudio %s: %d de %d trials hechos", cx.estudio, hechos, a.trials)
    if hechos < a.trials:
        study.optimize(objetivo, n_trials=a.trials - hechos, callbacks=[tras_trial])
    completos = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    t_trials = sum(t.user_attrs["duracion_s"] for t in completos)
    t_opt = t_trials + study.user_attrs["tiempo_dataset_s"] + study.user_attrs["tiempo_sonda_s"]
    resumen = {
        "estudio": cx.estudio, "replica_opt": cx.replica, "variante": cx.variante, "metodo": cx.metodo, "tasa": a.tasa, "hp": study.best_params,
        "auc_val": study.best_value, "n_trials": len(completos), "tiempo_trials_s": t_trials,
        "tiempo_dataset_s": study.user_attrs["tiempo_dataset_s"], "tiempo_sonda_s": study.user_attrs["tiempo_sonda_s"],
        "tiempo_optimizacion_s": t_opt,
        "filas_train": filas_train, "hash_muestra": hash_, "commit": cx.commit, "codigo_sucio": cx.sucio,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }
    cx.ruta_hp().parent.mkdir(parents=True, exist_ok=True)
    cx.ruta_hp().write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    lg.escribir_fila(cx.base / "corridas", cx.fila(
        id=id_, semilla=cx.semilla_opt, etapa_corrida="optimizar", hp=json.dumps(study.best_params),
        filas_train=filas_train, hash_muestra=hash_, auc_val=study.best_value, tiempo_preparacion_s=round(t_prep, 3),
        tiempo_optimizacion_s=round(t_opt, 3), memoria_max_mb=memoria_max_mb(),
    ))
    log.info("%s: AUC 201908 %.5f en %.1f s -> %s", cx.estudio, study.best_value, t_opt, cx.ruta_hp())


# --- etapa final --------------------------------------------------------------------


def final(cx: Contexto) -> None:
    a = cx.a
    semillas = semillas_pedidas(a.semilla)
    pendientes = [s for s in semillas if not lg.existe_fila(cx.base / "corridas", cx.id(s, "final"))] if cx.valida else semillas
    if not pendientes:
        log.info("todas las semillas de %s ya tienen fila: se saltea", cx.variante)
        return
    ruta_hp = cx.ruta_hp()
    if not ruta_hp.exists():
        raise FileNotFoundError(f"falta el JSON de hiperparámetros {ruta_hp}: correr --etapa optimizar o pasar --hp")
    hp = metodos.ajustar_hp(cx.metodo, a.tasa, json.loads(ruta_hp.read_text())["hp"])

    t0 = time.perf_counter()
    _, t_panel = dt.asegurar_panel(a.filas)
    train = dt.cargar_meses(bl.MESES_TRAIN_FINAL, a.filas)  # incluye 201908: el final no predice la validación
    test = dt.cargar_meses([bl.MES_TEST], a.filas)
    cols = dt.columnas_predictoras(train)
    x_te, y_te, b2_te = dt.matriz(test, cols), test[dt.Y].to_numpy(), test[dt.BAJA2].to_numpy()
    t_carga = t_panel + (time.perf_counter() - t0)

    for k, semilla in enumerate(pendientes):
        id_ = cx.id(semilla, "final")
        t0 = time.perf_counter()
        datos, params_variante, idx = metodos.FUNCIONES[cx.metodo](train, a.tasa, semilla)
        x_tr, y_tr = dt.matriz(datos, cols), datos[dt.Y].to_numpy()
        t_prep = (t_carga if k == 0 else 0.0) + (time.perf_counter() - t0)
        params = {**bl.PARAMS_FIJOS, **params_variante, **hp, "seed": semilla}

        t0 = time.perf_counter()
        dtrain = lgb.Dataset(x_tr, label=y_tr, weight=metodos.pesos(cx.metodo, datos, a.tasa), params=_dataset_params(),
                             free_raw_data=False)
        dtrain.construct()
        t1 = time.perf_counter()
        modelo = lgb.train(params, dtrain)
        t_lgb = time.perf_counter() - t1
        p_te = modelo.predict(x_te)
        t_ent = time.perf_counter() - t0
        # 201908 está en el train del final: su AUC y su curva serían dentro de la muestra, no se calculan (D3)

        curva_te = gn.curva_de_corte(p_te, b2_te)
        (cx.base / "curvas").mkdir(parents=True, exist_ok=True)
        r_te = f"{cx.rel}curvas/{id_}_{bl.MES_TEST}.csv"
        curva_te.to_csv(cx.raiz / r_te, index=False)
        # D12: predicciones de test en el orden del mes, para ensamblar semillas en la comparación a tiempo igual
        # van a DATOS_DIR, fuera del repo (D18); el ledger guarda la misma ruta relativa de siempre
        r_pred = f"{cx.rel}predicciones/{id_}.parquet"
        (rutas.ledger_datos(cx.dueno) / r_pred).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({
            dt.ID: test[dt.ID].to_numpy().astype(np.int64), "prob": p_te.astype(np.float32), dt.BAJA2: b2_te.astype(np.int8),
        }).to_parquet(rutas.ledger_datos(cx.dueno) / r_pred, index=False)
        envios, g_max = gn.ganancia_maxima(curva_te)
        lg.escribir_fila(cx.base / "corridas", cx.fila(
            id=id_, semilla=semilla, etapa_corrida="final", meses_final=ventana(bl.MESES_TRAIN_FINAL), hp=json.dumps(hp),
            filas_train=len(datos), hash_muestra=muestreo.hash_muestra(idx, len(train)), auc_val=None,
            auc_test=auc(y_te, p_te), ganancia_max_201910=g_max, envios_max_201910=envios, curva_201908=None,
            curva_201910=r_te,
            predicciones_201910=r_pred, tiempo_preparacion_s=round(t_prep, 3), tiempo_optimizacion_s=0.0, tiempo_entrenamiento_s=round(t_ent, 3),
            tiempo_lgbtrain_s=round(t_lgb, 3), memoria_max_mb=memoria_max_mb(),
        ))
        log.info("%s semilla %d: AUC 201910 %.5f, ganancia máx %.0f en %d envíos, %.1f s", cx.variante, semilla,
                 auc(y_te, p_te), g_max, envios, t_ent)


# --- CLI -------------------------------------------------------------------------------


def parsear(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--metodo", required=True)
    p.add_argument("--tasa", type=float, required=True, help="r (uniforme, opt-muestra) o fracción f (bagging)")
    p.add_argument("--semilla", default="0", help="un entero, lista separada por comas o `todas` (las 20 semillas finales)")
    p.add_argument("--etapa", required=True, choices=["optimizar", "final"])
    p.add_argument("--hp", help="JSON de hiperparámetros (por defecto <ledger del dueño del estudio>/hp/<estudio>.json)")
    p.add_argument("--filas", type=int, help="smoke test: panel de ~N filas, corrida exploratoria")
    p.add_argument("--replica", type=int, default=0, help="réplica de optimización k (semilla de TPE y de la muestra; estudio `<estudio>@k`)")
    p.add_argument("--variante", help="nombre de variante si no es el que sale del método (C-rep)")
    p.add_argument("--trials", type=int, default=bl.N_TRIALS, help="solo para pruebas: distinto de 40 es exploratorio")
    p.add_argument("--tras-trial", help="comando que corre tras cada trial; `{db}` es el SQLite del estudio")
    a = p.parse_args(argv)
    try:
        metodos.validar(a.metodo, a.tasa)
        efectivo = metodos.metodo_optimizacion(a.metodo) if a.etapa == "optimizar" else a.metodo
        pedida = a.variante or metodos.variante(a.metodo, a.tasa)
        variantes.validar_replica(pedida, a.replica)  # réplica negativa o no habilitada: falla antes de cargar datos
        variantes.dueno_variante(a.variante or metodos.variante(efectivo, a.tasa), a.replica)  # variante sin dueño: falla antes de cargar datos
        variantes.dueno_estudio(variantes.nombre_estudio(metodos.estudio(a.metodo, a.tasa), a.replica))
        if a.etapa == "optimizar" and a.semilla not in ("0", str(bl.SEMILLA_OPTUNA)):
            raise ValueError(f"--semilla inválida para optimizar: {a.semilla} (la de Optuna es {bl.SEMILLA_OPTUNA})")
        if a.etapa == "final":
            semillas_pedidas(a.semilla)
    except ValueError as e:
        p.error(str(e))
    return a


def main(argv: list[str] | None = None) -> None:
    a = parsear(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", stream=sys.stderr)
    cx = Contexto(a)
    if a.etapa == "optimizar" and cx.metodo != a.metodo:
        log.info("%s no tiene búsqueda propia: se corre la de %s con r=%g (estudio %s)", a.metodo, cx.metodo, a.tasa, cx.estudio)
    (optimizar if a.etapa == "optimizar" else final)(cx)


if __name__ == "__main__":
    main()
