"""El reporte se regenera igual salvo la fecha, y con un ledger vacío deja las variantes pendientes sin fallar."""

import re

import pytest

from comun import variantes as reg
from comun import reporte, rutas

EXPERIMENTOS = [reg.CONTROL, *[e for e in reg.duenos() if e != reg.CONTROL], reg.AGREGADOR]


def generar(exp: str, figuras=None) -> tuple[dict[str, str], dict]:
    """Los bloques del README de `exp` (nombre -> texto) y los archivos de figuras que `planificar` escribiría."""
    plan, archivos, _ = reporte.planificar([exp], figuras)
    assert plan, f"el README de {exp} no tiene marcadores"
    return plan[0][1], archivos


def anexo_de(exp: str) -> dict[str, str]:
    """Los bloques del Anexo de `exp` (`anexo.md`)."""
    plan, _, _ = reporte.planificar([exp])
    return next(b for ruta, b in plan if ruta.name == "anexo.md")


def texto(exp: str, figuras=None) -> str:
    return "\n\n".join(generar(exp, figuras)[0].values())


def svg(exp: str, nombre: str) -> str:
    return generar(exp)[1][rutas.experimento(exp) / "figuras" / f"{nombre}.svg"].decode()


@pytest.mark.parametrize("exp", EXPERIMENTOS)
def test_dos_veces_da_lo_mismo(exp):
    assert generar(exp) == generar(exp)


def test_agregador_lista_todos_los_variantes_de_las_hipotesis():
    ctx = reporte.Contexto(reg.AGREGADOR)
    esperados = {b.nombre for b in reg.VARIANTES.values() if b.dueno != reg.CONTROL}
    assert set(ctx.variantes) == esperados


def test_hipotesis_nueva_aparece_sin_tocar_el_generador(monkeypatch):
    nuevo = reg.Variante("X1", "h1", "uniforme", 0.7, "U0.5")
    monkeypatch.setitem(reg.VARIANTES, "X1", nuevo)
    monkeypatch.setattr(reporte, "N_SEMILLAS", 10)
    monkeypatch.setattr(reporte, "VENTANA", "201903-201906")  # hasta que haya finales de la ronda nueva
    assert "X1" in reporte.Contexto(reg.AGREGADOR).variantes
    assert "X1" in texto(reg.AGREGADOR)


def test_ledger_vacio_deja_pendientes(monkeypatch, tmp_path):
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path)
    for e in EXPERIMENTOS:
        (tmp_path / e / "ledger").mkdir(parents=True)
    (tmp_path / "h1" / "README.md").write_text("# H1 · prueba\n\n<!-- generado:resultado -->\n<!-- /generado:resultado -->\n")
    html = texto("h1")
    assert "pendiente" in html and "<table>" in html


def test_exploratorio_sin_csv_sale_pendiente_con_el_nombre_del_archivo(tmp_path):
    import json
    carpeta = tmp_path / "experimentos" / "h3" / "sm"
    carpeta.mkdir(parents=True)
    (carpeta / "exploratorio.json").write_text(json.dumps(dict(
        autor="A", fecha="2026-11-04", pregunta="p", protocolo="q", advertencia="w",
        tablas=[dict(csv="resultados/falta.csv", columnas=["x"])])))
    (fila,) = reporte.bloque_b(tmp_path)
    assert fila["cifras"] == ["pendiente: falta resultados/falta.csv"]
    assert fila["advertencia"] == "w"
    assert "- pendiente: falta resultados/falta.csv" in reporte.lista_b([fila])


def test_variante_de_una_replica_lleva_la_nota_sin_replicas():
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    ap = pd.DataFrame(dict(g_control=[1e8], delta_g_media=[1e6], delta_g_ic_inf=[0.0], delta_g_ic_sup=[2e6],
                           tiempo_total_s=[100.0], aceleracion=[3.0], veredicto=["no pierde"]), index=["U0.1"])
    fin = pd.DataFrame(dict(variante=["U0.1"] * 10))
    f = reporte.fila_bloque_a(ctx, "U0.1", fin, ap, pd.DataFrame(), None, None, None)
    assert f["nota"] == "sin réplicas" and f["fuente"] == "réplica 0" and f["dR"] is None
    celdas = reporte.celdas_bloque_a(f)
    assert celdas[4] == "—" and celdas[8] == "sin réplicas"


