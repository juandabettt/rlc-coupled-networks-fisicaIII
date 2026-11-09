"""Fase 5: figuras para proyectar (una idea por diapositiva, letra grande).

Las figuras G1 a G10 son rejillas densas, adecuadas para el informe. Para la
presentación se generan versiones con menos paneles y letra más grande,
reutilizando las mismas funciones de graficos.py con subconjuntos de datos:

    p1_validacion           G2 completa (por qué confiar en el código)
    p2_llegada_k0p1         tγ frente a d, 4 redes, κ = 0.1            (P1, P3)
    p3_rapidez              v/ω₀ frente a κ, umbral 10⁻⁶                (P2, P7)
    p4_energia_distancia    Ē(d) con κ = 0.01 y κ = 1                   (P4)
    p5_igual_distancia      γt frente a Nᵢ (κ = 0.1); ⟨Eᵢ⟩ frente a Wᵢ (κ = 1)  (P5)
    p6_topologias           4 métricas por red                         (P6)

Salidas: resultados/figuras/presentacion/*.png (200 dpi) y *.pdf

Requiere los datos de la Fase 3 y g10_metricas.csv (scripts/g10_topologias.py).

Uso, desde la raíz del proyecto:
    python scripts/f5_figuras_presentacion.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from red_rlc import graficos, redes, resultados

REDES = list(redes.TOPOLOGIAS)

# Letra más grande para proyectar; el resto del estilo es el de graficos.py.
PRESENTACION = {
    "font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12.5, "ytick.labelsize": 12.5, "legend.fontsize": 12.5,
    "figure.titlesize": 19, "lines.linewidth": 2.4,
}


def cargar(prefijo: str, con_meta: bool = False) -> dict:
    datos = {}
    for r in REDES:
        meta, x = resultados.cargar_npz(f"{prefijo}_{r}")
        if con_meta:
            p = meta["parametros_base"]
            x["gamma"] = p["R"] / p["L"]
            x["omega0"] = 1 / np.sqrt(p["L"] * p["C"])
        datos[r] = x
    return datos


def guardar(fig, nombre: str) -> list:
    return graficos.guardar(fig, f"presentacion/{nombre}")


def redimensionar(fig, ancho: float, alto: float, rect=(0, 0, 1, 1), titulo: str = "",
                  etiqueta_fila: str = "mover"):
    """Cambia el tamaño de una figura ya armada y recalcula su distribución con
    el mismo margen (rect) que usa la función original de graficos.py.

    etiqueta_fila : qué hacer con el rótulo «κ = …» de la izquierda de cada
        fila, que con letra grande choca con la etiqueta del eje y:
        "mover" lo integra en la etiqueta del eje y; "quitar" lo elimina
        (cuando el título ya dice el valor de κ).
    """
    for ax in fig.axes:
        for t in list(ax.texts):
            # El rótulo de fila es una anotación anclada en (0, 0.5) del eje;
            # los textos «κ = … ρ = …» de G9 son otros y no se tocan.
            if t.get_text().startswith("κ =") and tuple(getattr(t, "xy", ())) == (0, 0.5):
                if etiqueta_fila == "mover":
                    ax.set_ylabel(f"{t.get_text()}\n{ax.get_ylabel()}", fontweight="bold")
                t.remove()
    fig.set_size_inches(ancho, alto)
    if titulo:
        fig.suptitle(titulo, y=1.0)
    fig.tight_layout(rect=rect)
    return fig


def main():
    try:
        e2 = cargar("e2", con_meta=True)
        e3 = cargar("e3")
        e4 = cargar("e4")
        with open(resultados.DATOS / "g10_metricas.csv", encoding="utf-8") as f:
            g10 = list(csv.DictReader(f))
    except FileNotFoundError:
        sys.exit("Faltan datos. Corre antes fase3_completa.py.")

    rutas = []
    with plt.rc_context(PRESENTACION):
        # P1: validación. Es G2 tal cual (2 × 2 paneles, ya legible a pantalla
        # completa); se copia para tener todas las figuras de la presentación juntas.
        (graficos.FIGURAS / "presentacion").mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            origen = graficos.FIGURAS / f"g2_validacion.{ext}"
            if not origen.exists():
                sys.exit("Falta G2. Corre antes: python scripts/g2_validacion.py")
            destino = graficos.FIGURAS / "presentacion" / f"p1_validacion.{ext}"
            destino.write_bytes(origen.read_bytes())
            rutas.append(destino)

        # P2: tγ frente a d con κ = 0.1
        fig = graficos.g5_llegada_vs_distancia(e2, REDES, [0.1])
        redimensionar(fig, 18, 6.2, (0, 0.08, 1, 1),
                      "El tiempo de llegada crece con la distancia, más rápido que una "
                      "recta (κ = 0.1)", etiqueta_fila="quitar")
        rutas += guardar(fig, "p2_llegada_k0p1")

        # P3: rapidez frente a κ, solo el umbral del PDF
        for r in REDES:
            e2[r]["_rapidez"] = graficos.rapideces(e2[r])
        solo_1e6 = {r: {**x, "umbrales": np.array([1e-6]),
                        "_rapidez": x["_rapidez"][:, :, [list(x["umbrales"]).index(1e-6)]]}
                    for r, x in e2.items()}
        fig = graficos.g6_rapidez_vs_kappa(solo_1e6, REDES)
        redimensionar(fig, 12, 8, (0, 0.12, 1, 1),
                      "La rapidez del frente crece como κ y luego como √κ")
        rutas += guardar(fig, "p3_rapidez")

        # P4: energía media por distancia con κ = 0.01 y κ = 1
        fig = graficos.g7_energia_media_vs_distancia(e3, REDES, [0.01, 1.0])
        redimensionar(fig, 18, 9, (0.03, 0.06, 1, 1),
                      "La energía media cae con la distancia: exponencial con κ pequeño, "
                      "casi plana con κ grande")
        rutas += guardar(fig, "p4_energia_distancia")

        # P5: igual distancia, distinta respuesta
        paneles = [("t_gamma", "caminos", 0.1, "γtᵢ relativo a su distancia",
                    "caminos más cortos Nᵢ (relativo)"),
                   ("E_rel", "peso_modal", 1.0, "⟨Eᵢ⟩ relativa a su distancia",
                    "peso modal Wᵢ (relativo)")]
        fig = graficos.g9_posicion(e4, REDES, paneles)
        redimensionar(fig, 18, 9, (0, 0, 1, 1),
                      "A igual distancia, Nᵢ decide la llegada y el peso modal decide la "
                      "energía")
        rutas += guardar(fig, "p5_igual_distancia")

        # P6: comparación de topologías (4 métricas)
        def valores(metrica):
            v = {}
            for f in g10:
                if f["metrica"] == metrica:
                    v.setdefault(f["red"], {}).setdefault(f["serie"], []).append(float(f["valor"]))
            return {r: v[r] for r in REDES}
        metricas = [
            {"titulo": "Rapidez del frente", "ylabel": "v/ω₀", "log": True,
             "valores": valores("rapidez")},
            {"titulo": "Alcance (κ = 0.01)", "ylabel": "fracción alcanzada",
             "valores": valores("alcance")},
            {"titulo": "Caída de la energía con d", "ylabel": "pendiente de log₁₀Ē por enlace",
             "valores": valores("pendiente")},
            {"titulo": "Heterogeneidad a igual d", "ylabel": "σ_E/Ē",
             "valores": valores("heterogeneidad")},
        ]
        fig = graficos.g10_topologias(metricas, REDES, columnas=4)
        redimensionar(fig, 19, 6.4, (0, 0.1, 1, 1),
                      "La topología fija rapidez, alcance y reparto: ER la más rápida, "
                      "el anillo la más lenta")
        rutas += guardar(fig, "p6_topologias")

    print("Guardado:", *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
