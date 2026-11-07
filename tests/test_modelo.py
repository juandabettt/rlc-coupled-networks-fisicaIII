"""Validación de red_rlc.modelo.

Incluye las pruebas de la tabla «Validación del código» del plan que no son
de energía (las de energía están en test_energia.py):

- Oscilador aislado (K = 0)
- Dos nodos (batidos con ω₀ y √(ω₀² + 2K))
- Modo uniforme (ΣQᵢ igual al oscilador aislado)
- Simetría (anillo: +d y −d responden igual)
- Convergencia (RK4 de orden 4)
- Referencia (DOP853 frente a modos normales, error ≪ 10⁻³ Q₀)
"""

import numpy as np
import pytest

from red_rlc import modelo, redes
from conftest import P_BASE, REDES


def oscilador_aislado(p, t):
    """Solución exacta de un oscilador con Q(0) = Q₀, I(0) = 0 (teoría, punto 2)."""
    g, w0 = p.gamma, p.omega0
    W = np.sqrt(w0**2 - g**2 / 4)
    env = np.exp(-g * t / 2)
    Q = p.Q0 * env * (np.cos(W * t) + g / (2 * W) * np.sin(W * t))
    I = -p.Q0 * w0**2 / W * env * np.sin(W * t)
    return Q, I


# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------

def test_parametros_base():
    p = P_BASE
    assert p.gamma == pytest.approx(1000.0)
    assert p.omega0 == pytest.approx(31622.7766, rel=1e-8)
    assert p.factor_calidad == pytest.approx(31.6227766, rel=1e-8)
    assert p.E0 == pytest.approx(5e-7)
    assert p.T == pytest.approx(10e-3)
    assert p.periodo == pytest.approx(198.69e-6, rel=1e-4)
    assert p.K == pytest.approx(0.1 * p.omega0**2)
    assert p.Cc == pytest.approx(p.C / 0.1)


def test_parametros_con_y_limites():
    p = P_BASE.con(kappa=1.0)
    assert p.kappa == 1.0 and P_BASE.kappa == 0.1   # no modifica el original
    assert P_BASE.con(kappa=0.0).Cc == np.inf
    assert P_BASE.con(R=0.0).factor_calidad == np.inf
    with pytest.raises(ValueError):
        P_BASE.con(R=0.0).T                          # sin γ no hay escala 1/γ
    with pytest.raises(ValueError):
        modelo.Parametros(L=0.0)
    with pytest.raises(ValueError):
        modelo.Parametros(kappa=-1.0)


def test_kappas_del_plan():
    assert modelo.KAPPAS_BASE == (0.01, 0.03, 0.1, 0.3, 1.0)
    assert modelo.KAPPAS_E2[-2:] == (3.0, 10.0)


# ---------------------------------------------------------------------------
# Piezas del sistema
# ---------------------------------------------------------------------------

def test_condiciones_iniciales():
    Q, I = modelo.condiciones_iniciales(5, 2, 1e-6)
    assert Q.tolist() == [0, 0, 1e-6, 0, 0]
    assert np.all(I == 0)


def test_matriz_rigidez_y_omega_maxima():
    Lambda = REDES["malla"].laplaciano
    p = P_BASE.con(kappa=1.0)
    M = modelo.matriz_rigidez(Lambda, p)
    assert np.allclose(M, p.omega0**2 * np.eye(100) + p.K * Lambda)
    lam_max = np.linalg.eigvalsh(Lambda)[-1]
    assert modelo.omega_maxima(Lambda, p) == pytest.approx(
        np.sqrt(p.omega0**2 + p.K * lam_max))


def test_malla_temporal():
    t = modelo.malla_temporal(1e-3, 2 * np.pi * 1000, puntos_por_periodo=50)
    assert t[0] == 0 and t[-1] == pytest.approx(1e-3)
    assert t.size == 51                       # 1 período × 50 puntos + 1
    assert np.allclose(np.diff(t), np.diff(t)[0])


def test_metodo_desconocido():
    with pytest.raises(ValueError):
        modelo.simular(REDES["malla"], P_BASE, metodo="euler")


