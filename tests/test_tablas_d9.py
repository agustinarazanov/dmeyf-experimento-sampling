"""inicio-y-resultados 1.8 y 1.9: tabla de una hipótesis sin redundancias y vocabulario de «clientes contactados»."""

import re

from comun import reporte
from comun import variantes as reg


def _h3():
    ctx = reporte.Contexto("h3")
    fin, ap = reporte.cargar([reg.CONTROL, "h3"])
    return ctx, fin, ap


def test_tabla_de_una_hipotesis_sin_redundancias():
    ctx, fin, ap = _h3()
    t = reporte.tabla_variantes(ctx, fin, ap)
    cab = re.findall(r"<th>(.*?)</th>", t)
    assert "hipótesis" not in cab and "semillas" not in cab
    assert {"aceleración (×)", "ganancia contra el control", "vale la pena (no pierde y ≥ 2×)"} <= set(cab)
    assert "A" not in cab and "veredicto" not in cab
    assert "Todas las variantes con 20 semillas." in t
    assert "class='prop'" in t  # semillas ganadas como barrita con su número


def test_si_las_semillas_difieren_la_columna_vuelve():
    ctx, fin, ap = _h3()
    ap = ap.copy()
    ap.loc[ctx.variantes[0], "n_semillas"] = 10
    ap.loc[ctx.variantes[0], "semillas_ganadas"] = min(10, ap.loc[ctx.variantes[0], "semillas_ganadas"])
    t = reporte.tabla_variantes(ctx, fin, ap)
    assert "semillas</th>" in t and "Todas las variantes con" not in t


def test_el_texto_generado_no_dice_envios():
    plan, _, _ = reporte.planificar([reg.AGREGADOR, "h1", "h3"])
    for _, bloques in plan:
        assert not any("envíos" in t.lower() for t in bloques.values())
    assert "clientes contactados" in reporte.linea_ronda(_h3()[2])
