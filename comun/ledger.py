"""Ledger como archivos: una fila por corrida, consolidación y tablas apareadas por semilla.

Cada corrida escribe `<ledger>/corridas/<id>.csv`; `consolidar` arma `resultados.csv` (solo corridas válidas, sin
duplicados por clave) y `apareado.csv` (diferencia contra el control por semilla). Las reglas de decisión son las de
`docs/hipotesis.md` y el cálculo, el de `docs/diseno.md` § Métricas.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy import stats

#: Columnas obligatorias de cada fila (`specs/ledger-resultados`). Sin valor se escribe vacío, pero la columna tiene que
#: estar: una fila a la que le falta una no se escribe.
COLUMNAS: list[str] = [
    "id", "fecha", "variante", "metodo", "tasa", "semilla", "replica_opt", "etapa", "etapa_corrida", "estudio", "meses_final", "hp",
    "filas_train", "hash_muestra", "auc_val", "auc_test", "ganancia_max_201910", "envios_max_201910",
    "curva_201908", "curva_201910", "predicciones_201910",
    "tiempo_preparacion_s", "tiempo_optimizacion_s", "tiempo_entrenamiento_s", "tiempo_lgbtrain_s",
    "memoria_max_mb", "maquina", "cpu", "hilos", "load_avg", "commit", "codigo_sucio", "persona", "valida",
]
#: Sin `commit`: la misma semilla no puede contar dos veces; una repetición con código más nuevo reemplaza a la anterior.
#: `meses_final` separa las rondas: un final de 201903-201908 no reemplaza a uno de 201903-201906 (D4).
CLAVE: list[str] = ["variante", "metodo", "tasa", "replica_opt", "semilla", "etapa", "meses_final"]
#: Ventana de train de los finales anteriores al cambio `final-con-julio-agosto`.
MESES_FINAL_VIEJA = "201903-201906"
CONTROL = "C"
#: Variantes que no entran en Δ: el control y su réplica (`docs/diseno.md` § Grilla).
SIN_DELTA = {"C", "C-rep"}
DELTA_REL = 0.02  # δ = 2% de la ganancia media del control


def escribir_fila(directorio: Path, fila: dict) -> Path:
    """Escribe `<directorio>/<id>.csv`. Falla nombrando la columna que falta (o la que sobra) sin escribir nada."""
    faltan = [c for c in COLUMNAS if c not in fila]
    if faltan:
        raise ValueError(f"fila de ledger incompleta, falta la columna: {', '.join(faltan)}")
    sobran = [c for c in fila if c not in COLUMNAS]
    if sobran:
        raise ValueError(f"fila de ledger con columna que no es del esquema: {', '.join(sobran)}")
    if fila["etapa_corrida"] == "final" and (fila["meses_final"] is None or str(fila["meses_final"]).strip() in ("", "nan")):
        raise ValueError("fila final de ledger sin `meses_final`: la ventana de train del final es obligatoria")
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / f"{fila['id']}.csv"
    parcial = destino.with_suffix(".csv.tmp")
    pd.DataFrame([{c: fila[c] for c in COLUMNAS}]).to_csv(parcial, index=False)
    os.replace(parcial, destino)
    return destino


def existe_fila(directorio: Path, id_corrida: str) -> bool:
    return (directorio / f"{id_corrida}.csv").exists()


def leer_csv(ruta: Path) -> pd.DataFrame:
    """Lee un CSV de ledger. Una cabecera `brazo` (nombre anterior de `variante`, `renombrar-brazos` D2) no se traduce:
    falla nombrando el archivo, para que un ledger viejo no entre en silencio a una consolidación nueva."""
    tabla = pd.read_csv(ruta)
    if "brazo" in tabla.columns:
        raise ValueError(f"{ruta}: la columna 'brazo' se llama 'variante' desde renombrar-brazos; "
                         "migrar con scripts/renombrar_columna.py")
    return tabla


def leer_corridas(directorio: Path) -> pd.DataFrame:
    archivos = sorted(directorio.glob("*.csv"))
    if not archivos:
        return pd.DataFrame(columns=COLUMNAS)
    # Las filas anteriores a D12 no tienen `predicciones_201910`: se leen con la columna vacía.
    corridas = pd.concat([leer_csv(a) for a in archivos], ignore_index=True)
    corridas = corridas.reindex(columns=list(dict.fromkeys([*COLUMNAS, *corridas.columns])))
    # Las filas anteriores a las réplicas (`h3-semillas-optuna`) no tienen `replica_opt`: son la réplica 0.
    corridas["replica_opt"] = corridas["replica_opt"].fillna(0).astype(int)
    return corridas


# --- consolidación ------------------------------------------------------------


def consolidar_corridas(corridas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(resultados, reemplazadas). Solo corridas `valida`; por clave se queda la más reciente.

    Las anteriores van a `reemplazadas` con el id de la que las reemplazó.
    """
    if corridas.empty:
        return corridas.copy(), corridas.assign(reemplazada_por=pd.Series(dtype=str))
    c = corridas[corridas["valida"].astype(str).str.lower().eq("true") & corridas["etapa"].isin(["optimizar", "final"])]
    c = c.sort_values(["fecha", "id"]).reset_index(drop=True)
    ultima = c.groupby(CLAVE, dropna=False)["id"].transform("last")
    quedan = c["id"] == ultima
    reemplazadas = c[~quedan].assign(reemplazada_por=ultima[~quedan])
    resultados = c[quedan].sort_values(["etapa", "variante", "semilla", "commit"]).reset_index(drop=True)
    return resultados, reemplazadas.reset_index(drop=True)


