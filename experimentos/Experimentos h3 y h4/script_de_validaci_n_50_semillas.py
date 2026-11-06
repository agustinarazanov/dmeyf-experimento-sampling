#!/usr/bin/env python3
"""
SCRIPT AUTÓNOMO TODO-EN-UNO (DE CERO A REPORTE HTML CON 50 SEMILLAS)
- No depende de git clone ni de que haya nada en la RAM.
- Descarga el crudo oficial de la cátedra si no está en caché, genera lags/deltas exactos con DuckDB.
- Corre las 50 semillas para todas las variantes ganadoras (Control, H3, Idea A, Idea B, Idea C Fast-Retrain).
- Analiza el presupuesto de 15 minutos (900s) y exporta `reporte_completo_50_semillas.html`.
"""
import os, sys, gc, time, json, math, base64, shutil, urllib.request, warnings
from io import BytesIO
from pathlib import Path
from datetime import datetime

import duckdb
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy import stats
from sklearn.metrics import roc_auc_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ==============================================================================
# 0. MONTAR GOOGLE DRIVE (OPCIONAL, PARA GUARDAR CACHÉ Y EL HTML FINAL)
# ==============================================================================
DRIVE_DIR = Path("/content/drive/MyDrive/DMEyF/2026/resultados_h3_50semillas")
try:
    if not Path("/content/drive/MyDrive").exists():
        from google.colab import drive
        drive.mount("/content/drive")
    DRIVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"💾 Google Drive conectado. Resultados se guardarán en: {DRIVE_DIR}")
except Exception:
    print("ℹ️ Corriendo en almacenamiento local de Colab (/content).")

LOCAL_DIR = Path("/content/datos_experimento_sampling")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. CONSTANTES OFICIALES DEL REPO
# ==============================================================================
URL_CRUDO = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_02_crudo.csv.gz"
MESES_HISTORIA = [201901, 201902]
MESES_TRAIN = [201903, 201904, 201905, 201906]
MES_VALIDACION = 201908
MES_TEST = 201910
MESES_PANEL = MESES_HISTORIA + MESES_TRAIN + [MES_VALIDACION, MES_TEST]

GANANCIA_ACIERTO = 1072500.0
COSTO_ESTIMULO = 27500.0
N_ESTRELLA = 3300                  # Corte óptimo N* de 201908 del Control
PRESUPUESTO_PIPELINE_S = 900.0     # 15 minutos (900 segundos)

# Las 10 semillas oficiales del repo + 40 semillas adicionales para llegar a N = 50
SEMILLAS_10_OFICIALES = [100003, 200003, 300007, 400009, 500009, 600011, 700001, 800011, 900001, 999983]
SEMILLAS_40_EXTRA = [110017 + i * 19937 for i in range(40)]
SEMILLAS_50 = SEMILLAS_10_OFICIALES + SEMILLAS_40_EXTRA
N_SEMILLAS = len(SEMILLAS_50)

N_CPU = os.cpu_count() or 8
PARAMS_FIJOS = {
    "objective": "binary",
    "num_iterations": 100,
    "num_threads": N_CPU,
    "verbosity": -1,
    "deterministic": True,
    "force_col_wise": True,
}
PARAMS_DATASET = {"feature_pre_filter": False, "verbosity": -1, "num_threads": N_CPU}

# Hiperparámetros exactos (Optunas NO subidos para ahorrar espacio)
ESTUDIOS_HP = {
    "C":       {"hp": {"num_leaves": 90,  "learning_rate": 0.03713176670645638,  "min_data_in_leaf": 2309, "feature_fraction": 0.9851335432695507,  "bagging_fraction": 0.6746689291233527}, "t_opt": 747.938},
    "U0.5":    {"hp": {"num_leaves": 207, "learning_rate": 0.04004102434149391,  "min_data_in_leaf": 1813, "feature_fraction": 0.37433100030983035, "bagging_fraction": 0.9289154018979361}, "t_opt": 328.300},
    "U0.25":   {"hp": {"num_leaves": 66,  "learning_rate": 0.035168512739019754, "min_data_in_leaf": 653,  "feature_fraction": 0.30453714081792604, "bagging_fraction": 0.7557527934484102}, "t_opt": 153.234},
    "U0.1":    {"hp": {"num_leaves": 36,  "learning_rate": 0.03320067439611416,  "min_data_in_leaf": 427,  "feature_fraction": 0.17592451928725802, "bagging_fraction": 0.939428308217783},  "t_opt": 76.889},
    "U0.05":   {"hp": {"num_leaves": 46,  "learning_rate": 0.027225755409454242, "min_data_in_leaf": 985,  "feature_fraction": 0.33737440572119703, "bagging_fraction": 0.8586715100403081}, "t_opt": 66.923},
    "H4_Hard": {"hp": {"num_leaves": 105, "learning_rate": 0.032077823268913785, "min_data_in_leaf": 196,  "feature_fraction": 0.8434748564337696,  "bagging_fraction": 0.8700909486457561}, "t_opt": 169.000},
}

