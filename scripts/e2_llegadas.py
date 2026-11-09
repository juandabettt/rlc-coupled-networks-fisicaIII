"""E2. Tiempos de llegada frente a la distancia (preguntas P2, P3 y P5).

Qué se varía:
    κ ∈ {0.01, 0.03, 0.1, 0.3, 1, 3, 10}  (KAPPAS_E2 del plan)
    red: malla y anillo (1 realización); mundo pequeño y ER (30 realizaciones,
         semillas 2026 a 2055)
    umbral E_th/E₀ ∈ {10⁻⁴, 10⁻⁶, 10⁻⁸}
El resto de parámetros queda fijo (L = 1 mH, C = 1 µF, R = 1 Ω, T = 10/γ).

Qué se mide, para cada nodo: γtᵢ (NaN si no llega), y para cada simulación
la rapidez media del frente (ajuste lineal de tᵢ frente a dᵢ).

De paso guarda ⟨Eᵢ⟩ de cada nodo: el experimento E3 (energía por distancia)
usa exactamente estas simulaciones y así no hay que repetirlas.

Salidas (en resultados/datos/):
    e2_<red>.npz     — arreglos con ejes [κ, realización, umbral, nodo]
    e2_resumen.csv   — una fila por (red, κ, umbral) con medianas y rangos
                       entre realizaciones

Uso, desde la raíz del proyecto (≈ 3–5 min con 6 procesos):
    python scripts/e2_llegadas.py
"""

import os

# Un hilo de álgebra lineal por proceso: el paralelismo va por simulaciones.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, modelo, redes, resultados

KAPPAS = modelo.KAPPAS_E2
UMBRALES = analisis.UMBRALES
PROCESOS = max(1, min(6, (os.cpu_count() or 2) - 2))


def tarea(nombre: str, semilla: int, kappa: float) -> dict:
    """Una simulación: llegadas para los tres umbrales y ⟨Eᵢ⟩."""
    inicio = time.perf_counter()
    red = redes.construir(nombre, semilla=semilla)
    p = modelo.Parametros(kappa=kappa)
    sim = modelo.simular(red, p, denso=True)
    en = analisis.energias(sim)
    llegadas = np.array([analisis.llegadas(sim, en, umbral=u).t for u in UMBRALES])
    H0_teo = analisis.energia_inicial(p, int(red.grados[red.fuente]))
    return {
        "nombre": nombre, "semilla": semilla, "kappa": kappa,
        "t_llegada": llegadas,
        "E_media": analisis.energia_media(sim.t, en.E),
        "residuo": float(np.abs(en.residuo_balance()).max()),
        "error_H0": abs(en.H[0] - H0_teo) / H0_teo,
        "red": {"distancias": red.distancias, "caminos": red.caminos,
                "grados": red.grados, "fuente": red.fuente, "intentos": red.intentos},
        "tiempo_s": time.perf_counter() - inicio,
    }


def semillas_de(nombre: str) -> list:
    return redes.semillas() if nombre in redes.ALEATORIAS else [redes.SEMILLA_BASE]


