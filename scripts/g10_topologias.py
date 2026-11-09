"""G10: comparación directa de las cuatro topologías (pregunta P6).

Reúne en una figura, una métrica por panel, lo que distingue a cada red con
κ = 0.1 y κ = 1 (mediana y percentiles 10–90 entre realizaciones):

    rapidez del frente v/ω₀ (umbral 10⁻⁶ E₀)              de E2
    fracción de nodos alcanzados con κ = 0.01             de E2
    caída de la energía media: pendiente de log₁₀Ē(d)     de E3
    heterogeneidad σ_E/Ē mediana (d ≥ 1)                  de E3
    fracción de la energía media que queda en la fuente   de E3
    conectividad algebraica λ₂ (estructura)               de las redes

λ₂ se incluye para la hipótesis de la teoría (punto 4): un λ₂ mayor podría
asociarse a un reparto más rápido de la energía.

Requiere haber corrido antes:
    python scripts/e2_llegadas.py
    python scripts/e3_energia_distancia.py

Salidas:
    resultados/figuras/g10_topologias.png y .pdf
    resultados/datos/g10_metricas.csv  (una fila por red, métrica, serie y realización)

Uso, desde la raíz del proyecto:
    python scripts/g10_topologias.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, graficos, redes, resultados

KAPPAS = (0.1, 1.0)
UMBRAL = 1e-6


def pendiente(media_d: np.ndarray) -> float:
    d = np.arange(media_d.size)
    ok = (d >= 1) & np.isfinite(media_d) & (media_d > 0)
    return float(np.polyfit(d[ok], np.log10(media_d[ok]), 1)[0]) if ok.sum() >= 2 else np.nan


def main():
    redes_ = list(redes.TOPOLOGIAS)
    try:
        e2 = {r: resultados.cargar_npz(f"e2_{r}") for r in redes_}
        e3 = {r: resultados.cargar_npz(f"e3_{r}")[1] for r in redes_}
    except FileNotFoundError:
        sys.exit("Faltan datos de E2 o E3. Corre antes e2_llegadas.py y e3_energia_distancia.py.")

    nombres = ("rapidez", "alcance", "pendiente", "heterogeneidad", "fuente", "lambda2")
    val = {m: {r: {} for r in redes_} for m in nombres}
    for r in redes_:
        meta, x = e2[r]
        p = meta["parametros_base"]
        omega0 = 1 / np.sqrt(p["L"] * p["C"])
        ks = [float(k) for k in x["kappas"]]
        u = list(x["umbrales"]).index(UMBRAL)
        dist = x["distancias"]
        nr = dist.shape[0]
        y = e3[r]
        for kappa in KAPPAS:
            i = ks.index(kappa)
            serie = f"κ = {kappa:g}"
            val["rapidez"][r][serie] = [analisis.rapidez_frente(x["t_llegada"][i, j, u],
                                                                dist[j])[0] / omega0
                                        for j in range(nr)]
            val["pendiente"][r][serie] = [pendiente(y["media"][i, j]) for j in range(nr)]
            with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                rel = np.where((y["media"][i] > 1e-12) & (np.arange(y["media"].shape[2]) >= 1),
                               y["sigma"][i] / y["media"][i], np.nan)
                val["heterogeneidad"][r][serie] = np.nanmedian(rel, axis=1)
            val["fuente"][r][serie] = y["fraccion"][i, np.arange(nr), x["fuente"]]
        i01 = ks.index(0.01)
        alc = np.isfinite(x["t_llegada"][i01, :, u, :]).sum(axis=1) - 1
        val["alcance"][r]["κ = 0.01"] = alc / (dist.shape[1] - 1)
        l2 = []
        for s in x["semillas"]:
            lam = np.linalg.eigvalsh(redes.construir(r, semilla=int(s)).laplaciano)
            l2.append(lam[1])
        val["lambda2"][r]["estructura"] = l2

    metricas = [
        {"titulo": "Rapidez del frente", "ylabel": "v/ω₀", "log": True, "valores": val["rapidez"]},
        {"titulo": "Alcance con acoplamiento débil (κ = 0.01)",
         "ylabel": "fracción de nodos alcanzados", "valores": val["alcance"]},
        {"titulo": "Caída de la energía media con d",
         "ylabel": "pendiente de log₁₀ Ē(d) por enlace", "valores": val["pendiente"]},
        {"titulo": "Heterogeneidad a igual distancia",
         "ylabel": "σ_E/Ē (mediana sobre d ≥ 1)", "valores": val["heterogeneidad"]},
        {"titulo": "Energía media que queda en la fuente",
         "ylabel": "⟨E_fuente⟩ / Σⱼ⟨Eⱼ⟩", "valores": val["fuente"]},
        {"titulo": "Conectividad algebraica (estructura)", "ylabel": "λ₂ de Λ", "log": True,
         "valores": val["lambda2"]},
    ]

    filas = [{"red": r, "metrica": m, "serie": s, "realizacion": j, "valor": float(v)}
             for m in nombres for r in redes_ for s, vs in val[m][r].items()
             for j, v in enumerate(vs)]
    ruta = resultados.guardar_csv("g10_metricas", filas)
    rutas = graficos.guardar(graficos.g10_topologias(metricas, redes_), "g10_topologias")

    print("Medianas por red")
    print(f"{'métrica':16s} {'serie':10s} " + "".join(f"{r:>15s}" for r in redes_))
    for m in nombres:
        for s in val[m][redes_[0]]:
            print(f"{m:16s} {s:10s} " + "".join(
                f"{np.nanmedian(val[m][r][s]):15.4g}" for r in redes_))
    print("\nGuardado:", ruta, *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
