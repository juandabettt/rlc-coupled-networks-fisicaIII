"""G2: validación del código (balance de H, solución modal y convergencia de RK4).

Resume en una figura las pruebas de validación del plan, que además corren como
pruebas automáticas (tests/test_modelo.py y tests/test_energia.py):

    (a) H(t) decae como H(0)e^(−γt) y ΣEᵢ no es la energía total (malla, κ = 1)
    (b) residuo del balance integrado de H en las 4 redes (κ = 0.1)
    (c) error de DOP853 frente a la solución exacta por modos normales, en las
        4 redes y los 7 valores de κ del plan
    (d) convergencia de RK4: el error baja como h⁴

Genera sus propias simulaciones (≈ 1 min); no necesita otros datos.

Salidas:
    resultados/figuras/g2_validacion.png y .pdf
    resultados/datos/g2_validacion.csv  (errores de la referencia y de RK4)

Uso, desde la raíz del proyecto:
    python scripts/g2_validacion.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import analisis, graficos, modelo, redes, resultados


def main():
    p0 = modelo.Parametros()
    ref = redes.redes_referencia()
    filas = []

    # (a) energía total frente a suma de energías de malla
    sim = modelo.simular(ref["malla"], p0.con(kappa=1.0))
    en = analisis.energias(sim)
    energia = {"tg": sim.t_gamma, "H": en.H / p0.E0, "suma_E": en.suma_nodos / p0.E0,
               "H_teo": en.H[0] / p0.E0 * np.exp(-sim.t_gamma),
               "titulo": "Energía total y suma de Eᵢ (malla, κ = 1)"}

    # (b) balance de H
    balance = {}
    for nombre, red in ref.items():
        s = modelo.simular(red, p0.con(kappa=0.1))
        balance[nombre] = (s.t_gamma, analisis.energias(s).residuo_balance())

    # (c) DOP853 frente a la solución modal
    referencia = {}
    for nombre, red in ref.items():
        errores = []
        for k in modelo.KAPPAS_E2:
            p = p0.con(kappa=k)
            a = modelo.simular(red, p)
            b = modelo.simular(red, p, "modal", t=a.t)
            e = float(np.abs(a.Q - b.Q).max() / p.Q0)
            errores.append(e)
            filas.append({"prueba": "referencia_modal", "red": nombre, "kappa": k,
                          "h_s": "", "error_Q_sobre_Q0": e})
        referencia[nombre] = (np.array(modelo.KAPPAS_E2), np.array(errores))

    # (d) convergencia de RK4 (mismo caso que tests/test_modelo.py)
    red = ref["malla"]
    p = p0.con(kappa=1.0)
    t = modelo.malla_temporal(2e-3, modelo.omega_maxima(red.laplaciano, p), 10)
    exacta = modelo.simular(red, p, "modal", t=t)
    hs, errs = [], []
    for sub in (1, 2, 4, 8, 16):
        s = modelo.simular(red, p, "rk4", t=t, subpasos=sub)
        hs.append(s.info["h"])
        errs.append(float(np.abs(s.Q - exacta.Q).max() / p.Q0))
        filas.append({"prueba": "convergencia_rk4", "red": "malla", "kappa": 1.0,
                      "h_s": hs[-1], "error_Q_sobre_Q0": errs[-1]})
    convergencia = {"h": hs, "error": errs,
                    "titulo": "Convergencia de RK4 (malla, κ = 1, 2 ms)"}

    ruta = resultados.guardar_csv("g2_validacion", filas)
    rutas = graficos.guardar(graficos.g2_validacion(balance, energia, referencia, convergencia),
                             "g2_validacion")

    print(f"Residuo máximo del balance (κ = 0.1): "
          f"{max(np.abs(r).max() for _, r in balance.values()):.1e}")
    print(f"Error máximo DOP853 frente a modal: "
          f"{max(e.max() for _, e in referencia.values()):.1e} Q₀")
    print("Órdenes de RK4:", np.round(np.log2(np.array(errs[:-1]) / np.array(errs[1:])), 2))
    print("Guardado:", ruta, *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
