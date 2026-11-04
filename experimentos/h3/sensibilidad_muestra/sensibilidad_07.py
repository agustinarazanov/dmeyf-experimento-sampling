"""07 — Sensibilidad de H3 a la muestra: diez muestras del 25 % del train con las 20 configuraciones de 06.

Exploratorio. Agosto completo ya se usó en 06 para elegir y evaluar; acá se lo parte en dos mitades para medir
cuánto cambia la elección de H3 cuando cambia SOLO qué filas entran en la muestra de búsqueda. Las diez muestras
comparten la misma mitad de evaluación: no son diez tests independientes.

Diseño (se congela en diseno.json antes de entrenar):
  - Datos de `insumos.py`: features (760 predictores en el orden del manifiesto), clase_binaria, train
    201903-201906 y validación 201908. Sólo se leen esos meses; 201909 queda reservado y 201910 es test.
    Las huellas sha256 de claves, y y X (float64) se comparan con `referencia/huellas_datos.json`: son los datos
    exactos de las corridas reportadas (y el mismo orden de train que 06).
  - Partición de 201908: se ordena por (numero_de_cliente, foto_mes) y se parte una vez, estratificada por
    clase_binaria, con default_rng(20261102). En cada clase, floor(n/2) filas van a "seleccion" y el resto a
    "evaluacion". sha256 contra la referencia.
  - Configuraciones: las 20 de 06, versionadas en `referencia/grilla_06.json` y regeneradas (busqueda.py).
  - Modelo: los parámetros fijos de 06 (100 árboles sin early stopping, 4 hilos, bagging_freq=1,
    objective=binary, seed=20261102), con la verificación de parámetros efectivos en cada ajuste.
  - Semillas: partición 20261102; modelo 20261102; muestreo 20261102..20261111, cada una con
    `comun.muestreo.indices_uniformes(n, 0.25, s)` = default_rng(s).choice(n, 126718, replace=False) ordenado, sobre
    el orden del train. sha256 de índices y claves contra la referencia.

Control (una vez): las 20 configuraciones sobre todo el train. Se guardan modelos y predicciones de agosto. Se elige
por AUC en la mitad de selección (a igual AUC, menor id) y el ranking se congela en control_seleccion.json ANTES de
calcular cualquier AUC sobre la mitad de evaluación. Se comprueba que reproduce 06 (`referencia/corrida_06.json`).

H3 (por semilla): las 20 configuraciones sobre la muestra, elección por AUC en la mitad de selección con el mismo
desempate. El modelo final de H3 es el ajuste completo de Control para la configuración elegida (reutilizado, no se
reentrena). Delta = AUC_eval(H3) - AUC_eval(Control).

Reanudación: cada ajuste se agrega a ajustes.jsonl apenas termina (con la huella de sus predicciones).
--reanudar <carpeta> recalcula y compara el diseño y saltea los ajustes hechos.

    python -m experimentos.h3.sensibilidad_muestra.sensibilidad_07 [--salida DIR]
    python -m experimentos.h3.sensibilidad_muestra.sensibilidad_07 --reanudar <carpeta de la corrida>
    python -m experimentos.h3.sensibilidad_muestra.sensibilidad_07 --prueba [--detener-tras N]
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import logging
import os
import platform
import shutil
import sys
import time
from pathlib import Path

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd
import psutil
import sklearn
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from comun import baseline as bl
from comun import muestreo
from experimentos.h3.sensibilidad_muestra import busqueda as B06
from experimentos.h3.sensibilidad_muestra import carga as B05
from experimentos.h3.sensibilidad_muestra import rutas

NOMBRE = "07_sensibilidad_muestra_h3"
PARTICIONES = {"train": list(bl.MESES_TRAIN), "validacion": [bl.MES_VALIDACION]}
MESES_RESERVADOS = {201909: "reservado para un eventual acuerdo grupal", bl.MES_TEST: "test"}
SEMILLA_PARTICION = 20261102
SEMILLA_MODELO = 20261102
SEMILLAS_MUESTRA = [20261102, 20261103, 20261104, 20261105, 20261106,
                    20261107, 20261108, 20261109, 20261110, 20261111]
TASA_MUESTRA = 0.25
FILAS_MUESTRA = 126_718
MITADES = ["seleccion", "evaluacion"]
PRUEBA = {"ids": [2, 12], "semillas": SEMILLAS_MUESTRA[:2]}  # ids con pocas hojas: los ajustes más rápidos de 06
HILOS = B06.HILOS
BLOQUE = 16384
HUELLAS = rutas.REFERENCIA / "huellas_datos.json"
CORRIDA_06 = rutas.REFERENCIA / "corrida_06.json"

log = logging.getLogger("07")


class Detenida(Exception):
    """Corte pedido con --detener-tras (sólo para probar la reanudación)."""


def sha(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def sha_matriz(X) -> str:
    h = hashlib.sha256(str(X.shape).encode())
    for i in range(0, X.shape[0], BLOQUE):
        h.update(np.ascontiguousarray(X[i:i + BLOQUE]).tobytes())
    return h.hexdigest()


def sha_archivo(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def escribir_json(p: Path, d) -> None:
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def leer_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def copiar_parquet(df: pd.DataFrame, destino: Path) -> None:
    c = duckdb.connect()
    c.register("df", df)
    c.execute(f"COPY (SELECT * FROM df) TO '{destino.as_posix()}' (FORMAT parquet)")
    c.close()


def leer_parquet(p: Path) -> dict:
    c = duckdb.connect()
    c.execute("SET threads = 1")
    r = c.execute(f"SELECT * FROM read_parquet('{p.as_posix()}')").fetchnumpy()
    c.close()
    return r


def borrar(p: Path, intentos: int = 15) -> bool:
    """Borra un archivo o carpeta reintentando: el antivirus abre los archivos recién escritos."""
    for _ in range(intentos):
        try:
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
            return True
        except OSError:
            time.sleep(2)
    log.warning("no se pudo borrar %s", p)
    return False


class Sesion:
    """Tiempo de pared y memoria por etapa de esta sesión, en sesiones.json (una entrada por sesión)."""

    def __init__(self, run: Path, proc, reanudacion: bool):
        self.path, self.proc = run / "sesiones.json", proc
        self.todas = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        self.d = {"pid": os.getpid(), "inicio": time.strftime("%Y-%m-%dT%H:%M:%S"), "reanudacion": reanudacion,
                  "etapas": {}, "ajustes_nuevos": 0}
        self.todas.append(self.d)
        self.t = time.perf_counter()

    def etapa(self, nombre: str, **extra) -> None:
        ahora = time.perf_counter()
        self.d["etapas"][nombre] = {"segundos": round(ahora - self.t, 1), "hora": time.strftime("%H:%M:%S"),
                                    **B05.memoria(self.proc), **extra}
        self.t = ahora
        self.guardar()
        log.info("[%s] %.1fs | %s", nombre, self.d["etapas"][nombre]["segundos"], B05.memoria(self.proc))

    def guardar(self, **extra) -> None:
        self.d.update(extra)
        escribir_json(self.path, self.todas)


# --- diseño --------------------------------------------------------------------------------------


def particionar(cli: np.ndarray, mes: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, dict, pd.DataFrame]:
    """Mitad (0 selección, 1 evaluación) por fila de agosto, en el orden de carga; estratificada por clase."""
    orden = np.lexsort((mes, cli))  # por numero_de_cliente y foto_mes
    rng = np.random.default_rng(SEMILLA_PARTICION)
    mitad = np.full(len(y), -1, np.int8)
    for c in (0, 1):
        pos = orden[y[orden] == c]
        perm = rng.permutation(len(pos))
        k = len(pos) // 2
        mitad[pos[perm[:k]]] = 0
        mitad[pos[perm[k:]]] = 1
    claves = set(zip(cli.tolist(), mes.tolist()))
    sel = set(zip(cli[mitad == 0].tolist(), mes[mitad == 0].tolist()))
    ev = set(zip(cli[mitad == 1].tolist(), mes[mitad == 1].tolist()))
    checks = {"claves_unicas": len(claves) == len(y), "todas_asignadas": bool((mitad >= 0).all()),
              "disjuntas": not (sel & ev), "cubren_agosto": (sel | ev) == claves}
    tabla = pd.DataFrame({"numero_de_cliente": cli[orden], "foto_mes": mes[orden],
                          "mitad": np.array(MITADES)[mitad[orden]]})
    conteos = {m: {"filas": int((mitad == i).sum()), "positivos": int(y[mitad == i].sum()),
                   "negativos": int((y[mitad == i] == 0).sum())} for i, m in enumerate(MITADES)}
    info = {"mes": PARTICIONES["validacion"], "semilla": SEMILLA_PARTICION,
            "metodo": "orden por (numero_de_cliente, foto_mes); por clase binaria (0 y después 1), "
                      "default_rng(semilla).permutation; floor(n/2) a selección y el resto a evaluación",
            "conteos": conteos, "checks": checks,
            "sha256": sha(cli[orden], mes[orden], mitad[orden])}
    ref = leer_json(HUELLAS)["particion_201908"]
    checks["igual_a_la_referencia"] = info["sha256"] == ref["sha256"] and conteos == ref["conteos"]
    if not all(checks.values()):
        raise RuntimeError(f"partición inválida: {checks}")
    return mitad, info, tabla


def muestras(n: int, y: np.ndarray, mes: np.ndarray, cli: np.ndarray, semillas: list[int]) -> dict:
    """Muestras de H3 con `comun.muestreo`, comprobadas contra el generador de 07 y contra la referencia."""
    ref = leer_json(HUELLAS)["muestras"]
    out = {}
    for s in semillas:
        idx = np.asarray(muestreo.indices_uniformes(n, TASA_MUESTRA, s), np.int64)
        original = np.sort(np.random.default_rng(s).choice(n, size=FILAS_MUESTRA, replace=False)).astype(np.int64)
        if len(idx) != FILAS_MUESTRA or not np.array_equal(idx, original):
            raise RuntimeError(f"semilla {s}: comun.muestreo no reproduce el generador de 07")
        info = {"semilla": s, "generador": "default_rng(semilla).choice(n, k, replace=False), índices ordenados "
                                           "(comun.muestreo.indices_uniformes(n, 0.25, semilla))",
                "filas": int(len(idx)), "positivos": int(y[idx].sum()),
                "filas_por_mes": {str(m): int((mes[idx] == m).sum()) for m in PARTICIONES["train"]},
                "sha256_indices": sha(idx), "sha256_claves": sha(cli[idx], mes[idx])}
        r = ref[str(s)]
        if any(info[k] != r[k] for k in ("filas", "positivos", "filas_por_mes", "sha256_indices", "sha256_claves")):
            raise RuntimeError(f"semilla {s}: la muestra no es la de las corridas reportadas")
        out[s] = {"idx": idx, "info": info}
    return out


def comparar_diseno(previo: dict, actual: dict) -> None:
    claves = ["modo", "datos", "particion", "configuraciones", "semillas", "muestras", "modelo"]
    malos = [k for k in claves if json.loads(json.dumps(previo.get(k), default=str))
             != json.loads(json.dumps(actual.get(k), default=str))]
    if malos:
        raise RuntimeError(f"la reanudación no coincide con el diseño guardado en: {malos}")
    if previo.get("script_sha256") != actual.get("script_sha256"):
        log.warning("el script cambió desde la sesión anterior (sha256 distinto); el diseño sí coincide")


# --- datos ---------------------------------------------------------------------------------------


def preparar(mats: Path, proc) -> tuple[dict, dict]:
    """Carga validada (carga.py): unión 1:1, BIGINT -> float64 exacto, NULL -> NaN, memmaps; huellas contra la referencia."""
    con = duckdb.connect()
    con.execute(f"SET threads = {HILOS}")
    con.execute("SET memory_limit = '1GB'")
    con.execute("SET preserve_insertion_order = true")
    con.execute(f"SET temp_directory = '{(mats / 'duckdb').as_posix()}'")
    manifest_path = rutas.features_dir() / "manifiesto.json"
    pred = leer_json(manifest_path)["predictores"]
    meses = sorted(m for ms in PARTICIONES.values() for m in ms)
    if set(meses) & set(MESES_RESERVADOS) or len(pred) != 760:
        raise RuntimeError("meses o predictores fuera del diseño")
    tipos = {c: t for c, t, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet({B05.archivos(meses)})").fetchall()}
    union = {p: B05.validar_union(con, ms) for p, ms in PARTICIONES.items()}
    for p, u in union.items():
        if not all(u["checks"].values()):
            raise RuntimeError(f"unión {p} inválida: {u['checks']}")
    perfil = {p: B05.perfil_tipos(con, ms, pred, tipos) for p, ms in PARTICIONES.items()}
    if not all(v["bigint_exacto_en_float64"] for v in perfil.values()):
        raise RuntimeError("hay BIGINT con |x| > 2^53")
    datos = {}
    for p, ms in PARTICIONES.items():
        X, cli, mes = B05.cargar(con, ms, pred, tipos, mats / f"X_{p}.npy")
        y, _ = B05.etiquetas(con, ms, cli, mes)
        datos[p] = {"X": X, "y": y, "cli": cli, "mes": mes}
    con.close()
    leidos = sorted({int(m) for d in datos.values() for m in np.unique(d["mes"])})
    if leidos != meses:
        raise RuntimeError(f"se leyeron meses fuera del diseño: {leidos}")

    # Mismos datos y mismo orden que las corridas reportadas (y que 06): huellas sha256 versionadas
    t = time.perf_counter()
    huellas = {p: {"filas": int(len(d["y"])), "positivos": int(d["y"].sum()), "sha256_claves": sha(d["cli"], d["mes"]),
                   "sha256_y": sha(d["y"]), "sha256_X": sha_matriz(d["X"])} for p, d in datos.items()}
    ref = leer_json(HUELLAS)
    sha_pred = B06.sha256_bytes(json.dumps(pred).encode())
    iguales = {p: huellas[p] == ref[p] for p in PARTICIONES}
    if not all(iguales.values()) or sha_pred != ref["predictores"]["sha256"]:
        raise RuntimeError(f"BLOQUEO: los datos no son los de las corridas reportadas: {iguales}, predictores "
                           f"{sha_pred == ref['predictores']['sha256']}; ver insumos.py")
    info = {"meses_leidos": leidos, "meses_reservados": MESES_RESERVADOS, "predictores": len(pred),
            "sha256_predictores": sha_pred, "sha256_manifiesto": sha_archivo(manifest_path), "huellas": huellas,
            "orden_train_igual_a_06": iguales["train"], "union": union, "tipos": perfil,
            "huella_X_s": round(time.perf_counter() - t, 1)}
    datos["pred"] = pred
    return datos, info


# --- ajustes -------------------------------------------------------------------------------------


def leer_ajustes(run: Path) -> dict:
    """Ajustes terminados, con sus predicciones verificadas por huella. Clave: (brazo, semilla de muestra, id)."""
    hechos = {}
    p = run / "ajustes.jsonl"
    if not p.exists():
        return hechos
    for linea in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(linea)
        archivo = run / r["predicciones"]
        if not archivo.exists() or sha(np.load(archivo)) != r["sha256_predicciones"]:
            raise RuntimeError(f"el ajuste {r['brazo']} {r['semilla_muestra']} {r['id']} no tiene sus predicciones")
        hechos[(r["brazo"], r["semilla_muestra"], r["id"])] = r
    return hechos


def ajustar(run: Path, brazo: str, semilla: int | None, cfg: dict, X, y, datos: dict, sel: np.ndarray) -> dict:
    """Un ajuste: entrena, verifica parámetros, predice agosto y guarda su checkpoint."""
    params = B06.params_de(cfg)
    booster, tiempos = B06.ajustar(X, y, datos["pred"], params)
    ef = B06.efectivos(booster)
    B06.verificar_parametros(params, ef)
    t = time.perf_counter()
    prob = booster.predict(datos["validacion"]["X"], num_threads=HILOS)
    tiempos["prediccion_s"] = round(time.perf_counter() - t, 1)
    tiempos["total_s"] = round(tiempos["dataset_s"] + tiempos["entrenamiento_s"] + tiempos["prediccion_s"], 1)
    if not (np.isfinite(prob).all() and ((prob >= 0) & (prob <= 1)).all()):
        raise RuntimeError("probabilidades fuera de [0, 1]")
    yv = datos["validacion"]["y"]
    if brazo == "control":
        rel = f"control/pred_{cfg['id']:02d}.npy"  # todo agosto, en el orden de carga
        booster.save_model(str(run / "control" / f"modelo_{cfg['id']:02d}.txt"))
        guardar = prob
    else:
        rel = f"h3/{semilla}/pred_seleccion_{cfg['id']:02d}.npy"  # sólo la mitad de selección
        guardar = prob[sel]
    np.save(run / rel, guardar)
    r = {"brazo": brazo, "semilla_muestra": semilla, "id": cfg["id"], "params": params,
         "filas_entrenamiento": int(len(y)), "positivos_entrenamiento": int(y.sum()),
         "auc_seleccion": float(roc_auc_score(yv[sel], prob[sel])),
         "predicciones": rel, "sha256_predicciones": sha(guardar), "tiempos": tiempos,
         "memoria": B05.memoria(psutil.Process()), "parametros_verificados": True,
         "hora": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if brazo == "control":
        r["parametros_efectivos"] = ef
    with open(run / "ajustes.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log.info("%-7s %-8s cfg %02d | AUC sel %.6f | %s", brazo, semilla or "", cfg["id"], r["auc_seleccion"], tiempos)
    del booster, prob
    gc.collect()
    return r


def ranking(filas: list[dict]) -> list[dict]:
    """Mayor AUC de selección primero; a igual AUC, menor id."""
    orden = sorted(filas, key=lambda r: (-r["auc_seleccion"], r["id"]))
    return [{"posicion": i + 1, "id": r["id"], "auc_seleccion": r["auc_seleccion"]} for i, r in enumerate(orden)]


def congelar_control(run: Path, ctrl: dict[int, dict]) -> dict:
    """Ranking y ganadora de Control, escritos antes de mirar la mitad de evaluación."""
    rk = ranking(list(ctrl.values()))
    d = {"criterio": "mayor AUC en la mitad de selección de 201908; a igual AUC, menor id",
         "ranking": rk, "ganadora": rk[0]["id"], "sha256": B06.sha256_bytes(json.dumps(rk).encode())}
    p = run / "control_seleccion.json"
    if p.exists():
        previo = leer_json(p)
        if previo["sha256"] != d["sha256"]:
            raise RuntimeError("el ranking de Control no coincide con el congelado")
        return previo
    d["congelado"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    escribir_json(p, d)
    log.info("Control congelado: ganadora cfg %d (AUC sel %.6f)", d["ganadora"], rk[0]["auc_seleccion"])
    return d


def evaluar_control(run: Path, ctrl: dict[int, dict], datos: dict, mitad: np.ndarray, seleccion: dict) -> dict:
    """AUC en la mitad de evaluación de los ajustes completos, y reproducción de 06 sobre agosto completo."""
    if not (run / "control_seleccion.json").exists():
        raise RuntimeError("el ranking de Control tiene que estar congelado antes de evaluar")
    yv, ev = datos["validacion"]["y"], mitad == 1
    preds = {i: np.load(run / r["predicciones"]) for i, r in ctrl.items()}
    ref06 = leer_json(CORRIDA_06)
    auc06 = {int(k): v for k, v in ref06["auc_validacion_control"].items()}
    if sha(datos["validacion"]["cli"], datos["validacion"]["mes"]) != ref06["sha256_claves_validacion"]:
        raise RuntimeError("agosto no está en el orden de carga de 06")
    finales06 = {f["config_id"]: (b, f) for b, f in ref06["finales"].items()}
    por_cfg, repro = {}, {}
    for i, p in preds.items():
        auc_ag = float(roc_auc_score(yv, p))
        por_cfg[i] = {"auc_evaluacion": float(roc_auc_score(yv[ev], p[ev])), "auc_agosto_completo": auc_ag}
        repro[i] = {"auc_06": auc06[i], "auc_07": auc_ag, "igual": auc_ag == auc06[i]}
        if i in finales06:
            b, f = finales06[i]
            repro[i].update({"final_06": b, "prob_igual_a_06": sha(np.asarray(p, np.float64)) == f["sha256_prob_201908"],
                             "parametros_efectivos_iguales": f["parametros_efectivos"] == ctrl[i]["parametros_efectivos"]})
    g = seleccion["ganadora"]
    d = {"auc_evaluacion_ganadora": por_cfg[g]["auc_evaluacion"], "ganadora": g,
         "por_configuracion": {str(i): v for i, v in sorted(por_cfg.items())},
         "reproduccion_06": {str(i): v for i, v in sorted(repro.items())},
         "reproduce_06": all(v["igual"] and v.get("prob_igual_a_06", True) and v.get("parametros_efectivos_iguales", True)
                             for v in repro.values())}
    escribir_json(run / "control_evaluacion.json", d)
    tabla = pd.DataFrame({"numero_de_cliente": datos["validacion"]["cli"], "foto_mes": datos["validacion"]["mes"],
                          "mitad": np.array(MITADES)[mitad],
                          **{f"prob_cfg_{i:02d}": preds[i] for i in sorted(preds)}})
    copiar_parquet(tabla, run / "control" / "predicciones_201908.parquet")
    log.info("Control: AUC evaluación de la ganadora %.6f | reproduce 06: %s", d["auc_evaluacion_ganadora"],
             d["reproduce_06"])
    return d


def matriz_muestra(Xt, idx: np.ndarray, destino: Path):
    Xh = np.lib.format.open_memmap(destino, mode="w+", dtype=np.float64, shape=(len(idx), Xt.shape[1]))
    for i in range(0, len(idx), BLOQUE):
        Xh[i:i + BLOQUE] = Xt[idx[i:i + BLOQUE]]
    Xh.flush()
    return Xh


def buscar_h3(run: Path, mats: Path, s: int, idx: np.ndarray, configs: list[dict], hechos: dict, datos: dict,
              sel: np.ndarray, contar) -> None:
    """Las configuraciones pendientes de una semilla, sobre su muestra (memmap que se borra al terminar)."""
    pendientes = [c for c in configs if ("h3", s, c["id"]) not in hechos]
    if not pendientes:
        return
    (run / "h3" / str(s)).mkdir(parents=True, exist_ok=True)
    destino = mats / f"X_h3_{s}.npy"
    t = time.perf_counter()
    Xh = matriz_muestra(datos["train"]["X"], idx, destino)
    yh = datos["train"]["y"][idx]
    log.info("muestra %d: %d filas, %d positivos | matriz en %.1fs", s, len(idx), int(yh.sum()), time.perf_counter() - t)
    try:
        for cfg in pendientes:
            hechos[("h3", s, cfg["id"])] = ajustar(run, "h3", s, cfg, Xh, yh, datos, sel)
            contar()
    finally:
        del Xh
        gc.collect()
        borrar(destino)


# --- resumen -------------------------------------------------------------------------------------


def resumir(run: Path, configs: list[dict], semillas: list[int], hechos: dict, sel_ctrl: dict, ev_ctrl: dict,
            info_muestras: dict) -> dict:
    ids = [c["id"] for c in configs]
    pos_ctrl = {r["id"]: r["posicion"] for r in sel_ctrl["ranking"]}
    auc_sel_ctrl = np.array([hechos[("control", None, i)]["auc_seleccion"] for i in ids])
    auc_ev = {int(k): v["auc_evaluacion"] for k, v in ev_ctrl["por_configuracion"].items()}
    g = sel_ctrl["ganadora"]
    filas = []
    for s in semillas:
        h = [hechos[("h3", s, i)] for i in ids]
        rk = ranking(h)
        e = rk[0]["id"]
        rho = spearmanr(auc_sel_ctrl, [r["auc_seleccion"] for r in h]).statistic
        filas.append({
            "semilla_muestra": s, "positivos_muestra": info_muestras[s]["positivos"], "config_h3": e,
            "posicion_en_control": pos_ctrl[e], "auc_seleccion_h3": rk[0]["auc_seleccion"],
            "auc_final_h3": auc_ev[e], "auc_final_control": auc_ev[g], "delta": auc_ev[e] - auc_ev[g],
            "spearman_seleccion": float(rho),
            "tiempo_busqueda_s": round(sum(r["tiempos"]["total_s"] for r in h), 1),
            "final_h3": "reutilizado (ajuste completo de Control)",
            "tiempo_ajuste_completo_reutilizado_s": hechos[("control", None, e)]["tiempos"]["total_s"]})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(run / "resumen_por_semilla.csv", index=False)

    def rango(col):
        v = tabla[col].to_numpy(dtype=float)
        return {"mediana": float(np.median(v)), "min": float(v.min()), "max": float(v.max())}

    frec = tabla["config_h3"].value_counts().sort_index()
    return {
        "filas": filas,
        "delta": rango("delta"), "tiempo_busqueda_s": rango("tiempo_busqueda_s"),
        "spearman_seleccion": rango("spearman_seleccion"),
        "veces_que_h3_elige_la_ganadora_de_control": int((tabla["config_h3"] == g).sum()),
        "frecuencia_por_configuracion": {str(int(k)): int(v) for k, v in frec.items()},
        "tiempo_control_20_ajustes_s": round(sum(hechos[("control", None, i)]["tiempos"]["total_s"] for i in ids), 1),
    }


# --- principal -----------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sensibilidad de H3 a la muestra de búsqueda (exploratorio).")
    ap.add_argument("--salida", type=Path, default=None,
                    help="carpeta de ejecuciones (por defecto DATOS_DIR/h3_sensibilidad_muestra/ejecuciones)")
    ap.add_argument("--reanudar", type=Path, help="carpeta de una corrida previa de 07")
    ap.add_argument("--prueba", action="store_true", help=f"prueba corta: cfg {PRUEBA['ids']}, 2 semillas, otra carpeta")
    ap.add_argument("--detener-tras", type=int, help="corta tras N ajustes nuevos (para probar la reanudación)")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    proc = psutil.Process()
    salida = (a.salida or rutas.salida_por_defecto()).resolve()

    if a.reanudar:
        run = a.reanudar.resolve()
        if not (run / "diseno.json").exists():
            raise FileNotFoundError(f"{run} no es una corrida de 07")
        previo = leer_json(run / "diseno.json")
        prueba = previo["modo"] == "prueba"
        if a.prueba and not prueba:
            raise RuntimeError("--prueba no corresponde a esta carpeta")
    else:
        prueba = a.prueba
        run = salida / (NOMBRE + ("_prueba" if prueba else "")) / f"{time.strftime('%Y%m%dT%H%M%S')}_{os.getpid()}"
        run.mkdir(parents=True, exist_ok=False)
        previo = None
    mats = run / "matrices_tmp"
    mats.mkdir(exist_ok=True)
    (run / "control").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S",
                        handlers=[logging.FileHandler(run / "log.txt", encoding="utf-8"),
                                  logging.StreamHandler(sys.stdout)])
    log.info("Corrida %s | %s | %s", run.as_posix(), "reanudación" if a.reanudar else "nueva",
             "PRUEBA" if prueba else "completa")
    sesion = Sesion(run, proc, bool(a.reanudar))

    todas, huella_cfg = B06.cargar_grilla()
    configs = [c for c in todas if c["id"] in PRUEBA["ids"]] if prueba else todas
    semillas = PRUEBA["semillas"] if prueba else SEMILLAS_MUESTRA
    assert SEMILLA_MODELO == B06.SEMILLA == B06.FIJOS["seed"] and B06.FIJOS["num_threads"] == 4

    datos = None
    nuevos = 0

    def contar():
        nonlocal nuevos
        nuevos += 1
        sesion.guardar(ajustes_nuevos=nuevos)
        if a.detener_tras and nuevos >= a.detener_tras:
            raise Detenida(f"corte pedido tras {nuevos} ajustes nuevos")

    try:
        datos, info_datos = preparar(mats, proc)
        sesion.etapa("carga_y_validacion", huella_X_s=info_datos["huella_X_s"])
        v, tr = datos["validacion"], datos["train"]
        mitad, info_part, tabla_part = particionar(v["cli"], v["mes"], v["y"])
        sel = np.flatnonzero(mitad == 0)
        ms = muestras(len(tr["y"]), tr["y"], tr["mes"], tr["cli"], semillas)
        diseno = {
            "naturaleza": "exploratorio: sensibilidad de H3 a la muestra; agosto completo ya se usó en 06; "
                          "las muestras comparten la mitad de evaluación y no son tests independientes",
            "modo": "prueba" if prueba else "completa",
            "particiones": PARTICIONES, "meses_reservados": MESES_RESERVADOS,
            "datos": {k: info_datos[k] for k in ("meses_leidos", "predictores", "sha256_predictores",
                                                  "sha256_manifiesto", "huellas", "orden_train_igual_a_06")},
            "particion": {k: info_part[k] for k in ("semilla", "metodo", "conteos", "sha256")},
            "configuraciones": {"origen": "experimentos/h3/sensibilidad_muestra/referencia/grilla_06.json",
                                "sha256_las_20": huella_cfg,
                                "ids": [c["id"] for c in configs], "configuraciones": configs},
            "semillas": {"particion": SEMILLA_PARTICION, "modelo": SEMILLA_MODELO, "muestreo": semillas},
            "muestras": {str(s): m["info"] for s, m in ms.items()},
            "modelo": {"fijos": B06.FIJOS, "arboles": B06.ARBOLES, "early_stopping": False},
            "criterio": "mayor AUC en la mitad de selección; a igual AUC, menor id; final de H3 = ajuste completo "
                        "de Control de la configuración elegida; delta = AUC_eval(H3) - AUC_eval(Control)",
            "script_sha256": sha_archivo(Path(__file__)),
        }
        if previo is not None:
            comparar_diseno(previo, diseno)
            log.info("diseño verificado contra la sesión anterior")
        else:
            escribir_json(run / "diseno.json", diseno)
            escribir_json(run / "particion_201908.json", info_part)
            copiar_parquet(tabla_part, run / "particion_201908.parquet")
            (run / "muestras").mkdir()
            for s, m in ms.items():
                np.save(run / "muestras" / f"indices_{s}.npy", m["idx"])
                copiar_parquet(pd.DataFrame({"numero_de_cliente": tr["cli"][m["idx"]], "foto_mes": tr["mes"][m["idx"]]}),
                               run / "muestras" / f"claves_{s}.parquet")
                escribir_json(run / "muestras" / f"muestra_{s}.json", m["info"])
        log.info("partición %s | muestras %s", info_part["conteos"],
                 {s: m["info"]["positivos"] for s, m in ms.items()})
        sesion.etapa("diseno")

        hechos = leer_ajustes(run)
        log.info("ajustes ya completados: %d de %d", len(hechos), len(configs) * (1 + len(semillas)))
        for cfg in configs:
            if ("control", None, cfg["id"]) not in hechos:
                hechos[("control", None, cfg["id"])] = ajustar(run, "control", None, cfg, tr["X"], tr["y"], datos, sel)
                contar()
        ctrl = {c["id"]: hechos[("control", None, c["id"])] for c in configs}
        sesion.etapa("control")
        sel_ctrl = congelar_control(run, ctrl)
        ev_ctrl = evaluar_control(run, ctrl, datos, mitad, sel_ctrl)
        sesion.etapa("control_evaluacion")

        for s in semillas:
            buscar_h3(run, mats, s, ms[s]["idx"], configs, hechos, datos, sel, contar)
            sesion.etapa(f"h3_{s}")

        res = resumir(run, configs, semillas, hechos, sel_ctrl, ev_ctrl, {s: m["info"] for s, m in ms.items()})
        rep = {
            "naturaleza": diseno["naturaleza"], "modo": diseno["modo"],
            "versiones": {"python": sys.version.split()[0], "plataforma": platform.platform(),
                          "procesador": platform.processor(), "nucleos_logicos": psutil.cpu_count(),
                          "ram_gb": round(psutil.virtual_memory().total / 2**30, 1), "lightgbm": lgb.__version__,
                          "sklearn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__,
                          "duckdb": duckdb.__version__},
            "datos": {"union": info_datos["union"], "tipos": info_datos["tipos"], **diseno["datos"]},
            "particion": info_part, "semillas": diseno["semillas"],
            "control": {"seleccion": sel_ctrl, "evaluacion": ev_ctrl},
            "resultado": res,
            "tiempos": {"control_20_ajustes_s": res["tiempo_control_20_ajustes_s"],
                        "busqueda_por_semilla_s": {str(f["semilla_muestra"]): f["tiempo_busqueda_s"] for f in res["filas"]},
                        "sesiones": "sesiones.json (pared y memoria por etapa)"},
            "memoria": B05.memoria(proc),
        }
        escribir_json(run / "reporte.json", rep)
        sesion.etapa("resumen")
        log.info("delta mediana %.6f [%.6f, %.6f] | elige la ganadora de Control %d de %d | Spearman mediana %.3f",
                 res["delta"]["mediana"], res["delta"]["min"], res["delta"]["max"],
                 res["veces_que_h3_elige_la_ganadora_de_control"], len(semillas), res["spearman_seleccion"]["mediana"])
        log.info("Salida para ganancia_08: --corrida-07 %s", run.as_posix())
        codigo = 0
    except Detenida as e:
        log.warning("%s. Reanudar con: python -m experimentos.h3.sensibilidad_muestra.sensibilidad_07 --reanudar %s",
                    e, run.as_posix())
        codigo = 3
    finally:
        # cierra los memmaps antes de borrar los temporales: vaciar los dicts también suelta las referencias de tr y v
        for d in (datos or {}).values():
            if isinstance(d, dict):
                d.clear()
        datos = None
        gc.collect()
        borrado = borrar(mats)
        sesion.guardar(fin=time.strftime("%Y-%m-%dT%H:%M:%S"), total_s=round(time.perf_counter() - t0, 1),
                       temporales_borrados=borrado, memoria_fin=B05.memoria(proc))
    log.info("Fin (código %d) en %.1fs", codigo, time.perf_counter() - t0)
    return codigo


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.exception("la corrida falló; se puede reanudar con --reanudar")
        raise
