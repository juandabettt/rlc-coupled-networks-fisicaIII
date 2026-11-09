"""Videos de la propagación de energía en la red (objetivo O11 del PDF).

Cada video muestra varias redes (o varios κ) lado a lado. Cada nodo se
colorea según log₁₀(Eᵢ/E₀), con la misma escala azul de G4: claro = casi sin
energía, oscuro = mucha energía. La fuente lleva un anillo naranja.

Dos decisiones de diseño:

- Tiempo no lineal. Con κ grande el frente cruza la red en γt < 0.2 (un 2 %
  de la simulación); a velocidad constante pasaría en un instante. Los
  cuadros se reparten como t = T·(k/n)³: el video va lento al principio y
  rápido al final. El valor de γt se muestra siempre.
- Envolvente. Eᵢ oscila a 2ω y, mostrada tal cual, haría parpadear los
  nodos. Cada cuadro muestra el máximo de Eᵢ desde el cuadro anterior (el
  mismo criterio de G3 y G4).

Los videos se guardan en resultados/videos/ (.mp4, no se versionan). Para el
informe en PDF, `cuadro` genera imágenes fijas de instantes elegidos.
"""

from __future__ import annotations

import matplotlib
import numpy as np

from . import graficos as _g
from .resultados import VIDEOS

matplotlib.use("Agg")

import imageio_ffmpeg
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FFMpegWriter
from matplotlib.colors import Normalize

plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

LOG_MIN, LOG_MAX = _g.E_MIN_LOG, 0.0
NORMA = Normalize(vmin=LOG_MIN, vmax=LOG_MAX, clip=True)


# ---------------------------------------------------------------------------
# Tiempo de los cuadros y energía por cuadro
# ---------------------------------------------------------------------------

def tiempos_cuadros(T: float, n: int, potencia: float = 3.0) -> np.ndarray:
    """Instantes de los n cuadros: t_k = T·(k/(n−1))^potencia."""
    return T * np.linspace(0.0, 1.0, n) ** potencia


def energia_por_cuadro(t: np.ndarray, E: np.ndarray, t_cuadros: np.ndarray) -> np.ndarray:
    """Máximo de Eᵢ entre cada cuadro y el anterior (envolvente), forma (n, N).

    El primer cuadro usa el estado inicial. Si entre dos cuadros no cae
    ninguna muestra, se usa la muestra más cercana.
    """
    idx = np.searchsorted(t, t_cuadros, side="right")
    salida = np.empty((t_cuadros.size, E.shape[1]))
    salida[0] = E[0]
    for k in range(1, t_cuadros.size):
        a, b = idx[k - 1], idx[k]
        salida[k] = E[a:b].max(axis=0) if b > a else E[min(b, t.size - 1)]
    return salida


def log_relativa(E: np.ndarray, E0: float) -> np.ndarray:
    """log₁₀(E/E₀), con piso en LOG_MIN − 1 para evitar log(0)."""
    return np.log10(np.maximum(E / E0, 10.0 ** (LOG_MIN - 1)))


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------

def _preparar_panel(ax, panel: dict):
    """Dibuja enlaces, nodos y título de un panel; devuelve el objeto de nodos."""
    red = panel["red"]
    pos = _g.posiciones(red)
    xy = np.array([pos[i] for i in range(red.N)])
    nx.draw_networkx_edges(red.grafo, pos, ax=ax, edge_color=_g.EJE, width=0.5, alpha=0.8)
    tam = panel.get("tam_nodo", 120 if red.N <= 100 else 40)
    nodos = ax.scatter(xy[:, 0], xy[:, 1], c=np.full(red.N, LOG_MIN), cmap=_g.MAPA_AZUL,
                       norm=NORMA, s=tam, edgecolors=_g.FONDO, linewidths=0.6, zorder=3)
    f = red.fuente
    ax.scatter(*xy[f], s=tam * 2.6, facecolors="none", edgecolors=_g.ACENTO, linewidths=2.2,
               zorder=4)
    ax.set_title(panel["titulo"], fontsize=17, fontweight="bold", color=_g.TINTA, pad=12)
    ax.set_aspect("equal")
    ax.axis("off")
    return nodos


