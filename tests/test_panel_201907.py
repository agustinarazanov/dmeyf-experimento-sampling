"""El panel con 201907 (D2), con un crudo de juguete: sin datos reales."""
import duckdb
import pandas as pd

from comun import baseline as bl
from comun import datos as d


def _crudo_de_juguete(destino):
    """Cliente 1: todos los meses (CONTINUA). Cliente 2: se va tras 201907 (BAJA+1 en 201907).
    Cliente 3: está hasta 201908 y no en 201909 (BAJA+2 en 201907)."""
    filas = [(1, m, 10.0 + m % 100) for m in range(201901, 201913)]
    filas += [(2, m, 5.0) for m in range(201901, 201908)]
    filas += [(3, m, 7.0) for m in range(201901, 201909)]
    pd.DataFrame(filas, columns=["numero_de_cliente", "foto_mes", "x"]).to_csv(destino, index=False, compression="gzip")


def test_etiqueta_de_201907_sale_de_201908_y_201909(tmp_path, monkeypatch):
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path)
    _crudo_de_juguete(tmp_path / "competencia_02_crudo.csv.gz")
    ruta = d.construir_panel(destino=tmp_path / "panel.parquet")
    clase = dict(duckdb.connect().execute(
        f"select numero_de_cliente, {d.CLASE} from read_parquet('{ruta}') where {d.MES} = 201907"
    ).fetchall())
    assert clase == {1: "CONTINUA", 2: "BAJA+1", 3: "BAJA+2"}


def test_panel_sin_201907_se_reconstruye(tmp_path, monkeypatch):
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path)
    _crudo_de_juguete(tmp_path / "competencia_02_crudo.csv.gz")
    viejo = d.ruta_panel()
    meses_viejos = [m for m in bl.MESES_PANEL if m != 201907]
    pd.DataFrame({"numero_de_cliente": 1, "foto_mes": meses_viejos}).to_parquet(viejo, index=False)
    assert not d._tiene_meses(viejo)
    ruta, seg = d.asegurar_panel()
    assert seg > 0 and d._tiene_meses(ruta)
    _, seg2 = d.asegurar_panel()
    assert seg2 == 0.0
