"""E4. Efecto de la posición: ¿igual distancia implica igual respuesta? (P5, P6, P8)

No simula: usa tᵢ y ⟨Eᵢ⟩ de cada nodo que el experimento E2 ya calculó.

Para los nodos a la misma distancia d de la fuente (en la misma realización),
mide cuánto de su variación en tiempo de llegada (umbral 10⁻⁶ E₀) y en energía
media explican tres predictores:

    Nᵢ  número de caminos más cortos desde la fuente (teoría, punto 7)
    kᵢ  grado del nodo
    Wᵢ  peso modal incoherente Σ_λ (Π_λ)ᵢ₀² (teoría, punto 6): la amplitud
        media que llegaría si los modos no interfirieran

Medidas (analisis.relacion_a_igual_distancia):
    ρ  correlación de Spearman dentro de cada grupo (mediana entre grupos)
    R² parte de la variación a igual d que explica el predictor, con una
       regresión de log(respuesta) sobre log(predictor) tras restar la media
       de cada grupo

Requiere haber corrido antes:
    python scripts/e2_llegadas.py

Salidas (en resultados/datos/):
    e4_<red>.npz    — por nodo: γtᵢ y ⟨Eᵢ⟩/E₀ [κ, realización, nodo] y los
                      predictores Nᵢ, kᵢ, Wᵢ [realización, nodo]
    e4_resumen.csv  — una fila por (red, κ, respuesta, predictor)

Uso, desde la raíz del proyecto:
    python scripts/e4_posicion.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, redes, resultados

UMBRAL = 1e-6


def main():
    filas = []
    tabla = {}
    for nombre in redes.TOPOLOGIAS:
        try:
            meta, x = resultados.cargar_npz(f"e2_{nombre}")
        except FileNotFoundError:
            sys.exit("Faltan datos de E2. Corre antes: python scripts/e2_llegadas.py")
        p = meta["parametros_base"]
        gamma, E0 = p["R"] / p["L"], p["Q0"] ** 2 / (2 * p["C"])
        u = list(x["umbrales"]).index(UMBRAL)
        dist, cam, grad = x["distancias"], x["caminos"], x["grados"]

        # Peso modal: se reconstruye cada red con su semilla y se verifica que
        # sea la misma que usó E2.
        W = np.zeros(dist.shape)
        for j, s in enumerate(x["semillas"]):
            red = redes.construir(nombre, semilla=int(s))
            if not np.array_equal(red.distancias, dist[j]):
                sys.exit(f"La red {nombre} con semilla {s} no coincide con la de E2.")
            W[j] = analisis.peso_modal_incoherente(red.laplaciano, red.fuente)

        tg = gamma * x["t_llegada"][:, :, u, :]               # [κ, realización, nodo]
        E_rel = x["E_media"] / E0
        resultados.guardar_npz(
            f"e4_{nombre}",
            meta={"experimento": "E4", "red": nombre, "fuente_datos": f"e2_{nombre}.npz",
                  "umbral": UMBRAL, "unidades": "t en γt; E en E0"},
            kappas=x["kappas"], semillas=x["semillas"], t_gamma=tg, E_rel=E_rel,
            distancias=dist, caminos=cam, grados=grad, peso_modal=W,
        )

        predictores = {"N_caminos": cam.astype(float), "grado": grad.astype(float),
                       "peso_modal": W}
        for i, kappa in enumerate(x["kappas"]):
            for resp, Y in (("t_llegada", tg[i]), ("E_media", E_rel[i])):
                for nom_p, X in predictores.items():
                    r = analisis.relacion_a_igual_distancia(Y, X, dist)
                    filas.append({"red": nombre, "kappa": float(kappa), "respuesta": resp,
                                  "predictor": nom_p, **r})
                    tabla[(nombre, float(kappa), resp, nom_p)] = r
    ruta = resultados.guardar_csv("e4_resumen", filas)

    print("E4: variación entre nodos a igual distancia explicada por cada predictor\n")
    for resp, signo in (("t_llegada", "se espera ρ < 0"), ("E_media", "se espera ρ > 0")):
        print(f"Respuesta: {resp} ({signo}).  Celdas: ρ mediana / R²")
        print(f"{'red':14s} {'κ':>5s} " + "".join(f"{p:>20s}" for p in
                                                  ("N_caminos", "grado", "peso_modal")))
        for nombre in redes.TOPOLOGIAS:
            for kappa in (0.01, 0.1, 1.0, 10.0):
                celdas = []
                for nom_p in ("N_caminos", "grado", "peso_modal"):
                    r = tabla[(nombre, kappa, resp, nom_p)]
                    celdas.append(f"{r['rho_mediana']:+6.2f} / {r['R2']:4.2f}")
                print(f"{nombre:14s} {kappa:5g} " + "".join(f"{c:>20s}" for c in celdas))
        print()
    print(f"Resumen guardado en {ruta}")


if __name__ == "__main__":
    main()
