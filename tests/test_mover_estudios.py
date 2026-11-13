"""`scripts/mover_estudios.py` (D10): mueve de h3 a h1 los estudios `U{r}@k` sin cambiar ids ni contenido, y se deshace."""

import json

import pandas as pd

from comun import ledger as lg
from scripts import mover_estudios as mv


def _fila(variante, id_, replica, etapa, estudio):
    f = {c: "" for c in lg.COLUMNAS}
    f.update(id=id_, variante=variante, replica_opt=str(replica), etapa=etapa, estudio=estudio, valida="True")
    return f


def armar(raiz):
    h1, h3 = (raiz / "experimentos" / e / "ledger" for e in ("h1", "h3"))
    for led in (h1, h3):
        for sub in ("hp", "corridas", "curvas"):
            (led / sub).mkdir(parents=True)
    filas1 = [_fila("U0.25", "U0.25_uniforme_0.25_0_optimizar_abc", 0, "optimizar", "U0.25")]
    filas3 = [_fila("U0.25", "U0.25@1_uniforme_0.25_1_optimizar_abc", 1, "optimizar", "U0.25@1"),
              _fila("H3-0.25", "H3-0.25_opt-muestra_0.25_1_final_abc", 1, "final", "U0.25@1"),
              _fila("H3-0.25", "H3-0.25_opt-muestra_0.25_2_final_abc", 0, "final", "U0.25")]
    pd.DataFrame(filas1).to_csv(h1 / "resultados.csv", index=False)
    pd.DataFrame(filas1).to_csv(h1 / "estudios.csv", index=False)
    pd.DataFrame(filas3).to_csv(h3 / "resultados.csv", index=False)
    pd.DataFrame(filas3[:1]).to_csv(h3 / "estudios.csv", index=False)
    (h1 / "hp" / "U0.25.json").write_text(json.dumps({"estudio": "U0.25"}))
    (h3 / "hp" / "U0.25@1.json").write_text(json.dumps({"estudio": "U0.25@1"}))
    (h1 / "corridas" / "U0.25_uniforme_0.25_0_optimizar_abc.csv").write_text("x\n")
    (h3 / "corridas" / "U0.25@1_uniforme_0.25_1_optimizar_abc.csv").write_text("x\n")
    (h3 / "corridas" / "H3-0.25_opt-muestra_0.25_1_final_abc.csv").write_text("x\n")
    (h3 / "curvas" / "H3-0.25_opt-muestra_0.25_1_final_abc_201910.csv").write_text("x\n")
    return h1, h3


def test_mueve_hp_corridas_y_filas_de_h3_a_h1_y_deja_lo_demas(tmp_path):
    h1, h3 = armar(tmp_path)
    plan = mv.planificar("h3", raiz=tmp_path)
    assert plan["hp"] == {"U0.25@1.json": "h1"}
    assert plan["corridas"] == {"U0.25@1_uniforme_0.25_1_optimizar_abc.csv": "h1"}
    assert plan["curvas"] == {}
    mv.mover_repo("h3", raiz=tmp_path)
    assert (h1 / "hp" / "U0.25@1.json").exists() and not (h3 / "hp" / "U0.25@1.json").exists()
    assert (h1 / "corridas" / "U0.25@1_uniforme_0.25_1_optimizar_abc.csv").exists()
    assert (h3 / "corridas" / "H3-0.25_opt-muestra_0.25_1_final_abc.csv").exists()  # las filas de H3 no se mueven
    for t in ("resultados", "estudios"):
        ids1 = set(pd.read_csv(h1 / f"{t}.csv")["id"])
        assert "U0.25@1_uniforme_0.25_1_optimizar_abc" in ids1
        assert "U0.25@1_uniforme_0.25_1_optimizar_abc" not in set(pd.read_csv(h3 / f"{t}.csv")["id"])
    assert len(pd.read_csv(h3 / "resultados.csv")) == 2 and len(pd.read_csv(h1 / "resultados.csv")) == 2


def test_no_pisa_un_archivo_que_ya_existe_en_el_destino(tmp_path):
    h1, h3 = armar(tmp_path)
    (h1 / "hp" / "U0.25@1.json").write_text("{}")
    try:
        mv.mover_repo("h3", raiz=tmp_path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("tenía que fallar")
    assert (h3 / "hp" / "U0.25@1.json").exists()  # no movió nada


def test_deshacer_devuelve_las_replicas_a_h3(tmp_path):
    h1, h3 = armar(tmp_path)
    antes = {t: pd.read_csv(h3 / f"{t}.csv", dtype=str, keep_default_na=False) for t in ("resultados", "estudios")}
    mv.mover_repo("h3", raiz=tmp_path)
    mv.mover_repo("h1", deshacer=True, raiz=tmp_path)
    assert (h3 / "hp" / "U0.25@1.json").exists() and not (h1 / "hp" / "U0.25@1.json").exists()
    assert (h1 / "hp" / "U0.25.json").exists()  # la réplica 0 sigue siendo de h1
    for t, previa in antes.items():
        despues = pd.read_csv(h3 / f"{t}.csv", dtype=str, keep_default_na=False)
        assert sorted(despues["id"]) == sorted(previa["id"])
        assert list(pd.read_csv(h1 / f"{t}.csv")["id"]) == ["U0.25_uniforme_0.25_0_optimizar_abc"]


def test_el_dueno_viejo_de_las_replicas_es_h3():
    assert mv.dueno_viejo_estudio("U0.25@1") == "h3" and mv.dueno_nuevo_estudio("U0.25@1") == "h1"
    assert mv.dueno_viejo_variante("U0.25@1") == "h3" and mv.dueno_nuevo_variante("U0.25@1") == "h1"
    assert mv.dueno_viejo_estudio("U0.25") == "h1" == mv.dueno_nuevo_estudio("U0.25")
