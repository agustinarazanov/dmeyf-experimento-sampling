"""Ledger como archivos: una fila por corrida, consolidación y tablas apareadas por semilla.

Cada corrida escribe `<ledger>/corridas/<id>.csv`; `consolidar` arma `resultados.csv` (solo corridas válidas, sin
duplicados por clave) y `apareado.csv` (diferencia contra el control por semilla). Las reglas de decisión son las de
`docs/hipotesis.md` y el cálculo, el de `docs/diseno.md` § Métricas.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

#: Columnas obligatorias de cada fila (`specs/ledger-resultados`). Sin valor se escribe vacío, pero la columna tiene que
#: estar: una fila a la que le falta una no se escribe.
COLUMNAS: list[str] = [
    "id", "fecha", "variante", "metodo", "tasa", "semilla", "etapa", "etapa_corrida", "estudio", "hp",
    "filas_train", "hash_muestra", "auc_val", "auc_test", "ganancia_max_201910", "envios_max_201910",
    "curva_201908", "curva_201910", "predicciones_201910",
    "tiempo_preparacion_s", "tiempo_optimizacion_s", "tiempo_entrenamiento_s", "tiempo_lgbtrain_s",
    "memoria_max_mb", "maquina", "cpu", "hilos", "load_avg", "commit", "codigo_sucio", "persona", "valida",
]
#: Sin `commit`: la misma semilla no puede contar dos veces; una repetición con código más nuevo reemplaza a la anterior.
CLAVE: list[str] = ["variante", "metodo", "tasa", "semilla", "etapa"]
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
    return corridas.reindex(columns=list(dict.fromkeys([*COLUMNAS, *corridas.columns])))


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
