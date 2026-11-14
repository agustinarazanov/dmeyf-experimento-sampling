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
    t = reporte.tabla_replica0(ctx, fin, ap)
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
    t = reporte.tabla_replica0(ctx, fin, ap)
    assert "semillas</th>" in t and "Todas las variantes con" not in t


def _fila_html(t: str, variante: str) -> str:
    return next(f for f in re.findall(r"<tr>.*?</tr>", t) if f"<td><span class='v'>{variante}" in f or f"<td>{variante}</td>" in f)


def test_tabla_de_h1_trae_el_veredicto_con_replicas_y_el_de_cada_variante_es_el_del_bloque_a():
    plan, _, _ = reporte.planificar([reg.AGREGADOR, "h1", "h2", "h3", "h4"])
    por_exp = {ruta.parent.name: b for ruta, b in plan if ruta.name == "README.md"}
    u05 = _fila_html(por_exp["h1"]["resultado"], "U0.5")
    assert "indeterminado" in u05 and "−3.64" in u05.replace("-", "−") and "−1.38" not in u05.replace("-", "−")
    ctx = reporte.Contexto(reg.AGREGADOR)
    fin, ap = reporte.cargar([reg.CONTROL, *ctx.exps])
    a = reporte.calcular_bloque_a(ctx, fin, ap, n_boot=20)
    for f in a["filas"]:
        fila_h = _fila_html(por_exp[f["hipotesis"].lower()]["resultado"], f["variante"])
        assert f"pill {reporte.clase_veredicto(f['veredicto'])}'>{f['veredicto']}" in fila_h


def test_el_anexo_trae_la_replica_0_de_cada_hipotesis():
    anexo = {ruta.name: b for ruta, b in reporte.planificar([reg.AGREGADOR])[0]}["anexo.md"]
    for h in ("h1", "h2", "h3", "h4"):
        assert f"replica0-{h}" in reporte.BLOQUES_ANEXO and "semillas ganadas" in anexo[f"replica0-{h}"]
    assert "−1.38" in anexo["replica0-h1"].replace("-", "−")


def test_el_texto_generado_no_dice_envios():
    plan, _, _ = reporte.planificar([reg.AGREGADOR, "h1", "h3"])
    for _, bloques in plan:
        assert not any("envíos" in t.lower() for t in bloques.values())
    assert "clientes contactados" in reporte.linea_ronda(_h3()[2])
