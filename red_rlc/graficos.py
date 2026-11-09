"""Gráficos del proyecto (G1 a G10 del plan).

Todas las figuras siguen el mismo estilo: fondo claro, rejilla tenue, trazos
finos, título, ejes con unidades y escala logarítmica cuando la energía abarca
varias décadas. Los colores salen de una paleta validada para daltonismo:

- Categórica (identidad: una topología, un valor de κ), en orden fijo.
- Secuencial azul (magnitud: distancia, energía), de claro a oscuro.

Cada función `gN_...` devuelve una figura de matplotlib; `guardar` la escribe
en resultados/figuras/ como PNG y PDF.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")   # sin ventana: las figuras se guardan en archivo

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap
from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator, NullFormatter

from . import analisis as _analisis
from . import redes as _redes
from .resultados import FIGURAS

# ---------------------------------------------------------------------------
# Paleta y estilo
# ---------------------------------------------------------------------------

# Categórica, en orden fijo (nunca se recicla ni se reordena).
CATEGORICA = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100",
              "#e87ba4", "#008300", "#6250d6", "#e34948")

# Color fijo por topología: sigue a la red en todas las figuras.
COLOR_RED = dict(zip(_redes.TOPOLOGIAS, CATEGORICA))
NOMBRE_RED = {"malla": "Malla 10 × 10", "anillo": "Anillo regular (k = 4)",
              "mundo_pequeno": "Mundo pequeño (WS, p = 0.1)",
              "erdos_renyi": "Erdős–Rényi (p = 4/99)"}

# Secuencial azul, de claro a oscuro (pasos 150 a 700 de la rampa).
AZULES = ("#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
          "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b")

TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_TENUE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"
FONDO = "#fcfcfb"
ACENTO = CATEGORICA[1]          # naranja: marca la fuente

ESTILO = {
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "axes.edgecolor": EJE, "axes.labelcolor": TINTA_2, "axes.titlecolor": TINTA,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.labelsize": 9.5,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "xtick.color": TINTA_TENUE, "ytick.color": TINTA_TENUE,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.frameon": False, "legend.fontsize": 8.5,
    "lines.linewidth": 2.0, "font.size": 9.5,
    "figure.titlesize": 13, "figure.titleweight": "bold",
}
plt.rcParams.update(ESTILO)

TAMANO_BASE = ESTILO["font.size"]


def _fs(tamano: float) -> float:
    """Tamaño de letra escalado con el estilo vigente.

    Con el estilo normal devuelve el mismo valor; con el de presentación
    (font.size mayor, ver scripts/f5_figuras_presentacion.py) crece en la
    misma proporción, para que ningún texto quede diminuto al proyectar.
    """
    return tamano * plt.rcParams["font.size"] / TAMANO_BASE


def guardar(fig, nombre: str, formatos=("png", "pdf"), dpi: int = 200):
    """Guarda la figura en resultados/figuras/<nombre>.<formato> y la cierra."""
    rutas = []
    for fmt in formatos:
        ruta = FIGURAS / f"{nombre}.{fmt}"
        ruta.parent.mkdir(parents=True, exist_ok=True)     # admite subcarpetas
        fig.savefig(ruta, dpi=dpi, bbox_inches="tight")
        rutas.append(ruta)
    plt.close(fig)
    return rutas


# ---------------------------------------------------------------------------
# G1. Redes y sus distribuciones de distancia
# ---------------------------------------------------------------------------

def posiciones(red) -> dict:
    """Posición de cada nodo para dibujar la red, según su topología."""
    G = red.grafo
    if red.nombre == "malla":
        lado = int(round(np.sqrt(red.N)))
        return {i: (i % lado, -(i // lado)) for i in G.nodes}
    if red.nombre in ("anillo", "mundo_pequeno"):
        # En círculo: los atajos de Watts–Strogatz se ven como cuerdas.
        ang = 2 * np.pi * np.arange(red.N) / red.N
        return {i: (np.cos(a), np.sin(a)) for i, a in zip(G.nodes, ang)}
    return nx.spring_layout(G, seed=7, iterations=200)


def _dibujar_red(ax, red):
    pos = posiciones(red)
    d = red.distancias
    dmax = red.distancia_maxima
    # Un tono por distancia, de claro (cerca) a oscuro (lejos).
    idx = np.linspace(0, len(AZULES) - 1, dmax + 1).round().astype(int)
    cmap = ListedColormap([AZULES[k] for k in idx])
    norm = BoundaryNorm(np.arange(-0.5, dmax + 1.5), cmap.N)

    nx.draw_networkx_edges(red.grafo, pos, ax=ax, edge_color=EJE, width=0.6)
    xy = np.array([pos[i] for i in range(red.N)])
    sc = ax.scatter(xy[:, 0], xy[:, 1], c=d, cmap=cmap, norm=norm, s=26,
                    edgecolors=FONDO, linewidths=0.8, zorder=3)
    f = red.fuente
    ax.scatter(*xy[f], s=110, c=ACENTO, edgecolors=FONDO, linewidths=1.2, zorder=4)
    ax.annotate("fuente", xy[f], xytext=(6, 6), textcoords="offset points",
                fontsize=_fs(8.5), color=TINTA, fontweight="bold", zorder=5,
                path_effects=[pe.withStroke(linewidth=3, foreground=FONDO)])
    ax.set_aspect("equal")
    ax.axis("off")
    return sc


def g1_redes(redes: dict, realizaciones: dict | None = None):
    """G1: las cuatro topologías (arriba) y su distribución de distancias N_d (abajo).

    redes : {nombre: Red} con la realización de referencia de cada topología.
    realizaciones : {nombre: [Red, ...]} opcional. Para las redes aleatorias se
        superpone la mediana de N_d sobre todas las realizaciones y el rango
        entre sus percentiles 10 y 90 (N_d no puede ser negativo, así que no
        se usa ± σ, y la media puede caer fuera de ese rango).
    """
    realizaciones = realizaciones or {}
    nombres = list(redes)
    fig, ejes = plt.subplots(2, len(nombres), figsize=(4.1 * len(nombres), 8.6),
                             gridspec_kw={"height_ratios": [1.25, 1]})
    hay_realizaciones = False
    for c, nombre in enumerate(nombres):
        red = redes[nombre]
        ax_r, ax_d = ejes[0, c], ejes[1, c]

        sc = _dibujar_red(ax_r, red)
        cb = fig.colorbar(sc, ax=ax_r, orientation="horizontal", fraction=0.05,
                          pad=0.02, aspect=30)
        dmax = red.distancia_maxima
        paso = 1 if dmax <= 10 else 5
        cb.set_ticks(np.arange(0, dmax + 1, paso))
        cb.set_label("distancia a la fuente, d₀ᵢ", fontsize=_fs(8.5), color=TINTA_2)
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=8, colors=TINTA_TENUE)
        enlaces = red.grafo.number_of_edges()
        ax_r.set_title(NOMBRE_RED.get(nombre, nombre), pad=8)

        Nd = red.distribucion_distancias
        d = np.arange(Nd.size)
        ax_d.bar(d, Nd, width=0.78, color=COLOR_RED.get(nombre, CATEGORICA[0]), zorder=2)
        reals = realizaciones.get(nombre)
        if reals and len(reals) > 1:
            hay_realizaciones = True
            largo = max(r.distancia_maxima for r in reals) + 1
            M = np.zeros((len(reals), largo))
            for k, r in enumerate(reals):
                nd = r.distribucion_distancias
                M[k, :nd.size] = nd
            p10, mediana, p90 = np.percentile(M, [10, 50, 90], axis=0)
            # Se omiten las distancias que casi ninguna realización alcanza.
            v = p90 > 0
            p10, mediana, p90 = p10[v], mediana[v], p90[v]
            ax_d.errorbar(np.arange(largo)[v], mediana, yerr=[mediana - p10, p90 - mediana],
                          fmt="o", ms=4.5, color=TINTA, ecolor=TINTA_2, elinewidth=1,
                          capsize=2.5, zorder=3)
        ax_d.set_xlabel("distancia a la fuente, d")
        if c == 0:
            ax_d.set_ylabel("nodos a distancia d, N_d")
        ax_d.set_xlim(-0.7, max(ax_d.get_xlim()[1], 6.7))
        ax_d.set_ylim(bottom=0)
        ax_d.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax_d.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax_d.grid(axis="x", visible=False)
        ax_d.set_title(f"d máx = {red.distancia_maxima} · {enlaces} enlaces · "
                       f"⟨k⟩ = {red.grados.mean():.2f}",
                       fontsize=_fs(9.5), fontweight="normal", color=TINTA_2)

    # Una sola leyenda para toda la figura: los colores de las barras ya
    # identifican la red por su columna.
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    marcas = [Patch(color=TINTA_TENUE, label="N_d de la realización de referencia (barras)")]
    if hay_realizaciones:
        marcas.append(Line2D([], [], marker="o", color=TINTA, ls="", ms=4.5,
                             label="redes aleatorias: mediana de 30 realizaciones, "
                                   "barra = percentiles 10–90"))
    fig.suptitle("G1. Topologías estudiadas y distribución de distancias a la fuente",
                 y=0.995)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.legend(handles=marcas, loc="lower center", ncol=len(marcas),
               bbox_to_anchor=(0.5, 0.0))
    return fig


# ---------------------------------------------------------------------------
# G2. Validación del código
# ---------------------------------------------------------------------------

def g2_validacion(balance: dict, energia: dict, referencia: dict, convergencia: dict):
    """G2: por qué confiar en el código (balance de H, solución modal, RK4).

    balance : {red: (γt, residuo)} — residuo del balance integrado de H.
    energia : {"tg", "H", "suma_E", "H_teo", "titulo"} — energías / E₀ de un caso.
    referencia : {red: (kappas, error)} — máx |Q_DOP853 − Q_modal| / Q₀.
    convergencia : {"h", "error"} — error de RK4 frente a la solución modal.
    """
    fig, ejes = plt.subplots(2, 2, figsize=(11, 7.6))
    numero = FuncFormatter(lambda v, _: f"{v:g}")

    ax = ejes[0, 0]
    ax.plot(energia["tg"], energia["H"], color=TINTA, lw=2.2, label="H(t): energía total",
            zorder=2)
    ax.plot(energia["tg"], energia["suma_E"], color=ACENTO, lw=1.0,
            label="Σᵢ Eᵢ(t): sin la energía de acoplamiento", zorder=1)
    # Encima de H, discontinua: si coinciden, se ve la línea negra «punteada».
    ax.plot(energia["tg"], energia["H_teo"], color="#c3c2b7", lw=1.2, ls=(0, (4, 4)),
            label="H(0) e^(−γt) (teoría; coincide con H)", zorder=3)
    ax.set_yscale("log")
    ax.set_xlabel("tiempo, γt")
    ax.set_ylabel("energía / E₀")
    ax.set_title(energia["titulo"], fontsize=_fs(10))
    ax.legend(loc="upper right", fontsize=_fs(8))

    ax = ejes[0, 1]
    for red, (tg, res) in balance.items():
        tb, rb = _agrupar_maximo(tg, np.abs(res)[:, None], 250)   # envolvente
        ax.plot(tb, np.maximum(rb[:, 0], 1e-14), color=COLOR_RED.get(red, TINTA), lw=1.4,
                label=NOMBRE_RED.get(red, red).split(" (")[0])
    ax.axhline(1e-6, color=TINTA_2, lw=0.9, ls="--")
    ax.text(0.2, 1.4e-6, "criterio de las pruebas: 10⁻⁶", fontsize=_fs(8), color=TINTA_2)
    ax.set_yscale("log")
    ax.set_ylim(1e-11, 1e-5)
    ax.set_xlabel("tiempo, γt")
    ax.set_ylabel("|H(t) + ∫RΣIᵢ² dt − H(0)| / H(0)")
    ax.set_title("Balance dH/dt = −RΣIᵢ² (κ = 0.1; envolvente)", fontsize=_fs(10))
    ax.legend(loc="lower right", fontsize=_fs(8), ncol=2)

    ax = ejes[1, 0]
    ax.axhline(1e-3, color=TINTA_2, lw=0.9, ls="--")
    ax.text(0.012, 1.4e-3, "criterio del plan: ≪ 10⁻³ Q₀ (amplitud del umbral)", fontsize=_fs(8),
            color=TINTA_2)
    for k, (red, (ks, err)) in enumerate(referencia.items()):
        ax.plot(ks, err, "-" + MARCADOR_SERIE[k % len(MARCADOR_SERIE)],
                color=COLOR_RED.get(red, TINTA), ms=5, lw=1.4,
                markeredgecolor=FONDO, label=NOMBRE_RED.get(red, red).split(" (")[0])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1e-11, 1e-2)
    ax.set_xlabel("acoplamiento, κ")
    ax.set_ylabel("máx |Q_DOP853 − Q_modal| / Q₀")
    ax.set_title("DOP853 frente a la solución exacta por modos", fontsize=_fs(10))
    ax.legend(loc="center right", fontsize=_fs(8))

    ax = ejes[1, 1]
    h, err = np.asarray(convergencia["h"]), np.asarray(convergencia["error"])
    ordenes = np.log2(err[:-1] / err[1:])
    ref = err[0] * (h / h[0]) ** 4
    ax.plot(h * 1e6, ref, color=TINTA_TENUE, lw=1.2, ls="--", label="pendiente 4 (referencia)")
    ax.plot(h * 1e6, err, "-o", color=CATEGORICA[0], ms=6, lw=1.8, markeredgecolor=FONDO,
            label="RK4 propio")
    for hi, ei, o in zip(h[1:], err[1:], ordenes):
        ax.annotate(f"orden {o:.2f}", (hi * 1e6, ei), xytext=(6, -10),
                    textcoords="offset points", fontsize=_fs(8), color=TINTA)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_locator(LogLocator(subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_major_formatter(numero)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("paso h (µs)")
    ax.set_ylabel("máx |Q_RK4 − Q_modal| / Q₀")
    ax.set_title(convergencia.get("titulo", "Convergencia de RK4"), fontsize=_fs(10))
    ax.legend(loc="upper left", fontsize=_fs(8))

    fig.suptitle("G2. Validación del código", y=1.0)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Utilidades para los datos de E1
# ---------------------------------------------------------------------------
#
# G3 y G4 reciben `datos`: {(red, κ): dict}, donde cada dict tiene los arreglos
# guardados por scripts/e1_dinamica.py (t, E, H, nodos_repr, distancias,
# caminos, t_llegada, ...) más "gamma" y "E0".

E_MIN_LOG = -12          # piso de la escala de energía: 10⁻¹² E₀


def _distancias_a_mostrar(dmax: int, n: int = 6) -> list[int]:
    """Hasta n distancias repartidas entre 1 y d_max (la fuente va aparte)."""
    if dmax <= n:
        return list(range(1, dmax + 1))
    return sorted(set(np.round(np.linspace(1, dmax, n)).astype(int)))


def _tono_distancia(d: int, dmax: int) -> str:
    """Azul de la rampa según la distancia: claro cerca, oscuro lejos.

    Empieza en el paso 300 para que la línea más clara siga visible sobre el
    fondo (regla de rampas ordinales).
    """
    tonos = AZULES[3:]
    k = int(round((d - 1) / max(dmax - 1, 1) * (len(tonos) - 1)))
    return tonos[k]


def _rejilla(redes_: list, kappas: list, ancho=4.0, alto=2.9, **kw):
    fig, ejes = plt.subplots(len(kappas), len(redes_), figsize=(ancho * len(redes_),
                                                               alto * len(kappas)),
                             squeeze=False, **kw)
    for c, red in enumerate(redes_):
        ejes[0, c].set_title(NOMBRE_RED.get(red, red), pad=8)
    for f, kappa in enumerate(kappas):
        ejes[f, 0].annotate(f"κ = {kappa:g}", xy=(0, 0.5), xycoords="axes fraction",
                            xytext=(-58, 0), textcoords="offset points", rotation=90,
                            ha="center", va="center", fontsize=_fs(11), fontweight="bold",
                            color=TINTA)
    return fig, ejes


# ---------------------------------------------------------------------------
# G3. Eᵢ(t) por distancia
# ---------------------------------------------------------------------------

def g3_energia_por_distancia(datos: dict, redes_: list, kappas: list,
                             umbral: float = 1e-6, n_bins: int = 400):
    """G3: Eᵢ(t)/E₀ de un nodo representativo por distancia (pregunta P1).

    Columnas = redes, filas = valores de κ. Eje y logarítmico. La fuente va en
    naranja; las demás distancias en azul, más oscuro cuanto más lejos. La
    línea punteada es H(t)/E₀ (energía total) y la discontinua, el umbral.

    Cada curva es la envolvente de Eᵢ: el máximo en n_bins intervalos de
    tiempo. Con κ grande Eᵢ oscila tan rápido que la curva completa se vuelve
    una mancha; la envolvente conserva la tendencia y los picos.
    """
    fig, ejes = _rejilla(redes_, kappas, alto=2.8, sharex=True, sharey=True)
    for c, red in enumerate(redes_):
        for f, kappa in enumerate(kappas):
            ax = ejes[f, c]
            x = datos[(red, kappa)]
            tg_completo = x["gamma"] * x["t"]
            dist = x["distancias"]
            dmax = int(dist.max())
            fuente = int(x["fuente"])
            nodos = [fuente] + [int(x["nodos_repr"][d]) for d in _distancias_a_mostrar(dmax)]
            tg, Eb = _agrupar_maximo(tg_completo, x["E"][:, nodos] / x["E0"], n_bins)
            Eb = np.maximum(Eb, 10.0**E_MIN_LOG)

            ax.plot(tg_completo, x["H"] / x["E0"], color=TINTA_TENUE, lw=1.2, ls=":",
                    label="H(t)/E₀, energía total")
            ax.axhline(umbral, color=TINTA_2, lw=0.9, ls="--",
                       label=f"umbral {umbral:.0e} E₀".replace("e-0", "e−"))
            ax.plot(tg, Eb[:, 0], color=ACENTO, lw=1.3, label="d = 0 (fuente)")
            for k, d in enumerate(_distancias_a_mostrar(dmax), start=1):
                ax.plot(tg, Eb[:, k], lw=1.1, color=_tono_distancia(d, dmax), label=f"d = {d}")
            ax.set_yscale("log")
            ax.set_ylim(10.0**E_MIN_LOG, 20)
            ax.set_xlim(0, tg_completo[-1])
            if f == len(kappas) - 1:
                ax.set_xlabel("tiempo, γt")
                ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=3,
                          fontsize=_fs(7.8), handlelength=1.6, columnspacing=1.0)
            if c == 0:
                ax.set_ylabel("Eᵢ / E₀ (envolvente)")
    fig.suptitle("G3. Energía de un nodo representativo por distancia a la fuente",
                 y=1.0)
    fig.tight_layout(rect=(0.03, 0, 1, 1))
    return fig


# ---------------------------------------------------------------------------
# G4. Mapa nodo × tiempo
# ---------------------------------------------------------------------------

MAPA_AZUL = LinearSegmentedColormap.from_list(
    "azul_secuencial", ["#f4f8fd", "#cde2fb"] + list(AZULES))


def _agrupar_maximo(t: np.ndarray, M: np.ndarray, n_bins: int):
    """Reduce el eje temporal a n_bins intervalos tomando el máximo de cada uno.

    Conserva la envolvente de Eᵢ (que oscila rápido) al dibujar miles de
    instantes en pocos cientos de píxeles.
    """
    if t.size <= n_bins:
        return t, M
    bordes = np.linspace(0, t.size, n_bins + 1).astype(int)[:-1]
    return t[bordes], np.maximum.reduceat(M, bordes, axis=0)


def g4_mapa_nodo_tiempo(datos: dict, redes_: list, kappas: list, n_bins: int = 600):
    """G4: log₁₀(Eᵢ/E₀) por nodo y tiempo, con los nodos ordenados por d (P1, P2).

    Filas del mapa = nodos, de la fuente (arriba) al más lejano (abajo); a
    igual d, primero los de más caminos más cortos. Los puntos naranjas son
    los tiempos de llegada con el umbral 10⁻⁶ E₀: dibujan el frente.
    """
    fig, ejes = _rejilla(redes_, kappas, alto=3.0, sharex=True)
    imagen = None
    for c, red in enumerate(redes_):
        for f, kappa in enumerate(kappas):
            ax = ejes[f, c]
            x = datos[(red, kappa)]
            dist, cam = x["distancias"], x["caminos"]
            orden = np.lexsort((-cam, dist))
            tg = x["gamma"] * x["t"]
            logE = np.log10(np.maximum(x["E"][:, orden] / x["E0"], 10.0**(E_MIN_LOG - 1)))
            tb, Mb = _agrupar_maximo(tg, logE, n_bins)
            N = orden.size
            imagen = ax.imshow(Mb.T, aspect="auto", cmap=MAPA_AZUL, vmin=E_MIN_LOG, vmax=0,
                               extent=(0, tg[-1], N, 0), interpolation="nearest")
            # Frente: tiempo de llegada de cada nodo (fila).
            tl = x["gamma"] * x["t_llegada"][orden]
            ok = np.isfinite(tl)
            ax.scatter(tl[ok], np.arange(N)[ok] + 0.5, s=3, color=ACENTO, lw=0, zorder=3)
            # Separadores y etiquetas de distancia.
            ds = dist[orden]
            cortes = np.flatnonzero(np.diff(ds)) + 1
            for y in cortes:
                ax.axhline(y, color=FONDO, lw=0.4, alpha=0.7)
            # Etiqueta de cada distancia en el centro de su grupo, omitiendo las
            # que quedarían encimadas (los grupos cercanos a la fuente son chicos).
            centros, etiquetas = [], []
            separacion = 0.055 * N
            for d in range(int(ds.max()) + 1):
                filas = np.flatnonzero(ds == d)
                y = filas.mean() + 0.5
                if not centros or y - centros[-1] >= separacion:
                    centros.append(y)
                    etiquetas.append(str(d))
            ax.set_yticks(centros, etiquetas)
            ax.grid(False)
            if c == 0:
                ax.set_ylabel("nodos, ordenados por d")
            if f == len(kappas) - 1:
                ax.set_xlabel("tiempo, γt")
            no_alc = int((~ok).sum())
            if no_alc:
                ax.text(0.98, 0.03, f"{no_alc} sin llegar", transform=ax.transAxes,
                        ha="right", va="bottom", fontsize=_fs(8), color=TINTA,
                        path_effects=[pe.withStroke(linewidth=3, foreground=FONDO)])
    fig.suptitle("G4. Energía de cada nodo en el tiempo, log₁₀(Eᵢ/E₀)", y=1.0)
    fig.tight_layout(rect=(0.03, 0.06, 1, 1))
    cax = fig.add_axes((0.30, 0.018, 0.40, 0.014))
    cb = fig.colorbar(imagen, cax=cax, orientation="horizontal", extend="min")
    cb.set_label("log₁₀(Eᵢ/E₀)  ·  eje y: distancia d a la fuente  ·  "
                 "puntos naranjas: llegada con umbral 10⁻⁶ E₀", color=TINTA_2)
    cb.outline.set_visible(False)
    return fig


# ---------------------------------------------------------------------------
# Utilidades para los datos de E2
# ---------------------------------------------------------------------------
#
# G5 y G6 reciben `datos`: {red: dict} con los arreglos de e2_<red>.npz
# (kappas, umbrales, t_llegada [κ, realización, umbral, nodo], distancias
# [realización, nodo], ...) más "gamma" y "omega0".

ESTILO_UMBRAL = {1e-4: "--", 1e-6: "-", 1e-8: ":"}


def _texto_umbral(u: float) -> str:
    """10⁻⁶ en vez de 1e-06: solo el exponente va en superíndice."""
    exponente = str(-int(round(np.log10(u))))
    return "10⁻" + exponente.translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))


def _mediana_por_d(tg: np.ndarray, dist: np.ndarray):
    """Mediana de γtᵢ por distancia, juntando nodos de todas las realizaciones.

    tg y dist tienen la misma forma (realizaciones, N). Se usan solo nodos
    alcanzados; se omiten las distancias donde menos de la mitad de los nodos
    llegó (la mediana no estaría definida con los no alcanzados).
    """
    ds, med = [], []
    for d in range(1, int(dist.max()) + 1):
        v = tg[dist == d]
        if v.size == 0:
            continue
        ok = np.isfinite(v)
        if ok.sum() >= 0.5 * v.size:
            ds.append(d)
            med.append(np.median(v[ok]))
    return np.array(ds), np.array(med)


# ---------------------------------------------------------------------------
# G5. Tiempo de llegada frente a la distancia
# ---------------------------------------------------------------------------

def g5_llegada_vs_distancia(datos: dict, redes_: list, kappas: list,
                            umbral: float = 1e-6):
    """G5: γtᵢ frente a d₀ᵢ, por κ (filas) y red (columnas) (P2, P3, P5).

    Puntos: cada nodo alcanzado con el umbral principal (en las redes
    aleatorias, los de las 30 realizaciones, con desplazamiento horizontal
    para que no se tapen). Línea continua: mediana por distancia con ese
    umbral; discontinua y punteada: medianas con 10⁻⁴ y 10⁻⁸. El texto indica
    los nodos que no llegan (promedio por realización).
    """
    # Cada panel con su propia escala vertical: el anillo tarda hasta 5 veces
    # más que las otras redes y con un eje compartido quedaba cortado.
    fig, ejes = _rejilla(redes_, kappas, alto=2.7, sharex="col")
    rng = np.random.default_rng(0)
    for c, red in enumerate(redes_):
        x = datos[red]
        ks, us = list(x["kappas"]), list(x["umbrales"])
        dist = x["distancias"]
        color = COLOR_RED.get(red, CATEGORICA[0])
        for f, kappa in enumerate(kappas):
            ax = ejes[f, c]
            i = ks.index(kappa)
            tl = x["t_llegada"][i]                           # [realización, umbral, nodo]
            tg = x["gamma"] * tl[:, us.index(umbral)]
            ok = np.isfinite(tg) & (dist >= 1)
            nr = tg.shape[0]
            jitter = rng.uniform(-0.18, 0.18, size=tg.shape) if nr > 1 else 0.0
            alfa = 0.6 if nr == 1 else 0.12
            ax.scatter((dist + jitter)[ok], tg[ok], s=7 if nr == 1 else 4, color=color,
                       alpha=alfa, lw=0, zorder=2)
            for u in us:
                ds, med = _mediana_por_d(x["gamma"] * tl[:, us.index(u)], dist)
                if ds.size:
                    ax.plot(ds, med, ls=ESTILO_UMBRAL.get(u, "-"), color=TINTA,
                            lw=1.6 if u == umbral else 1.0, zorder=3,
                            label=f"mediana, umbral {_texto_umbral(u)} E₀")
            no_alc = ((~np.isfinite(tg)) & (dist >= 1)).sum() / nr
            if no_alc > 0:
                ax.text(0.97, 0.95, f"{no_alc:.0f} de 99 sin llegar", transform=ax.transAxes,
                        ha="right", va="top", fontsize=_fs(8), color=TINTA,
                        path_effects=[pe.withStroke(linewidth=3, foreground=FONDO)])
            ax.set_ylim(bottom=0)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            if f == len(kappas) - 1:
                ax.set_xlabel("distancia a la fuente, d₀ᵢ")
            if c == 0:
                ax.set_ylabel("tiempo de llegada, γtᵢ")
    fig.suptitle("G5. Tiempo de llegada frente a la distancia topológica "
                 f"(puntos: nodos con umbral {_texto_umbral(umbral)} E₀; "
                 "redes aleatorias: 30 realizaciones)", y=1.0, fontsize=_fs(12))
    fig.tight_layout(rect=(0.03, 0.03, 1, 1))
    manejos, etiquetas = ejes[-1, 0].get_legend_handles_labels()
    fig.legend(manejos, etiquetas, loc="lower center", ncol=len(etiquetas),
               bbox_to_anchor=(0.5, 0.0), handlelength=2.6)
    return fig


# ---------------------------------------------------------------------------
# G6. Rapidez del frente frente a κ
# ---------------------------------------------------------------------------

def rapideces(x: dict) -> np.ndarray:
    """v/ω₀ de cada (κ, realización, umbral) a partir de los datos de E2."""
    tl, dist = x["t_llegada"], x["distancias"]
    nk, nr, nu, _ = tl.shape
    v = np.full((nk, nr, nu), np.nan)
    for i in range(nk):
        for j in range(nr):
            for u in range(nu):
                v[i, j, u] = _analisis.rapidez_frente(tl[i, j, u], dist[j])[0] / x["omega0"]
    return v


def g6_rapidez_vs_kappa(datos: dict, redes_: list):
    """G6: rapidez del frente v/ω₀ frente a κ, log–log, un panel por umbral (P2, P7).

    Línea: mediana entre realizaciones; franja: percentiles 10–90 (redes
    aleatorias). Referencias grises: límites de la teoría para la cadena,
    v = K/ω₀ (acoplamiento débil, pendiente 1) y v = √K (fuerte, pendiente 1/2).
    """
    primero = datos[redes_[0]]
    us = list(primero["umbrales"])
    fig, ejes = plt.subplots(1, len(us), figsize=(5.0 * len(us), 4.8), sharey=True,
                             squeeze=False)
    ejes = ejes[0]                      # también funciona con un solo umbral
    kref = np.geomspace(0.006, 16, 100)
    for a, u in enumerate(us):
        ax = ejes[a]
        ax.plot(kref, kref, color=TINTA_TENUE, lw=1.0, ls="--", zorder=1,
                label="cadena, acoplamiento débil: v = K/ω₀ (pendiente 1)")
        ax.plot(kref, np.sqrt(kref), color=TINTA_TENUE, lw=1.0, ls=":", zorder=1,
                label="cadena, acoplamiento fuerte: v = √K (pendiente ½)")
        finales = []
        for red in redes_:
            x = datos[red]
            ks = np.array(x["kappas"], float)
            v = x["_rapidez"][:, :, a]                       # [κ, realización]
            color = COLOR_RED.get(red, CATEGORICA[0])
            med = np.nanmedian(v, axis=1)
            if v.shape[1] > 1:
                p10, p90 = np.nanpercentile(v, [10, 90], axis=1)
                ax.fill_between(ks, p10, p90, color=color, alpha=0.18, lw=0, zorder=2)
            ax.plot(ks, med, "-o", color=color, ms=5, lw=2, zorder=3,
                    markeredgecolor=FONDO, markeredgewidth=1.0,
                    label=NOMBRE_RED.get(red, red))
            finales.append([np.log10(med[-1]), NOMBRE_RED.get(red, red).split(" (")[0],
                            ks[-1], med[-1]])
        # Etiquetas directas al final de cada línea, separadas al menos 0.12
        # décadas para que no se encimen.
        finales.sort(key=lambda e: e[0])
        for k in range(1, len(finales)):
            finales[k][0] = max(finales[k][0], finales[k - 1][0] + 0.12)
        for y_log, texto, xk, yk in finales:
            ax.annotate(texto, (xk, yk), xytext=(xk * 1.35, 10**y_log), va="center",
                        fontsize=plt.rcParams["legend.fontsize"], color=TINTA,
                        textcoords="data")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(0.006, 60)
        ax.set_xlabel("acoplamiento, κ = K/ω₀²")
        ax.set_title(f"umbral {_texto_umbral(u)} E₀", fontsize=_fs(10.5))
        ax.grid(True, which="major")
    ejes[0].set_ylabel("rapidez del frente, v/ω₀")
    fig.suptitle("G6. Rapidez del frente frente al acoplamiento "
                 "(mediana; franja: percentiles 10–90 de 30 realizaciones)", y=1.0, fontsize=_fs(12))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    manejos, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manejos, etiquetas, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0),
               fontsize=_fs(8.5))
    return fig


# ---------------------------------------------------------------------------
# Utilidades para los datos de E3
# ---------------------------------------------------------------------------
#
# G7 y G8 reciben `datos`: {red: dict} con los arreglos de e3_<red>.npz
# (kappas, d, N_d [realización, d], media y sigma [κ, realización, d],
# E_rel [κ, realización, nodo], distancias [realización, nodo]). Las energías
# ya vienen divididas por E₀.

E_PISO_G7 = 1e-10
E_MIN_G8 = 1e-12      # Ē(d) mínima para que σ_E(d) sea interpretable


def _resumen_realizaciones(M: np.ndarray, N_d: np.ndarray, minimo: int = 1):
    """Mediana y percentiles 10–90 entre realizaciones de un arreglo [real, d].

    Solo para las distancias que existen en al menos la mitad de las
    realizaciones y tienen al menos `minimo` nodos (2 para σ).
    """
    import warnings
    con_d = N_d >= minimo
    usar = con_d.sum(axis=0) >= 0.5 * N_d.shape[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        Mv = np.where(con_d, M, np.nan)
        med = np.nanmedian(Mv, axis=0)
        p10, p90 = np.nanpercentile(Mv, [10, 90], axis=0)
    d = np.arange(M.shape[1])
    usar &= np.isfinite(med)
    return d[usar], med[usar], p10[usar], p90[usar]


def _tono_kappa(k: int, n: int) -> str:
    """Azul ordinal para el k-ésimo valor de κ de n: claro = κ pequeño."""
    tonos = AZULES[3:]
    return tonos[int(round(k / max(n - 1, 1) * (len(tonos) - 1)))]


# ---------------------------------------------------------------------------
# G7. Energía media por distancia
# ---------------------------------------------------------------------------

def g7_energia_media_vs_distancia(datos: dict, redes_: list, kappas: list):
    """G7: Ē(d)/E₀ con σ_E(d), por κ (filas) y red (columnas) (P2, P4).

    Puntos: ⟨Eᵢ⟩/E₀ de cada nodo (en redes aleatorias, de las 30
    realizaciones). Línea negra: Ē(d) (mediana entre realizaciones). Barras:
    Ē ± σ_E(d), la dispersión entre nodos de una misma red; si Ē − σ ≤ 0 la
    barra llega al borde inferior. Franja de color: percentiles 10–90 de Ē(d)
    entre realizaciones. Los paneles de una misma fila (mismo κ) comparten el
    eje y, para comparar redes; cada fila se ajusta a sus datos. Los valores
    menores que el borde inferior se dibujan sobre él.
    """
    fig, ejes = _rejilla(redes_, kappas, alto=2.7, sharex="col", sharey="row")
    rng = np.random.default_rng(1)
    # Borde inferior de cada fila: una década por debajo del menor Ē(d) de la
    # fila, para que todas las curvas Ē(d) se vean completas.
    pisos = []
    for kappa in kappas:
        minimos = []
        for r in redes_:
            i = [float(k) for k in datos[r]["kappas"]].index(kappa)
            _, med, _, _ = _resumen_realizaciones(datos[r]["media"][i], datos[r]["N_d"])
            if (med > 0).any():
                minimos.append(med[med > 0].min())
        pisos.append(max(E_PISO_G7, 10 ** (np.floor(np.log10(min(minimos))) - 1)))
    for c, red in enumerate(redes_):
        x = datos[red]
        ks = [float(k) for k in x["kappas"]]
        dist, N_d = x["distancias"], x["N_d"]
        nr = dist.shape[0]
        color = COLOR_RED.get(red, CATEGORICA[0])
        for f, kappa in enumerate(kappas):
            ax = ejes[f, c]
            i = ks.index(kappa)
            piso = pisos[f]
            E = np.maximum(x["E_rel"][i], piso)
            jitter = rng.uniform(-0.18, 0.18, size=E.shape) if nr > 1 else 0.0
            ax.scatter(dist + jitter, E, s=7 if nr == 1 else 4, color=color,
                       alpha=0.6 if nr == 1 else 0.12, lw=0, zorder=2)
            d, med, p10, p90 = _resumen_realizaciones(x["media"][i], N_d)
            if nr > 1:
                ax.fill_between(d, p10, p90, color=color, alpha=0.25, lw=0, zorder=1)
            ds, sig, _, _ = _resumen_realizaciones(x["sigma"][i], N_d, minimo=2)
            m_s = np.interp(ds, d, med)
            visible = m_s > piso           # sin barras donde Ē cae bajo el borde
            ax.vlines(ds[visible], np.maximum(m_s - sig, piso)[visible],
                      (m_s + sig)[visible], color=TINTA, lw=1.0, zorder=3)
            ax.plot(d, med, "-o", color=TINTA, ms=3.5, lw=1.5, zorder=4)
            ax.set_yscale("log")
            ax.set_ylim(piso * 0.6, 0.5)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            if f == len(kappas) - 1:
                ax.set_xlabel("distancia a la fuente, d")
            if c == 0:
                ax.set_ylabel("⟨Eᵢ⟩/E₀ y Ē(d)/E₀")
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    marcas = [Line2D([], [], color=TINTA, marker="o", ms=3.5, lw=1.5,
                     label="Ē(d)/E₀ (mediana entre realizaciones)"),
              Line2D([], [], color=TINTA, lw=1.0, marker="|", ms=8, ls="",
                     label="Ē ± σ_E(d): dispersión entre nodos"),
              Patch(color=TINTA_TENUE, alpha=0.35,
                    label="percentiles 10–90 de Ē(d) entre las 30 realizaciones"),
              Line2D([], [], color=TINTA_TENUE, marker="o", ls="", ms=4, alpha=0.6,
                     label="⟨Eᵢ⟩/E₀ de cada nodo")]
    fig.suptitle("G7. Energía media por distancia a la fuente (promedio temporal en "
                 "T = 10/γ)", y=1.0)
    fig.tight_layout(rect=(0.03, 0.035, 1, 1))
    fig.legend(handles=marcas, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.0))
    return fig


# ---------------------------------------------------------------------------
# G8. Heterogeneidad por distancia
# ---------------------------------------------------------------------------

def g8_heterogeneidad(datos: dict, redes_: list, kappas: list):
    """G8: σ_E(d)/E₀ (arriba) y σ_E/Ē (abajo) frente a d, una línea por κ (P8).

    σ_E(d) mide las diferencias entre nodos a la misma distancia; σ_E/Ē es su
    versión relativa. Solo se dibujan las distancias con al menos 2 nodos (σ
    no está definida con N_d = 1) y con Ē(d) > 10⁻¹² E₀: energías menores
    están muy por debajo de todos los umbrales y se acercan a la precisión del
    integrador (atol = 10⁻¹² Q₀ equivale a ~10⁻²⁴ E₀), así que su dispersión
    no es interpretable. En redes aleatorias, cada punto es la mediana entre
    realizaciones.
    """
    fig, ejes = plt.subplots(2, len(redes_), figsize=(4.0 * len(redes_), 6.4),
                             sharex="col", squeeze=False)
    for c, red in enumerate(redes_):
        x = datos[red]
        ks = [float(k) for k in x["kappas"]]
        N_d = x["N_d"]
        ejes[0, c].set_title(NOMBRE_RED.get(red, red), pad=8)
        for n, kappa in enumerate(kappas):
            i = ks.index(kappa)
            tono = _tono_kappa(n, len(kappas))
            significativa = x["media"][i] > E_MIN_G8
            sig_M = np.where(significativa, x["sigma"][i], np.nan)
            d, sig, _, _ = _resumen_realizaciones(sig_M, N_d, minimo=2)
            with np.errstate(invalid="ignore", divide="ignore"):
                rel_M = np.where(significativa, x["sigma"][i] / x["media"][i], np.nan)
            dr, rel, _, _ = _resumen_realizaciones(rel_M, N_d, minimo=2)
            ejes[0, c].plot(d, sig, "-o", color=tono, ms=3.5, lw=1.6, label=f"κ = {kappa:g}")
            ejes[1, c].plot(dr, rel, "-o", color=tono, ms=3.5, lw=1.6, label=f"κ = {kappa:g}")
        ejes[0, c].set_yscale("log")
        ejes[1, c].set_ylim(bottom=0)
        ejes[1, c].set_xlabel("distancia a la fuente, d")
        ejes[1, c].xaxis.set_major_locator(MaxNLocator(integer=True))
    ejes[0, 0].set_ylabel("σ_E(d)/E₀ (absoluta)")
    ejes[1, 0].set_ylabel("σ_E(d)/Ē(d) (relativa)")
    fig.suptitle("G8. Heterogeneidad energética entre nodos a la misma distancia "
                 "(distancias con Ē > 10⁻¹² E₀ y al menos 2 nodos)", y=1.0)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    manejos, etiquetas = ejes[0, 0].get_legend_handles_labels()
    fig.legend(manejos, etiquetas, loc="lower center", ncol=len(kappas),
               bbox_to_anchor=(0.5, 0.0))
    return fig


# ---------------------------------------------------------------------------
# G9. Nodos a igual distancia
# ---------------------------------------------------------------------------
#
# G9 recibe `datos`: {red: dict} con los arreglos de e4_<red>.npz (kappas,
# t_gamma y E_rel [κ, realización, nodo], distancias, caminos, grados y
# peso_modal [realización, nodo]).

def _relativo_al_grupo(V: np.ndarray, dist: np.ndarray) -> np.ndarray:
    """V dividido por la media geométrica de su grupo (realización, d).

    Quita el efecto de la distancia para poder juntar todas las d en un panel.
    Es la misma normalización que usa la regresión de E4 (restar la media de
    los logaritmos). Valores no positivos o no finitos quedan en NaN.
    """
    R = np.full(V.shape, np.nan)
    for r in range(V.shape[0]):
        for d in np.unique(dist[r]):
            if d < 1:
                continue
            g = (dist[r] == d) & np.isfinite(V[r]) & (V[r] > 0)
            if g.sum() >= 2:
                R[r, g] = V[r, g] / np.exp(np.log(V[r, g]).mean())
    return R


def g9_posicion(datos: dict, redes_: list, paneles: list | None = None):
    """G9: a igual distancia, ¿qué explica la respuesta de cada nodo? (P5, P6, P8)

    Cada fila es un par (respuesta, predictor, κ). Las respuestas se dividen
    por la media geométrica de su grupo (misma realización y distancia), así
    que 1 = «como el promedio de su distancia». Los puntos son nodos (de las
    30 realizaciones en redes aleatorias); la línea negra es la mediana por
    valor del predictor. Cada panel indica ρ (Spearman dentro de grupos,
    mediana) y R² (variación a igual d explicada), de
    `analisis.relacion_a_igual_distancia`.
    """
    if paneles is None:
        paneles = [("t_gamma", "caminos", 0.1, "γtᵢ relativo a su distancia",
                    "caminos más cortos Nᵢ, relativo a su distancia"),
                   ("E_rel", "caminos", 0.01, "⟨Eᵢ⟩ relativa a su distancia",
                    "caminos más cortos Nᵢ, relativo a su distancia"),
                   ("E_rel", "grados", 1.0, "⟨Eᵢ⟩ relativa a su distancia",
                    "grado kᵢ, relativo a su distancia"),
                   ("E_rel", "peso_modal", 1.0, "⟨Eᵢ⟩ relativa a su distancia",
                    "peso modal Wᵢ, relativo a su distancia")]
    numero = FuncFormatter(lambda v, _: f"{v:g}")
    fig, ejes = plt.subplots(len(paneles), len(redes_),
                             figsize=(4.0 * len(redes_), 3.0 * len(paneles)), squeeze=False)
    rng = np.random.default_rng(2)
    for c, red in enumerate(redes_):
        x = datos[red]
        ks = [float(k) for k in x["kappas"]]
        dist = x["distancias"]
        color = COLOR_RED.get(red, CATEGORICA[0])
        ejes[0, c].set_title(NOMBRE_RED.get(red, red), pad=8)
        for f, (resp, pred, kappa, ylab, xlab) in enumerate(paneles):
            ax = ejes[f, c]
            Y = x[resp][ks.index(kappa)]
            X = x[pred].astype(float)
            stats = _analisis.relacion_a_igual_distancia(Y, X, dist)
            # Respuesta y predictor relativos a su grupo (misma realización y
            # distancia): así se juntan todas las d sin mezclar escalas.
            Yr = _relativo_al_grupo(Y, dist)
            Xp = _relativo_al_grupo(X, dist)
            ok = np.isfinite(Yr) & np.isfinite(Xp) & (dist >= 1)
            if np.unique(np.round(Xp[ok], 9)).size <= 1:
                # Predictor igual en todos los nodos de cada grupo (grado en el
                # anillo): no hay nada que comparar.
                ax.text(0.5, 0.5, f"{xlab.split(',')[0]} igual en todos los nodos\n"
                                  "de cada distancia: no explica diferencias",
                        transform=ax.transAxes, ha="center", va="center", fontsize=_fs(8.5),
                        color=TINTA_2)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.grid(False)
                ax.set_xlabel(xlab, fontsize=_fs(8.5))
                ax.text(0.03, 0.96, f"κ = {kappa:g}", transform=ax.transAxes, ha="left",
                        va="top", fontsize=_fs(8), color=TINTA)
                continue
            discreto = pred != "peso_modal"
            xj = Xp * np.exp(rng.uniform(-0.03, 0.03, Xp.shape)) if discreto else Xp
            nr = dist.shape[0]
            ax.scatter(xj[ok], Yr[ok], s=7 if nr == 1 else 4, color=color,
                       alpha=0.6 if nr == 1 else 0.15, lw=0, zorder=2)
            # Tendencia: mediana por intervalo logarítmico del predictor.
            if ok.sum() >= 3 and Xp[ok].max() > Xp[ok].min() * 1.001:
                bordes = np.geomspace(Xp[ok].min(), Xp[ok].max() * 1.0001, 9)
                vals, med = [], []
                for a, b in zip(bordes[:-1], bordes[1:]):
                    s = ok & (Xp >= a) & (Xp < b)
                    if s.sum() >= 3:
                        vals.append(np.median(Xp[s]))
                        med.append(np.median(Yr[s]))
                if len(vals) > 1:
                    ax.plot(vals, med, "-o", color=TINTA, ms=3.5, lw=1.5, zorder=3)
            ax.axhline(1, color=TINTA_TENUE, lw=0.8, ls="--", zorder=1)
            ax.set_xscale("log")
            ax.set_yscale("log")
            for eje in (ax.xaxis, ax.yaxis):
                eje.set_major_locator(LogLocator(subs=(1.0, 2.0, 5.0)))
                eje.set_major_formatter(numero)
                eje.set_minor_formatter(NullFormatter())
            texto = (f"ρ = {stats['rho_mediana']:+.2f}   R² = {stats['R2']:.2f}"
                     if np.isfinite(stats["R2"]) else "sin variación a igual d")
            ax.text(0.03, 0.96, f"κ = {kappa:g}\n{texto}", transform=ax.transAxes,
                    ha="left", va="top", fontsize=_fs(8), color=TINTA,
                    path_effects=[pe.withStroke(linewidth=3, foreground=FONDO)])
            ax.set_xlabel(xlab, fontsize=_fs(8.5))
            if c == 0:
                ax.set_ylabel(ylab, fontsize=_fs(8.5))
    fig.suptitle("G9. Nodos a la misma distancia: qué explica sus diferencias "
                 "(1 = promedio de su distancia; línea: mediana)", y=1.0)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figuras de ajuste (Fase 4): datos, modelos y residuos
# ---------------------------------------------------------------------------

# Estilos de línea para los modelos de una figura, en orden: los colores
# quedan para las redes. El primero es el que la teoría o el AICc favorecen.
ESTILOS_MODELOS = (("-", TINTA), ("--", TINTA_2), (":", TINTA_2))


def figura_ajustes(bloques: list, titulos_columnas: list, titulo: str,
                   ylabel_datos: list, ylabel_residuos: str, xlabel: str,
                   xlog: bool = False, orden_modelos: list | None = None):
    """Figura de ajustes: por cada bloque, una fila de datos y otra de residuos.

    orden_modelos : nombres de los modelos en el orden de ESTILOS_MODELOS
        (continuo, discontinuo, punteado). Así cada modelo tiene un estilo
        único dentro de la figura.

    bloques : lista (una por fila de datos) de listas (una por columna) de
        dicts con:
            "x", "y"        datos (cada nodo o realización), en el espacio del ajuste
            "color"         color de la red
            "curvas"        {modelo: (x_curva, y_curva)}
            "residuos"      {modelo: (x, mediana del residuo por x)}
            "texto"         resumen del AICc (opcional)
            "etiqueta"      p. ej. «κ = 0.1» (opcional)
    """
    if orden_modelos is None:
        orden_modelos = list(dict.fromkeys(m for bl in bloques for p in bl for m in p["curvas"]))
    estilo = {m: ESTILOS_MODELOS[k % len(ESTILOS_MODELOS)] for k, m in enumerate(orden_modelos)}
    nfil = 2 * len(bloques)
    ncol = len(titulos_columnas)
    alturas = [1.0, 0.55] * len(bloques)
    fig, ejes = plt.subplots(nfil, ncol, figsize=(4.1 * ncol, 2.2 * sum(alturas) + 0.8),
                             gridspec_kw={"height_ratios": alturas}, squeeze=False,
                             sharex="col")
    rng = np.random.default_rng(5)
    for b, bloque in enumerate(bloques):
        for c, panel in enumerate(bloque):
            ax, axr = ejes[2 * b, c], ejes[2 * b + 1, c]
            if b == 0:
                ax.set_title(titulos_columnas[c], pad=8)
            x, y = np.asarray(panel["x"], float), np.asarray(panel["y"], float)
            ok = np.isfinite(x) & np.isfinite(y)
            n = ok.sum()
            jit = 0.0 if xlog else rng.uniform(-0.15, 0.15, x.shape)
            ax.scatter((x + jit)[ok], y[ok], s=5 if n > 200 else 9, color=panel["color"],
                       alpha=0.15 if n > 200 else 0.55, lw=0, zorder=1)
            for nombre in [m for m in orden_modelos if m in panel["curvas"]]:
                xc, yc = panel["curvas"][nombre]
                ls, col = estilo[nombre]
                ax.plot(xc, yc, ls=ls, color=col, lw=1.6, zorder=3, label=nombre)
                xr, rr = panel["residuos"][nombre]
                axr.plot(xr, rr, ls=ls, color=col, lw=1.4, marker="o", ms=3, zorder=3)
            axr.axhline(0, color=TINTA_TENUE, lw=0.8, zorder=1)
            if "texto" in panel:
                ax.text(0.03, 0.04 if panel.get("texto_abajo") else 0.96, panel["texto"],
                        transform=ax.transAxes, ha="left",
                        va="bottom" if panel.get("texto_abajo") else "top", fontsize=_fs(7.8),
                        color=TINTA, path_effects=[pe.withStroke(linewidth=3, foreground=FONDO)])
            if xlog:
                ax.set_xscale("log")
            if c == 0:
                etiqueta = panel.get("etiqueta", "")
                ax.set_ylabel(f"{ylabel_datos[b]}" + (f"\n{etiqueta}" if etiqueta else ""))
                axr.set_ylabel(ylabel_residuos, fontsize=_fs(8.5))
            if b == len(bloques) - 1:
                axr.set_xlabel(xlabel)
            if not xlog:
                axr.xaxis.set_major_locator(MaxNLocator(integer=True))
    from matplotlib.lines import Line2D
    marcas = [Line2D([], [], ls=estilo[m][0], color=estilo[m][1], lw=1.6,
                     label=f"modelo: {m}") for m in orden_modelos]
    fig.suptitle(titulo, y=1.0)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.legend(handles=marcas, loc="lower center", ncol=len(marcas),
               bbox_to_anchor=(0.5, 0.0))
    return fig


# ---------------------------------------------------------------------------
# G10. Comparación de topologías
# ---------------------------------------------------------------------------

MARCADOR_SERIE = ("o", "D", "s", "^")


def g10_topologias(metricas: list, redes_: list, columnas: int = 3):
    """G10: una métrica por panel, las cuatro redes lado a lado (P6).

    metricas : lista de dicts con
        "titulo", "ylabel", "log" (bool) y
        "valores": {red: {serie: arreglo de valores por realización}}.
        Cada serie (p. ej. «κ = 0.1») se dibuja con su propio marcador; las
        redes llevan su color fijo. Punto: mediana; barra: percentiles 10–90
        entre realizaciones (solo si hay más de una).
    """
    filas = int(np.ceil(len(metricas) / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(4.6 * columnas, 3.6 * filas),
                             squeeze=False)
    corto = {"malla": "Malla", "anillo": "Anillo", "mundo_pequeno": "Mundo\npequeño",
             "erdos_renyi": "ER"}
    numero = FuncFormatter(lambda v, _: f"{v:g}")
    series_vistas = {}       # solo las series de paneles con más de una (van a la leyenda)
    for m, met in enumerate(metricas):
        ax = ejes.flat[m]
        series = list(next(iter(met["valores"].values())).keys())
        n_s = len(series)
        for c, red in enumerate(redes_):
            color = COLOR_RED.get(red, CATEGORICA[0])
            for s, serie in enumerate(series):
                v = np.asarray(met["valores"][red][serie], float)
                v = v[np.isfinite(v)]
                if v.size == 0:
                    continue
                x = c + (s - (n_s - 1) / 2) * 0.22
                med = np.median(v)
                if v.size > 1:
                    p10, p90 = np.percentile(v, [10, 90])
                    ax.vlines(x, p10, p90, color=color, lw=1.6, zorder=2)
                ax.plot(x, med, MARCADOR_SERIE[s % len(MARCADOR_SERIE)], color=color, ms=7,
                        markeredgecolor=FONDO, markeredgewidth=1.0, zorder=3)
                if n_s > 1:
                    series_vistas[serie] = MARCADOR_SERIE[s % len(MARCADOR_SERIE)]
        ax.set_xticks(range(len(redes_)), [corto.get(r, r) for r in redes_], fontsize=_fs(8.5))
        ax.set_xlim(-0.6, len(redes_) - 0.4)
        ax.grid(axis="x", visible=False)
        if met.get("log"):
            ax.set_yscale("log")
            ax.yaxis.set_major_locator(LogLocator(subs=(1.0, 2.0, 5.0)))
            ax.yaxis.set_major_formatter(numero)
            ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_title(met["titulo"], fontsize=_fs(10))
        ax.set_ylabel(met["ylabel"], fontsize=_fs(8.5))
    for k in range(len(metricas), filas * columnas):
        ejes.flat[k].axis("off")
    from matplotlib.lines import Line2D
    marcas = [Line2D([], [], marker=mk, ls="", color=TINTA_2, ms=7, label=s)
              for s, mk in series_vistas.items()]
    marcas.append(Line2D([], [], color=TINTA_2, lw=1.6,
                         label="barra: percentiles 10–90 de 30 realizaciones"))
    fig.suptitle("G10. Comparación de topologías (mediana por red; color = red)", y=1.0)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.legend(handles=marcas, loc="lower center", ncol=len(marcas), bbox_to_anchor=(0.5, 0.0))
    return fig
