"""G1: las cuatro topologías y su distribución de distancias a la fuente.

No necesita simulaciones: solo la estructura de las redes. Para las redes
aleatorias usa la realización de referencia (semilla 2026) y superpone la
media de N_d sobre las 30 realizaciones del plan.

Salidas:
    resultados/figuras/g1_redes.png y .pdf
    resultados/datos/g1_distancias.csv  (N_d por red y realización)

Uso, desde la raíz del proyecto:
    python scripts/g1_redes.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import graficos, redes, resultados


def main():
    referencia = redes.redes_referencia()
    realizaciones = {n: redes.realizaciones(n) for n in redes.ALEATORIAS}

    filas = []
    for nombre in redes.TOPOLOGIAS:
        lista = realizaciones.get(nombre, [referencia[nombre]])
        for r in lista:
            for d, n in enumerate(r.distribucion_distancias):
                filas.append({"red": nombre, "semilla": r.semilla, "intentos": r.intentos,
                              "d": d, "N_d": int(n)})
    ruta_csv = resultados.guardar_csv("g1_distancias", filas)

    fig = graficos.g1_redes(referencia, realizaciones)
    rutas = graficos.guardar(fig, "g1_redes")

    print("Resumen estructural")
    print(f"{'red':15s} {'enlaces':>7s} {'<k>':>5s} {'d max':>5s} {'<d max> (30)':>12s} "
          f"{'<k> (30)':>9s} {'intentos ER':>11s}")
    for nombre in redes.TOPOLOGIAS:
        r = referencia[nombre]
        lista = realizaciones.get(nombre, [r])
        dm = np.mean([x.distancia_maxima for x in lista])
        km = np.mean([x.grados.mean() for x in lista])
        it = sum(x.intentos for x in lista)
        print(f"{nombre:15s} {r.grafo.number_of_edges():7d} {r.grados.mean():5.2f} "
              f"{r.distancia_maxima:5d} {dm:12.2f} {km:9.2f} "
              f"{(str(it) + ' para ' + str(len(lista))) if nombre == 'erdos_renyi' else '-':>11s}")
    print("\nGuardado:", ruta_csv, *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