# --- ganancia al corte N* ------------------------------------------------------


def leer_curva(base: Path, ruta: str) -> pd.DataFrame:
    return pd.read_csv(base / ruta)


def corte_control(finales: pd.DataFrame, leer) -> int:
    """N*: el N que maximiza la ganancia media de las curvas de `C` en 201908 (`leer(ruta)` devuelve la curva)."""
    curvas = [leer(r).set_index("envios")["ganancia"] for r in finales.loc[finales["variante"] == CONTROL, "curva_201908"]]
    if not curvas:
        raise ValueError("no hay corridas finales del control (variante C): no se puede fijar N*")
    media = pd.concat(curvas, axis=1).mean(axis=1)
    return int(media.idxmax())


def agregar_ganancia(finales: pd.DataFrame, leer, n_estrella: int) -> pd.DataFrame:
    """Agrega `g` = ganancia en 201910 al corte `n_estrella`, leída de la curva guardada de cada corrida."""
    def en_corte(ruta: str) -> float:
        curva = leer(ruta).set_index("envios")["ganancia"]
        return float(curva.loc[n_estrella])
    return finales.assign(g=finales["curva_201910"].map(en_corte))


# --- veredicto y apareado ------------------------------------------------------


def veredicto(delta_media: float, ic_inf: float, delta: float) -> str:
    """Los cuatro casos de `hipotesis.md` § Métricas: gana, no pierde, pierde, indeterminado."""
    if not np.isnan(ic_inf) and ic_inf > 0:
        return "gana"
    if not np.isnan(ic_inf) and ic_inf >= -delta:
        return "no pierde"
    if delta_media < -delta:
        return "pierde"
    return "indeterminado"


def _ic(dif: np.ndarray) -> tuple[float, float, float, float]:
    n = len(dif)
    media = float(dif.mean())
    if n < 2:
        return media, float("nan"), float("nan"), float("nan")
    sd = float(dif.std(ddof=1))
    mitad = float(stats.t.ppf(0.975, n - 1)) * sd / np.sqrt(n)
    return media, sd, media - mitad, media + mitad


