"""E1. Dinámica: cómo se propaga la perturbación inicial (pregunta P1).

Qué se varía: κ = K/ω₀² ∈ {0.01, 0.03, 0.1, 0.3, 1}, en cada una de las cuatro
redes de referencia (semilla 2026 para las aleatorias). El resto de los
parámetros queda fijo (L = 1 mH, C = 1 µF, R = 1 Ω, Q₀ = 1 µC, T = 10/γ).

Qué se mide: Qᵢ(t), Eᵢ(t) y H(t), más los tiempos de llegada con el umbral
del PDF (10⁻⁶ E₀) para ubicar el frente.

Salidas (en resultados/datos/):
    e1_<red>_k<κ>.npz  — una simulación: t, Eᵢ(t) de todos los nodos, Qᵢ(t)
                          de un nodo representativo por distancia, H, U, ΣRIᵢ²,
                          ⟨Eᵢ⟩, tiempos de llegada y la estructura de la red.
    e1_resumen.csv      — una fila por simulación con los controles de calidad.

Uso, desde la raíz del proyecto:
    python scripts/e1_dinamica.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, modelo, redes, resultados

KAPPAS = modelo.KAPPAS_BASE


def nodos_representativos(red) -> np.ndarray:
    """Un nodo por distancia: el de más caminos más cortos (empate: menor índice).

    Así G3 muestra, para cada d, el nodo al que la señal llega con más fuerza.
    """
    elegidos = []
    for d in range(red.distancia_maxima + 1):
        candidatos = np.flatnonzero(red.distancias == d)
        elegidos.append(candidatos[np.argmax(red.caminos[candidatos])])
    return np.array(elegidos)


def nombre_archivo(red: str, kappa: float) -> str:
    return f"e1_{red}_k{kappa:g}"


def correr(red, p: modelo.Parametros) -> dict:
    """Simula una red con unos parámetros, guarda el .npz y devuelve su resumen."""
    inicio = time.perf_counter()
    sim = modelo.simular(red, p, denso=True)
    en = analisis.energias(sim)
    lleg = analisis.llegadas(sim, en)                  # refina con la solución densa
    Em = analisis.energia_media(sim.t, en.E)
    duracion = time.perf_counter() - inicio

    repr_ = nodos_representativos(red)
    H = en.H
    k0 = int(red.grados[red.fuente])
    H0_teo = analisis.energia_inicial(p, k0)
    alcanzados = int(lleg.alcanzado.sum()) - 1          # sin contar la fuente
    tg = lleg.t_gamma

    resultados.guardar_npz(
        nombre_archivo(red.nombre, p.kappa),
        meta={"experimento": "E1", "red": red.nombre, "semilla": red.semilla,
              "intentos": red.intentos, "parametros": p, "metodo": "dop853",
              "umbral": lleg.umbral, "n_t": sim.t.size},
        t=sim.t, E=en.E.astype(np.float32), H=H, U=en.U, P=en.P,
        nodos_repr=repr_, Q_repr=sim.Q[:, repr_].astype(np.float32),
        E_media=Em, t_llegada=lleg.t,
        distancias=red.distancias, caminos=red.caminos, grados=red.grados,
        fuente=np.array(red.fuente), A=red.A.astype(np.int8),
    )

    return {
        "red": red.nombre, "kappa": p.kappa, "n_t": sim.t.size,
        "tiempo_s": round(duracion, 2), "nfev": sim.info["nfev"],
        "H0_E0": H[0] / p.E0, "H0_teorico_E0": H0_teo / p.E0,
        "max_sumaE_E0": en.suma_nodos.max() / p.E0,
        "U_H_inicial": en.U[0] / H[0],
        "residuo_balance_max": float(np.abs(en.residuo_balance()).max()),
        "H_final_H0": H[-1] / H[0], "e_menos_10": float(np.exp(-p.gamma * p.T)),
        "alcanzados": alcanzados, "de": red.N - 1,
        "tg_llegada_max": float(np.nanmax(tg)),
        "E_fuente_media_E0": Em[red.fuente] / p.E0,
        "fraccion_fuente": float(analisis.fraccion_energia(Em)[red.fuente]),
    }


def main():
    p_base = modelo.Parametros()
    referencia = redes.redes_referencia()
    filas = []
    print(f"E1: {len(referencia)} redes × {len(KAPPAS)} valores de κ, T = {p_base.T * 1e3:g} ms\n")
    print(f"{'red':14s} {'κ':>5s} {'n_t':>6s} {'s':>5s} {'H0/E0':>6s} {'teo':>5s} "
          f"{'máxΣE/E0':>8s} {'residuo':>8s} {'alcanz.':>8s} {'γt máx':>7s} {'frac. fuente':>12s}")
    for nombre, red in referencia.items():
        for kappa in KAPPAS:
            f = correr(red, p_base.con(kappa=kappa))
            filas.append(f)
            print(f"{nombre:14s} {kappa:5g} {f['n_t']:6d} {f['tiempo_s']:5.1f} "
                  f"{f['H0_E0']:6.3f} {f['H0_teorico_E0']:5.2f} {f['max_sumaE_E0']:8.3f} "
                  f"{f['residuo_balance_max']:8.1e} {f['alcanzados']:4d}/{f['de']:<3d} "
                  f"{f['tg_llegada_max']:7.3f} {f['fraccion_fuente']:12.3f}")
    ruta = resultados.guardar_csv("e1_resumen", filas)

    # Controles de calidad: si alguno falla, los datos no se usan.
    problemas = [f for f in filas if f["residuo_balance_max"] > 1e-6
                 or abs(f["H0_E0"] - f["H0_teorico_E0"]) > 1e-9 * f["H0_teorico_E0"]]
    print(f"\nResumen guardado en {ruta}")
    print("Controles de calidad:", "OK" if not problemas else f"FALLAN {len(problemas)}")


if __name__ == "__main__":
    main()
