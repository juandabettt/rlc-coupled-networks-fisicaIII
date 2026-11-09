"""Validación de los tiempos de llegada y de las estadísticas por distancia
(red_rlc.analisis, Fase 3).

Los valores de referencia de la malla salen del punto 7 de la teoría (Fase 1),
calculados con la solución exacta.
"""

import numpy as np
import pytest

from red_rlc import analisis, modelo, redes
from conftest import P_BASE, REDES

idx = redes.indice_malla


# ---------------------------------------------------------------------------
# Detección del cruce del umbral
# ---------------------------------------------------------------------------

def test_indice_primer_cruce():
    E = np.array([[1.0, 0.0, 0.0],
                  [1.0, 0.5, 0.0],
                  [1.0, 2.0, 0.1]])
    assert analisis.indice_primer_cruce(E, 1.0).tolist() == [0, 2, -1]


def test_interpolacion_exacta_para_ley_de_potencia():
    """Con E ∝ tᵖ y muestras con t > 0, la interpolación log–log es exacta."""
    t = np.linspace(1e-6, 1e-4, 50)
    p, tau = 6.0, 3e-5
    E = ((t / tau) ** p)[:, None]
    E_th = 1e-3
    tl = analisis.tiempos_llegada(t, E, E_th)
    assert tl[0] == pytest.approx(tau * E_th ** (1 / p), rel=1e-12)


def test_fuente_llega_en_cero_y_no_alcanzados_son_nan():
    t = np.linspace(0, 1, 11)
    E = np.column_stack([np.ones_like(t), np.zeros_like(t)])
    tl = analisis.tiempos_llegada(t, E, 0.5)
    assert tl[0] == 0.0
    assert np.isnan(tl[1])


def test_refinamiento_con_funcion_exacta():
    t = np.linspace(0, 1, 5)
    f = lambda s: np.array([s**2])
    E = np.array([f(s) for s in t])
    tl = analisis.tiempos_llegada(t, E, 0.3, energia_en=f)
    assert tl[0] == pytest.approx(np.sqrt(0.3), rel=1e-10)


def test_llegadas_propiedades():
    L = analisis.Llegadas(np.array([0.0, 2e-3, np.nan]), gamma=1000.0, umbral=1e-6)
    assert np.allclose(L.t_gamma[:2], [0.0, 2.0])
    assert L.alcanzado.tolist() == [True, True, False]
    assert L.n_no_alcanzados == 1


def test_opciones_invalidas(simulacion):
    sim = simulacion("malla", 0.1)
    with pytest.raises(ValueError):
        analisis.llegadas(sim, refinar="spline")
    with pytest.raises(ValueError):
        analisis.evaluador_denso(sim)          # se simuló sin denso=True


# ---------------------------------------------------------------------------
# Comparación con la teoría (malla, fuente interior)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kappa, alcanzados", [(0.003, 12), (0.01, 44), (0.03, 99)])
def test_nodos_alcanzados_como_la_teoria(simulacion, kappa, alcanzados):
    """Con T = 10/γ, el número de nodos que cruzan 10⁻⁶ E₀ (sin la fuente)."""
    L = analisis.llegadas(simulacion("malla", kappa))
    assert int(L.alcanzado.sum()) - 1 == alcanzados


@pytest.mark.parametrize("kappa, nodo, t_teoria_us", [
    (0.01, idx(4, 5), 3.18),     # d = 1
    (0.01, idx(4, 6), 323),      # d = 2, Nᵢ = 1
    (0.1, idx(4, 6), 28.3),
    (0.1, idx(4, 9), 587),       # d = 5, Nᵢ = 1
    (1.0, idx(4, 6), 5.80),
    (1.0, idx(4, 9), 71.7),
    (10.0, idx(4, 9), 18.5),
])
def test_tiempos_como_la_teoria(simulacion, kappa, nodo, t_teoria_us):
    """Tabla del punto 7 de la teoría; se admite 1 % porque aquella prueba usó
    un muestreo más grueso."""
    L = analisis.llegadas(simulacion("malla", kappa))
    assert L.t[nodo] * 1e6 == pytest.approx(t_teoria_us, rel=0.01)