def apareado(finales: pd.DataFrame, estudios: pd.DataFrame | None = None) -> pd.DataFrame:
    """Tabla apareada por semilla de cada variante contra `C`. `finales` ya trae `g`.

    Usa solo las semillas que tienen la variante y el control, e informa cuántas. El tiempo T de una variante es el tiempo del
    estudio (fila `optimizar` cuyo id de estudio es `estudio`) más la media del tiempo final; solo se compara si el
    variante corrió en la misma máquina, CPU e hilos que el control.
    """
    ctrl = finales[finales["variante"] == CONTROL].set_index("semilla")
    if ctrl.empty:
        raise ValueError("no hay corridas finales del control (variante C)")
    g_c = float(ctrl["g"].mean())
    delta = DELTA_REL * g_c
    estudios = estudios if estudios is not None else pd.DataFrame(columns=COLUMNAS)
    t_estudio = estudios.set_index("estudio")["tiempo_optimizacion_s"] if len(estudios) else pd.Series(dtype=float)

    def tiempo(variante_df: pd.DataFrame) -> float:
        est = variante_df["estudio"].iloc[0]
        if est not in t_estudio.index:
            return float("nan")
        return float(t_estudio[est]) + float(variante_df["tiempo_entrenamiento_s"].mean())

    maquina_c = tuple(ctrl[["maquina", "cpu", "hilos"]].iloc[0])
    t_c = tiempo(ctrl.reset_index())
    filas = []
    for variante, df in finales[~finales["variante"].isin(SIN_DELTA)].groupby("variante", sort=True):
        b = df.set_index("semilla")
        comunes = sorted(set(b.index) & set(ctrl.index))
        nota = ""
        if len(comunes) < len(ctrl):
            nota = f"{len(comunes)} semillas en común de {len(ctrl)} del control"
        if not comunes:
            filas.append({"variante": variante, "n_semillas": 0, "veredicto": "indeterminado", "nota": "sin semillas en común"})
            continue
        dg = (b.loc[comunes, "g"] - ctrl.loc[comunes, "g"]).to_numpy(dtype=float)
        media, sd, lo, hi = _ic(dg)
        da = (b.loc[comunes, "auc_test"] - ctrl.loc[comunes, "auc_test"]).to_numpy(dtype=float)
        dt = (b.loc[comunes, "tiempo_entrenamiento_s"] - ctrl.loc[comunes, "tiempo_entrenamiento_s"]).to_numpy(dtype=float)
        misma = tuple(b[["maquina", "cpu", "hilos"]].iloc[0]) == maquina_c
        t_b = tiempo(df) if misma else float("nan")
        if not misma:
            nota = (nota + "; " if nota else "") + "tiempo excluido: otra máquina, CPU o hilos que el control"
        filas.append({
            "variante": variante,
            "metodo": b["metodo"].iloc[0],
            "tasa": b["tasa"].iloc[0],
            "n_semillas": len(comunes),
            "semillas": " ".join(str(s) for s in comunes),
            "g_control": g_c,
            "delta_g_margen": delta,
            "delta_g_media": media,
            "delta_g_sd": sd,
            "delta_g_ic_inf": lo,
            "delta_g_ic_sup": hi,
            "semillas_ganadas": int((dg > 0).sum()),
            "veredicto": veredicto(media, lo, delta),
            "delta_auc_media": float(da.mean()),
            "delta_auc_ic_inf": _ic(da)[2],
            "delta_auc_ic_sup": _ic(da)[3],
            "delta_tiempo_final_media_s": float(dt.mean()) if misma else float("nan"),
            "tiempo_total_s": t_b,
            "tiempo_total_control_s": t_c,
            "aceleracion": t_c / t_b if t_b == t_b and t_b > 0 else float("nan"),
            "nota": nota,
        })
    return pd.DataFrame(filas)


# --- réplicas de optimización (`h3-semillas-optuna` D5) -------------------------


def con_replica(tabla: pd.DataFrame) -> pd.DataFrame:
    """La tabla con `replica_opt` entera; una tabla anterior a las réplicas (sin la columna o con huecos) es la réplica 0."""
    t = tabla.copy()
    t["replica_opt"] = t["replica_opt"].fillna(0).astype(int) if "replica_opt" in t.columns else 0
    return t


def _welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float, float]:
    """(media(a) − media(b), error estándar de la diferencia, ic_inf, ic_sup) con IC 95% de Welch."""
    dif = float(a.mean() - b.mean())
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = float(np.sqrt(va + vb))
    if se == 0:
        return dif, se, dif, dif
    gl = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    mitad = float(stats.t.ppf(0.975, gl)) * se
    return dif, se, dif - mitad, dif + mitad


