"""E3. Energía por distancia (preguntas P2, P4 y P8).

No simula: usa ⟨Eᵢ⟩ (ecuación 16 del PDF, T = 10/γ) que el experimento E2 ya
calculó para cada nodo, red, κ y realización.

Qué se calcula, para cada red, κ y realización:
    ⟨Eᵢ⟩/E₀                         energía media de cada nodo (ec. 18)
    Ē(d)/E₀                         media sobre los nodos a distancia d (ec. 21)
    σ_E(d)/E₀                       desviación entre esos nodos, ddof = 1 (ec. 23)
    ⟨Eᵢ⟩/Σⱼ⟨Eⱼ⟩                     fracción de energía (apoyo, suma 1)

Las dos variabilidades del plan se mantienen separadas:
    - σ_E(d): diferencias entre nodos dentro de una red;
    - percentiles 10–90 de Ē(d) entre las 30 realizaciones (redes aleatorias).

Requiere haber corrido antes:
    python scripts/e2_llegadas.py

Salidas (en resultados/datos/):
    e3_<red>.npz    — ejes [κ, realización, d] para Ē y σ; [κ, realización, nodo]
                      para ⟨Eᵢ⟩/E₀ y la fracción
    e3_resumen.csv  — una fila por (red, κ, d) con medianas y rangos

Uso, desde la raíz del proyecto:
    python scripts/e3_energia_distancia.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, redes, resultados


def q(a, p):
    """Percentil ignorando NaN; NaN si no hay datos."""
    return float(np.nanpercentile(a, p)) if np.isfinite(a).any() else np.nan


def main():
    filas = []
    resumen = {}
    for nombre in redes.TOPOLOGIAS:
        try:
            meta, x = resultados.cargar_npz(f"e2_{nombre}")
        except FileNotFoundError:
            sys.exit("Faltan datos de E2. Corre antes: python scripts/e2_llegadas.py")
        p = meta["parametros_base"]
        E0 = p["Q0"] ** 2 / (2 * p["C"])
        kappas = x["kappas"]
        dist = x["distancias"]                                  # [realización, nodo]
        E_rel = x["E_media"] / E0                               # [κ, realización, nodo]
        nk, nr, N = E_rel.shape
        D = int(dist.max()) + 1

        media = np.full((nk, nr, D), np.nan)
        sigma = np.full((nk, nr, D), np.nan)
        fraccion = E_rel / E_rel.sum(axis=2, keepdims=True)
        for i in range(nk):
            r = analisis.por_distancia_realizaciones(E_rel[i], dist)
            media[i], sigma[i] = r["media"], r["sigma"]
        N_d = r["N_d"]

        resultados.guardar_npz(
            f"e3_{nombre}",
            meta={"experimento": "E3", "red": nombre, "fuente_datos": f"e2_{nombre}.npz",
                  "unidades": "energías divididas por E0 = Q0²/(2C)",
                  "ejes_media_sigma": "[kappa, realizacion, d]", "T_gamma": 10},
            kappas=kappas, semillas=x["semillas"], d=np.arange(D), N_d=N_d,
            media=media, sigma=sigma, E_rel=E_rel, fraccion=fraccion, distancias=dist,
        )

        for i, kappa in enumerate(kappas):
            for d in range(D):
                con_d = N_d[:, d] > 0
                m, s = media[i, con_d, d], sigma[i, con_d, d]
                with np.errstate(invalid="ignore", divide="ignore"):
                    rel = s / m
                filas.append({
                    "red": nombre, "kappa": float(kappa), "d": d,
                    "realizaciones_con_d": int(con_d.sum()), "de": nr,
                    "N_d_mediana": q(N_d[con_d, d], 50),
                    "Ebar_E0_mediana": q(m, 50), "Ebar_E0_p10": q(m, 10), "Ebar_E0_p90": q(m, 90),
                    "sigma_E0_mediana": q(s, 50),
                    "sigma_relativa_mediana": q(rel, 50),
                })

        # Resumen para la consola: decaimiento de Ē(d) y heterogeneidad relativa.
        for i, kappa in enumerate(kappas):
            med_d = np.nanmedian(media[i], axis=0)
            ds = np.arange(1, D)
            ok = np.isfinite(med_d[1:]) & (np.median(N_d, axis=0)[1:] > 0)
            pend = np.polyfit(ds[ok], np.log10(med_d[1:][ok]), 1)[0] if ok.sum() >= 2 else np.nan
            # σ no está definida en d = 0 (un solo nodo): esa columna es toda NaN.
            with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                rel = np.nanmedian(sigma[i] / media[i], axis=0)[1:]
            frac_fuente = np.median(fraccion[i, np.arange(nr), x["fuente"]])
            resumen[(nombre, float(kappa))] = (med_d[0], med_d[1], pend,
                                               np.nanmax(rel[ok]), float(frac_fuente))
    ruta = resultados.guardar_csv("e3_resumen", filas)

    print("E3: energía media por distancia (medianas entre realizaciones)\n")
    print(f"{'red':14s} {'κ':>5s} {'Ē(0)/E₀':>9s} {'Ē(1)/E₀':>9s} {'pend. log₁₀Ē por d':>19s} "
          f"{'máx σ/Ē':>8s} {'fracción fuente':>15s}")
    for (nombre, kappa), (e0, e1, pend, rel, fr) in resumen.items():
        print(f"{nombre:14s} {kappa:5g} {e0:9.2e} {e1:9.2e} {pend:19.3f} {rel:8.2f} {fr:15.3f}")
    print(f"\nResumen guardado en {ruta}")


if __name__ == "__main__":
    main()
