"""Fase 4: ajustes funcionales con comparación por AICc (preguntas P2, P3, P4, P8).

Usa los datos de E2 y E3; no simula. Para cada red, κ y realización:

    tγ(d)   tiempos de llegada de cada nodo (umbral 10⁻⁶ E₀, d ≥ 1, nodos
            alcanzados) → lineal, potencia, logarítmico. Además, el mejor
            modelo se ajusta sin d = 1 para ver si d = 1 se aparta de la
            tendencia (pedido explícito del plan).
    E(d)    log₁₀(⟨Eᵢ⟩/E₀) de cada nodo con d ≥ 1 y ⟨Eᵢ⟩ > 10⁻¹² E₀
            → exponencial, potencia.
    σ(d)    log₁₀(σ_E(d)/E₀) por distancia, con N_d ≥ 2 y Ē > 10⁻¹² E₀
            → exponencial, potencia (se excluye N_d = 1, como pide el plan).
    v(κ)    rapidez del frente en los 7 valores de κ (una curva por
            realización) → potencia, por tramos (1 y ½), transición suave.

En las redes aleatorias se ajusta cada realización por separado y se reporta
cuántas veces gana cada modelo, más la mediana y los percentiles 10–90 de sus
parámetros.

Requiere haber corrido antes E2 y E3 (o scripts/fase3_completa.py).

Salidas (en resultados/datos/):
    f4_ajustes_t.csv, f4_ajustes_E.csv, f4_ajustes_sigma.csv, f4_ajustes_v.csv
        una fila por (red, κ, realización, modelo)

Uso, desde la raíz del proyecto:
    python scripts/f4_ajustes.py
"""

import sys
import warnings
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import ajustes, analisis, redes, resultados

UMBRAL = 1e-6
E_MIN = 1e-12


def filas_de(comparacion, base: dict) -> list:
    """Una fila por modelo comparado."""
    filas = []
    for a in comparacion:
        f = {**base, "modelo": a.nombre, "n": a.n, "delta_aicc": a.delta, "peso": a.peso,
             "r2": a.r2, "rss": a.rss}
        for nombre, (v, e) in a.parametros().items():
            f[f"p_{nombre}"] = v
            f[f"err_{nombre}"] = e
        filas.append(f)
    return filas


def resumen(filas: list, claves: tuple, etiqueta: str):
    """Imprime, por (red, κ), qué modelo gana y con qué peso mediano."""
    grupos = {}
    for f in filas:
        grupos.setdefault(tuple(f[c] for c in claves), []).append(f)
    print(f"\n{etiqueta}")
    print(f"{'red':14s} {'κ':>5s} {'gana (veces)':32s} {'peso mediano del ganador':>24s} "
          f"{'R² mediano':>10s}")
    for clave, g in grupos.items():
        ganadores = [f for f in g if f["delta_aicc"] == 0]
        cuenta = Counter(f["modelo"] for f in ganadores)
        texto = ", ".join(f"{m} {c}" for m, c in cuenta.most_common())
        top = cuenta.most_common(1)[0][0] if cuenta else "-"
        pesos = [f["peso"] for f in ganadores if f["modelo"] == top]
        r2 = [f["r2"] for f in ganadores if f["modelo"] == top]
        print(f"{clave[0]:14s} {clave[1] if len(clave) > 1 else '':>5} {texto:32s} "
              f"{np.median(pesos) if pesos else np.nan:24.2f} "
              f"{np.median(r2) if r2 else np.nan:10.3f}")