def descomposicion(g: pd.DataFrame) -> dict:
    """Suma de cuadrados de G entre réplicas y dentro de cada réplica (`g` trae `replica_opt` y `g`).

    SS_total = SS_entre + SS_dentro sin resto. Las varianzas dividen por el total de observaciones, así
    var_total = var_entre + var_dentro vale también con réplicas incompletas."""
    x = g["g"].to_numpy(dtype=float)
    por_replica = g.groupby("replica_opt")["g"]
    medias, n = por_replica.mean(), por_replica.size()
    ss_total = float(((x - x.mean()) ** 2).sum())
    ss_entre = float((n * (medias - x.mean()) ** 2).sum())
    ss_dentro = float((g["g"] - g["replica_opt"].map(medias)).pow(2).sum())
    sd_dentro = por_replica.std(ddof=1)
    return {
        "ss_total": ss_total, "ss_entre": ss_entre, "ss_dentro": ss_dentro,
        "var_total": ss_total / len(x), "var_entre": ss_entre / len(x), "var_dentro": ss_dentro / len(x),
        "frac_entre": ss_entre / ss_total if ss_total > 0 else float("nan"),
        "sd_entre_replicas": float(medias.std(ddof=1)) if len(medias) > 1 else float("nan"),
        "sd_dentro_medio": float(sd_dentro.mean()) if sd_dentro.notna().any() else float("nan"),
    }


def _resumen_replicas(g: pd.DataFrame) -> dict:
    medias = g.groupby("replica_opt")["g"].mean()
    return {"n_replicas": len(medias), "n_semillas": len(g), "replicas": " ".join(str(k) for k in medias.index),
            "g_media_replicas": float(medias.mean()), "g_mediana_replicas": float(medias.median()),
            "g_min_replicas": float(medias.min()), "g_max_replicas": float(medias.max())}


def _veredicto_par(lo: float, hi: float) -> str:
    """Diferencia entre variantes que comparten estudios (`H3R-0.1` − `H3-0.1`): mejora, empeora o no cambia."""
    if lo > 0:
        return "mejora"
    if hi < 0:
        return "empeora"
    return "no cambia"


