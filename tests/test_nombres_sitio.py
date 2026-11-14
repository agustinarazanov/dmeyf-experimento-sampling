"""`nombres_sitio` rechaza títulos de proceso (cambio, fecha, Zulip, cambio archivado) fuera de `## Predicción`."""
from scripts import nombres_sitio as ns

ARCHIVADOS = ["tiempos-confiables-y-consistencia"]


def _hallazgos(texto):
    return ns.titulos_de_proceso(texto, ARCHIVADOS)


def test_titulo_con_cambio_y_fecha_falla():
    texto = "# H1\n\n## Diseño\n\n### X (cambio `y`, 13-nov-2026)\n"
    [(n, titulo, motivo)] = _hallazgos(texto)
    assert n == 5 and "cambio" in motivo


def test_fecha_iso_zulip_y_cambio_archivado_fallan():
    for titulo in ["Resultados (2026-11-13)", "Zulip 211718", "Se movió por `tiempos-confiables-y-consistencia`"]:
        assert _hallazgos(f"## Diseño\n\n### {titulo}\n"), titulo


def test_dentro_de_prediccion_se_acepta():
    texto = "## Predicción\n\n### Réplicas (cambio `x`, 13-nov-2026)\n\n## Diseño\n\n### Variantes\n"
    assert _hallazgos(texto) == []


def test_despues_de_prediccion_vuelve_a_regir():
    texto = "## Predicción\n\n### A (13-nov)\n\n## Diseño\n\n### B (13-nov)\n"
    assert [n for n, _, _ in _hallazgos(texto)] == [7]


def test_codigo_y_titulos_normales_no_fallan():
    texto = "## Diseño\n\n### H3-0.5 y grilla\n\n```\n# cambio 13-nov\n```\n"
    assert _hallazgos(texto) == []


def test_las_paginas_publicadas_estan_limpias():
    assert ns.buscar_titulos() == []