# ---------------------------------------------------------------------------
# Plan: oscilador aislado (K = 0)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("metodo", ["dop853", "modal"])
def test_oscilador_aislado(simulacion, metodo):
    """Con K = 0 la fuente sigue la solución analítica y los demás nodos no se
    mueven."""
    sim = simulacion("malla", 0.0, metodo=metodo)
    p, f = sim.parametros, sim.fuente
    Qa, Ia = oscilador_aislado(p, sim.t)
    assert np.abs(sim.Q[:, f] - Qa).max() < 1e-8 * p.Q0
    assert np.abs(sim.I[:, f] - Ia).max() < 1e-8 * p.omega0 * p.Q0
    otros = np.delete(np.arange(sim.N), f)
    if metodo == "dop853":
        # Sin acoplamiento, los demás nodos no reciben nada: cero exacto.
        assert np.all(sim.Q[:, otros] == 0)
        assert np.all(sim.I[:, otros] == 0)
    else:
        # La solución modal pasa por los autovectores: queda redondeo (~1e−16 Q₀).
        assert np.abs(sim.Q[:, otros]).max() < 1e-13 * p.Q0
        assert np.abs(sim.I[:, otros]).max() < 1e-13 * p.omega0 * p.Q0


# ---------------------------------------------------------------------------
# Plan: dos nodos
# ---------------------------------------------------------------------------

LAMBDA_PAR = np.array([[1.0, -1.0], [-1.0, 1.0]])


def test_dos_nodos_frecuencias_modales():
    p = P_BASE.con(kappa=0.1)
    modos = modelo.modos_normales(LAMBDA_PAR, p)
    assert np.allclose(modos.lam, [0.0, 2.0])
    assert np.allclose(modos.omega2, [p.omega0**2, p.omega0**2 + 2 * p.K])


def test_dos_nodos_batidos_sin_resistencia():
    """Con R = 0: Q₁ = (Q₀/2)(cos ω₀t + cos ω_D t), Q₂ = (Q₀/2)(cos ω₀t − cos ω_D t)."""
    p = P_BASE.con(kappa=0.1, R=0.0)
    wS, wD = p.omega0, np.sqrt(p.omega0**2 + 2 * p.K)
    t = np.linspace(0, 2e-3, 4001)
    Q_ini, I_ini = modelo.condiciones_iniciales(2, 0, p.Q0)
    Q, I, _ = modelo.integrar_dop853(LAMBDA_PAR, p, t, Q_ini, I_ini)
    Q1 = p.Q0 / 2 * (np.cos(wS * t) + np.cos(wD * t))
    Q2 = p.Q0 / 2 * (np.cos(wS * t) - np.cos(wD * t))
    assert np.abs(Q[:, 0] - Q1).max() < 1e-8 * p.Q0
    assert np.abs(Q[:, 1] - Q2).max() < 1e-8 * p.Q0


def test_dos_nodos_con_resistencia_coincide_con_modal():
    p = P_BASE.con(kappa=1.0)
    t = np.linspace(0, 5e-3, 5001)
    Q_ini, I_ini = modelo.condiciones_iniciales(2, 0, p.Q0)
    Qd, Id, _ = modelo.integrar_dop853(LAMBDA_PAR, p, t, Q_ini, I_ini)
    Qm, Im = modelo.solucion_modal(LAMBDA_PAR, p, t, Q_ini, I_ini)
    assert np.abs(Qd - Qm).max() < 1e-8 * p.Q0


# ---------------------------------------------------------------------------
# Plan: modo uniforme
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nombre", redes.TOPOLOGIAS)
def test_modo_uniforme(simulacion, nombre):
    """ΣQᵢ(t) evoluciona como el oscilador aislado para cualquier K y red."""
    sim = simulacion(nombre, 1.0)
    Qa, Ia = oscilador_aislado(sim.parametros, sim.t)
    p = sim.parametros
    assert np.abs(sim.Q.sum(axis=1) - Qa).max() < 1e-8 * p.Q0
    assert np.abs(sim.I.sum(axis=1) - Ia).max() < 1e-8 * p.omega0 * p.Q0


# ---------------------------------------------------------------------------
# Plan: simetría
# ---------------------------------------------------------------------------

