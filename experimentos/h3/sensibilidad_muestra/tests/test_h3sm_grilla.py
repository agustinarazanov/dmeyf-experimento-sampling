"""La grilla de 06 y las muestras de H3 se regeneran exactamente desde lo versionado (sin datos)."""
import json

import numpy as np

from comun import muestreo
from experimentos.h3.sensibilidad_muestra import busqueda, rutas
from experimentos.h3.sensibilidad_muestra import sensibilidad_07 as s07


def _json(nombre):
    return json.loads((rutas.REFERENCIA / nombre).read_text(encoding="utf-8"))


def test_grilla_regenerada_igual_a_la_versionada():
    configs, huella = busqueda.cargar_grilla()  # bloquea si algo difiere
    g = _json("grilla_06.json")
    assert [c["id"] for c in configs] == list(range(20))
    assert configs == g["configuraciones"] and huella == g["sha256"]
    assert g["fijos"] == busqueda.FIJOS and g["arboles"] == 100
    # las elegidas que se reportan
    por_id = {c["id"]: c for c in configs}
    assert por_id[6] == {"id": 6, "num_leaves": 47, "learning_rate": 0.0329875, "min_data_in_leaf": 784,
                         "feature_fraction": 0.642466, "bagging_fraction": 0.641699}
    assert (por_id[13]["num_leaves"], por_id[16]["num_leaves"], por_id[3]["num_leaves"]) == (34, 47, 49)


def test_muestras_comun_igual_al_generador_de_07_y_a_la_referencia():
    ref = _json("huellas_datos.json")
    n = ref["train"]["filas"]
    assert (n, ref["train"]["positivos"]) == (506_871, 5_313)
    for s in s07.SEMILLAS_MUESTRA:
        idx = np.asarray(muestreo.indices_uniformes(n, s07.TASA_MUESTRA, s), np.int64)
        original = np.sort(np.random.default_rng(s).choice(n, size=s07.FILAS_MUESTRA, replace=False)).astype(np.int64)
        assert len(idx) == s07.FILAS_MUESTRA and np.array_equal(idx, original)
        assert s07.sha(idx) == ref["muestras"][str(s)]["sha256_indices"]


def test_particion_y_semillas_documentadas():
    g = _json("grilla_06.json")
    assert g["semillas"]["muestreo_h3"] == s07.SEMILLAS_MUESTRA
    assert g["semillas"]["modelo"] == s07.SEMILLA_MODELO == g["fijos"]["seed"]
    assert _json("huellas_datos.json")["particion_201908"]["conteos"] == {
        "seleccion": {"filas": 65887, "positivos": 601, "negativos": 65286},
        "evaluacion": {"filas": 65888, "positivos": 601, "negativos": 65287}}
