"""G3 y G4 a partir de los datos del experimento E1 (pregunta P1).

G3: Eᵢ(t)/E₀ de un nodo representativo por distancia.
G4: mapa de log₁₀(Eᵢ/E₀) por nodo y tiempo, con el frente de llegada.

Ambas en una rejilla de 4 redes × κ ∈ {0.01, 0.1, 1}: así se ve el efecto de
la topología (columnas) y del acoplamiento (filas) en la misma figura.

Requiere haber corrido antes:
    python scripts/e1_dinamica.py

Salidas:
    resultados/figuras/g3_energia_por_distancia.png y .pdf
    resultados/figuras/g4_mapa_nodo_tiempo.png y .pdf

Uso, desde la raíz del proyecto:
    python scripts/g3_g4_dinamica.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from red_rlc import graficos, redes, resultados

KAPPAS = (0.01, 0.1, 1.0)


def cargar_e1(red: str, kappa: float) -> dict:
    meta, x = resultados.cargar_npz(f"e1_{red}_k{kappa:g}")
    p = meta["parametros"]
    x["gamma"] = p["R"] / p["L"]
    x["E0"] = p["Q0"] ** 2 / (2 * p["C"])
    return x


def main():
    redes_ = list(redes.TOPOLOGIAS)
    try:
        datos = {(r, k): cargar_e1(r, k) for r in redes_ for k in KAPPAS}
    except FileNotFoundError as e:
        sys.exit(f"Faltan datos de E1 ({e.filename}). Corre antes: python scripts/e1_dinamica.py")

    rutas = graficos.guardar(graficos.g3_energia_por_distancia(datos, redes_, KAPPAS),
                             "g3_energia_por_distancia")
    rutas += graficos.guardar(graficos.g4_mapa_nodo_tiempo(datos, redes_, KAPPAS),
                              "g4_mapa_nodo_tiempo")
    print("Guardado:", *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