def test_variante_con_replicas_marca_su_g_y_la_referencia_del_control():
    """Ḡ de una variante con réplicas es la media entre réplicas: la celda lo dice y la cabecera da Ḡ_C con réplicas."""
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    ap = pd.DataFrame(dict(g_control=[1e8], delta_g_media=[3e6], delta_g_ic_inf=[0.0], delta_g_ic_sup=[6e6],
                           tiempo_total_s=[100.0], aceleracion=[3.0], veredicto=["no pierde"]), index=["H3-0.1"])
    rep = pd.DataFrame(dict(delta_g_media=[1e6, None], delta_g_ic_inf=[-1e6, None], delta_g_ic_sup=[3e6, None],
                            n_replicas=[8, 8], g_media_replicas=[1.01e8, 1e8], veredicto=["no pierde", ""]),
                       index=["H3-0.1", reg.CONTROL])
    f = reporte.fila_bloque_a(ctx, "H3-0.1", pd.DataFrame(), ap, rep, None, None, None)
    assert reporte.celdas_bloque_a(f)[2] == "101.00 (R=8)"
    a = dict(n_est=3300, g_c1=9.9e7, g_c10=None, g_cR=1e8, n_cR=8)
    assert "Ḡ_C con réplicas = 100.00 M$ (R=8)" in reporte.referencia_control(a)


def _predicciones(tmp_path, variante, semilla_azar, k):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(semilla_azar)
    n = 3000
    baja2 = np.arange(n) < 100
    filas = []
    for s in reporte.SEMILLAS_FINALES[:k]:
        ruta = tmp_path / f"{variante}_{s}.parquet"
        pd.DataFrame(dict(numero_de_cliente=np.arange(n), prob=rng.random(n) + baja2 * 0.5, es_baja2=baja2)).to_parquet(ruta)
        filas.append(dict(variante=variante, semilla=s, predicciones_201910=str(ruta)))
    return filas


def test_bootstrap_de_clientes_identico_en_dos_corridas(tmp_path):
    import pandas as pd
    fin = pd.DataFrame(_predicciones(tmp_path, "C", 1, 20) + _predicciones(tmp_path, "U0.5", 2, 20))
    datos = {"U0.5": (10.0, 5.0, 3, 1.0)}
    a = reporte.bootstrap_tiempo_igual(fin, datos, 300, n_boot=50)
    b = reporte.bootstrap_tiempo_igual(fin, datos, 300, n_boot=50)
    assert a == b and a["U0.5"][1] <= a["U0.5"][0] <= a["U0.5"][2]


@pytest.fixture
def ronda_anterior(monkeypatch):
    """La ronda 201903-201906 de 10 semillas, completa en el ledger: con ella hay figuras y tablas con números."""
    monkeypatch.setattr(reporte, "VENTANA", "201903-201906")
    monkeypatch.setattr(reporte, "N_SEMILLAS", 10)


@pytest.fixture(scope="module")
def pagina_s1():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(reporte, "VENTANA", "201903-201906")
        mp.setattr(reporte, "N_SEMILLAS", 10)
        return generar(reg.AGREGADOR)[0]["bloque-a"]


@pytest.mark.parametrize("exp", ["h3", reg.AGREGADOR])
def test_con_figuras_dos_veces_da_lo_mismo_en_svg(ronda_anterior, exp):
    bloques, archivos = generar(exp)
    assert archivos and {k.suffix for k in archivos} == {".svg"}
    assert all(b"<svg" in v for v in archivos.values())
    assert "<svg" not in "".join(bloques.values()) and "](figuras/" in "".join(bloques.values())
    assert (bloques, archivos) == generar(exp)


def test_figuras_guarda_png(ronda_anterior, tmp_path):
    _, archivos = generar("h1", tmp_path)
    assert {k.suffix for k in archivos if tmp_path in k.parents} == {".png"}


