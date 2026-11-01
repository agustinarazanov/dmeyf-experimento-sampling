import numpy as np

from comun import ganancia as g


def test_vector_sintetico_de_10_scores():
    scores = np.array([0.9, 0.1, 0.8, 0.2, 0.7, 0.3, 0.6, 0.4, 0.5, 0.0])
    baja2 = np.array([1, 0, 1, 0, 0, 1, 0, 0, 1, 0], dtype=bool)
    # orden por score: idx 0,2,4,6,8,7,5,3,1,9 -> aciertos: 1,1,0,0,1,0,1,0,0,0
    A, C = g.GANANCIA_ACIERTO, g.COSTO_ESTIMULO
    esperado = np.cumsum([A, A, -C, -C, A, -C, A, -C, -C, -C])
    np.testing.assert_array_equal(g.ganancia_acumulada(scores, baja2), esperado)
    assert g.ganancia(scores, baja2, 2) == 2 * A
    assert g.ganancia(scores, baja2, 5) == 3 * A - 2 * C
    assert g.ganancia(scores, baja2, 100) == esperado[-1]
    assert g.ganancia(scores, baja2, 0) == 0.0
    curva = g.curva_de_corte(scores, baja2, hasta=10, paso=5)
    assert list(curva["envios"]) == [5, 10]
    assert list(curva["ganancia"]) == [esperado[4], esperado[9]]
    assert g.ganancia_maxima(curva) == (10, esperado[9])
