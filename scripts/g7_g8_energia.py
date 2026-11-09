"""G7 y G8 a partir de los datos del experimento E3 (preguntas P2, P4 y P8).

G7: Ē(d)/E₀ con σ_E(d), por κ (filas) y red (columnas).
G8: σ_E(d)/E₀ y σ_E/Ē frente a d, una línea por κ.

Requiere haber corrido antes:
    python scripts/e2_llegadas.py
    python scripts/e3_energia_distancia.py

Salidas:
    resultados/figuras/g7_energia_media_vs_distancia.png y .pdf
    resultados/figuras/g8_heterogeneidad.png y .pdf

Uso, desde la raíz del proyecto:
    python scripts/g7_g8_energia.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from red_rlc import graficos, redes, resultados

KAPPAS = (0.01, 0.1, 1.0, 10.0)


def main():
    redes_ = list(redes.TOPOLOGIAS)
    try:
        datos = {r: resultados.cargar_npz(f"e3_{r}")[1] for r in redes_}
    except FileNotFoundError:
        sys.exit("Faltan datos de E3. Corre antes: python scripts/e3_energia_distancia.py")

    rutas = graficos.guardar(graficos.g7_energia_media_vs_distancia(datos, redes_, KAPPAS),
                             "g7_energia_media_vs_distancia")
    rutas += graficos.guardar(graficos.g8_heterogeneidad(datos, redes_, KAPPAS),
                              "g8_heterogeneidad")
    print("Guardado:", *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