def test_simetria_anillo(simulacion):
    """En el anillo, los nodos a +d y −d de la fuente responden igual."""
    sim = simulacion("anillo", 0.1)
    N = sim.N
    for i in range(1, N // 2):
        assert np.abs(sim.Q[:, i] - sim.Q[:, N - i]).max() < 1e-9 * sim.parametros.Q0


def test_simetria_malla_diagonal(simulacion):
    """La fuente (4, 4) está sobre la diagonal: (f, c) y (c, f) responden igual."""
    sim = simulacion("malla", 0.1)
    for f in range(10):
        for c in range(f + 1, 10):
            a, b = redes.indice_malla(f, c), redes.indice_malla(c, f)
            assert np.abs(sim.Q[:, a] - sim.Q[:, b]).max() < 1e-9 * sim.parametros.Q0


# ---------------------------------------------------------------------------
# Plan: convergencia de RK4
# ---------------------------------------------------------------------------

def test_rk4_orden_4():
    """Al dividir el paso entre 2, el error de RK4 debe bajar unas 2⁴ = 16 veces."""
    red = REDES["malla"]
    p = P_BASE.con(kappa=1.0)
    t = modelo.malla_temporal(2e-3, modelo.omega_maxima(red.laplaciano, p), 10)
    ref = modelo.simular(red, p, "modal", t=t)
    errores = []
    for subpasos in (1, 2, 4, 8):
        sim = modelo.simular(red, p, "rk4", t=t, subpasos=subpasos)
        errores.append(np.abs(sim.Q - ref.Q).max())
    ordenes = np.log2(np.array(errores[:-1]) / np.array(errores[1:]))
    assert np.all((ordenes > 3.8) & (ordenes < 4.2)), ordenes


def test_rk4_exige_paso_fijo():
    t = np.array([0.0, 1e-6, 3e-6])
    Q, I = modelo.condiciones_iniciales(2, 0, 1e-6)
    with pytest.raises(ValueError):
        modelo.integrar_rk4(LAMBDA_PAR, P_BASE, t, Q, I)


# ---------------------------------------------------------------------------
# Plan: referencia (DOP853 frente a modos normales)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nombre", redes.TOPOLOGIAS)
@pytest.mark.parametrize("kappa", [0.01, 0.1, 1.0])
def test_dop853_coincide_con_modal(simulacion, nombre, kappa):
    """El plan pide error ≪ 10⁻³ Q₀ (amplitud del umbral); exigimos 10⁻⁷ Q₀."""
    a = simulacion(nombre, kappa)
    b = modelo.simular(REDES[nombre], a.parametros, "modal", t=a.t)
    p = a.parametros
    w = modelo.omega_maxima(a.Lambda, p)
    assert np.abs(a.Q - b.Q).max() < 1e-7 * p.Q0
    assert np.abs(a.I - b.I).max() < 1e-7 * w * p.Q0


def test_dop853_coincide_con_modal_acoplamiento_fuerte(simulacion):
    a = simulacion("erdos_renyi", 10.0)
    b = modelo.simular(REDES["erdos_renyi"], a.parametros, "modal", t=a.t)
    assert np.abs(a.Q - b.Q).max() < 1e-7 * a.parametros.Q0


# ---------------------------------------------------------------------------
# Solución modal: casos generales
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("R", [100.0, 2 * np.sqrt(1e-3 / 1e-6)],
                         ids=["sobreamortiguado", "critico"])
def test_modal_otros_regimenes(R):
    """La solución modal sigue siendo exacta con amortiguamiento crítico o fuerte."""
    red = REDES["anillo"]
    p = P_BASE.con(R=R, kappa=0.1)
    a = modelo.simular(red, p, "dop853", T=2e-3)
    b = modelo.simular(red, p, "modal", t=a.t)
    assert np.abs(a.Q - b.Q).max() < 1e-8 * p.Q0


def test_modal_condiciones_iniciales_arbitrarias():
    rng = np.random.default_rng(0)
    red = REDES["mundo_pequeno"]
    p = P_BASE.con(kappa=0.3)
    Q0 = rng.normal(size=red.N) * p.Q0
    I0 = rng.normal(size=red.N) * p.omega0 * p.Q0
    t = np.linspace(0, 1e-3, 2001)
    Qm, Im = modelo.solucion_modal(red.laplaciano, p, t, Q0, I0)
    assert np.allclose(Qm[0], Q0, atol=1e-12 * p.Q0, rtol=0)
    assert np.allclose(Im[0], I0, atol=1e-12 * p.omega0 * p.Q0, rtol=0)
    Qd, Id, _ = modelo.integrar_dop853(red.laplaciano, p, t, Q0, I0)
    assert np.abs(Qd - Qm).max() < 1e-7 * np.abs(Q0).max()


def test_pesos_modales():
    """Σₙ vₙ(i) vₙ(0) = δᵢ₀ (completitud), y el modo uniforme pesa 1/N."""
    red = REDES["malla"]
    modos = modelo.modos_normales(red.laplaciano, P_BASE)
    W = modos.pesos(red.fuente)
    esperado = np.zeros(red.N)
    esperado[red.fuente] = 1
    assert np.allclose(W.sum(axis=1), esperado)
    assert modos.lam[0] == 0
    assert np.allclose(W[:, 0], 1 / red.N)


def test_simulacion_metadatos(simulacion):
    sim = simulacion("malla", 0.1)
    assert sim.N == 100 and sim.fuente == 44 and sim.red == "malla"
    assert sim.Q.shape == sim.I.shape == (sim.t.size, 100)
    assert sim.t_gamma[-1] == pytest.approx(10.0)
    assert np.array_equal(sim.Lambda, REDES["malla"].laplaciano)