def _textos(svg: str) -> list[str]:
    return re.findall(r"<text[^>]*>([^<]*)</text>", svg)


@pytest.mark.parametrize("exp, nombre", [(reg.AGREGADOR, "tradeoff"), ("h1", "tradeoff_h1")])
def test_tradeoff_una_variante_por_fila_y_el_titulo(ronda_anterior, exp, nombre):
    pagina = texto(exp)
    assert f"](figuras/{nombre}.svg)" in pagina
    textos = _textos(svg(exp, nombre))
    assert any("variantes no pierden" in t or t.startswith("Ninguna de las") for t in textos)
    ctx = reporte.Contexto(exp)
    ap = reporte.cargar([reg.CONTROL, *ctx.exps])[1]
    for b in ctx.variantes:  # las que tienen Δ, una etiqueta cada una; las pendientes no se dibujan
        assert textos.count(b) == (1 if b in ap.index else 0)


def test_fraccion_sin_familias_de_dos_tasas_sale_pendiente(monkeypatch):
    for k, v in list(reg.VARIANTES.items()):
        monkeypatch.setitem(reg.VARIANTES, k, v._replace(tasa=1.0))
    ctx = reporte.Contexto(reg.AGREGADOR)
    f = dict(variante="U0.1", hipotesis="H1", dR=None, d0=(1.0, 0.0, 2.0))
    assert "pendiente" in reporte.fig_fraccion(ctx, {"filas": [f, dict(f, variante="U0.5")], "delta": 1.0}, None)


def test_desplazador_separa_etiquetas_en_el_mismo_punto():
    (x1, y1), (x2, y2) = reporte.desplazar([(0.5, 0.5), (0.5, 0.5)], alto=0.07, ancho=0.2)
    assert abs(y1 - y2) >= 0.07 - 1e-9
    # tres etiquetas pegadas cerca del techo se apilan hacia abajo y quedan dentro del panel
    pos = reporte.desplazar_dentro([(0.5, 0.9), (0.5, 0.9), (0.52, 0.91)], alto=0.07, ancho=0.2)
    assert max(y for _, y in pos) <= 0.97 and len({round(y, 6) for _, y in pos}) == 3


def test_sin_replicas_semillas_se_dibuja_y_varianza_y_diferencias_salen_pendientes(ronda_anterior, monkeypatch):
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    a = {"filas": [], "rep": pd.DataFrame(), "g_rep": {}, "semillas": {}, "desglose": []}
    for fig in (reporte.fig_semillas, reporte.fig_diferencias, reporte.fig_desglose, reporte.fig_grilla,
                reporte.fig_tradeoff, reporte.fig_fraccion, reporte.fig_rondas, reporte.fig_tiempo_igual_ic):
        assert "class='pend'" in fig(ctx, a, None)
    cargar = reporte.cargar_replicas
    monkeypatch.setattr(reporte, "cargar_replicas",
                        lambda exps, n: (*cargar(exps, n)[:2], pd.DataFrame(columns=["variante"]).set_index("variante")))
    bloques = generar(reg.AGREGADOR)[0]
    assert "](figuras/tradeoff.svg)" in bloques["mapa"]
    assert "](figuras/semillas_replicas.svg)" in bloques["semillas"]
    anexo = anexo_de(reg.AGREGADOR)
    assert "class='pend'" in anexo["varianza"] and "class='pend'" in anexo["diferencias"]


def _tabla(pagina: str, primera: str) -> str:
    m = re.search(rf"<table><tr><th>{re.escape(primera)}</th>.*?</table>", pagina, re.S)
    assert m
    return m.group(0)


def _filas(tabla: str) -> dict[str, list[str]]:
    filas = re.findall(r"<tr>(.*?)</tr>", tabla, re.S)[1:]
    celdas = [re.findall(r"<td[^>]*>.*?</td>", f, re.S) for f in filas]
    return {re.sub(r"<[^>]+>", "", c[0]): c for c in celdas}