def replicas(finales: pd.DataFrame, delta: float, propias: set[str] | None = None,
             pares: Sequence[tuple[str, str]] = (), semillas_por_replica: int = 10,
             pares_welch: Sequence[tuple[str, str]] = ()) -> pd.DataFrame:
    """Tabla de réplicas: una fila por variante con al menos dos réplicas y, salvo el control, su Δ con réplicas.

    `finales` ya trae `g` y `replica_opt`; `delta` es δ de la réplica 0 (no se recalcula). `propias` limita las filas a las
    variantes del experimento (por defecto, todas). Cada fila trae la descomposición de la varianza de G entre réplicas y
    entre semillas; Δ con réplicas = media de las medias por réplica menos la del control, con IC de Welch entre réplicas,
    y solo se calcula si el control también tiene dos réplicas. `pares` (a, b) suma una fila `a - b` apareada por réplica y
    semilla, con IC t entre réplicas; `pares_welch` (a, b), una fila `a - b` sin aparear (variantes que no comparten
    estudios), con IC de Welch entre las medias por réplica de cada una."""
    finales = con_replica(finales[finales["variante"] != "C-rep"])
    por_variante = {v: d for v, d in finales.groupby("variante", sort=True) if d["replica_opt"].nunique() >= 2}
    ctrl = por_variante.get(CONTROL)
    filas = []
    for variante, g in por_variante.items():
        if propias is not None and variante not in propias:
            continue
        fila = {"variante": variante, "contra": "", **_resumen_replicas(g), **descomposicion(g)}
        notas = [f"réplicas con menos de {semillas_por_replica} semillas"] if g.groupby("replica_opt").size().lt(semillas_por_replica).any() else []
        if variante != CONTROL and ctrl is not None:
            medias_v = g.groupby("replica_opt")["g"].mean().to_numpy(dtype=float)
            medias_c = ctrl.groupby("replica_opt")["g"].mean().to_numpy(dtype=float)
            dif, se, lo, hi = _welch(medias_v, medias_c)
            fila.update(contra=CONTROL, delta_g_media=dif, delta_g_se=se, delta_g_ic_inf=lo, delta_g_ic_sup=hi,
                        delta_g_margen=delta, veredicto=veredicto(dif, lo, delta),
                        n_replicas_control=int(ctrl["replica_opt"].nunique()), n_semillas_control=len(ctrl))
            # ΔAUC con réplicas (D10): igual que Δ de ganancia, con el AUC en 201910; el veredicto no lo usa
            if "auc_test" in g.columns:
                auc_v = g.groupby("replica_opt")["auc_test"].mean().to_numpy(dtype=float)
                auc_c = ctrl.groupby("replica_opt")["auc_test"].mean().to_numpy(dtype=float)
                d_auc, _, lo_a, hi_a = _welch(auc_v, auc_c)
                fila.update(delta_auc_media=d_auc, delta_auc_ic_inf=lo_a, delta_auc_ic_sup=hi_a)
            if set(g["replica_opt"]) != set(ctrl["replica_opt"]):
                notas.append("réplicas distintas a las del control")
            if ctrl.groupby("replica_opt").size().lt(semillas_por_replica).any():
                notas.append("control con réplicas incompletas")
        elif variante != CONTROL:
            notas.append("control con menos de dos réplicas: sin Δ con réplicas")
        fila["nota"] = "; ".join(notas)
        filas.append(fila)
    for a, b in pares:
        if (propias is not None and a not in propias) or a not in por_variante or b not in por_variante:
            continue
        ga = por_variante[a].set_index(["replica_opt", "semilla"])["g"]
        gb = por_variante[b].set_index(["replica_opt", "semilla"])["g"]
        comunes = ga.index.intersection(gb.index)
        dif = (ga.loc[comunes] - gb.loc[comunes]).rename("d").reset_index()
        por_replica = dif.groupby("replica_opt")["d"].mean().to_numpy(dtype=float)
        if len(por_replica) < 2:
            continue
        media, sd, lo, hi = _ic(por_replica)
        filas.append({
            "variante": f"{a} - {b}", "contra": b, "n_replicas": len(por_replica), "n_semillas": len(dif),
            "replicas": " ".join(str(k) for k in sorted(dif["replica_opt"].unique())),
            "delta_g_media": media, "delta_g_se": sd / np.sqrt(len(por_replica)), "delta_g_ic_inf": lo, "delta_g_ic_sup": hi,
            "veredicto": _veredicto_par(lo, hi),
            "nota": f"apareado por réplica y semilla; IC t entre réplicas ({len(por_replica) - 1} g.l.)",
        })
    for a, b in pares_welch:
        if (propias is not None and a not in propias) or a not in por_variante or b not in por_variante:
            continue
        ga, gb = por_variante[a], por_variante[b]
        dif, se, lo, hi = _welch(ga.groupby("replica_opt")["g"].mean().to_numpy(dtype=float),
                                 gb.groupby("replica_opt")["g"].mean().to_numpy(dtype=float))
        filas.append({
            "variante": f"{a} - {b}", "contra": b, "n_replicas": int(ga["replica_opt"].nunique()),
            "n_semillas": len(ga), "replicas": " ".join(str(k) for k in sorted(ga["replica_opt"].unique())),
            "delta_g_media": dif, "delta_g_se": se, "delta_g_ic_inf": lo, "delta_g_ic_sup": hi,
            "veredicto": _veredicto_par(lo, hi),
            "nota": f"sin aparear; IC de Welch entre réplicas ({ga['replica_opt'].nunique()} y "
                    f"{gb['replica_opt'].nunique()})",
        })
    return pd.DataFrame(filas)


# --- pares entre experimentos (`tiempos-confiables-y-consistencia` D12) ------------------------------------