def test_mas_caminos_llegan_antes(simulacion):
    """A d = 2, el nodo con Nᵢ = 2 llega antes que el de Nᵢ = 1. La teoría
    predice una razón entre 2^(−1/2) = 0.71 y 2^(−1/3) = 0.79."""
    m = REDES["malla"]
    a, b = idx(5, 5), idx(4, 6)
    assert m.caminos[a] == 2 and m.caminos[b] == 1
    for kappa, esperado in ((0.01, 0.70), (0.1, 0.78), (1.0, 0.79)):
        L = analisis.llegadas(simulacion("malla", kappa))
        assert L.t[a] / L.t[b] == pytest.approx(esperado, abs=0.02)


def test_denso_coincide_con_modal():
    sim = modelo.simular(REDES["malla"], P_BASE.con(kappa=0.1), denso=True)
    en = analisis.energias(sim)
    a = analisis.llegadas(sim, en, refinar="denso")
    b = analisis.llegadas(sim, en, refinar="modal")
    assert np.nanmax(np.abs(a.t - b.t)) < 1e-6 * np.nanmax(b.t)
    assert analisis.llegadas(sim, en).t == pytest.approx(a.t)   # "auto" usa denso


def test_umbral_menor_llega_antes(simulacion):
    sim = simulacion("mundo_pequeno", 0.1)
    en = analisis.energias(sim)
    t4, t6, t8 = (analisis.llegadas(sim, en, umbral=u).t for u in analisis.UMBRALES)
    # Todo nodo que cruza un umbral alto cruza también los más bajos...
    assert np.all(np.isfinite(t6[np.isfinite(t4)]))
    assert np.all(np.isfinite(t8[np.isfinite(t6)]))
    # ...y antes. (NaN = no alcanzado; se compara solo donde ambos existen.)
    ok = np.isfinite(t4)
    assert np.all(t6[ok] <= t4[ok])
    ok = np.isfinite(t6)
    assert np.all(t8[ok] <= t6[ok])


