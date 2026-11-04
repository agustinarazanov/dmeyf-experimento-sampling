"""Ganancia, desempate y etiqueta contra el código del grupo en el commit de referencia 4a42bc6 (sin datos)."""
import numpy as np
import pytest

from comun import ganancia as ganancia_head
from comun import rutas as rutas_grupo
from experimentos.h3.sensibilidad_muestra import ganancia_08 as g08


@pytest.fixture(scope="module")
def grupo_ref(tmp_path_factory):
    grp, info = g08.referencia_grupo(rutas_grupo.RAIZ, tmp_path_factory.mktemp("referencia"))
    return grp, info


def test_referencia_4a42bc6(grupo_ref):
    _, info = grupo_ref
    assert info["commit"].startswith("4a42bc6")
    assert all(info["checks"].values())


def test_pruebas_sinteticas_con_el_modulo_de_la_referencia(grupo_ref):
    grp, _ = grupo_ref
    assert all(g08.pruebas_sinteticas(grp).values())


def test_pruebas_sinteticas_con_comun_ganancia_de_head():
    assert all(g08.pruebas_sinteticas(ganancia_head).values())


def test_desempate_menor_cliente_en_el_corte():
    prob = np.array([0.9, 0.5, 0.5, 0.5, 0.1])
    tern = np.array(["CONTINUA", "CONTINUA", "BAJA+2", "BAJA+1", "BAJA+2"], object)
    cli = np.array([5, 30, 10, 20, 1])
    g = g08.ganancia_al_corte(prob, tern, cli, 2)
    # entran 5 (0,9) y 10 (el menor de los empatados en 0,5)
    assert (g["baja2"], g["continua"], g["empatados_en_el_corte"], g["empatados_dentro"]) == (1, 1, 3, 1)
    assert g["ganancia"] == g08.GANANCIA_BAJA2 - g08.COSTO_ESTIMULO
    assert g08.ganancia_grupo(ganancia_head, prob, tern, cli, 2) == g["ganancia"]


def test_etiqueta_sql_grupo_igual_a_insumos():
    assert g08.prueba_etiqueta()
