"""Validación de la parte de energía de red_rlc.analisis.

Incluye las pruebas de energía de la tabla «Validación del código» del plan:

- Conservación (K = 0 y R = 0: E₀ constante)
- Decaimiento (K = 0 y R > 0: la energía decae, no se conserva)
- Balance general (K > 0 y R > 0: dH/dt = −RΣIᵢ²)

y las propiedades del punto 5 de la teoría (H(0) = E₀(1 + k₀κ), ΣEᵢ ≤ H(0),
ΣEᵢ no se conserva con K ≠ 0).
"""

import numpy as np
import pytest
from scipy.integrate import cumulative_simpson

from red_rlc import analisis, modelo, redes
from conftest import P_BASE, REDES


# ---------------------------------------------------------------------------
# Fórmulas individuales
# ---------------------------------------------------------------------------

def test_energia_nodos_formula():
    p = P_BASE
    Q = np.array([[p.Q0, 0.0]])
    I = np.array([[0.0, 2.0]])
    E = analisis.energia_nodos(Q, I, p)
    assert E[0, 0] == pytest.approx(p.E0)
    assert E[0, 1] == pytest.approx(p.L * 4 / 2)


def test_energia_acoplamiento_es_suma_sobre_enlaces():
    """(LK/2) QᵀΛQ = (LK/2) Σ_{enlaces} (Qᵢ − Qⱼ)², la energía de los C_c."""
    rng = np.random.default_rng(1)
    red = REDES["erdos_renyi"]
    p = P_BASE.con(kappa=0.3)
    Q = rng.normal(size=(5, red.N)) * p.Q0
    U = analisis.energia_acoplamiento(Q, red.laplaciano, p)
    suma = np.array([sum((q[i] - q[j])**2 for i, j in red.grafo.edges) for q in Q])
    assert np.allclose(U, p.L * p.K / 2 * suma, rtol=1e-12)
    assert np.all(U >= 0)


def test_potencia_intercambio_suma_menos_dU_dt():
    """Σᵢ Pᵢ = −LK IᵀΛQ = −dU/dt: lo que pierden las mallas lo ganan los enlaces."""
    rng = np.random.default_rng(2)
    red = REDES["malla"]
    p = P_BASE.con(kappa=1.0)
    Q = rng.normal(size=(4, red.N)) * p.Q0
    I = rng.normal(size=(4, red.N)) * p.omega0 * p.Q0
    P = analisis.potencia_intercambio(Q, I, red.laplaciano, p)
    dU = p.L * p.K * np.einsum("ti,ij,tj->t", I, red.laplaciano, Q)
    assert np.allclose(P.sum(axis=1), -dU, rtol=1e-10)


def test_potencia_disipada():
    p = P_BASE.con(R=2.0)
    I = np.array([[1.0, 2.0], [0.0, 3.0]])
    assert np.allclose(analisis.potencia_disipada(I, p), [10.0, 18.0])


def test_energia_media_y_fraccion():
    t = np.linspace(0, 1e-2, 2001)
    g = 1000.0
    E = np.column_stack([np.full_like(t, 3.0), np.exp(-g * t)])
    Em = analisis.energia_media(t, E)
    assert Em[0] == pytest.approx(3.0)
    assert Em[1] == pytest.approx((1 - np.exp(-g * 1e-2)) / (g * 1e-2), rel=1e-8)
    f = analisis.fraccion_energia(Em)
    assert f.sum() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Plan: conservación (K = 0, R = 0)
# ---------------------------------------------------------------------------

def test_conservacion_sin_acoplamiento_ni_resistencia(simulacion):
    sim = simulacion("malla", 0.0, R=0.0, T=5e-3)
    en = analisis.energias(sim)
    E_f = en.E[:, sim.fuente]
    assert np.abs(E_f - sim.parametros.E0).max() < 1e-8 * sim.parametros.E0
    assert np.allclose(en.U, 0) and np.allclose(en.P, 0)


# ---------------------------------------------------------------------------
# Plan: decaimiento (K = 0, R > 0)
# ---------------------------------------------------------------------------