def test_llegadas_simetricas_en_el_anillo(simulacion):
    L = analisis.llegadas(simulacion("anillo", 0.1))
    N = L.t.size
    for i in range(1, N // 2):
        assert L.t[i] == pytest.approx(L.t[N - i], rel=1e-8)


# ---------------------------------------------------------------------------
# Rapidez del frente
# ---------------------------------------------------------------------------

def test_rapidez_frente_recta_exacta():
    d = np.array([0, 1, 2, 3, 4, 5])
    t = 2e-6 + 5e-6 * d                       # 5 µs por enlace
    t[0] = 0.0                                # la fuente se excluye
    v, b, a = analisis.rapidez_frente(t, d)
    assert b == pytest.approx(5e-6) and a == pytest.approx(2e-6)
    assert v == pytest.approx(2e5)            # nodos por segundo


def test_rapidez_frente_ignora_no_alcanzados_y_casos_insuficientes():
    d = np.array([0, 1, 2, 3])
    t = np.array([0.0, 1e-6, 2e-6, np.nan])
    assert analisis.rapidez_frente(t, d)[0] == pytest.approx(1e6)
    t_un_solo_d = np.array([0.0, 1e-6, np.nan, np.nan])
    assert np.isnan(analisis.rapidez_frente(t_un_solo_d, d)[0])


def test_rapidez_crece_con_kappa(simulacion):
    """En el anillo, el frente es más rápido con más acoplamiento."""
    d = REDES["anillo"].distancias
    v = [analisis.rapidez_frente(analisis.llegadas(simulacion("anillo", k)).t, d)[0]
         for k in (0.1, 1.0)]
    assert v[1] > 2 * v[0]


# ---------------------------------------------------------------------------
# Estadísticas por distancia
# ---------------------------------------------------------------------------

def test_por_distancia_sintetico():
    d = np.array([0, 1, 1, 1, 2, 2, -1])
    v = np.array([5.0, 1.0, 2.0, 3.0, 4.0, np.nan, 9.0])
    r = analisis.por_distancia(v, d)
    assert r.d.tolist() == [0, 1, 2]                 # el nodo inalcanzable se ignora
    assert r.N_d.tolist() == [1, 3, 2]
    assert r.n_validos.tolist() == [1, 3, 1]         # el NaN no cuenta
    assert r.media.tolist() == [5.0, 2.0, 4.0]
    assert np.isnan(r.sigma[0]) and np.isnan(r.sigma[2])   # menos de 2 valores
    assert r.sigma[1] == pytest.approx(1.0)          # ddof = 1
    assert r.sigma_relativa[1] == pytest.approx(0.5)
    assert r.minimo[1] == 1.0 and r.maximo[1] == 3.0


def test_por_distancia_realizaciones():
    """Dos realizaciones con distinta d máx: eje d común y NaN donde no hay nodos."""
    d = np.array([[0, 1, 1, 2], [0, 1, 1, 1]])
    v = np.array([[9.0, 1.0, 3.0, 5.0], [8.0, 2.0, 2.0, 2.0]])
    r = analisis.por_distancia_realizaciones(v, d)
    assert r["d"].tolist() == [0, 1, 2]
    assert r["N_d"].tolist() == [[1, 2, 1], [1, 3, 0]]
    assert r["media"][0].tolist() == [9.0, 2.0, 5.0]
    assert r["media"][1, :2].tolist() == [8.0, 2.0] and np.isnan(r["media"][1, 2])
    assert r["sigma"][0, 1] == pytest.approx(np.sqrt(2))     # ddof = 1
    assert r["sigma"][1, 1] == 0.0
    assert np.isnan(r["sigma"][0, 0])                         # N_d = 1


# ---------------------------------------------------------------------------
# Nodos a igual distancia (E4)
# ---------------------------------------------------------------------------

def test_peso_modal_simetrico_y_coherente_con_autovectores():
    """Wᵢ ≥ 0, es igual en nodos simétricos del anillo (pese a los autovalores
    repetidos) y, sin degeneración, coincide con Σₙ vₙ(i)² vₙ(0)²."""
    red = REDES["anillo"]
    W = analisis.peso_modal_incoherente(red.laplaciano, red.fuente)
    assert np.all(W >= 0)
    N = red.N
    for i in range(1, N // 2):
        assert W[i] == pytest.approx(W[N - i], rel=1e-9)
    # Sin autovalores repetidos, W coincide con la suma sobre autovectores.
    red = REDES["erdos_renyi"]
    lam, V = np.linalg.eigh(red.laplaciano)
    W2 = ((V * V[red.fuente]) ** 2).sum(axis=1)
    if np.min(np.diff(lam)) > 1e-6:
        assert np.allclose(analisis.peso_modal_incoherente(red.laplaciano, red.fuente), W2)


def test_peso_modal_en_la_fuente_es_el_mayor():
    for red in REDES.values():
        W = analisis.peso_modal_incoherente(red.laplaciano, red.fuente)
        assert np.argmax(W) == red.fuente


def test_relacion_a_igual_distancia():
    # Dos realizaciones; dentro de cada distancia, y = x⁻² exacto.
    d = np.array([[0, 1, 1, 1, 2, 2, 2], [0, 1, 1, 1, 2, 2, 2]])
    x = np.array([[1, 1, 2, 4, 1, 3, 9], [1, 2, 3, 5, 2, 4, 8]], dtype=float)
    y = x ** -2.0
    r = analisis.relacion_a_igual_distancia(y, x, d)
    assert r["rho_mediana"] == pytest.approx(-1.0)
    assert r["frac_positiva"] == 0.0
    assert r["n_grupos"] == 4
    assert r["pendiente"] == pytest.approx(-2.0)
    assert r["R2"] == pytest.approx(1.0)


def test_relacion_ignora_no_alcanzados():
    d = np.array([[0, 1, 1, 1, 1]])
    x = np.array([[1.0, 1, 2, 3, 4]])
    y = np.array([[1.0, 4, 3, np.nan, 1]])
    r = analisis.relacion_a_igual_distancia(y, x, d)
    assert r["n_grupos"] == 1 and r["rho_mediana"] == pytest.approx(-1.0)


@pytest.mark.parametrize("nombre", redes.TOPOLOGIAS)
def test_por_distancia_en_las_redes(simulacion, nombre):
    sim = simulacion(nombre, 0.1)
    red = REDES[nombre]
    en = analisis.energias(sim)
    Em = analisis.energia_media(sim.t, en.E)
    r = analisis.por_distancia(Em, red.distancias)
    assert np.array_equal(r.N_d, red.distribucion_distancias)
    assert r.N_d.sum() == red.N
    # La fuente es el nodo con más energía media.
    assert r.media[0] == Em.max()