def _figura(paneles: list, titulo: str, ancho_px: int = 1920, alto_px: int = 1080):
    n = len(paneles)
    fig = plt.figure(figsize=(ancho_px / 100, alto_px / 100), dpi=100)
    fig.patch.set_facecolor(_g.FONDO)
    margen_inf = 0.14
    ancho = 0.96 / n
    ejes = [fig.add_axes((0.02 + k * ancho, margen_inf, ancho * 0.95, 0.76)) for k in range(n)]
    nodos = [_preparar_panel(ax, p) for ax, p in zip(ejes, paneles)]
    fig.suptitle(titulo, fontsize=22, fontweight="bold", color=_g.TINTA, y=0.975)
    cax = fig.add_axes((0.30, 0.065, 0.40, 0.022))
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORMA, cmap=_g.MAPA_AZUL), cax=cax,
                      orientation="horizontal", extend="min")
    cb.set_label("log₁₀(Eᵢ/E₀)   ·   anillo naranja: fuente", fontsize=13, color=_g.TINTA_2)
    cb.ax.tick_params(labelsize=12, colors=_g.TINTA_2)
    cb.outline.set_visible(False)
    reloj = fig.text(0.95, 0.07, "", ha="right", va="center", fontsize=24,
                     fontweight="bold", color=_g.TINTA, family="monospace")
    return fig, nodos, reloj


def _texto_reloj(gamma: float, t: float) -> str:
    return f"γt = {gamma * t:5.2f}"


def video(paneles: list, nombre: str, titulo: str, fps: int = 30,
          duracion_s: float = 20.0, potencia: float = 3.0, dpi: int = 100) -> str:
    """Genera un video .mp4 con los paneles lado a lado.

    paneles : lista de dicts con "red" (Red), "t", "E" (n_t, N), "E0", "gamma",
        "titulo". Todos deben tener la misma duración T.
    Devuelve la ruta del archivo.
    """
    VIDEOS.mkdir(parents=True, exist_ok=True)
    T = min(p["t"][-1] for p in paneles)
    n = int(round(fps * duracion_s))
    tc = tiempos_cuadros(T, n, potencia)
    valores = [log_relativa(energia_por_cuadro(p["t"], p["E"], tc), p["E0"]) for p in paneles]
    fig, nodos, reloj = _figura(paneles, titulo)
    ruta = VIDEOS / f"{nombre}.mp4"
    escritor = FFMpegWriter(fps=fps, codec="libx264", bitrate=4000,
                            extra_args=["-pix_fmt", "yuv420p"])
    with escritor.saving(fig, str(ruta), dpi=dpi):
        for k in range(n):
            for sc, v in zip(nodos, valores):
                sc.set_array(v[k])
            reloj.set_text(_texto_reloj(paneles[0]["gamma"], tc[k]))
            escritor.grab_frame()
    plt.close(fig)
    return str(ruta)


def cuadro(paneles: list, nombre: str, titulo: str, tiempos_gamma: list,
           ventana_s: float = 2e-4) -> list:
    """Imágenes fijas (PNG y PDF) de los paneles en los instantes γt pedidos.

    Sirven para el informe en PDF y como respaldo en la presentación. Cada
    imagen muestra la envolvente de Eᵢ en una ventana corta antes del instante
    (por defecto 200 µs ≈ un período de oscilación).
    """
    rutas = []
    gamma = paneles[0]["gamma"]
    for tg in tiempos_gamma:
        t1 = tg / gamma
        tc = np.array([max(0.0, t1 - ventana_s), t1])
        fig, nodos, reloj = _figura(paneles, titulo)
        for sc, p in zip(nodos, paneles):
            sc.set_array(log_relativa(energia_por_cuadro(p["t"], p["E"], tc), p["E0"])[1])
        reloj.set_text(_texto_reloj(gamma, t1))
        rutas += _g.guardar(fig, f"{nombre}_gt{tg:g}".replace(".", "p"), formatos=("png",),
                            dpi=100)
    return rutas