def test_resumen_corto(pagina_s1):
    resumen = re.search(r"<table><tr><th>variante</th><th>hipótesis</th><th>R</th>.*?</table>", pagina_s1, re.S).group(0)
    assert len(re.findall(r"<th>", resumen.split("</tr>")[0])) <= 6
    for celdas in _filas(resumen).values():
        assert all(c.count("class='ic'") <= 1 for c in celdas)
    assert "<summary>Detalle del bloque A</summary>" in pagina_s1
    assert "(R=" not in resumen and "no aplica" not in resumen and "sin réplicas" not in resumen


def test_resaltado(pagina_s1):
    tablas = re.findall(r"<table><tr><th>variante</th><th>hipótesis</th><th>R</th>.*?</table>", pagina_s1, re.S)
    assert len(tablas) == 5  # «Lo mejor de cada hipótesis» y una pestaña por hipótesis
    por_tabla = [_filas(t) for t in tablas]
    assert 1 <= len(por_tabla[0]) <= 4  # a lo sumo una fila por hipótesis
    assert '=== "Lo mejor de cada hipótesis"' in pagina_s1 and "Valen la pena" not in pagina_s1
    filas = {v: c for t in por_tabla[1:] for v, c in t.items()}
    assert "class='sig-neg'" in filas["U0.05"][3]
    assert "<span class='pill pierde'>pierde</span>" in filas["U0.05"][5]
    for t in por_tabla:
        for j in (3, 4):
            assert sum("mejor" in c[j] for c in t.values()) <= 1  # uno por tabla: el mejor de esa pestaña
    assert "mejor" in filas["H4F-0.05"][4]


def test_regenerar_resalta_igual(pagina_s1, ronda_anterior):
    clases = lambda p: re.findall(r"class='([^']*)'", p)
    assert clases(pagina_s1) == clases(generar(reg.AGREGADOR)[0]["bloque-a"])


# --- sitio-legible grupo 2: marcadores, figuras como archivo, figuras nuevas ---

def test_regenerar_no_toca_el_texto_de_afuera():
    texto = "# H9\n\nantes\n\n<!-- generado:resultado -->\nviejo\n<!-- /generado:resultado -->\n\n## Limitaciones\n\nmías\n"
    nuevo = reporte.reemplazar_bloques(texto, {"resultado": "tabla nueva"}, fecha="2026-11-13")
    assert "tabla nueva" in nuevo and "viejo" not in nuevo
    assert "Generado por `comun/reporte.py` el 2026-11-13; no editar." in nuevo
    assert nuevo.split("<!-- generado:resultado -->")[0] == texto.split("<!-- generado:resultado -->")[0]
    assert nuevo.split("<!-- /generado:resultado -->")[1] == texto.split("<!-- /generado:resultado -->")[1]
    assert reporte.reemplazar_bloques(nuevo, {"resultado": "tabla nueva"}, fecha="2026-11-13") == nuevo


def test_marcador_faltante_falla_sin_escribir_nada(tmp_path):
    bueno, malo = tmp_path / "a.md", tmp_path / "b.md"
    bueno.write_text("<!-- generado:x -->\nviejo\n<!-- /generado:x -->\n")
    malo.write_text("<!-- generado:x -->\nviejo\n<!-- /generado:x -->\n")
    figura = tmp_path / "figuras" / "f.svg"
    with pytest.raises(reporte.MarcadorFaltante, match=r"b\.md.*generado:y"):
        reporte.escribir_bloques([(bueno, {"x": "nuevo"}), (malo, {"x": "nuevo", "y": "falta"})], {figura: b"<svg/>"})
    assert "viejo" in bueno.read_text() and "viejo" in malo.read_text() and not figura.exists()


def test_figura_como_archivo_svg_identico_en_dos_corridas(monkeypatch, tmp_path):
    import matplotlib.pyplot as plt
    def una():
        monkeypatch.setattr(reporte, "DESTINO", reporte.Destino(tmp_path / "figuras"))
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3])
        fig.suptitle("Qué mirar")
        enlace = reporte.figura(fig, "prueba", None)
        return enlace, dict(reporte.DESTINO.archivos)
    (e1, a1), (e2, a2) = una(), una()
    assert e1 == e2 and "![Qué mirar](figuras/prueba.svg)" in e1
    assert a1 == a2 and list(a1) == [tmp_path / "figuras" / "prueba.svg"]
    assert b"<svg" in a1[tmp_path / "figuras" / "prueba.svg"]


