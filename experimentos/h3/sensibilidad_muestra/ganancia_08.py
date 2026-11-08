"""08 — Ganancia en 201910 de los modelos de 07: Control y la elección de H3 en cada semilla.

Evaluación final autorizada por el grupo. No se reentrena nada: se usan los modelos completos que guardó 07
(`<corrida 07>/control/modelo_XX.txt`) y se predice 201910 una sola vez por configuración distinta. El corte es fijo,
N = 3.300 envíos (N* del control del grupo, fijado en 201908: `experimentos/h3/informe/informe.md`); octubre no se usa
para elegir nada.

Entrada: `--corrida-07 <carpeta>`, la que imprime sensibilidad_07 al terminar. De ahí se leen `diseno.json`
(modo, configuraciones y semillas), `ajustes.jsonl` (AUC de selección, parámetros efectivos y sha256 de las
predicciones de agosto), `control_seleccion.json`, `resumen_por_semilla.csv`, `control/modelo_XX.txt` y
`control/pred_XX.npy`.

Ganancia (convención del grupo en el commit de referencia 4a42bc6, `comun/ganancia.py`): se estimula a los N
clientes de mayor probabilidad; cada BAJA+2 suma 1.072.500 y cada estimulado que no es BAJA+2 (BAJA+1 o CONTINUA)
resta 27.500. A igual probabilidad entra primero el menor numero_de_cliente: es el orden de aparición en el panel del
grupo (ORDER BY foto_mes, numero_de_cliente) con su argsort estable.

Referencia fija: `comun/ganancia.py`, `comun/datos.py`, `comun/baseline.py` y `tests/test_ganancia.py` se leen con
`git show 4a42bc6:<archivo>` (no del árbol de trabajo), se guardan en la corrida y el módulo de ganancia se importa
de esa copia. Se informa si cambiaron hasta HEAD.

Verificaciones antes de presentar números:
  - pruebas sintéticas de la ganancia (contra el módulo del grupo en el commit de referencia, su test de 10 scores,
    empates y orden de filas) y de la etiqueta (SQL del grupo contra la regla de insumos.py, con casos borde);
  - importes, fórmula y SQL de la etiqueta del grupo leídos del commit; el SQL que se ejecuta se compara con su fuente;
  - etiquetas ternarias por cliente: SQL del grupo sobre el crudo contra el target de insumos.py, en todos los
    meses que el grupo etiqueta, 201910 incluido;
  - modelos: parámetros efectivos iguales a los de 07 y predicción de agosto idéntica (sha256) a la de ajustes.jsonl;
  - elección: ganadora de Control y elegida de cada semilla, recalculadas desde ajustes.jsonl e iguales a 07;
  - 201910: huellas sha256 de claves y X contra `referencia/huellas_datos.json`.

    python -m experimentos.h3.sensibilidad_muestra.ganancia_08 --corrida-07 <carpeta>
    python -m experimentos.h3.sensibilidad_muestra.ganancia_08 --solo-pruebas
    python -m experimentos.h3.sensibilidad_muestra.ganancia_08 --corrida-07 <carpeta de prueba> --hasta-modelos
"""
from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd
import psutil
import sklearn

from comun import rutas as rutas_grupo
from experimentos.h3.sensibilidad_muestra import busqueda as B06
from experimentos.h3.sensibilidad_muestra import carga as B05
from experimentos.h3.sensibilidad_muestra import insumos as B03
from experimentos.h3.sensibilidad_muestra import rutas
from experimentos.h3.sensibilidad_muestra import sensibilidad_07 as B07

NOMBRE = "08_evaluar_ganancia_h3"
COMMIT_REF = "4a42bc6"
MES_TEST = 201910
ENVIOS = 3_300
GANANCIA_BAJA2 = 1_072_500
COSTO_ESTIMULO = 27_500
GANADORA_REPORTADA = 6  # ganadora de Control en la corrida completa de 07 (20261103T191818_13788)
HILOS = B07.HILOS

log = logging.getLogger("08")

# Fuente del grupo (comun/datos.py en COMMIT_REF), copiada tal cual; referencia_grupo() la compara con el commit.
FUENTE_MACROS = """
create or replace macro mes_indice(m) as ((m // 100) * 12 + (m % 100) - 1);
create or replace macro indice_mes(i) as ((i // 12) * 100 + (i % 12) + 1);
create or replace macro mes_mas(m, n) as indice_mes(mes_indice(m) + n);
"""
FUENTE_ETIQUETA = """
        create table etiqueta as
        select k.{ID}, k.{MES},
               case when p1.{ID} is null then 'BAJA+1'
                    when p2.{ID} is null then 'BAJA+2'
                    else 'CONTINUA' end as {CLASE}
        from crudo k
        left join crudo p1 on p1.{ID} = k.{ID} and p1.{MES} = mes_mas(k.{MES}, 1)
        left join crudo p2 on p2.{ID} = k.{ID} and p2.{MES} = mes_mas(k.{MES}, 2)
        where k.{MES} in ({_lista(bl.MESES_TRAIN + [bl.MES_VALIDACION, bl.MES_TEST])})
    """
