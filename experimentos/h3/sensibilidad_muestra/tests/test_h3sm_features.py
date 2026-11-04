"""Features de insumos.py con datos sintéticos: huecos de meses, nulos y negativos (prueba de 04)."""
import duckdb

from experimentos.h3.sensibilidad_muestra import insumos

SINTETICO = [  # (cliente, mes, a BIGINT, b DOUBLE)
    (1, 201901, 10, 1.5), (1, 201902, 20, None), (1, 201903, None, 4.0), (1, 201904, 25, -0.5),
    (2, 201901, 5, 0.1), (2, 201903, 7, 0.2),                       # falta 201902
    (3, 201902, 100, None),                                          # una sola observación
    (4, 201901, 1, 1.0), (4, 201902, 2, 2.0), (4, 201904, 4, 4.0), (4, 201905, 8, 8.0),
    (5, 201903, -3, 3.0), (5, 201905, 9, None),                      # empieza tarde, con hueco
]


def esperado_python(rows):
    out, por_cli = {}, {}
    for r in rows:
        por_cli.setdefault(r[0], []).append(r)
    for rs in por_cli.values():
        rs = sorted(rs, key=lambda r: r[1])
        for i, (c, m, a, b) in enumerate(rs):
            fila = {"a": a, "b": b}
            for k in (1, 2):
                prev = rs[i - k] if i - k >= 0 else None
                for name, j in (("a", 2), ("b", 3)):
                    lag = prev[j] if prev else None
                    cur = fila[name]
                    fila[f"{name}_lag{k}"] = lag
                    fila[f"{name}_delta{k}"] = None if lag is None or cur is None else cur - lag
            out[(c, m)] = fila
    return out


def test_features_sinteticas():
    con = duckdb.connect()
    con.execute("CREATE TABLE syn (numero_de_cliente BIGINT, foto_mes BIGINT, a BIGINT, b DOUBLE)")
    con.executemany("INSERT INTO syn VALUES (?, ?, ?, ?)", SINTETICO)
    insumos.crear_prev(con, "syn")
    names = insumos.KEYS + insumos.nombres(["a", "b"])
    got = {}
    for mes in sorted({r[1] for r in SINTETICO}):
        for row in con.execute(insumos.sql_mes("syn", ["a", "b"], mes)).fetchall():
            d = dict(zip(names, row))
            got[(d["numero_de_cliente"], d["foto_mes"])] = {k: d[k] for k in names[2:]}
    con.close()
    exp = esperado_python(SINTETICO)
    assert {k: {c: got[k][c] for c in exp[k]} for k in exp} == exp
    assert got[(2, 201903)]["a_lag1"] == 5 and got[(2, 201903)]["a_lag2"] is None   # hueco: observación previa
    assert got[(1, 201904)]["a_lag1"] is None and got[(1, 201904)]["a_lag2"] == 20  # lag1 nulo no se saltea


def test_orden_de_predictores():
    assert insumos.nombres(["x", "y"]) == ["x", "y", "x_lag1", "y_lag1", "x_delta1", "y_delta1",
                                           "x_lag2", "y_lag2", "x_delta2", "y_delta2"]
