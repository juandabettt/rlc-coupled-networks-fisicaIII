"""G9 a partir de los datos del experimento E4 (preguntas P5, P6 y P8).

Muestra, para nodos a la misma distancia de la fuente, cómo varían el tiempo
de llegada y la energía media con el número de caminos más cortos Nᵢ, el grado
kᵢ y el peso modal Wᵢ.

Requiere haber corrido antes:
    python scripts/e2_llegadas.py
    python scripts/e4_posicion.py

Salidas:
    resultados/figuras/g9_posicion.png y .pdf

Uso, desde la raíz del proyecto:
    python scripts/g9_posicion.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from red_rlc import graficos, redes, resultados


def main():
    redes_ = list(redes.TOPOLOGIAS)
    try:
        datos = {r: resultados.cargar_npz(f"e4_{r}")[1] for r in redes_}
    except FileNotFoundError:
        sys.exit("Faltan datos de E4. Corre antes: python scripts/e4_posicion.py")
    rutas = graficos.guardar(graficos.g9_posicion(datos, redes_), "g9_posicion")
    print("Guardado:", *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