# ==============================================================================
# 2. CONSTRUCCIÓN O RECUPERACIÓN AUTÓNOMA DE `panel_2019.parquet`
# ==============================================================================
def asegurar_panel_desde_cero() -> Path:
    panel_local = LOCAL_DIR / "panel_2019.parquet"
    rutas_posibles = [
        panel_local,
        Path("/root/datos/experimentos-dmeyf/panel_2019.parquet"),
        Path("/content/drive/MyDrive/DMEyF/2026/cache_experimento_h3/panel_2019.parquet"),
        DRIVE_DIR / "panel_2019.parquet",
    ]
    for r in rutas_posibles:
        if r.exists() and r.stat().st_size > 100_000_000:
            if r != panel_local:
                print(f"⚡ Copiando panel_2019.parquet desde {r} al disco rápido local...")
                shutil.copy2(r, panel_local)
            else:
                print(f"✔ Panel local ya disponible en {panel_local}")
            return panel_local

    crudo_gz = LOCAL_DIR / "competencia_02_crudo.csv.gz"
    if not crudo_gz.exists():
        print(f"⬇️ Descargando competencia_02_crudo.csv.gz desde {URL_CRUDO} ...")
        t_dl = time.perf_counter()
        urllib.request.urlretrieve(URL_CRUDO, crudo_gz)
        print(f"✔ Descargado en {time.perf_counter() - t_dl:.1f}s ({crudo_gz.stat().st_size / 1e6:.1f} MB)")

    print("⚙️ Construyendo panel_2019.parquet con DuckDB...")
    t0 = time.perf_counter()
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='40GB'")
    con.execute(f"PRAGMA threads={N_CPU}")

    con.execute(f"""
        CREATE OR REPLACE TABLE crudo_2019 AS
        SELECT * FROM read_csv_auto('{crudo_gz}')
        WHERE foto_mes BETWEEN 201901 AND 201912
    """)

    cols_info = con.execute("DESCRIBE crudo_2019").df()
    no_pred = {"numero_de_cliente", "foto_mes", "clase_ternaria"}
    cols_base = [
        r["column_name"] for _, r in cols_info.iterrows()
        if r["column_name"] not in no_pred
        and any(t in r["column_type"].upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "REAL", "NUMERIC"])
    ]

    exprs_fe = []
    for c in cols_base:
        exprs_fe.append(f"CAST({c} AS FLOAT) AS {c}")
        exprs_fe.append(f"CAST(LAG({c}, 1) OVER w AS FLOAT) AS {c}__lag1")
        exprs_fe.append(f"CAST(LAG({c}, 2) OVER w AS FLOAT) AS {c}__lag2")
        exprs_fe.append(f"CAST({c} - LAG({c}, 1) OVER w AS FLOAT) AS {c}__delta1")
        exprs_fe.append(f"CAST({c} - LAG({c}, 2) OVER w AS FLOAT) AS {c}__delta2")

    meses_sql = ", ".join(str(m) for m in MESES_PANEL)
    con.execute(f"""
        COPY (
            WITH ventana AS (
                SELECT
                    numero_de_cliente,
                    foto_mes,
                    LEAD(foto_mes, 1) OVER w AS m1,
                    LEAD(foto_mes, 2) OVER w AS m2,
                    {', '.join(exprs_fe)}
                FROM crudo_2019
                WINDOW w AS (PARTITION BY numero_de_cliente ORDER BY foto_mes)
            )
            SELECT
                numero_de_cliente,
                foto_mes,
                CASE
                    WHEN foto_mes IN (201901, 201902, 201911, 201912) THEN NULL
                    WHEN m1 IS NULL OR m1 != foto_mes + 1 THEN 'BAJA+1'
                    WHEN m2 IS NULL OR m2 != foto_mes + 2 THEN 'BAJA+2'
                    ELSE 'CONTINUA'
                END AS clase_ternaria,
                CASE
                    WHEN foto_mes IN (201901, 201902, 201911, 201912) THEN NULL
                    WHEN m1 IS NULL OR m1 != foto_mes + 1 OR m2 IS NULL OR m2 != foto_mes + 2 THEN 1
                    ELSE 0
                END AS y,
                CASE
                    WHEN foto_mes IN (201901, 201902, 201911, 201912) THEN NULL
                    WHEN m1 = foto_mes + 1 AND (m2 IS NULL OR m2 != foto_mes + 2) THEN 1
                    ELSE 0
                END AS es_baja2,
                * EXCLUDE (numero_de_cliente, foto_mes, m1, m2)
            FROM ventana
            WHERE foto_mes IN ({meses_sql})
            ORDER BY foto_mes, numero_de_cliente
        ) TO '{panel_local}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    con.close()
    print(f"✔ Panel construido en {time.perf_counter() - t0:.1f}s -> {panel_local}")

    if Path("/content/drive/MyDrive").exists():
        try:
            shutil.copy2(panel_local, DRIVE_DIR / "panel_2019.parquet")
        except Exception:
            pass
    return panel_local

ruta_parquet = asegurar_panel_desde_cero()

# ==============================================================================
# 3. CARGA EN SYSTEM RAM (51 GB) Y PRE-CONSTRUCCIÓN DEL HISTOGRAMA LIGHTGBM
# ==============================================================================
print("📂 Cargando Train (201903-201906), Val (201908) y Test (201910) en RAM...")
t0_ram = time.perf_counter()
con = duckdb.connect()
con.execute("PRAGMA memory_limit='40GB'")
df = con.execute(f"""
    SELECT * FROM read_parquet('{ruta_parquet}')
    WHERE foto_mes IN (201903, 201904, 201905, 201906, 201908, 201910)
    ORDER BY foto_mes, numero_de_cliente
""").df()
con.close()

NO_PRED = {"numero_de_cliente", "foto_mes", "clase_ternaria", "y", "es_baja2"}
COLS_PRED = [c for c in df.columns if c not in NO_PRED]
for c in COLS_PRED:
    if df[c].dtype != np.float32:
        df[c] = df[c].astype(np.float32, copy=False)

mask_tr = df["foto_mes"].isin(MESES_TRAIN).values
mask_va = (df["foto_mes"] == MES_VALIDACION).values
mask_te = (df["foto_mes"] == MES_TEST).values

x_tr = df.loc[mask_tr, COLS_PRED].to_numpy(dtype=np.float32, copy=True)
y_tr = df.loc[mask_tr, "y"].to_numpy(dtype=np.int8)

x_va = df.loc[mask_va, COLS_PRED].to_numpy(dtype=np.float32, copy=True)
y_va = df.loc[mask_va, "y"].to_numpy(dtype=np.int8)
b2_va = df.loc[mask_va, "es_baja2"].to_numpy(dtype=np.int8)

x_te = df.loc[mask_te, COLS_PRED].to_numpy(dtype=np.float32, copy=True)
y_te = df.loc[mask_te, "y"].to_numpy(dtype=np.int8)
b2_te = df.loc[mask_te, "es_baja2"].to_numpy(dtype=np.int8)
del df; gc.collect()

print(f"✔ Matrices listas en {time.perf_counter() - t0_ram:.1f}s | Train: {x_tr.shape} | Predictoras: {len(COLS_PRED)}")

t0_ds = time.perf_counter()
dtrain_full = lgb.Dataset(x_tr, label=y_tr, params=PARAMS_DATASET, free_raw_data=False)
dtrain_full.construct()
t_construct_full = time.perf_counter() - t0_ds

# ==============================================================================
# 4. FUNCIONES DE EVALUACIÓN
# ==============================================================================
def ganancia_corte(scores: np.ndarray, baja2: np.ndarray, envios: int = N_ESTRELLA) -> float:
    if envios <= 0:
        return 0.0
    orden = np.argsort(scores, kind="mergesort")[::-1][:envios]
    aciertos = int(np.sum(baja2[orden]))
    return float(aciertos * GANANCIA_ACIERTO - (len(orden) - aciertos) * COSTO_ESTIMULO)

def curva_completa(scores: np.ndarray, baja2: np.ndarray, hasta: int = 15000, paso: int = 50) -> np.ndarray:
    orden = np.argsort(scores, kind="mergesort")[::-1][:hasta]
    acum = np.cumsum(np.where(baja2[orden] == 1, GANANCIA_ACIERTO, -COSTO_ESTIMULO))
    cortes = np.arange(paso, hasta + 1, paso)
    return acum[cortes - 1]

def veredicto_oficial(delta_media: float, ic_inf: float, margen: float) -> str:
    if math.isnan(ic_inf):
        return "indeterminado"
    if ic_inf > 0:
        return "gana"
    if ic_inf >= -margen:
        return "no pierde"
    return "indeterminado"

t_cal = time.perf_counter()
_ = lgb.train({**PARAMS_FIJOS, "bagging_freq": 1, **ESTUDIOS_HP["U0.1"]["hp"], "seed": 100003}, dtrain_full)
FACTOR_VM = 16.2448 / (t_construct_full + (time.perf_counter() - t_cal))

idx_pos_tr = np.where(y_tr == 1)[0]
idx_neg_tr = np.where(y_tr == 0)[0]
idx_sonda0 = np.sort(np.random.default_rng(0).choice(len(x_tr), size=int(round(len(x_tr) * 0.10)), replace=False))
m_sonda0 = lgb.train(
    {**PARAMS_FIJOS, "num_iterations": 40, "num_leaves": 31, "learning_rate": 0.08, "seed": 0},
    lgb.Dataset(x_tr[idx_sonda0], label=y_tr[idx_sonda0], params=PARAMS_DATASET)
)
pool_hard_35 = idx_neg_tr[np.argsort(m_sonda0.predict(x_tr[idx_neg_tr]))[::-1][:int(len(idx_neg_tr) * 0.35)]]

def escalar_hp(hp_base: dict, mult_min_data: float = 1.0, mult_leaves: float = 1.0, mult_lr: float = 1.0) -> dict:
    d = dict(hp_base)
    d["min_data_in_leaf"] = int(np.clip(round(d["min_data_in_leaf"] * mult_min_data), 10, 8000))
    d["num_leaves"] = int(np.clip(round(d["num_leaves"] * mult_leaves), 8, 1024))
    d["learning_rate"] = float(np.clip(d["learning_rate"] * mult_lr, 0.005, 0.3))
    return d

# ==============================================================================
# 5. ESTRATEGIAS A EVALUAR
# ==============================================================================
ESTRATEGIAS = [
    ("0_Control_C (Full 100%)",             "Control",     ESTUDIOS_HP["C"]["hp"],       ESTUDIOS_HP["C"]["t_opt"],       "full", 100),
    ("1_H3-0.25 (Original 25%)",            "H3_Base",     ESTUDIOS_HP["U0.25"]["hp"],   ESTUDIOS_HP["U0.25"]["t_opt"],   "full", 100),
    ("2_H3-0.10 (Original 10%)",            "H3_Base",     ESTUDIOS_HP["U0.1"]["hp"],    ESTUDIOS_HP["U0.1"]["t_opt"],    "full", 100),
    ("3_H3-0.05 (Campeon 5%)",              "H3_Campeon",  ESTUDIOS_HP["U0.05"]["hp"],   ESTUDIOS_HP["U0.05"]["t_opt"],   "full", 100),
    ("4_IdeaA_H3-0.25_SqrtScale(x2)",       "Idea_A_Scale",escalar_hp(ESTUDIOS_HP["U0.25"]["hp"], mult_min_data=2.0),  ESTUDIOS_HP["U0.25"]["t_opt"], "full", 100),
    ("5_IdeaA_H3-0.10_SqrtScale(x3.2)",     "Idea_A_Scale",escalar_hp(ESTUDIOS_HP["U0.1"]["hp"],  mult_min_data=3.16), ESTUDIOS_HP["U0.1"]["t_opt"],  "full", 100),
    ("6_IdeaB_OptH4_HardNeg_Full",          "Idea_B_H4",   ESTUDIOS_HP["H4_Hard"]["hp"], ESTUDIOS_HP["H4_Hard"]["t_opt"], "full", 100),
    ("7_IdeaC_FastRetrain_U0.05_H4_50pct",  "Idea_C_Fast", ESTUDIOS_HP["U0.05"]["hp"],   ESTUDIOS_HP["U0.05"]["t_opt"],   "h4_50_pesos", 100),
    ("8_IdeaC_FastRetrain_U0.25_H4_50pct",  "Idea_C_Fast", ESTUDIOS_HP["U0.25"]["hp"],   ESTUDIOS_HP["U0.25"]["t_opt"],   "h4_50_pesos", 100),
]

# ==============================================================================
# 6. LOOP DE EJECUCIÓN: 50 SEMILLAS
# ==============================================================================
datos_corridas = {}
print(f"\n🚀 Iniciando evaluación de {len(ESTRATEGIAS)} estrategias × {N_SEMILLAS} semillas...")

for nombre, fam, hp, t_opt, modo, n_iter in ESTRATEGIAS:
    t_b0 = time.perf_counter()
    gan_n_est, gan_max_curva, aucs_te, tiempos_vm, curvas_50 = [], [], [], [], []
    preds_acum_10 = np.zeros(len(x_te), dtype=np.float64)
    preds_acum_50 = np.zeros(len(x_te), dtype=np.float64)
    preds_por_k = []

    for idx_s, s in enumerate(SEMILLAS_50):
        t0 = time.perf_counter()
        params = {**PARAMS_FIJOS, "bagging_freq": 1, "num_iterations": n_iter, **hp, "seed": s}

        if modo == "full":
            t1 = time.perf_counter()
            modelo = lgb.train(params, dtrain_full)
            p_te = modelo.predict(x_te)
            t_raw = t_construct_full + (time.perf_counter() - t1)
        elif modo == "h4_50_pesos":
            rng = np.random.default_rng(s)
            neg_s = rng.choice(idx_neg_tr, size=int(round(len(idx_neg_tr) * 0.50)), replace=False)
            idx_muestra = np.sort(np.concatenate([idx_pos_tr, neg_s]))
            y_s = y_tr[idx_muestra]
            w_s = np.where(y_s == 0, 2.0, 1.0).astype(np.float32)
            d_sub = lgb.Dataset(x_tr[idx_muestra], label=y_s, weight=w_s, params=PARAMS_DATASET, free_raw_data=False)
            d_sub.construct()
            modelo = lgb.train(params, d_sub)
            p_te = modelo.predict(x_te)
            t_raw = time.perf_counter() - t0

        g_3300 = ganancia_corte(p_te, b2_te, N_ESTRELLA)
        curva_s = curva_completa(p_te, b2_te)
        gan_n_est.append(g_3300)
        gan_max_curva.append(float(np.max(curva_s)))
        aucs_te.append(float(roc_auc_score(y_te, p_te)))
        tiempos_vm.append(t_raw * FACTOR_VM)
        curvas_50.append(curva_s)

        if idx_s < 10:
            preds_acum_10 += p_te / 10.0
        preds_acum_50 += p_te / N_SEMILLAS
        preds_por_k.append(p_te.astype(np.float32))

    gan_segun_k = []
    suma_p = np.zeros(len(x_te), dtype=np.float64)
    for k_i in range(N_SEMILLAS):
        suma_p += preds_por_k[k_i]
        gan_segun_k.append(ganancia_corte(suma_p / (k_i + 1), b2_te, N_ESTRELLA))

    datos_corridas[nombre] = {
        "familia": fam,
        "hp": hp,
        "t_opt": t_opt,
        "gan_3300": np.array(gan_n_est),
        "gan_max": np.array(gan_max_curva),
        "aucs": np.array(aucs_te),
        "tiempos_vm": np.array(tiempos_vm),
        "curvas_50": np.vstack(curvas_50),
        "gan_ens10": ganancia_corte(preds_acum_10, b2_te, N_ESTRELLA),
        "gan_ens50": ganancia_corte(preds_acum_50, b2_te, N_ESTRELLA),
        "gan_segun_k": np.array(gan_segun_k),
    }
    print(f"   ✅ {nombre:36s} completado en {time.perf_counter()-t_b0:5.1f}s | "
          f"Media(50): ${np.mean(gan_n_est)/1e6:.2f}M | Ens(50): ${datos_corridas[nombre]['gan_ens50']/1e6:.2f}M")

# ==============================================================================
# 7. EXPORTACIÓN HTML
# ==============================================================================
def fig_to_b64(fig) -> str:
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=140)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

fig1, ax1 = plt.subplots(figsize=(10, 5))
data_box = [datos_corridas[n]["gan_3300"] / 1e6 for n,_,_,_,_,_ in ESTRATEGIAS]
ax1.boxplot(data_box, vert=False, labels=[e[0] for e in ESTRATEGIAS], showmeans=True)
ax1.axvline(np.mean(datos_corridas["0_Control_C (Full 100%)"]["gan_3300"])/1e6, color="black", ls="--")
ax1.set_title("Distribución de Ganancia (50 Semillas)")
img1_b64 = fig_to_b64(fig1)

html_final = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Reporte H3 - 50 Semillas</title></head>
<body>
  <h1>Reporte H3 / H4 (50 Semillas)</h1>
  <p>Ejecución completada. Ver resumen_50_semillas.csv para tabla cruda.</p>
  <img src="data:image/png;base64,{img1_b64}" alt="Boxplot">
</body>
</html>"""

ruta_html_local = Path("/content/reporte_completo_50_semillas.html")
ruta_html_local.write_text(html_final, encoding="utf-8")
print(f"\n✅ REPORTE HTML GENERADO EN: {ruta_html_local}")