FUENTE_CRUDO = ("f\"create table crudo as select * from read_csv('{crudo}', sample_size=-1) \"\n"
                "        f\"where {MES} between {bl.CRUDO_DESDE} and {bl.CRUDO_HASTA}\"")
FUENTE_BAJA2 = "(e.{CLASE} = 'BAJA+2')::TINYINT as {BAJA2}"
FUENTE_ORDEN = "order by {MES}, {ID}"


def _modulo(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --- referencia del grupo ------------------------------------------------------------------------


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          encoding="utf-8").stdout


def normalizar(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def referencia_grupo(repo: Path, destino: Path) -> tuple[object, dict]:
    """Lee comun/ganancia.py, datos.py y baseline.py del commit de referencia y verifica lo que 08 replica."""
    completo = git(repo, "rev-parse", f"{COMMIT_REF}^{{commit}}").strip()
    destino.mkdir(parents=True, exist_ok=True)
    fuentes = {}
    for f in ("comun/ganancia.py", "comun/datos.py", "comun/baseline.py", "tests/test_ganancia.py"):
        texto = git(repo, "show", f"{COMMIT_REF}:{f}")
        (destino / f"{Path(f).stem}_{COMMIT_REF}.py").write_text(texto, encoding="utf-8")
        fuentes[f] = texto
    grp = _modulo("ganancia_grupo", destino / f"ganancia_{COMMIT_REF}.py")
    datos = normalizar(fuentes["comun/datos.py"])
    base = fuentes["comun/baseline.py"]
    constantes = {k: re.search(rf"^{k}[^=]*=\s*(.+?)\s*(#.*)?$", base, re.M).group(1)
                  for k in ("MESES_TRAIN", "MES_VALIDACION", "MES_TEST", "CRUDO_DESDE", "CRUDO_HASTA")}
    checks = {
        "importe_baja2": grp.GANANCIA_ACIERTO == GANANCIA_BAJA2,
        "costo_estimulo": grp.COSTO_ESTIMULO == COSTO_ESTIMULO,
        "aporte_solo_baja2_suma": "np.where(np.asarray(es_baja2, dtype=bool), GANANCIA_ACIERTO, -COSTO_ESTIMULO)"
                                  in fuentes["comun/ganancia.py"],
        "desempate_argsort_estable": 'np.argsort(-scores, kind="stable")' in fuentes["comun/ganancia.py"],
        "sql_macros_igual": normalizar(FUENTE_MACROS) in datos,
        "sql_etiqueta_igual": normalizar(FUENTE_ETIQUETA) in datos,
        "sql_crudo_igual": normalizar(FUENTE_CRUDO) in datos,
        "baja2_es_la_de_ganancia": normalizar(FUENTE_BAJA2) in datos,
        "panel_ordenado_por_mes_y_cliente": normalizar(FUENTE_ORDEN) in datos,
        "constantes_esperadas": constantes == {"MESES_TRAIN": "[201903, 201904, 201905, 201906]",
                                               "MES_VALIDACION": "201908", "MES_TEST": "201910",
                                               "CRUDO_DESDE": "201901", "CRUDO_HASTA": "201912"},
    }
    sin_cambios = {f: git(repo, "diff", "--name-only", COMMIT_REF, "HEAD", "--", f).strip() == ""
                   for f in fuentes}
    info = {"commit": completo, "head": git(repo, "rev-parse", "HEAD").strip(),
            "archivos_sin_cambios_hasta_head": sin_cambios, "constantes": constantes,
            "importes": {"BAJA+2": grp.GANANCIA_ACIERTO, "BAJA+1": -grp.COSTO_ESTIMULO,
                         "CONTINUA": -grp.COSTO_ESTIMULO},
            "sha256_fuentes": {f: B06.sha256_bytes(t.encode("utf-8")) for f, t in fuentes.items()},
            "checks": checks}
    if not all(checks.values()):
        raise RuntimeError(f"BLOQUEO: el código del grupo en {COMMIT_REF} no coincide con lo que 08 replica: {checks}")
    if not all(sin_cambios.values()):
        log.warning("hay archivos de referencia que cambiaron entre %s y HEAD: %s; se usa la versión de %s",
                    COMMIT_REF, sin_cambios, COMMIT_REF)
    return grp, info


def sql_grupo(crudo: str) -> list[str]:
    """Sentencias del grupo con sus constantes. Única diferencia: del crudo sólo se proyectan las dos claves."""
    lista = "201903, 201904, 201905, 201906, 201908, 201910"
    etiqueta = (FUENTE_ETIQUETA.replace("{ID}", "numero_de_cliente").replace("{MES}", "foto_mes")
                .replace("{CLASE}", "clase_ternaria")
                .replace("{_lista(bl.MESES_TRAIN + [bl.MES_VALIDACION, bl.MES_TEST])}", lista))
    return [FUENTE_MACROS,
            f"create table crudo as select numero_de_cliente, foto_mes from read_csv('{crudo}', sample_size=-1) "
            f"where foto_mes between 201901 and 201912",
            etiqueta]


# --- ganancia ------------------------------------------------------------------------------------


def ganancia_al_corte(prob: np.ndarray, ternaria: np.ndarray, cli: np.ndarray, envios: int = ENVIOS) -> dict:
    """Implementación propia: mayor probabilidad primero; a igual probabilidad, menor numero_de_cliente."""
    orden = np.lexsort((cli, -prob))
    top = orden[:envios]
    clases = ternaria[top]
    b2, b1, co = (int((clases == c).sum()) for c in ("BAJA+2", "BAJA+1", "CONTINUA"))
    if b2 + b1 + co != len(top):
        raise RuntimeError("hay clases fuera de BAJA+1, BAJA+2 y CONTINUA entre los estimulados")
    umbral = prob[top[-1]]
    return {"envios": int(len(top)), "ganancia": int(b2 * GANANCIA_BAJA2 - (len(top) - b2) * COSTO_ESTIMULO),
            "baja2": b2, "baja1": b1, "continua": co, "prob_corte": float(umbral),
            "empatados_en_el_corte": int((prob == umbral).sum()),
            "empatados_dentro": int((prob[top] == umbral).sum())}


def ganancia_grupo(grp, prob: np.ndarray, ternaria: np.ndarray, cli: np.ndarray, envios: int = ENVIOS) -> float:
    """El módulo del grupo sobre las filas en su orden de panel (numero_de_cliente creciente dentro del mes)."""
    o = np.argsort(cli, kind="stable")
    return grp.ganancia(prob[o], ternaria[o] == "BAJA+2", envios)


# --- pruebas sintéticas --------------------------------------------------------------------------


def pruebas_sinteticas(grp) -> dict:
    r = {}
    # 1. el test del grupo (10 scores) con la implementación propia
    s = np.array([0.9, 0.1, 0.8, 0.2, 0.7, 0.3, 0.6, 0.4, 0.5, 0.0])
    b = np.array([1, 0, 1, 0, 0, 1, 0, 0, 1, 0], bool)
    t = np.where(b, "BAJA+2", "CONTINUA").astype(object)
    c = np.arange(10)
    A, C = GANANCIA_BAJA2, COSTO_ESTIMULO
    esp = np.cumsum([A, A, -C, -C, A, -C, A, -C, -C, -C])
    r["test_10_scores_del_grupo"] = all(ganancia_al_corte(s, t, c, k)["ganancia"] == esp[k - 1] for k in range(1, 11)) \
        and ganancia_al_corte(s, t, c, 100)["ganancia"] == esp[-1]
    # 2. BAJA+1 entre los estimulados cuesta como CONTINUA
    t1 = np.array(["BAJA+1", "BAJA+2", "CONTINUA"], object)
    g1 = ganancia_al_corte(np.array([0.9, 0.8, 0.7]), t1, np.arange(3), 3)
    r["baja1_cuesta"] = g1["ganancia"] == A - 2 * C and (g1["baja1"], g1["baja2"], g1["continua"]) == (1, 1, 1)
    # 3. desempate: a igual probabilidad entra el menor numero_de_cliente, sin importar el orden de las filas
    pe = np.array([0.5, 0.5, 0.5, 0.9])
    te = np.array(["CONTINUA", "BAJA+2", "CONTINUA", "CONTINUA"], object)
    ce = np.array([30, 10, 20, 40])
    g_e = ganancia_al_corte(pe, te, ce, 2)
    r["desempate_menor_cliente"] = g_e["baja2"] == 1 and g_e["empatados_en_el_corte"] == 3 and g_e["empatados_dentro"] == 1
    # 4. azar con muchos empates: propia == grupo en cualquier orden de filas y cualquier corte
    rng = np.random.default_rng(8)
    n = 20_000
    prob = np.round(rng.random(n) ** 3, 3)  # pocos valores distintos: empates en todos los cortes
    tern = rng.choice(np.array(["CONTINUA", "BAJA+1", "BAJA+2"], object), n, p=[0.97, 0.015, 0.015])
    cli = rng.choice(10**8, n, replace=False)
    ok = True
    for envios in (1, 50, 3_300, 3_301, n, n + 7):
        ref = ganancia_al_corte(prob, tern, cli, envios)["ganancia"]
        for perm in (np.arange(n), rng.permutation(n), rng.permutation(n)):
            ok &= ganancia_al_corte(prob[perm], tern[perm], cli[perm], envios)["ganancia"] == ref
            ok &= ganancia_grupo(grp, prob[perm], tern[perm], cli[perm], envios) == ref
    r["propia_igual_al_grupo_con_empates"] = bool(ok)
    # 5. el orden de las filas sí importa en el módulo del grupo si no se ordena por cliente (control del test 4)
    r["sin_ordenar_el_grupo_cambia"] = grp.ganancia(pe, te == "BAJA+2", 2) == -2 * C \
        and ganancia_grupo(grp, pe, te, ce, 2) == g_e["ganancia"] == A - C
    # 6. etiqueta: SQL del grupo contra la regla de 03 sobre un crudo sintético con casos borde
    r["etiqueta_sql_grupo_igual_a_03"] = prueba_etiqueta()
    r = {k: bool(v) for k, v in r.items()}
    if not all(r.values()):
        raise RuntimeError(f"fallaron pruebas sintéticas: {r}")
    return r


def prueba_etiqueta() -> bool:
    meses = [201901 + i for i in range(12)]
    patrones = {  # cliente: meses presentes (índices 0..11)
        1: range(12),                       # continua siempre
        2: range(10),                       # sale en 201911: BAJA+2 en 201909, BAJA+1 en 201910
        3: list(range(8)) + [9, 10, 11],    # falta 201909 y vuelve: BAJA+1 en 201908 (regla de 03 y del grupo)
        4: [9, 10, 11],                     # alta en 201910
        5: [9],                             # sólo 201910: BAJA+1
        6: [9, 10],                         # 201910 y 201911: BAJA+2 en 201910
        7: [0, 2, 3, 5, 7, 9, 11],          # salteado
        8: range(2, 8),                     # sale en 201909: BAJA+1 en 201908
        9: range(0, 6),                     # sale en 201907: BAJA+2 en 201905
    }
    filas = [(c, meses[i]) for c, ms in patrones.items() for i in ms]
    df = pd.DataFrame(filas, columns=["numero_de_cliente", "foto_mes"])
    with tempfile.TemporaryDirectory() as d:
        csv = Path(d) / "crudo.csv"
        pq = Path(d) / "crudo.parquet"
        df.to_csv(csv, index=False)
        con = duckdb.connect()
        con.execute(f"COPY (SELECT * FROM read_csv('{csv.as_posix()}')) TO '{pq.as_posix()}' (FORMAT parquet)")
        for q in sql_grupo(csv.as_posix()):
            con.execute(q)
        g = con.execute("SELECT numero_de_cliente, foto_mes, clase_ternaria FROM etiqueta").df()
        p = con.execute(B03.SQL_TARGET, [pq.as_posix()]).df()
        con.close()
    m = g.merge(p, on=["numero_de_cliente", "foto_mes"], how="left", suffixes=("_grupo", "_03"))
    esperado = {(2, 201910): "BAJA+1", (3, 201908): "BAJA+1", (5, 201910): "BAJA+1", (6, 201910): "BAJA+2",
                (2, 201908): "CONTINUA", (7, 201910): "BAJA+1", (7, 201908): "BAJA+1", (8, 201908): "BAJA+1",
                (9, 201905): "BAJA+2", (4, 201910): "CONTINUA"}
    cubre = set(g["foto_mes"]) == {201903, 201904, 201905, 201906, 201908, 201910}
    iguales = bool((m["clase_ternaria_grupo"] == m["clase_ternaria_03"]).all())
    ok_esp = all(m.loc[(m.numero_de_cliente == c) & (m.foto_mes == f), "clase_ternaria_grupo"].item() == v
                 for (c, f), v in esperado.items())
    return cubre and iguales and ok_esp


# --- datos ---------------------------------------------------------------------------------------


def etiquetas_grupo(mats: Path) -> tuple[dict, pd.DataFrame]:
    """Etiqueta del grupo sobre el crudo (sólo claves) comparada con el target de insumos.py, por cliente y mes."""
    con = duckdb.connect()
    con.execute(f"SET threads = {HILOS}")
    con.execute("SET memory_limit = '2GB'")
    con.execute(f"SET temp_directory = '{(mats / 'duckdb').as_posix()}'")
    for q in sql_grupo(rutas.crudo().as_posix()):
        con.execute(q)
    tipo_id = con.execute("SELECT data_type FROM duckdb_columns() WHERE table_name = 'crudo' "
                          "AND column_name = 'numero_de_cliente'").fetchone()[0]
    no_entero = con.execute("SELECT count(*) FROM etiqueta WHERE numero_de_cliente <> round(numero_de_cliente)").fetchone()[0]
    con.execute(f"""CREATE TABLE nuestro AS SELECT numero_de_cliente, foto_mes, clase_ternaria
                    FROM read_parquet('{rutas.target().as_posix()}')
                    WHERE foto_mes IN (201903, 201904, 201905, 201906, 201908, 201910)""")
    por_mes = con.execute("""
        SELECT foto_mes,
               count(*) FILTER (WHERE g.clase_ternaria IS NOT NULL AND n.clase_ternaria IS NOT NULL) AS ambos,
               count(*) FILTER (WHERE n.numero_de_cliente IS NULL) AS solo_grupo,
               count(*) FILTER (WHERE g.numero_de_cliente IS NULL) AS solo_03,
               count(*) FILTER (WHERE g.clase_ternaria IS DISTINCT FROM n.clase_ternaria
                                AND g.numero_de_cliente IS NOT NULL AND n.numero_de_cliente IS NOT NULL) AS distintas,
               count(*) FILTER (WHERE g.clase_ternaria = 'BAJA+2') AS baja2_grupo,
               count(*) FILTER (WHERE n.clase_ternaria = 'BAJA+2') AS baja2_03
        FROM (SELECT CAST(numero_de_cliente AS BIGINT) AS numero_de_cliente, foto_mes, clase_ternaria FROM etiqueta) g
        FULL JOIN nuestro n USING (numero_de_cliente, foto_mes)
        GROUP BY foto_mes ORDER BY foto_mes""").df()
    detalle = con.execute("""
        SELECT n.numero_de_cliente, n.foto_mes, g.clase_ternaria AS grupo, n.clase_ternaria AS nuestra
        FROM (SELECT CAST(numero_de_cliente AS BIGINT) AS numero_de_cliente, foto_mes, clase_ternaria FROM etiqueta) g
        FULL JOIN nuestro n USING (numero_de_cliente, foto_mes)
        WHERE g.clase_ternaria IS DISTINCT FROM n.clase_ternaria""").df()
    oct_ = con.execute("""SELECT CAST(numero_de_cliente AS BIGINT) AS numero_de_cliente, clase_ternaria
                          FROM etiqueta WHERE foto_mes = 201910 ORDER BY 1""").df()
    con.close()
    tabla = {int(r.foto_mes): {k: int(getattr(r, k)) for k in ("ambos", "solo_grupo", "solo_03", "distintas",
                                                               "baja2_grupo", "baja2_03")} for r in por_mes.itertuples()}
    ref = B07.leer_json(B07.HUELLAS)["etiquetas_grupo_vs_03"]
    info = {"fuente": rutas.crudo().name, "tipo_numero_de_cliente_en_el_crudo": tipo_id,
            "ids_no_enteros": int(no_entero), "por_mes": tabla, "discrepancias": int(len(detalle)),
            "coinciden_en_201910": tabla[MES_TEST]["distintas"] == tabla[MES_TEST]["solo_grupo"]
                                   == tabla[MES_TEST]["solo_03"] == 0,
            "igual_a_la_referencia": {str(k): v for k, v in tabla.items()} == ref}
    return info, oct_


def cargar_mes(mats: Path, mes: int, pred: list[str]) -> dict:
    """Carga validada (carga.py: unión 1:1, BIGINT -> float64 exacto, NULL -> NaN) para un mes."""
    con = duckdb.connect()
    con.execute(f"SET threads = {HILOS}")
    con.execute("SET memory_limit = '1GB'")
    con.execute("SET preserve_insertion_order = true")
    con.execute(f"SET temp_directory = '{(mats / 'duckdb').as_posix()}'")
    tipos = {c: t for c, t, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet({B05.archivos([mes])})").fetchall()}
    union = B05.validar_union(con, [mes])
    if not all(union["checks"].values()):
        raise RuntimeError(f"unión {mes} inválida: {union['checks']}")
    perfil = B05.perfil_tipos(con, [mes], pred, tipos)
    if not perfil["bigint_exacto_en_float64"]:
        raise RuntimeError("hay BIGINT con |x| > 2^53")
    X, cli, mes_ = B05.cargar(con, [mes], pred, tipos, mats / f"X_{mes}.npy")
    y, tern = B05.etiquetas(con, [mes], cli, mes_)
    con.close()
    if set(np.unique(mes_).tolist()) != {mes} or len(np.unique(cli)) != len(cli):
        raise RuntimeError(f"{mes}: meses o clientes inesperados")
    return {"X": X, "y": y, "tern": tern, "cli": cli, "mes": mes_,
            "info": {"union": union, "tipos": perfil, "filas": int(len(y)),
                     "sha256_claves": B07.sha(cli, mes_), "sha256_X": B07.sha_matriz(X)}}


# --- modelos de 07 -------------------------------------------------------------------------------


def elecciones_07(corrida: Path) -> tuple[int, dict[int, int], dict, dict]:
    """Ganadora de Control y elegida por semilla, recalculadas desde ajustes.jsonl y comparadas con 07."""
    diseno = B07.leer_json(corrida / "diseno.json")
    ids_cfg = diseno["configuraciones"]["ids"]
    semillas = diseno["semillas"]["muestreo"]
    ajustes = [json.loads(l) for l in (corrida / "ajustes.jsonl").read_text(encoding="utf-8").splitlines()]
    ctrl = {r["id"]: r for r in ajustes if r["variante"] == "control"}
    sel = B07.leer_json(corrida / "control_seleccion.json")
    resumen = pd.read_csv(corrida / "resumen_por_semilla.csv")
    ganadora = B07.ranking(list(ctrl.values()))[0]["id"]
    elegidas = {}
    for s in semillas:
        h = [r for r in ajustes if r["variante"] == "h3" and r["semilla_muestra"] == s]
        if len(h) != len(ids_cfg):
            raise RuntimeError(f"semilla {s}: {len(h)} ajustes de H3, se esperaban {len(ids_cfg)}")
        elegidas[s] = B07.ranking(h)[0]["id"]
    del_resumen = dict(zip(resumen["semilla_muestra"].astype(int), resumen["config_h3"].astype(int)))
    ok = sorted(ctrl) == sorted(ids_cfg) and ganadora == sel["ganadora"] and elegidas == del_resumen
    if diseno["modo"] == "completa":
        ok &= ganadora == GANADORA_REPORTADA and len(ids_cfg) == B06.N_CONFIG
    if not ok:
        raise RuntimeError(f"las elecciones no coinciden con 07: Control {ganadora}/{sel['ganadora']}, H3 {elegidas}")
    return ganadora, elegidas, ctrl, diseno


def verificar_modelos(corrida: Path, ids: list[int], ctrl: dict, agosto: dict) -> tuple[dict[int, lgb.Booster], dict]:
    """Cada modelo guardado reproduce exactamente su predicción de agosto en 07 y sus parámetros efectivos."""
    pred07 = B07.leer_parquet(corrida / "control" / "predicciones_201908.parquet")
    if not (np.array_equal(np.asarray(pred07["numero_de_cliente"], np.int64), agosto["cli"])
            and np.array_equal(np.asarray(pred07["foto_mes"], np.int64), agosto["mes"])):
        raise RuntimeError("agosto no está en el orden de carga de 07")
    modelos, info = {}, {}
    for i in ids:
        ruta = corrida / "control" / f"modelo_{i:02d}.txt"
        b = lgb.Booster(model_file=str(ruta))
        ef = B06.efectivos(b)
        p = b.predict(agosto["X"], num_threads=HILOS)
        guardada = np.load(corrida / ctrl[i]["predicciones"])
        info[i] = {"archivo": f"control/modelo_{i:02d}.txt", "sha256_modelo": B07.sha_archivo(ruta),
                   "arboles": b.num_trees(), "parametros_efectivos_iguales_a_07": ef == ctrl[i]["parametros_efectivos"],
                   "prediccion_agosto_identica": B07.sha(p) == ctrl[i]["sha256_predicciones"]
                                                 and np.array_equal(p, guardada),
                   "max_dif_agosto": float(np.abs(p - guardada).max())}
        if not (info[i]["parametros_efectivos_iguales_a_07"] and info[i]["prediccion_agosto_identica"]
                and b.num_trees() == B06.ARBOLES):
            raise RuntimeError(f"el modelo {i} no es el de 07: {info[i]}")
        modelos[i] = b
    return modelos, info


# --- principal -----------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ganancia en 201910 de Control y H3 (modelos de 07, corte fijo).")
    ap.add_argument("--corrida-07", type=Path, help="carpeta de la corrida de sensibilidad_07 (su salida)")
    ap.add_argument("--repo-grupal", type=Path, default=rutas_grupo.RAIZ,
                    help="clon con el commit de referencia (por defecto, este repo)")
    ap.add_argument("--salida", type=Path, default=None,
                    help="carpeta de ejecuciones (por defecto DATOS_DIR/h3_sensibilidad_muestra/ejecuciones)")
    ap.add_argument("--solo-pruebas", action="store_true", help="sólo verificación de referencia y pruebas sintéticas")
    ap.add_argument("--hasta-modelos", action="store_true",
                    help="recorrido corto: elecciones y modelos de 07 verificados con agosto; no lee 201910")
    a = ap.parse_args(argv)
    if not a.solo_pruebas and a.corrida_07 is None:
        ap.error("--corrida-07 es obligatorio salvo con --solo-pruebas")
    t0 = time.perf_counter()
    proc = psutil.Process()
    salida = (a.salida or rutas.salida_por_defecto()).resolve()
    corrida = a.corrida_07.resolve() if a.corrida_07 else None
    modo_corto = a.solo_pruebas or a.hasta_modelos
    if corrida is not None and not a.solo_pruebas:
        modo07 = B07.leer_json(corrida / "diseno.json")["modo"]
        if modo07 != "completa" and not a.hasta_modelos:
            raise RuntimeError("la corrida de 07 es de prueba: sólo se admite con --hasta-modelos (no se mira 201910)")
    run = salida / (NOMBRE + ("_prueba" if modo_corto else "")) / f"{time.strftime('%Y%m%dT%H%M%S')}_{os.getpid()}"
    run.mkdir(parents=True, exist_ok=False)
    mats = run / "matrices_tmp"
    mats.mkdir()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S",
                        handlers=[logging.FileHandler(run / "log.txt", encoding="utf-8"),
                                  logging.StreamHandler(sys.stdout)])
    log.info("Corrida %s | %s", run.as_posix(),
             "SÓLO PRUEBAS" if a.solo_pruebas else "HASTA MODELOS" if a.hasta_modelos else "completa")
    sesion = B07.Sesion(run, proc, False)
    datos = {}
    rep = {"naturaleza": "evaluación final en 201910 autorizada por el grupo; sin reentrenar; corte fijo de "
                         f"{ENVIOS} envíos (N* del control del grupo, de 201908); octubre no elige nada",
           "corrida_07": corrida.name if corrida else None, "script_sha256": B07.sha_archivo(Path(__file__))}
    try:
        grp, rep["referencia_grupo"] = referencia_grupo(a.repo_grupal.resolve(), run / "referencia_grupo")
        log.info("referencia %s: %s", rep["referencia_grupo"]["commit"][:7], rep["referencia_grupo"]["checks"])
        rep["pruebas_sinteticas"] = pruebas_sinteticas(grp)
        log.info("pruebas sintéticas: %s", rep["pruebas_sinteticas"])
        sesion.etapa("referencia_y_pruebas")
        if a.solo_pruebas:
            B07.escribir_json(run / "reporte.json", rep)
            return 0

        ganadora, elegidas, ctrl, diseno07 = elecciones_07(corrida)
        ids = sorted({ganadora, *elegidas.values()})
        rep["elecciones_07"] = {"modo_07": diseno07["modo"], "control": ganadora,
                                "h3_por_semilla": {str(s): e for s, e in elegidas.items()},
                                "configuraciones_a_predecir": ids, "modelos_distintos": len(ids)}
        log.info("Control cfg %d | H3 %s | modelos distintos %s", ganadora, elegidas, ids)

        pred = B07.leer_json(rutas.features_dir() / "manifiesto.json")["predictores"]
        if len(pred) != 760 or B06.sha256_bytes(json.dumps(pred).encode()) != diseno07["datos"]["sha256_predictores"]:
            raise RuntimeError("predictores fuera del diseño o distintos a los de la corrida de 07")
        datos["agosto"] = cargar_mes(mats, 201908, pred)
        modelos, rep["modelos"] = verificar_modelos(corrida, ids, ctrl, datos["agosto"])
        log.info("modelos verificados contra 07: %s", {i: v["prediccion_agosto_identica"] for i, v in rep["modelos"].items()})
        datos["agosto"].clear()
        gc.collect()
        sesion.etapa("verificacion_modelos")
        if a.hasta_modelos:
            B07.escribir_json(run / "reporte.json", rep)
            log.info("--hasta-modelos: 201910 no se lee")
            return 0

        rep["etiquetas_grupo"], oct_grupo = etiquetas_grupo(mats)
        log.info("etiquetas del grupo vs 03: %s", rep["etiquetas_grupo"]["por_mes"])
        sesion.etapa("etiquetas_grupo")

        B05.MES_PROHIBIDO = None  # carga.py bloquea 201910; esta es la evaluación final autorizada
        datos["octubre"] = cargar_mes(mats, MES_TEST, pred)
        o = datos["octubre"]
        rep["octubre"] = {k: o["info"][k] for k in ("filas", "sha256_claves", "sha256_X", "union", "tipos")}
        rep["octubre"]["clases"] = {c: int((o["tern"] == c).sum()) for c in ("BAJA+2", "BAJA+1", "CONTINUA")}
        ref_oct = B07.leer_json(B07.HUELLAS)["octubre"]
        rep["octubre"]["igual_a_la_referencia"] = all(rep["octubre"][k] == ref_oct[k] for k in ref_oct)
        if not rep["octubre"]["igual_a_la_referencia"]:
            raise RuntimeError("BLOQUEO: 201910 no es el de las corridas reportadas (huellas distintas)")
        orden_cli = np.argsort(o["cli"], kind="stable")
        tern_grupo = oct_grupo["clase_ternaria"].to_numpy(object)
        if not np.array_equal(oct_grupo["numero_de_cliente"].to_numpy(np.int64), o["cli"][orden_cli]):
            raise RuntimeError("los clientes de 201910 del grupo no son los de las features")
        sesion.etapa("carga_octubre")

        probs, t_pred = {}, {}
        for i in ids:
            t = time.perf_counter()
            probs[i] = modelos[i].predict(o["X"], num_threads=HILOS)
            t_pred[i] = round(time.perf_counter() - t, 2)
            if not (np.isfinite(probs[i]).all() and ((probs[i] >= 0) & (probs[i] <= 1)).all()):
                raise RuntimeError("probabilidades fuera de [0, 1]")
        sesion.etapa("prediccion_octubre", segundos_por_modelo=t_pred)

        t = time.perf_counter()
        por_cfg = {}
        for i in ids:
            g = ganancia_al_corte(probs[i], o["tern"], o["cli"])
            g_grupo = ganancia_grupo(grp, probs[i], o["tern"], o["cli"])
            g_etiq_grupo = grp.ganancia(probs[i][orden_cli], tern_grupo == "BAJA+2", ENVIOS)
            curva = grp.curva_de_corte(probs[i][orden_cli], tern_grupo == "BAJA+2")
            g.update({"ganancia_modulo_grupo": g_grupo, "ganancia_etiquetas_grupo": g_etiq_grupo,
                      "ganancia_curva_grupo": float(curva.set_index("envios")["ganancia"].loc[ENVIOS]),
                      "segundos_prediccion": t_pred[i]})
            # con etiquetas distintas la diferencia se informa (etiquetas_grupo), no bloquea
            g["igual_con_etiquetas_del_grupo"] = g_etiq_grupo == g["ganancia"]
            if not g["ganancia"] == g_grupo:
                raise RuntimeError(f"cfg {i}: la ganancia propia no coincide con la del módulo del grupo: {g}")
            if rep["etiquetas_grupo"]["coinciden_en_201910"] and not g_etiq_grupo == g["ganancia_curva_grupo"] == g_grupo:
                raise RuntimeError(f"cfg {i}: con las mismas etiquetas, la curva del grupo da otra ganancia: {g}")
            por_cfg[i] = g
            log.info("cfg %02d | ganancia %s | BAJA+2 %d | BAJA+1 %d | CONTINUA %d | empates en el corte %d",
                     i, f"{g['ganancia']:,}", g["baja2"], g["baja1"], g["continua"], g["empatados_en_el_corte"])
        gc_ = por_cfg[ganadora]["ganancia"]
        filas = []
        for s, e in elegidas.items():
            gh = por_cfg[e]["ganancia"]
            filas.append({"semilla_muestra": s, "config_h3": e, "ganancia_h3": gh, "baja2_h3": por_cfg[e]["baja2"],
                          "ganancia_control": gc_, "baja2_control": por_cfg[ganadora]["baja2"],
                          "delta": gh - gc_, "delta_pct": 100 * (gh - gc_) / gc_})
        tabla = pd.DataFrame(filas)
        tabla.to_csv(run / "ganancia_por_semilla.csv", index=False)
        pd.DataFrame([{"config": i, "rol": "control" if i == ganadora else "h3", **v} for i, v in por_cfg.items()]) \
            .to_csv(run / "ganancia_por_configuracion.csv", index=False)
        B07.copiar_parquet(pd.DataFrame({"numero_de_cliente": o["cli"], "foto_mes": o["mes"],
                                         **{f"prob_cfg_{i:02d}": probs[i] for i in ids}}),
                           run / "predicciones_201910.parquet")
        sesion.etapa("ganancia")

        def rango(col):
            v = tabla[col].to_numpy(dtype=float)
            return {"mediana": float(np.median(v)), "min": float(v.min()), "max": float(v.max())}

        rep.update({
            "corte": {"envios": ENVIOS, "origen": "N* del control del grupo en 201908 (informe de h3); no se ajusta "
                                                  "con octubre",
                      "importes": {"BAJA+2": GANANCIA_BAJA2, "BAJA+1": -COSTO_ESTIMULO, "CONTINUA": -COSTO_ESTIMULO},
                      "desempate": "a igual probabilidad, menor numero_de_cliente"},
            "por_configuracion": {str(i): v for i, v in por_cfg.items()},
            "por_semilla": filas,
            "delta": rango("delta"), "delta_pct": rango("delta_pct"),
            "semillas_con_la_ganadora_de_control": int((tabla["config_h3"] == ganadora).sum()),
            "versiones": {"python": sys.version.split()[0], "plataforma": platform.platform(),
                          "procesador": platform.processor(), "nucleos_logicos": psutil.cpu_count(),
                          "lightgbm": lgb.__version__, "sklearn": sklearn.__version__, "numpy": np.__version__,
                          "pandas": pd.__version__, "duckdb": duckdb.__version__},
            "tiempos": {"prediccion_por_modelo_s": t_pred, "ganancia_y_verificacion_s": round(time.perf_counter() - t, 2),
                        "sesion": "sesiones.json"},
            "memoria": B05.memoria(proc),
        })
        B07.escribir_json(run / "reporte.json", rep)
        log.info("delta mediana %s [%s, %s] | %%: %.3f [%.3f, %.3f]", f"{rep['delta']['mediana']:,.0f}",
                 f"{rep['delta']['min']:,.0f}", f"{rep['delta']['max']:,.0f}", rep["delta_pct"]["mediana"],
                 rep["delta_pct"]["min"], rep["delta_pct"]["max"])
        return 0
    finally:
        for d in datos.values():
            d.clear()
        datos = None
        gc.collect()
        borrado = B07.borrar(mats)
        sesion.guardar(fin=time.strftime("%Y-%m-%dT%H:%M:%S"), total_s=round(time.perf_counter() - t0, 1),
                       temporales_borrados=borrado, memoria_fin=B05.memoria(proc))
        log.info("Fin en %.1fs", time.perf_counter() - t0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.exception("la corrida falló")
        raise