def main():
    p = modelo.Parametros()
    tareas = [(n, s, k) for n in redes.TOPOLOGIAS for s in semillas_de(n) for k in KAPPAS]
    # Primero las más costosas (κ grande), para repartir mejor la carga.
    tareas.sort(key=lambda x: -x[2])
    print(f"E2: {len(tareas)} simulaciones en {PROCESOS} procesos, "
          f"κ = {KAPPAS}, umbrales = {UMBRALES}\n")

    salidas = []
    inicio = time.perf_counter()
    with ProcessPoolExecutor(max_workers=PROCESOS) as pool:
        futuros = [pool.submit(tarea, *t) for t in tareas]
        for k, fut in enumerate(as_completed(futuros), start=1):
            salidas.append(fut.result())
            if k % 25 == 0 or k == len(tareas):
                print(f"  {k:3d}/{len(tareas)} listas ({time.perf_counter() - inicio:5.0f} s)")

    # Controles de calidad antes de guardar nada.
    peor_res = max(s["residuo"] for s in salidas)
    peor_H0 = max(s["error_H0"] for s in salidas)
    print(f"\nControles: residuo máx {peor_res:.1e}, error relativo de H(0) máx {peor_H0:.1e}")
    if peor_res > 1e-6 or peor_H0 > 1e-9:
        sys.exit("Los controles de calidad fallan: no se guardan los datos.")

    filas = []
    for nombre in redes.TOPOLOGIAS:
        sem = semillas_de(nombre)
        nk, nr, nu, N = len(KAPPAS), len(sem), len(UMBRALES), redes.N_BASE
        tl = np.full((nk, nr, nu, N), np.nan)
        Em = np.full((nk, nr, N), np.nan)
        residuo = np.full((nk, nr), np.nan)
        tiempo = np.full((nk, nr), np.nan)
        dist = np.zeros((nr, N), int)
        cam = np.zeros((nr, N), np.int64)
        grad = np.zeros((nr, N), int)
        fuente = np.zeros(nr, int)
        intentos = np.zeros(nr, int)
        for s in salidas:
            if s["nombre"] != nombre:
                continue
            i, j = KAPPAS.index(s["kappa"]), sem.index(s["semilla"])
            tl[i, j], Em[i, j] = s["t_llegada"], s["E_media"]
            residuo[i, j], tiempo[i, j] = s["residuo"], s["tiempo_s"]
            r = s["red"]
            dist[j], cam[j], grad[j] = r["distancias"], r["caminos"], r["grados"]
            fuente[j], intentos[j] = r["fuente"], r["intentos"]

        resultados.guardar_npz(
            f"e2_{nombre}",
            meta={"experimento": "E2", "red": nombre, "parametros_base": p,
                  "metodo": "dop853 + raíz con solución densa",
                  "ejes_t_llegada": "[kappa, realizacion, umbral, nodo]",
                  "unidades_t_llegada": "s"},
            kappas=np.array(KAPPAS), umbrales=np.array(UMBRALES),
            semillas=np.array(sem), intentos=intentos,
            t_llegada=tl, E_media=Em, residuo=residuo, tiempo_s=tiempo,
            distancias=dist, caminos=cam, grados=grad, fuente=fuente,
        )

        # Resumen por (κ, umbral): medianas y percentiles 10–90 entre realizaciones.
        for i, kappa in enumerate(KAPPAS):
            for u, umbral in enumerate(UMBRALES):
                alc, tgmax, v, pend = [], [], [], []
                for j in range(nr):
                    t = tl[i, j, u]
                    ok = np.isfinite(t)
                    alc.append(int(ok.sum()) - 1)
                    tgmax.append(p.gamma * np.nanmax(t))
                    vj, bj, _ = analisis.rapidez_frente(t, dist[j])
                    v.append(vj / p.omega0)
                    pend.append(p.gamma * bj)
                alc, tgmax, v, pend = map(np.array, (alc, tgmax, v, pend))
                q = lambda a, x: float(np.nanpercentile(a, x)) if np.isfinite(a).any() else np.nan
                filas.append({
                    "red": nombre, "kappa": kappa, "umbral": umbral, "realizaciones": nr,
                    "alcanzados_mediana": q(alc, 50), "alcanzados_min": int(alc.min()),
                    "alcanzados_max": int(alc.max()), "de": N - 1,
                    "tg_max_mediana": q(tgmax, 50),
                    "pendiente_tg_por_d_mediana": q(pend, 50),
                    "rapidez_sobre_w0_mediana": q(v, 50),
                    "rapidez_sobre_w0_p10": q(v, 10), "rapidez_sobre_w0_p90": q(v, 90),
                })
    ruta = resultados.guardar_csv("e2_resumen", filas)

    print(f"\nTiempo total: {time.perf_counter() - inicio:.0f} s; resumen en {ruta}")
    print("\nUmbral 10⁻⁶: rapidez del frente v/ω₀ (mediana) y nodos alcanzados (mediana)")
    print(f"{'κ':>6s} " + " ".join(f"{n:>22s}" for n in redes.TOPOLOGIAS))
    for kappa in KAPPAS:
        celdas = []
        for nombre in redes.TOPOLOGIAS:
            f = next(x for x in filas if x["red"] == nombre and x["kappa"] == kappa
                     and x["umbral"] == 1e-6)
            celdas.append(f"{f['rapidez_sobre_w0_mediana']:9.4f} {f['alcanzados_mediana']:5.0f}/99")
        print(f"{kappa:6g} " + " ".join(f"{c:>22s}" for c in celdas))


if __name__ == "__main__":
    main()