def test_figura_con_png_guarda_los_dos(monkeypatch, tmp_path):
    import matplotlib.pyplot as plt
    monkeypatch.setattr(reporte, "DESTINO", reporte.Destino(tmp_path / "figuras"))
    fig, _ = plt.subplots()
    reporte.figura(fig, "p", tmp_path / "png")
    assert {k.suffix for k in reporte.DESTINO.archivos} == {".svg", ".png"}


def test_etiquetas_del_mapa_no_se_pisan():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xscale("log")
    ax.set_xlim(0.5, 20)
    ax.set_ylim(-5, 5)
    puntos = [(2.0, 0.0)] * 4 + [(2.05, 0.1), (10.0, 1.0), (10.0, 1.1)]
    reporte._etiquetas_sin_pisar(ax, puntos, [f"V{i}" for i in range(len(puntos))])
    fig.canvas.draw()
    from matplotlib.text import Text
    cajas = [Text.get_window_extent(t) for t in ax.texts]  # el texto solo, sin la línea al punto
    for i, c in enumerate(cajas):
        assert not any(c.overlaps(o) for o in cajas[i + 1:])
    plt.close(fig)


def test_figuras_nuevas_sin_datos_salen_pendientes_y_la_curva_tambien(ronda_anterior):
    import pandas as pd
    ctx = reporte.Contexto("h1")
    assert "class='pend'" in reporte.fig_curva_diferencia(ctx, "H1", pd.DataFrame(columns=["variante"]), pd.DataFrame(), None)


def test_curva_de_u005_queda_por_debajo_de_cero_en_n_estrella(ronda_anterior):
    ctx = reporte.Contexto("h1")
    fin, ap = reporte.cargar([reg.CONTROL, "h1"])
    d = reporte.curvas_diferencia(fin, "U0.05")
    n_est = int(ap["n_estrella"].iloc[0])
    assert float(d.median(axis=1).loc[:n_est].iloc[-1]) < 0
    assert "curva_diferencia_H1" in reporte.fig_curva_diferencia(ctx, "H1", fin, ap, None)


def test_desglose_suma_el_tiempo_de_apareado(ronda_anterior):
    ctx = reporte.Contexto(reg.AGREGADOR)
    fin, ap = reporte.cargar([reg.CONTROL, *ctx.exps])
    for r in reporte.desglose_tiempo(ctx, fin, ap):
        t = ap["tiempo_total_control_s"].iloc[0] if r["variante"] == "C" else ap.loc[r["variante"], "tiempo_total_s"]
        assert r["optimizacion"] + r["final"] + r["resto"] == pytest.approx(t)


def test_bloque_b_sin_autor(tmp_path):
    import json
    carpeta = tmp_path / "experimentos" / "h3" / "sm"
    carpeta.mkdir(parents=True)
    (carpeta / "exploratorio.json").write_text(json.dumps(dict(
        autor="Fulano", fecha="2026-11-04", pregunta="p", protocolo="q", advertencia="w", tablas=[])))
    b = reporte.bloque_b(tmp_path)
    assert "Fulano" not in reporte.lista_b(b)
    assert reporte.lista_b(b).lower().count("autor") == 0


def test_html_tabla_sin_recuadro_propio():
    assert "table-wrapper" not in reporte.html_tabla(("a",), [["1"]])


def test_tarjetas_leen_el_veredicto_de_las_filas(ronda_anterior):
    ctx = reporte.Contexto(reg.AGREGADOR)
    fin, ap = reporte.cargar([reg.CONTROL, *ctx.exps])
    a = reporte.calcular_bloque_a(ctx, fin, ap, n_boot=20)
    texto = reporte.tarjetas(a, ctx, "../")
    assert texto.count("](../experimentos/") == len(ctx.exps)
    for nombre in ctx.hipotesis:
        filas = [f for f in a["filas"] if f["hipotesis"] == nombre]
        ok = sum(reporte.clase_veredicto(f["veredicto"]) == "ok" for f in filas)
        assert f"{len(filas)} variantes: " in texto and (f"{ok} no pierde" in texto or ok == 0)  # singular o plural


