"""Generación de topologías y distancias topológicas.

Construye las cuatro redes de referencia del plan (todas con N = 100 y grado
medio cercano a 4) y calcula las cantidades estructurales que usan los demás
módulos:

- matriz de adyacencia A (no dirigida, sin autoenlaces) y laplaciano Λ = D − A;
- distancia topológica d₀ᵢ desde la fuente (búsqueda en anchura);
- número de caminos más cortos Nᵢ desde la fuente (experimento E4);
- distribución de distancias N_d (gráfico G1).

Convenciones:

- Los nodos se numeran de 0 a N − 1.
- Las redes aleatorias usan semillas fijas, de modo que cada realización se
  puede reproducir.
- Una distancia de −1 indica que el nodo no es alcanzable desde la fuente.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import networkx as nx
import numpy as np

# Parámetros de las redes de referencia (ver «Parámetros y redes de referencia»
# en el plan del proyecto).
N_BASE = 100
LADO_MALLA = 10
K_ANILLO = 4
P_MUNDO_PEQUENO = 0.1
P_ERDOS_RENYI = 4 / 99
N_REALIZACIONES = 30
SEMILLA_BASE = 2026

# Valor que marca un nodo inalcanzable en los arreglos de distancias.
SIN_DISTANCIA = -1


@dataclass
class Red:
    """Una red lista para simular.

    Atributos
    ---------
    nombre : identificador de la topología ("malla", "anillo", ...).
    grafo : grafo de NetworkX con nodos 0..N−1.
    fuente : índice del nodo perturbado (Q₀ ≠ 0 en t = 0).
    A : matriz de adyacencia (N × N, float).
    distancias : d₀ᵢ para cada nodo (int); −1 si no es alcanzable.
    caminos : Nᵢ, número de caminos más cortos desde la fuente (int).
    semilla : semilla usada (None para redes deterministas).
    intentos : grafos generados hasta obtener uno conexo (1 si no se descartó
        ninguno). Sirve para declarar el sesgo de selección en ER.
    """

    nombre: str
    grafo: nx.Graph
    fuente: int
    A: np.ndarray = field(repr=False)
    distancias: np.ndarray = field(repr=False)
    caminos: np.ndarray = field(repr=False)
    semilla: int | None = None
    intentos: int = 1

    @property
    def N(self) -> int:
        return self.A.shape[0]

    @property
    def grados(self) -> np.ndarray:
        return self.A.sum(axis=1).astype(int)

    @property
    def laplaciano(self) -> np.ndarray:
        return laplaciano(self.A)

    @property
    def distancia_maxima(self) -> int:
        return int(self.distancias.max())

    @property
    def distribucion_distancias(self) -> np.ndarray:
        return distribucion_distancias(self.distancias)


# ---------------------------------------------------------------------------
# Cantidades estructurales
# ---------------------------------------------------------------------------

def matriz_adyacencia(G: nx.Graph) -> np.ndarray:
    """Matriz de adyacencia densa con los nodos en el orden 0..N−1."""
    return nx.to_numpy_array(G, nodelist=list(range(G.number_of_nodes())),
                            dtype=float)


def laplaciano(A: np.ndarray) -> np.ndarray:
    """Laplaciano combinatorio Λ = D − A, con D la matriz diagonal de grados."""
    return np.diag(A.sum(axis=1)) - A


def distancias_y_caminos(G: nx.Graph, fuente: int) -> tuple[np.ndarray, np.ndarray]:
    """Distancia d₀ᵢ y número de caminos más cortos Nᵢ desde la fuente.

    Búsqueda en anchura: un nodo a distancia d + 1 acumula los caminos de
    todos sus vecinos a distancia d. Los nodos inalcanzables quedan con
    d = −1 y N = 0.
    """
    n = G.number_of_nodes()
    dist = np.full(n, SIN_DISTANCIA, dtype=int)
    caminos = np.zeros(n, dtype=np.int64)
    dist[fuente] = 0
    caminos[fuente] = 1
    frontera = [fuente]
    while frontera:
        siguiente = []
        for u in frontera:
            for v in G.neighbors(u):
                if dist[v] == SIN_DISTANCIA:
                    dist[v] = dist[u] + 1
                    siguiente.append(v)
                if dist[v] == dist[u] + 1:
                    caminos[v] += caminos[u]
        frontera = siguiente
    return dist, caminos


def distribucion_distancias(distancias: np.ndarray) -> np.ndarray:
    """N_d: cantidad de nodos a cada distancia d = 0, 1, …, d_max.

    Ignora los nodos inalcanzables (d = −1).
    """
    alcanzables = distancias[distancias != SIN_DISTANCIA]
    return np.bincount(alcanzables)


def _crear_red(nombre, G, fuente, semilla=None, intentos=1) -> Red:
    """Empaqueta un grafo con sus cantidades estructurales."""
    if nx.number_of_selfloops(G) > 0:
        raise ValueError(f"La red {nombre!r} tiene autoenlaces.")
    if sorted(G.nodes) != list(range(G.number_of_nodes())):
        raise ValueError(f"Los nodos de {nombre!r} deben ser 0..N−1.")
    dist, caminos = distancias_y_caminos(G, fuente)
    return Red(nombre, G, fuente, matriz_adyacencia(G), dist, caminos,
               semilla, intentos)


# ---------------------------------------------------------------------------
# Topologías
# ---------------------------------------------------------------------------

def indice_malla(fila: int, columna: int, lado: int = LADO_MALLA) -> int:
    """Índice del nodo (fila, columna) de la malla, en orden por filas."""
    return fila * lado + columna


def malla(lado: int = LADO_MALLA, fuente: str | int = "interior") -> Red:
    """Rejilla lado × lado con borde abierto.

    fuente:
        "interior" — nodo (lado//2 − 1, lado//2 − 1); en 10 × 10 es el
            nodo 44 y da d_max = 10.
        "esquina" — nodo (0, 0), como comparación; en 10 × 10 da d_max = 18.
        int — índice explícito.
    """
    G = nx.convert_node_labels_to_integers(
        nx.grid_2d_graph(lado, lado), ordering="sorted")
    if fuente == "interior":
        c = lado // 2 - 1
        fuente = indice_malla(c, c, lado)
    elif fuente == "esquina":
        fuente = 0
    return _crear_red("malla", G, int(fuente))


def anillo(N: int = N_BASE, k: int = K_ANILLO, fuente: int = 0) -> Red:
    """Anillo regular: cada nodo se une a sus k/2 vecinos de cada lado.

    Todos los nodos son equivalentes, así que la fuente es el nodo 0.
    Con N = 100 y k = 4 se tiene d_max = 25.
    """
    if k % 2:
        raise ValueError("k debe ser par.")
    G = nx.circulant_graph(N, range(1, k // 2 + 1))
    return _crear_red("anillo", G, fuente)


def mundo_pequeno(N: int = N_BASE, k: int = K_ANILLO, p: float = P_MUNDO_PEQUENO,
                  semilla: int = SEMILLA_BASE, fuente: int = 0,
                  max_intentos: int = 1000) -> Red:
    """Red de Watts–Strogatz conexa (anillo con k vecinos y recableado p)."""
    return _aleatoria_conexa(
        "mundo_pequeno",
        lambda rng: nx.watts_strogatz_graph(N, k, p, seed=rng),
        semilla, fuente, max_intentos)


def erdos_renyi(N: int = N_BASE, p: float = P_ERDOS_RENYI,
                semilla: int = SEMILLA_BASE, fuente: int = 0,
                max_intentos: int = 10_000) -> Red:
    """Red de Erdős–Rényi G(N, p) conexa.

    Se descartan las muestras desconexas. Con p = 4/99 solo cerca del 18 %
    lo son, así que `Red.intentos` registra cuántas se generaron; este
    descarte selecciona un subconjunto de redes y debe declararse.
    """
    return _aleatoria_conexa(
        "erdos_renyi",
        lambda rng: nx.gnp_random_graph(N, p, seed=rng),
        semilla, fuente, max_intentos)


def _aleatoria_conexa(nombre, generar, semilla, fuente, max_intentos) -> Red:
    """Genera grafos con un único generador sembrado hasta obtener uno conexo.

    Usar un solo `random.Random(semilla)` para todos los intentos hace que el
    resultado dependa solo de la semilla.
    """
    rng = random.Random(semilla)
    for intento in range(1, max_intentos + 1):
        G = generar(rng)
        if nx.is_connected(G):
            return _crear_red(nombre, G, fuente, semilla, intento)
    raise RuntimeError(
        f"No se obtuvo una red {nombre!r} conexa en {max_intentos} intentos "
        f"(semilla {semilla}).")


# ---------------------------------------------------------------------------
# Catálogo y realizaciones
# ---------------------------------------------------------------------------

TOPOLOGIAS = ("malla", "anillo", "mundo_pequeno", "erdos_renyi")
ALEATORIAS = ("mundo_pequeno", "erdos_renyi")


def construir(nombre: str, semilla: int = SEMILLA_BASE, **kwargs) -> Red:
    """Construye una red de referencia por nombre.

    `semilla` solo se usa en las redes aleatorias; `kwargs` se pasan al
    constructor correspondiente (p. ej. fuente="esquina" en la malla).
    """
    constructores = {
        "malla": malla,
        "anillo": anillo,
        "mundo_pequeno": mundo_pequeno,
        "erdos_renyi": erdos_renyi,
    }
    if nombre not in constructores:
        raise ValueError(f"Topología desconocida {nombre!r}; opciones: {TOPOLOGIAS}")
    if nombre in ALEATORIAS:
        kwargs["semilla"] = semilla
    return constructores[nombre](**kwargs)


def con_fuente(red: Red, fuente: int) -> Red:
    """La misma red con otra fuente (recalcula distancias y caminos).

    Conserva el nombre, la semilla y los intentos. Se usa en el experimento
    E5 para estudiar el efecto de la posición de la fuente.
    """
    if not 0 <= fuente < red.N:
        raise ValueError(f"Fuente {fuente} fuera de rango (0..{red.N - 1}).")
    return _crear_red(red.nombre, red.grafo, int(fuente), red.semilla, red.intentos)


def semillas(n: int = N_REALIZACIONES, semilla_base: int = SEMILLA_BASE) -> list[int]:
    """Semillas fijas para n realizaciones: semilla_base, semilla_base + 1, …"""
    return [semilla_base + i for i in range(n)]


def realizaciones(nombre: str, n: int | None = None,
                  semilla_base: int = SEMILLA_BASE, **kwargs) -> list[Red]:
    """Lista de redes de una topología.

    Las redes aleatorias tienen n realizaciones (30 por defecto). Las
    deterministas devuelven una sola red.
    """
    if nombre not in ALEATORIAS:
        return [construir(nombre, **kwargs)]
    n = N_REALIZACIONES if n is None else n
    return [construir(nombre, semilla=s, **kwargs) for s in semillas(n, semilla_base)]


def redes_referencia(semilla: int = SEMILLA_BASE) -> dict[str, Red]:
    """Una red de cada topología (para pruebas, G1 y exploración rápida)."""
    return {nombre: construir(nombre, semilla=semilla) for nombre in TOPOLOGIAS}
