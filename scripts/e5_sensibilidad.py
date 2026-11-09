"""E5. Sensibilidad: γ, tamaño N y posición de la fuente (limitaciones, P7).

Un cambio a la vez respecto del caso base (L = 1 mH, C = 1 µF, R = 1 Ω,
N = 100, fuente de referencia), con κ = 0.1 y κ = 1:

    gamma   R ∈ {0.3, 1, 3, 10} Ω → factor de calidad ω₀/γ de 105 a 3.2.
            Las 4 redes de referencia. T = 10/γ en cada caso, para comparar
            el mismo número de tiempos de decaimiento.
    N       malla de lado 6, 10, 14 y 20 (N = 36 a 400) y anillo de 50, 100,
            200 y 400 nodos. Solo redes deterministas: en WS y ER cambiar N
            exige cambiar también p (dos cambios a la vez).
    fuente  malla: interior (4,4), borde (0,4) y esquina (0,0).
            ER (30 realizaciones): nodo 0, el de mayor grado y el de menor
            grado de cada realización.

Qué se mide en cada simulación: rapidez del frente v/ω₀ y fracción de nodos
alcanzados (umbral 10⁻⁶ E₀), γt de la última llegada, pendiente de log₁₀Ē(d)
frente a d, heterogeneidad σ/Ē mediana y fracción de energía en la fuente.

Salida: resultados/datos/e5_resumen.csv (una fila por simulación).

Uso, desde la raíz del proyecto (≈ 2–4 min con 6 procesos):
    python scripts/e5_sensibilidad.py
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, modelo, redes, resultados

KAPPAS = (0.1, 1.0)
RESISTENCIAS = (0.3, 1.0, 3.0, 10.0)
LADOS_MALLA = (6, 10, 14, 20)
N_ANILLO = (50, 100, 200, 400)
PROCESOS = max(1, min(6, (os.cpu_count() or 2) - 2))


def construir(estudio: str, red: str, variante, semilla: int):
    """Red de cada variante. Devuelve (Red, R en ohm)."""
    if estudio == "gamma":
        return redes.construir(red, semilla=semilla), float(variante)
    if estudio == "N":
        if red == "malla":
            return redes.malla(lado=int(variante)), 1.0
        return redes.anillo(N=int(variante)), 1.0
    # estudio == "fuente"
    if red == "malla":
        f = {"interior": "interior", "borde": redes.indice_malla(0, 4),
             "esquina": "esquina"}[variante]
        return redes.malla(fuente=f), 1.0
    base = redes.erdos_renyi(semilla=semilla)
    g = base.grados
    f = {"nodo 0": 0, "mayor grado": int(np.argmax(g)), "menor grado": int(np.argmin(g))}[variante]
    return redes.con_fuente(base, f), 1.0


def tarea(estudio, red_nombre, variante, kappa, semilla) -> dict:
    inicio = time.perf_counter()
    red, R = construir(estudio, red_nombre, variante, semilla)
    p = modelo.Parametros(R=R, kappa=kappa)
    sim = modelo.simular(red, p, denso=True)
    en = analisis.energias(sim)
    lleg = analisis.llegadas(sim, en)
    Em = analisis.energia_media(sim.t, en.E) / p.E0
    v = analisis.rapidez_frente(lleg.t, red.distancias)[0] / p.omega0

    pd_ = analisis.por_distancia(Em, red.distancias)
    ok = (pd_.d >= 1) & np.isfinite(pd_.media) & (pd_.media > 0)
    pend = np.polyfit(pd_.d[ok], np.log10(pd_.media[ok]), 1)[0] if ok.sum() >= 2 else np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        rel = pd_.sigma_relativa[(pd_.d >= 1) & (pd_.media > 1e-12)]
        het = float(np.nanmedian(rel)) if np.isfinite(rel).any() else np.nan

    return {
        "estudio": estudio, "red": red_nombre, "variante": variante, "kappa": kappa,
        "semilla": semilla, "N": red.N, "R_ohm": R, "factor_calidad": p.factor_calidad,
        "grado_fuente": int(red.grados[red.fuente]), "d_max": red.distancia_maxima,
        "v_sobre_w0": v, "fraccion_alcanzada": (lleg.alcanzado.sum() - 1) / (red.N - 1),
        "tg_ultima_llegada": float(np.nanmax(lleg.t_gamma)),
        "pendiente_log10E_por_d": float(pend), "sigma_rel_mediana": het,
        "fraccion_fuente": float(Em[red.fuente] / Em.sum()),
        "residuo_balance": float(np.abs(en.residuo_balance()).max()),
        "tiempo_s": round(time.perf_counter() - inicio, 2),
    }


def lista_tareas():
    t = []
    for k in KAPPAS:
        for red in redes.TOPOLOGIAS:
            for R in RESISTENCIAS:
                t.append(("gamma", red, R, k, redes.SEMILLA_BASE))
        for L in LADOS_MALLA:
            t.append(("N", "malla", L, k, redes.SEMILLA_BASE))
        for n in N_ANILLO:
            t.append(("N", "anillo", n, k, redes.SEMILLA_BASE))
        for f in ("interior", "borde", "esquina"):
            t.append(("fuente", "malla", f, k, redes.SEMILLA_BASE))
        for s in redes.semillas():
            for f in ("nodo 0", "mayor grado", "menor grado"):
                t.append(("fuente", "erdos_renyi", f, k, s))
    return t


def costo(t):
    """Orden aproximado de costo, para lanzar primero las tareas pesadas."""
    estudio, red, variante, k, _ = t
    n = 100
    if estudio == "N":
        n = variante ** 2 if red == "malla" else variante
    R = variante if estudio == "gamma" else 1.0
    return n * (1 + 3 * k) / R


def main():
    tareas = sorted(lista_tareas(), key=costo, reverse=True)
    print(f"E5: {len(tareas)} simulaciones en {PROCESOS} procesos\n")
    filas, inicio = [], time.perf_counter()
    with ProcessPoolExecutor(max_workers=PROCESOS) as pool:
        futuros = [pool.submit(tarea, *t) for t in tareas]
        for k, fut in enumerate(as_completed(futuros), start=1):
            filas.append(fut.result())
            if k % 25 == 0 or k == len(tareas):
                print(f"  {k:3d}/{len(tareas)} listas ({time.perf_counter() - inicio:5.0f} s)")

    peor = max(f["residuo_balance"] for f in filas)
    print(f"\nControl: residuo máximo del balance de H = {peor:.1e}")
    if peor > 1e-6:
        sys.exit("El control de calidad falla: no se guardan los datos.")
    orden = {"gamma": 0, "N": 1, "fuente": 2}
    filas.sort(key=lambda f: (orden[f["estudio"]], f["red"], f["kappa"], str(f["variante"]),
                              f["semilla"]))
    ruta = resultados.guardar_csv("e5_resumen", filas)

    # Resumen: medianas por (estudio, red, variante, κ).
    print(f"\n{'estudio':7s} {'red':14s} {'variante':>12s} {'κ':>4s} {'v/ω₀':>7s} "
          f"{'alcance':>7s} {'pend.Ē':>7s} {'σ/Ē':>5s} {'frac.f':>6s} {'k₀':>3s}")
    vistos = []
    for f in filas:
        clave = (f["estudio"], f["red"], f["variante"], f["kappa"])
        if clave in vistos:
            continue
        vistos.append(clave)
        g = [x for x in filas if (x["estudio"], x["red"], x["variante"], x["kappa"]) == clave]
        med = lambda c: float(np.nanmedian([x[c] for x in g]))
        print(f"{clave[0]:7s} {clave[1]:14s} {str(clave[2]):>12s} {clave[3]:4g} "
              f"{med('v_sobre_w0'):7.3f} {med('fraccion_alcanzada'):7.2f} "
              f"{med('pendiente_log10E_por_d'):7.3f} {med('sigma_rel_mediana'):5.2f} "
              f"{med('fraccion_fuente'):6.3f} {med('grado_fuente'):3.0f}")
    print(f"\nTiempo total {time.perf_counter() - inicio:.0f} s; resumen en {ruta}")


if __name__ == "__main__":
    main()
