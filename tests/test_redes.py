"""Validación de red_rlc.redes: topologías, laplaciano, distancias y caminos."""

from math import comb

import networkx as nx
import numpy as np
import pytest

from red_rlc import redes

REDES = redes.redes_referencia()


@pytest.fixture(params=redes.TOPOLOGIAS)
def red(request):
    return REDES[request.param]


# ---------------------------------------------------------------------------
# Propiedades comunes a las cuatro topologías
# ---------------------------------------------------------------------------

def test_tamano_y_nodos(red):
    assert red.N == redes.N_BASE
    assert red.A.shape == (redes.N_BASE, redes.N_BASE)
    assert sorted(red.grafo.nodes) == list(range(redes.N_BASE))


def test_adyacencia_simetrica_binaria_sin_autoenlaces(red):
    A = red.A
    assert np.array_equal(A, A.T)
    assert set(np.unique(A)) <= {0.0, 1.0}
    assert np.all(np.diag(A) == 0)


def test_laplaciano(red):
    """Λ = D − A: simétrico, filas que suman 0, semidefinido positivo y con un
    único autovalor nulo (la red es conexa)."""
    L = red.laplaciano
    assert np.array_equal(L, L.T)
    assert np.allclose(L.sum(axis=1), 0)
    assert np.array_equal(np.diag(L), red.grados)
    autovalores = np.linalg.eigvalsh(L)
    assert autovalores.min() > -1e-10
    assert np.sum(np.abs(autovalores) < 1e-9) == 1


def test_conexa_y_todos_alcanzables(red):
    assert nx.is_connected(red.grafo)
    assert np.all(red.distancias >= 0)
    assert np.all(red.caminos >= 1)


def test_distancias_coinciden_con_networkx(red):
    esperadas = nx.single_source_shortest_path_length(red.grafo, red.fuente)
    for nodo, d in esperadas.items():
        assert red.distancias[nodo] == d
    assert red.distancias[red.fuente] == 0


def test_caminos_coinciden_con_networkx(red):
    for nodo in range(red.N):
        n = sum(1 for _ in nx.all_shortest_paths(red.grafo, red.fuente, nodo))
        assert red.caminos[nodo] == n, f"nodo {nodo}"


def test_distribucion_distancias(red):
    Nd = red.distribucion_distancias
    assert Nd.sum() == red.N
    assert Nd[0] == 1
    assert len(Nd) == red.distancia_maxima + 1
    assert np.all(Nd > 0)


# ---------------------------------------------------------------------------
# Valores conocidos de las redes deterministas
# ---------------------------------------------------------------------------

def test_malla_fuente_interior():
    m = redes.malla()
    assert m.fuente == 44
    assert m.distancia_maxima == 10
    assert m.grafo.number_of_edges() == 2 * 10 * 9
    assert sorted(set(m.grados)) == [2, 3, 4]


def test_malla_fuente_esquina_y_caminos_binomiales():
    """Desde la esquina (0, 0), al nodo (f, c) llegan C(f + c, f) caminos."""
    m = redes.malla(fuente="esquina")
    assert m.fuente == 0
    assert m.distancia_maxima == 18
    for f in range(10):
        for c in range(10):
            i = redes.indice_malla(f, c)
            assert m.distancias[i] == f + c
            assert m.caminos[i] == comb(f + c, f)


def test_anillo():
    a = redes.anillo()
    assert np.all(a.grados == 4)
    assert a.distancia_maxima == 25
    # Nodo opuesto a la fuente: d = 25. Vecinos inmediatos: d = 1.
    assert a.distancias[50] == 25
    assert a.distancias[[1, 2, 98, 99]].tolist() == [1, 1, 1, 1]
    # Nodo 3: se llega por 1 y por 2 → 2 caminos; nodo 4: solo por 2 → 1.
    assert a.caminos[3] == 2
    assert a.caminos[4] == 1


def test_anillo_k_impar_falla():
    with pytest.raises(ValueError):
        redes.anillo(k=3)


