"""Figuras de ajuste de la Fase 4: datos, modelos y residuos.

    A1  tγ(d): lineal, potencia, logarítmico (κ = 0.1 y κ = 1)
    A2  log₁₀⟨Eᵢ⟩(d): exponencial y potencia (κ = 0.01 y κ = 1)
    A3  log₁₀v(κ): potencia, por tramos (1 y ½), transición suave

Las curvas se ajustan, para dibujarlas, sobre todos los nodos (en las redes
aleatorias, de las 30 realizaciones juntas). El texto de cada panel resume la
comparación hecha por realización en scripts/f4_ajustes.py: cuántas veces gana
cada modelo y la mediana del ΔAICc del segundo.

Requiere haber corrido antes:
    python scripts/fase3_completa.py   (o E2 y E3)
    python scripts/f4_ajustes.py

Salidas: resultados/figuras/a1_ajuste_llegada.png, a2_ajuste_energia.png,
a3_ajuste_rapidez.png (y .pdf)

Uso, desde la raíz del proyecto:
    python scripts/f4_figuras.py
"""

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import ajustes, analisis, graficos, redes, resultados

REDES = list(redes.TOPOLOGIAS)
TITULOS = [graficos.NOMBRE_RED[r] for r in REDES]


def leer_csv(nombre):
    with open(resultados.DATOS / f"{nombre}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def texto_aicc(filas, red, kappa=None) -> str:
    """«gana: potencia 30/30 · ΔAICc del 2.º: 24» a partir de los ajustes por realización."""
    g = [f for f in filas if f["red"] == red and (kappa is None or float(f["kappa"]) == kappa)]
    por_real = {}
    for f in g:
        por_real.setdefault(f["realizacion"], []).append(f)
    ganadores = Counter(min(v, key=lambda f: float(f["delta_aicc"]))["modelo"]
                        for v in por_real.values())
    segundos = [sorted(float(f["delta_aicc"]) for f in v)[1] for v in por_real.values()
                if len(v) > 1]
    m, c = ganadores.most_common(1)[0]
    return f"gana: {m} {c}/{len(por_real)}\nΔAICc del 2.º: {np.median(segundos):.0f}"


def panel(modelos, x, y, color, x_curva, texto, etiqueta="", **extra):
    """Ajusta cada modelo a (x, y) y arma el dict que espera figura_ajustes."""
    curvas, residuos = {}, {}
    for a in ajustes.comparar(modelos, x, y):
        curvas[a.nombre] = (x_curva, a.predecir(x_curva))
        ux = np.unique(a.x)
        residuos[a.nombre] = (ux, np.array([np.median(a.residuos[a.x == v]) for v in ux]))
    return {"x": x, "y": y, "color": color, "curvas": curvas, "residuos": residuos,
            "texto": texto, "etiqueta": etiqueta, **extra}


def main():
    try:
        e2 = {r: resultados.cargar_npz(f"e2_{r}") for r in REDES}
        e3 = {r: resultados.cargar_npz(f"e3_{r}")[1] for r in REDES}
        ft, fE, fv = leer_csv("f4_ajustes_t"), leer_csv("f4_ajustes_E"), leer_csv("f4_ajustes_v")
    except FileNotFoundError:
        sys.exit("Faltan datos. Corre antes fase3_completa.py y f4_ajustes.py.")

    # A1: tγ(d)
    bloques = []
    for kappa in (0.1, 1.0):
        fila = []
        for r in REDES:
            meta, x = e2[r]
            gamma = meta["parametros_base"]["R"] / meta["parametros_base"]["L"]
            i = list(x["kappas"]).index(kappa)
            u = list(x["umbrales"]).index(1e-6)
            d = x["distancias"].astype(float).ravel()
            tg = gamma * x["t_llegada"][i, :, u, :].ravel()
            ok = (d >= 1) & np.isfinite(tg)
            xc = np.linspace(1, d[ok].max(), 200)
            fila.append(panel(ajustes.MODELOS_T, d[ok], tg[ok], graficos.COLOR_RED[r], xc,
                              texto_aicc(ft, r, kappa), f"κ = {kappa:g}"))
        bloques.append(fila)
    fig = graficos.figura_ajustes(bloques, TITULOS,
                                  "A1. Tiempo de llegada frente a la distancia: modelos y residuos",
                                  ["tiempo de llegada, γtᵢ"] * 2, "residuo (γt)",
                                  "distancia a la fuente, d",
                                  orden_modelos=["potencia", "lineal", "logarítmico"])
    rutas = graficos.guardar(fig, "a1_ajuste_llegada")

    # A2: log₁₀⟨Eᵢ⟩(d)
    bloques = []
    for kappa in (0.01, 1.0):
        fila = []
        for r in REDES:
            y = e3[r]
            i = [float(k) for k in y["kappas"]].index(kappa)
            d = y["distancias"].astype(float).ravel()
            E = y["E_rel"][i].ravel()
            ok = (d >= 1) & (E > 1e-12)
            xc = np.linspace(1, d[ok].max(), 200)
            fila.append(panel(ajustes.MODELOS_E, d[ok], np.log10(E[ok]), graficos.COLOR_RED[r],
                              xc, texto_aicc(fE, r, kappa), f"κ = {kappa:g}", texto_abajo=True))
        bloques.append(fila)
    fig = graficos.figura_ajustes(bloques, TITULOS,
                                  "A2. Energía media frente a la distancia: modelos y residuos",
                                  ["log₁₀(⟨Eᵢ⟩/E₀)"] * 2, "residuo (décadas)",
                                  "distancia a la fuente, d",
                                  orden_modelos=["exponencial", "potencia"])
    rutas += graficos.guardar(fig, "a2_ajuste_energia")

    # A3: log₁₀v(κ)
    fila = []
    for r in REDES:
        meta, x = e2[r]
        omega0 = 1 / np.sqrt(meta["parametros_base"]["L"] * meta["parametros_base"]["C"])
        ks = np.array(x["kappas"], float)
        u = list(x["umbrales"]).index(1e-6)
        kk, vv = [], []
        for i, k in enumerate(ks):
            for j in range(x["distancias"].shape[0]):
                v = analisis.rapidez_frente(x["t_llegada"][i, j, u], x["distancias"][j])[0]
                kk.append(k)
                vv.append(np.log10(v / omega0))
        kk, vv = np.array(kk), np.array(vv)
        ok = np.isfinite(vv)
        xc = np.geomspace(ks.min(), ks.max(), 200)
        fila.append(panel(ajustes.MODELOS_V, kk[ok], vv[ok], graficos.COLOR_RED[r], xc,
                          texto_aicc(fv, r), texto_abajo=False))
    fig = graficos.figura_ajustes([fila], TITULOS,
                                  "A3. Rapidez del frente frente a κ: modelos y residuos",
                                  ["log₁₀(v/ω₀)"], "residuo (décadas)",
                                  "acoplamiento, κ", xlog=True,
                                  orden_modelos=["transición suave", "por tramos (1 y ½)",
                                                 "potencia"])
    rutas += graficos.guardar(fig, "a3_ajuste_rapidez")
    print("Guardado:", *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