def test_decaimiento_sin_acoplamiento(simulacion):
    """E(t)/E₀ = e^(−γt)[1 + a sen 2Ωt + a²(1 − cos 2Ωt)], a = γ/(2Ω) (teoría,
    punto 2, paso 14). La energía no se conserva: cae unas e¹⁰ veces en T."""
    sim = simulacion("malla", 0.0)
    p = sim.parametros
    t = sim.t
    W = np.sqrt(p.omega0**2 - p.gamma**2 / 4)
    a = p.gamma / (2 * W)
    teoria = np.exp(-p.gamma * t) * (1 + a * np.sin(2 * W * t) + a**2 * (1 - np.cos(2 * W * t)))
    E_rel = analisis.energias(sim).E_rel[:, sim.fuente]
    assert np.abs(E_rel - teoria).max() < 1e-8
    assert E_rel[-1] < 1e-4                     # ≈ 4.5 × 10⁻⁵, no se conserva
    envolvente = E_rel * np.exp(p.gamma * t)
    assert envolvente.min() > 1 - a - 1e-9
    assert envolvente.max() < 1 + a + 2 * a**2 + 1e-9


# ---------------------------------------------------------------------------
# Plan: balance general (K > 0, R > 0)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nombre", redes.TOPOLOGIAS)
@pytest.mark.parametrize("kappa", [0.01, 0.1, 1.0])
def test_balance_de_H(simulacion, nombre, kappa):
    """H(t) + ∫ RΣIᵢ² dt = H(0) en todo instante."""
    en = analisis.energias(simulacion(nombre, kappa))
    assert np.abs(en.residuo_balance()).max() < 1e-6


@pytest.mark.parametrize("nombre", redes.TOPOLOGIAS)
@pytest.mark.parametrize("kappa", [0.01, 0.1, 1.0])
def test_energia_inicial_y_cota(simulacion, nombre, kappa):
    """H(0) = E₀(1 + k₀κ), H nunca aumenta y ΣEᵢ(t) ≤ H(0)."""
    sim = simulacion(nombre, kappa)
    en = analisis.energias(sim)
    red = REDES[nombre]
    H0 = analisis.energia_inicial(sim.parametros, red.grados[red.fuente])
    H = en.H
    assert H[0] == pytest.approx(H0, rel=1e-12)
    assert np.all(np.diff(H) <= 1e-10 * H0)
    assert en.suma_nodos.max() <= H0 * (1 + 1e-10)


def test_H_decae_como_exponencial(simulacion):
    """H(t) ≈ H(0) e^(−γt) para cualquier K (teoría, punto 6, paso 9)."""
    for kappa in (0.01, 0.1, 1.0):
        sim = simulacion("malla", kappa)
        en = analisis.energias(sim)
        norm = en.H * np.exp(sim.parametros.gamma * sim.t) / en.H[0]
        assert norm.min() > 0.98 and norm.max() < 1.02


def test_sin_resistencia_H_se_conserva_y_suma_de_E_no(simulacion):
    sim = simulacion("malla", 0.1, R=0.0, T=10e-3)
    en = analisis.energias(sim)
    H, S = en.H, en.suma_nodos
    assert (H.max() - H.min()) / H[0] < 1e-8
    assert (S.max() - S.min()) / S[0] > 0.1


def test_balance_de_una_malla(simulacion):
    """dEᵢ/dt = −RIᵢ² + Pᵢ en un vecino de la fuente (teoría, punto 5, paso 7)."""
    sim = simulacion("malla", 0.1)
    p = sim.parametros
    en = analisis.energias(sim)
    i = int(np.flatnonzero(REDES["malla"].distancias == 1)[0])
    Pi = analisis.potencia_intercambio(sim.Q, sim.I, sim.Lambda, p)[:, i]
    dEi = -p.R * sim.I[:, i]**2 + Pi
    pred = en.E[0, i] + cumulative_simpson(dEi, x=sim.t, initial=0.0)
    assert np.abs(pred - en.E[:, i]).max() < 1e-5 * en.E[:, i].max()


def test_suma_de_E_puede_superar_E0(simulacion):
    """Con κ = 1 en la malla, ΣEᵢ llega a ≈ 4.7 E₀: no es una fracción de E₀."""
    en = analisis.energias(simulacion("malla", 1.0))
    assert en.suma_nodos.max() > 4 * en.E0
