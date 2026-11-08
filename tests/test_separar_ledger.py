import json

import pandas as pd
import pytest

from comun import ledger as lg
from scripts import separar_ledger as sep

VARIANTES = [("C", "uniforme", 1.0, "C"), ("U0.25", "uniforme", 0.25, "U0.25"), ("H3-0.25", "opt-muestra", 0.25, "U0.25")]


def armar_origen(raiz):
    origen = raiz / "experimentos" / "sampling_1" / "ledger"
    for sub in ("hp", "corridas", "curvas", "predicciones", "exploracion", "sesiones"):
        (origen / sub).mkdir(parents=True)
    filas = []
    for variante, metodo, tasa, estudio in VARIANTES:
        for semilla, etapa in [(0, "optimizar"), (1, "final"), (2, "final")]:
            if etapa == "optimizar" and variante.startswith("H3"):
                continue
            id_ = f"{variante}_{metodo}_{tasa:g}_{semilla}_{etapa}_abc"
            f = {c: "" for c in lg.COLUMNAS}
            f.update(id=id_, variante=variante, metodo=metodo, tasa=tasa, semilla=semilla, etapa=etapa, estudio=estudio, valida=True)
            filas.append(f)
            (origen / "corridas" / f"{id_}.csv").write_text("x\n")
            if etapa == "final":
                (origen / "curvas" / f"{id_}_201908.csv").write_text("x\n")
                (origen / "predicciones" / f"{id_}.parquet").write_text("x\n")
    tabla = pd.DataFrame(filas)
    tabla.to_csv(origen / "resultados.csv", index=False)
    tabla[tabla["etapa"] == "optimizar"].to_csv(origen / "estudios.csv", index=False)
    tabla.head(2).assign(reemplazada_por="z").to_csv(origen / "reemplazadas.csv", index=False)
    for estudio in ("C", "U0.25"):
        (origen / "hp" / f"{estudio}.json").write_text(json.dumps({"estudio": estudio}))
    (origen / "exploracion" / "log.txt").write_text("x")
    (origen / "tokens.csv").write_text("a\n")
    return origen


def test_reparte_sin_perder_ni_duplicar_ningun_id(tmp_path):
    origen = armar_origen(tmp_path)
    antes = {t: set(pd.read_csv(origen / f"{t}.csv")["id"]) for t in sep.TABLAS}
    sep.separar(origen, raiz=tmp_path)
    assert sep.verificar(origen, raiz=tmp_path) == []
    led = lambda e: tmp_path / "experimentos" / e / "ledger"
    for t in sep.TABLAS:
        partes = [list(pd.read_csv(led(e) / f"{t}.csv")["id"]) for e in ("control", "h1", "h3") if (led(e) / f"{t}.csv").exists()]
        union = [i for p in partes for i in p]
        assert len(union) == len(set(union)) and set(union) == antes[t]
    assert list(pd.read_csv(led("h3") / "resultados.csv")["variante"].unique()) == ["H3-0.25"]
    # hp por dueño del estudio; H3 no tiene hp propio (lee el de h1)
    assert [p.name for p in (led("h1") / "hp").iterdir()] == ["U0.25.json"]
    assert not (led("h3") / "hp").exists()
    assert (led("control") / "hp" / "C.json").exists()
    # lo que no tiene variante queda
    assert (origen / "exploracion" / "log.txt").exists() and (origen / "tokens.csv").exists()
    assert not list((origen / "corridas").iterdir())


def test_verificar_detecta_un_id_perdido(tmp_path):
    origen = armar_origen(tmp_path)
    sep.separar(origen, raiz=tmp_path)
    f = tmp_path / "experimentos" / "h1" / "ledger" / "resultados.csv"
    pd.read_csv(f).iloc[1:].to_csv(f, index=False)
    assert any("resultados.csv" in p for p in sep.verificar(origen, raiz=tmp_path))


def test_variante_desconocido_falla_nombrandolo_y_no_mueve(tmp_path):
    origen = armar_origen(tmp_path)
    (origen / "corridas" / "ZZ_uniforme_0.5_1_final_abc.csv").write_text("x\n")
    with pytest.raises(ValueError, match="ZZ"):
        sep.separar(origen, raiz=tmp_path)
    assert len(list((origen / "corridas").iterdir())) == 9  # 8 de las tres variantes + la desconocida, ninguna movida
    assert not (tmp_path / "experimentos" / "h1" / "ledger" / "corridas").exists()
