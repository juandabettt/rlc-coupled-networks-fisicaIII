"""G5 y G6 a partir de los datos del experimento E2 (preguntas P2, P3, P5, P7).

G5: γtᵢ frente a d₀ᵢ, por κ (filas) y red (columnas), con los nodos que no
    llegan y la sensibilidad al umbral.
G6: rapidez del frente v/ω₀ frente a κ (log–log), un panel por umbral, con
    las pendientes de referencia 1 y ½.

Requiere haber corrido antes:
    python scripts/e2_llegadas.py

Salidas:
    resultados/figuras/g5_llegada_vs_distancia.png y .pdf
    resultados/figuras/g6_rapidez_vs_kappa.png y .pdf
    resultados/datos/g6_rapidez.csv  (v/ω₀ por red, κ, umbral y realización)

Uso, desde la raíz del proyecto:
    python scripts/g5_g6_llegadas.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import graficos, redes, resultados

KAPPAS_G5 = (0.01, 0.1, 1.0, 10.0)


def cargar_e2(red: str) -> dict:
    meta, x = resultados.cargar_npz(f"e2_{red}")
    p = meta["parametros_base"]
    x["gamma"] = p["R"] / p["L"]
    x["omega0"] = 1 / np.sqrt(p["L"] * p["C"])
    return x


def main():
    redes_ = list(redes.TOPOLOGIAS)
    try:
        datos = {r: cargar_e2(r) for r in redes_}
    except FileNotFoundError as e:
        sys.exit(f"Faltan datos de E2 ({e.filename}). Corre antes: python scripts/e2_llegadas.py")

    filas = []
    for r, x in datos.items():
        x["_rapidez"] = graficos.rapideces(x)
        for i, k in enumerate(x["kappas"]):
            for j, s in enumerate(x["semillas"]):
                for u, um in enumerate(x["umbrales"]):
                    filas.append({"red": r, "kappa": float(k), "semilla": int(s),
                                  "umbral": float(um), "v_sobre_w0": x["_rapidez"][i, j, u]})
    ruta_csv = resultados.guardar_csv("g6_rapidez", filas)

    rutas = graficos.guardar(graficos.g5_llegada_vs_distancia(datos, redes_, KAPPAS_G5),
                             "g5_llegada_vs_distancia")
    rutas += graficos.guardar(graficos.g6_rapidez_vs_kappa(datos, redes_), "g6_rapidez_vs_kappa")
    print("Guardado:", ruta_csv, *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
