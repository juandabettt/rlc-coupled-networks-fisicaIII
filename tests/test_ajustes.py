"""Validación de red_rlc.ajustes: modelos, AICc y comparación."""

import numpy as np
import pytest

from red_rlc import ajustes


def test_aicc_formula():
    # n = 10, k = 2 → k' = 3: 10 ln(0.5/10) + 6 + 24/6
    assert ajustes.aicc(0.5, 10, 2) == pytest.approx(10 * np.log(0.05) + 6 + 4)
    assert np.isnan(ajustes.aicc(0.5, 4, 2))          # n − k' − 1 = 0
    assert np.isnan(ajustes.aicc(0.0, 10, 2))


@pytest.mark.parametrize("modelo, p", [
    (ajustes.T_LINEAL, (0.1, 0.25)),
    (ajustes.T_POTENCIA, (0.05, 1.4)),
    (ajustes.T_LOG, (0.2, 0.7)),
    (ajustes.E_EXPONENCIAL, (-2.0, -0.4)),
    (ajustes.E_POTENCIA, (-2.0, -3.0)),
    (ajustes.V_POTENCIA, (-0.3, 0.8)),
    (ajustes.V_TRAMOS, (0.4, -0.2)),
    (ajustes.V_SUAVE, (0.4, -0.2)),
])
def test_recupera_parametros_sin_ruido(modelo, p):
    x = np.array([0.01, 0.03, 0.1, 0.3, 1, 3, 10]) if modelo in ajustes.MODELOS_V \
        else np.arange(1, 11, dtype=float)
    y = modelo.f(x, *p)
    a = ajustes.ajustar(modelo, x, y)
    assert a is not None
    assert a.p == pytest.approx(p, rel=1e-4, abs=1e-6)
    assert a.rss < 1e-12 and a.r2 == pytest.approx(1.0)


def test_comparar_elige_el_modelo_verdadero():
    rng = np.random.default_rng(3)
    d = np.repeat(np.arange(1, 11), 8).astype(float)
    y = 0.05 * d**1.5 + rng.normal(0, 0.01, d.size)          # potencia con ruido
    r = ajustes.comparar(ajustes.MODELOS_T, d, y)
    assert r[0].nombre == "potencia" and r[0].delta == 0
    assert sum(a.peso for a in r) == pytest.approx(1.0)
    assert all(r[k].aicc <= r[k + 1].aicc for k in range(len(r) - 1))

    logE = -1.0 - 0.35 * d + rng.normal(0, 0.05, d.size)     # exponencial con ruido
    r = ajustes.comparar(ajustes.MODELOS_E, d, logE)
    assert r[0].nombre == "exponencial" and r[1].delta > 10


def test_transicion_suave_y_por_tramos_tienen_los_limites_de_la_teoria():
    k = np.array([1e-4, 1e4])
    for f in (ajustes.V_SUAVE.f, ajustes.V_TRAMOS.f):
        # log₁₀A = 0, κc = 1: v ≈ κ con κ ≪ 1 y v ≈ √κ con κ ≫ 1.
        v = 10 ** f(k, 0.0, 0.0)
        assert v[0] == pytest.approx(1e-4, rel=1e-3)
        assert v[1] == pytest.approx(1e2, rel=1e-3)


def test_datos_insuficientes():
    assert ajustes.ajustar(ajustes.T_LINEAL, [1, 2, 3], [1, 2, 3]) is None
    assert ajustes.ajustar(ajustes.T_LINEAL, [2, 2, 2, 2], [1, 2, 3, 4]) is None
    assert ajustes.comparar(ajustes.MODELOS_T, [1, 2], [1, 2]) == []


def test_ignora_valores_no_finitos():
    d = np.arange(1, 9, dtype=float)
    y = 0.3 * d
    y[2] = np.nan
    a = ajustes.ajustar(ajustes.T_LINEAL, d, y)
    assert a.n == 7 and a.p[1] == pytest.approx(0.3)


def test_desviacion_en_d1():
    rng = np.random.default_rng(4)
    d = np.repeat(np.arange(1, 9), 5).astype(float)
    y = 0.2 * d + rng.normal(0, 0.01, d.size)
    y[d == 1] += 0.1                                       # d = 1 adelantado
    sin_d1 = ajustes.ajustar(ajustes.T_LINEAL, d[d > 1], y[d > 1])
    assert ajustes.desviacion_en_d1(sin_d1, d, y) > 5