def test_anexo_e_inicio_tienen_los_bloques_que_salen_de_resultados(ronda_anterior):
    plan, _, _ = reporte.planificar([reg.AGREGADOR])
    por_pagina = {ruta.name if ruta.name != "README.md" else ruta.parent.name: b for ruta, b in plan}
    assert set(reporte.BLOQUES_ANEXO) <= set(por_pagina["anexo.md"])
    assert set(reporte.BLOQUES_INICIO) <= set(por_pagina["index.md"])
    sampling = por_pagina["sampling_1"]
    assert {"grilla", "desglose", "fraccion", "semillas"} <= set(sampling)
    assert not {"figuras", "varianza", "diferencias", "bloque-a-completo", "rondas"} & set(sampling)
    # las figuras de Inicio se enlazan desde la raíz del repo
    assert "](experimentos/sampling_1/figuras/tradeoff.svg)" in por_pagina["index.md"]["hallazgo-tradeoff"]


def _estudio(tmp_path, **datos):
    import json
    carpeta = tmp_path / "experimentos" / "sampling_1" / "exploratorios" / "est"
    (carpeta / "resultados").mkdir(parents=True)
    (carpeta / "figuras").mkdir()
    (carpeta / "resultados" / "r.csv").write_text("g,t\n300000000,10\n310000000,20\n")
    base = dict(autor="Fulano", fecha="2026-11-04", pregunta="¿Cambia?", protocolo="q", advertencia="w")
    base.update(datos)
    (carpeta / "exploratorio.json").write_text(json.dumps(base))
    return carpeta


def test_bloque_b_pregunta_figuras_cifras_y_advertencia_en_su_forma(tmp_path):
    _estudio(tmp_path, figuras=[dict(archivo="figuras/a.png", leyenda="Reporte original: bandas")],
             tablas=[dict(csv="resultados/r.csv", columnas=[dict(columna="g", etiqueta="G en 201908", escala=1e-6, unidad="M$"),
                                                            "t"])])
    texto_b = reporte.lista_b(reporte.bloque_b(tmp_path))
    assert '!!! question "Pregunta"\n    ¿Cambia?' in texto_b and '!!! warning "Advertencia"\n    w' in texto_b
    assert "![Reporte original: bandas](est/figuras/a.png)" in texto_b and "Reporte original: bandas</p>" in texto_b
    assert "<summary>Cifras principales</summary>" in texto_b
    assert "| G en 201908 | M$ | 305.00 | 300.00 | 310.00 | 2 |" in texto_b   # columna con escala y unidad
    assert "| r.csv, t |  | 15 | 10 | 20 | 2 |" in texto_b                       # columna declarada como texto: sigue valiendo
    assert "Fulano" not in texto_b


def test_bloque_b_figura_generada_desde_un_csv_sale_como_archivo_y_pendiente_sin_csv(tmp_path):
    _estudio(tmp_path, figuras=[dict(csv="resultados/r.csv", columna="g", escala=1e-6, unidad="M$", leyenda="Δ por muestra"),
                                dict(csv="resultados/falta.csv", columna="g", leyenda="x")], tablas=[])
    reporte.DESTINO = reporte.Destino(tmp_path / "experimentos" / "sampling_1" / "figuras")
    try:
        (fila,) = reporte.bloque_b(tmp_path)
        archivos = dict(reporte.DESTINO.archivos)
    finally:
        reporte.DESTINO = None
    (generada, _), (sin_csv, _) = fila["figuras"]
    assert "![Δ por muestra](figuras/est.svg)" in generada and "class='pend'" in sin_csv
    destino = tmp_path / "experimentos" / "sampling_1" / "exploratorios" / "figuras" / "est.svg"
    assert b"<svg" in archivos[destino]