# ---------------------------------------------------------------------------
# Redes aleatorias: reproducibilidad y conexidad
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nombre", redes.ALEATORIAS)
def test_misma_semilla_misma_red(nombre):
    r1 = redes.construir(nombre, semilla=123)
    r2 = redes.construir(nombre, semilla=123)
    assert np.array_equal(r1.A, r2.A)
    assert r1.intentos == r2.intentos


@pytest.mark.parametrize("nombre", redes.ALEATORIAS)
def test_semillas_distintas_redes_distintas(nombre):
    r1 = redes.construir(nombre, semilla=1)
    r2 = redes.construir(nombre, semilla=2)
    assert not np.array_equal(r1.A, r2.A)


def test_mundo_pequeno_conserva_enlaces():
    """El recableado de Watts–Strogatz no cambia el número de enlaces: N k / 2."""
    r = redes.mundo_pequeno()
    assert r.grafo.number_of_edges() == redes.N_BASE * redes.K_ANILLO // 2
    assert r.grados.mean() == redes.K_ANILLO


@pytest.mark.parametrize("nombre", redes.ALEATORIAS)
def test_realizaciones_todas_conexas(nombre):
    lista = redes.realizaciones(nombre)
    assert len(lista) == redes.N_REALIZACIONES
    assert [r.semilla for r in lista] == redes.semillas()
    for r in lista:
        assert nx.is_connected(r.grafo)
        assert r.intentos >= 1
        assert r.N == redes.N_BASE


def test_realizaciones_deterministas_es_una_sola():
    assert len(redes.realizaciones("malla")) == 1
    assert len(redes.realizaciones("anillo", n=30)) == 1


def test_semillas():
    assert redes.semillas(3) == [2026, 2027, 2028]
    assert redes.semillas(2, semilla_base=10) == [10, 11]


def test_erdos_renyi_sin_intentos_suficientes_falla():
    # Con p muy bajo es prácticamente imposible obtener una red conexa.
    with pytest.raises(RuntimeError):
        redes.erdos_renyi(p=0.001, max_intentos=5)


# ---------------------------------------------------------------------------
# Casos límite de las funciones auxiliares
# ---------------------------------------------------------------------------

def test_nodos_inalcanzables():
    G = nx.Graph([(0, 1), (1, 2)])
    G.add_node(3)
    dist, caminos = redes.distancias_y_caminos(G, 0)
    assert dist.tolist() == [0, 1, 2, redes.SIN_DISTANCIA]
    assert caminos.tolist() == [1, 1, 1, 0]
    assert redes.distribucion_distancias(dist).tolist() == [1, 1, 1]


def test_ciclo_par_dos_caminos_al_opuesto():
    dist, caminos = redes.distancias_y_caminos(nx.cycle_graph(6), 0)
    assert dist[3] == 3
    assert caminos[3] == 2


def test_autoenlaces_rechazados():
    G = nx.path_graph(3)
    G.add_edge(1, 1)
    with pytest.raises(ValueError):
        redes._crear_red("prueba", G, 0)


def test_nodos_mal_numerados_rechazados():
    G = nx.relabel_nodes(nx.path_graph(3), {0: 10})
    with pytest.raises(ValueError):
        redes._crear_red("prueba", G, 1)


def test_con_fuente():
    m = redes.malla()
    e = redes.con_fuente(m, 0)
    assert e.fuente == 0 and e.distancia_maxima == 18
    assert np.array_equal(e.A, m.A)                       # mismo grafo
    assert m.fuente == 44                                 # el original no cambia
    with pytest.raises(ValueError):
        redes.con_fuente(m, 100)


def test_tamanos_distintos():
    assert redes.malla(lado=6).N == 36 and redes.malla(lado=6).distancia_maxima == 6
    assert redes.anillo(N=50).distancia_maxima == 13


def test_topologia_desconocida():
    with pytest.raises(ValueError):
        redes.construir("estrella")