def pares_directos(finales: pd.DataFrame, apareados: Sequence[tuple[str, str]], welch: Sequence[tuple[str, str]],
                   info: dict[tuple[str, str], tuple[str, bool]] | None = None, semillas_por_replica: int = 20) -> pd.DataFrame:
    """Una fila por par declarado `a − b`, con las variantes de cualquier experimento (`finales` ya trae `g`, `replica_opt`
    y `filas_train`). La cuenta es la de `replicas`: diferencia apareada por réplica y semilla con IC t entre réplicas, o
    diferencia de medias por réplica con IC de Welch. Una réplica entra solo si tiene las `semillas_por_replica` semillas en
    los dos lados; la fila dice cuántas usó. Un par al que le falta un lado, o con menos de dos réplicas completas en común,
    sale `pendiente` y dice qué variante falta: `replicas` lo saltea sin avisar.
    `info` da, por par, la decisión que aísla y si es un contraste principal."""
    info = info or {}
    finales = con_replica(finales[finales["variante"] != "C-rep"])
    cuenta = finales.groupby(["variante", "replica_opt"]).size()

    def completas(v: str) -> set[int]:
        return {int(k) for (vv, k), n in cuenta.items() if vv == v and n >= semillas_por_replica}

    filas = []
    for tipo, lista in (("apareado", apareados), ("Welch", welch)):
        for a, b in lista:
            aisla, principal = info.get((a, b), ("", False))
            fila = {"variante": f"{a} - {b}", "a": a, "b": b, "tipo": tipo, "aisla": aisla, "principal": principal,
                    "estado": "pendiente", "faltan": "", "n_replicas": 0, "n_semillas": 0, "replicas": "",
                    "delta_g_media": np.nan, "delta_g_se": np.nan, "delta_g_ic_inf": np.nan, "delta_g_ic_sup": np.nan,
                    "veredicto": "pendiente", "filas_train_a": np.nan, "filas_train_b": np.nan, "nota": ""}
            faltan = [v for v in (a, b) if not (finales["variante"] == v).any()]
            ka, kb = completas(a), completas(b)
            ks = sorted(ka & kb)
            if faltan:
                fila.update(faltan=", ".join(faltan), nota="falta la variante " + " y ".join(faltan))
            elif len(ks) < 2:
                fila["nota"] = (f"menos de dos réplicas completas en común ({a}: {len(ka)}, {b}: {len(kb)}, "
                                f"en común: {len(ks)})")
            else:
                da, db = (finales[(finales["variante"] == v) & finales["replica_opt"].isin(ks)] for v in (a, b))
                if tipo == "apareado":
                    ga, gb = (d.set_index(["replica_opt", "semilla"])["g"] for d in (da, db))
                    comunes = ga.index.intersection(gb.index)
                    dif = (ga.loc[comunes] - gb.loc[comunes]).rename("d").reset_index()
                    por_replica = dif.groupby("replica_opt")["d"].mean().to_numpy(dtype=float)
                    media, sd, lo, hi = _ic(por_replica)
                    se, n_sem = sd / np.sqrt(len(por_replica)), len(dif)
                    nota = f"apareado por réplica y semilla; IC t entre réplicas ({len(por_replica) - 1} g.l.)"
                else:
                    media, se, lo, hi = _welch(da.groupby("replica_opt")["g"].mean().to_numpy(dtype=float),
                                               db.groupby("replica_opt")["g"].mean().to_numpy(dtype=float))
                    n_sem, nota = len(da), f"sin aparear; IC de Welch entre réplicas ({len(ks)} y {len(ks)})"
                hay = {v: int(finales.loc[finales["variante"] == v, "replica_opt"].nunique()) for v in (a, b)}
                if any(n > len(ks) for n in hay.values()):
                    nota += (f"; usa {len(ks)} réplicas de las que hay ({a}: {hay[a]}, {b}: {hay[b]}): las otras no "
                             f"tienen las {semillas_por_replica} semillas en los dos lados")
                fila.update(estado="completo", n_replicas=len(ks), n_semillas=n_sem, replicas=" ".join(str(k) for k in ks),
                            delta_g_media=media, delta_g_se=se, delta_g_ic_inf=lo, delta_g_ic_sup=hi,
                            veredicto=_veredicto_par(lo, hi), nota=nota,
                            filas_train_a=float(da["filas_train"].median()) if "filas_train" in da else np.nan,
                            filas_train_b=float(db["filas_train"].median()) if "filas_train" in db else np.nan)
            filas.append(fila)
    return pd.DataFrame(filas)