def main():
    filas_t, filas_E, filas_s, filas_v = [], [], [], []
    for nombre in redes.TOPOLOGIAS:
        try:
            meta, x = resultados.cargar_npz(f"e2_{nombre}")
            y3 = resultados.cargar_npz(f"e3_{nombre}")[1]
        except FileNotFoundError:
            sys.exit("Faltan datos de E2/E3. Corre antes: python scripts/fase3_completa.py")
        p = meta["parametros_base"]
        gamma = p["R"] / p["L"]
        omega0 = 1 / np.sqrt(p["L"] * p["C"])
        ks = [float(k) for k in x["kappas"]]
        u = list(x["umbrales"]).index(UMBRAL)
        dist = x["distancias"]
        nr = dist.shape[0]

        v_por_real = np.full((nr, len(ks)), np.nan)
        for i, kappa in enumerate(ks):
            for j in range(nr):
                base = {"red": nombre, "kappa": kappa, "realizacion": j,
                        "semilla": int(x["semillas"][j])}
                d = dist[j].astype(float)

                # tγ(d)
                tg = gamma * x["t_llegada"][i, j, u]
                ok = (d >= 1) & np.isfinite(tg)
                comp = ajustes.comparar(ajustes.MODELOS_T, d[ok], tg[ok])
                filas_comp = filas_de(comp, base)
                if comp:
                    mejor = comp[0]
                    sin1 = ajustes.ajustar(mejor.modelo, d[ok & (d >= 2)], tg[ok & (d >= 2)])
                    desv = ajustes.desviacion_en_d1(sin1, d[ok], tg[ok]) if sin1 else np.nan
                    for f in filas_comp:
                        f["desviacion_d1_sigmas"] = desv if f["delta_aicc"] == 0 else np.nan
                filas_t += filas_comp
                v_por_real[j, i] = analisis.rapidez_frente(x["t_llegada"][i, j, u],
                                                           dist[j])[0] / omega0

                # E(d), con los ⟨Eᵢ⟩ de cada nodo
                E = y3["E_rel"][i, j]
                ok = (d >= 1) & (E > E_MIN)
                filas_E += filas_de(ajustes.comparar(ajustes.MODELOS_E, d[ok],
                                                     np.log10(E[ok])), base)

                # σ(d), un valor por distancia
                s, m, Nd = y3["sigma"][i, j], y3["media"][i, j], y3["N_d"][j]
                dd = np.arange(s.size, dtype=float)
                ok = (dd >= 1) & (Nd >= 2) & np.isfinite(s) & (s > 0) & (m > E_MIN)
                filas_s += filas_de(ajustes.comparar(ajustes.MODELOS_E, dd[ok],
                                                     np.log10(s[ok])), base)

        # v(κ), una curva por realización
        for j in range(nr):
            v = v_por_real[j]
            ok = np.isfinite(v) & (v > 0)
            filas_v += filas_de(ajustes.comparar(ajustes.MODELOS_V, np.array(ks)[ok],
                                                 np.log10(v[ok])),
                                {"red": nombre, "realizacion": j,
                                 "semilla": int(x["semillas"][j])})

    for nombre_csv, filas in (("f4_ajustes_t", filas_t), ("f4_ajustes_E", filas_E),
                              ("f4_ajustes_sigma", filas_s), ("f4_ajustes_v", filas_v)):
        claves = sorted({k for f in filas for k in f})
        filas = [{k: f.get(k, "") for k in claves} for f in filas]
        resultados.guardar_csv(nombre_csv, filas)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        resumen(filas_t, ("red", "kappa"), "tγ(d): modelo ganador por AICc")
        resumen(filas_E, ("red", "kappa"), "E(d): modelo ganador por AICc (log₁₀⟨Eᵢ⟩ por nodo)")
        resumen(filas_s, ("red", "kappa"), "σ(d): modelo ganador por AICc")
        resumen(filas_v, ("red",), "v(κ): modelo ganador por AICc")

    # Parámetros del modelo suave de v(κ) y de la desviación en d = 1.
    print("\nv(κ), transición suave v = Aκ/√(1 + κ/κc): mediana [p10, p90]")
    for nombre in redes.TOPOLOGIAS:
        g = [f for f in filas_v if f["red"] == nombre and f["modelo"] == "transición suave"]
        A = 10 ** np.array([f["p_log₁₀A"] for f in g])
        kc = 10 ** np.array([f["p_log₁₀κc"] for f in g])
        q = lambda a: f"{np.median(a):.3f} [{np.percentile(a, 10):.3f}, {np.percentile(a, 90):.3f}]"
        print(f"  {nombre:14s} A = {q(A):26s} κc = {q(kc)}")
    print("\nd = 1 frente a la tendencia de d ≥ 2 (residuo medio en d = 1, en desviaciones "
          "estándar del ajuste; negativo = llega antes)")
    for nombre in redes.TOPOLOGIAS:
        for kappa in (0.1, 1.0, 10.0):
            g = [f["desviacion_d1_sigmas"] for f in filas_t if f["red"] == nombre
                 and f["kappa"] == kappa and f["delta_aicc"] == 0]
            g = np.array([v for v in g if v != "" and np.isfinite(v)])
            if g.size:
                print(f"  {nombre:14s} κ = {kappa:<5g} mediana {np.median(g):+6.2f}")
    print("\nGuardado en resultados/datos/f4_ajustes_{t,E,sigma,v}.csv")


if __name__ == "__main__":
    main()
