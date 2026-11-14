"""inicio-y-resultados 1.4: ensamble según K y según el tiempo, IC por ronda y curvas de ganancia por hipótesis."""

import pandas as pd
import pytest

from comun import reporte, rutas
from comun import variantes as reg


def test_figuras_nuevas_sin_datos_salen_pendientes():
    ctx = reporte.Contexto(reg.AGREGADOR)
    vacio = pd.DataFrame()
    a = {"filas": [], "rep": pd.DataFrame(), "semillas": {}, "delta": 0.0}
    assert "class='pend'" in reporte.fig_ensamble(ctx, vacio, vacio, a, None)
    assert "class='pend'" in reporte.fig_ic_rondas(ctx, a, None, vacio)
    assert "class='pend'" in reporte.fig_curvas_ganancia(ctx, "H1", vacio, vacio, None)


def test_ensamble_de_20_semillas_del_control_coincide_con_tiempo_igual():
    ctx, fin, ap, a = reporte._agregador({})
    g_c20, _ = reporte.calcular_tiempo_igual(ctx, fin, ap)
    curvas = reporte.curvas_ensamble(ctx, fin, ap, a)
    k, _, g = curvas[reporte.lg.CONTROL][-1]
    assert k == reporte.N_SEMILLAS and g == pytest.approx(g_c20)
    assert all(len(p) == reporte.N_SEMILLAS for p in curvas.values())


def test_figuras_nuevas_con_datos_son_deterministas_y_llevan_titulo():
    ctx, fin, ap, a = reporte._agregador({})
    hacer = (lambda: reporte.fig_ensamble(ctx, fin, ap, a, None), lambda: reporte.fig_ic_rondas(ctx, a, None),
             lambda: reporte.fig_curvas_ganancia(ctx, "H3", fin, ap, None))
    for f in hacer:
        salidas = []
        for _ in range(2):
            reporte.DESTINO = reporte.Destino(rutas.RAIZ / "x")
            try:
                salidas.append((f(), dict(reporte.DESTINO.archivos)))
            finally:
                reporte.DESTINO = None
        (e1, a1), (e2, a2) = salidas
        assert e1 == e2 and a1 == a2 and a1 and "![" in e1 and "class='pend'" not in e1
