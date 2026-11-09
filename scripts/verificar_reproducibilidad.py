"""Verifica que los resultados guardados se pueden reproducir.

Vuelve a correr una muestra de simulaciones del experimento E2 (las 4 redes,
varios κ y semillas de las redes aleatorias), con la misma función que usó E2,
y compara tiempos de llegada y energías medias con los guardados en
resultados/datos/e2_<red>.npz.

Como todo es determinista (semillas fijas, mismo integrador y tolerancias),
las diferencias deben ser del orden del redondeo de punto flotante.

Uso, desde la raíz del proyecto:
    python scripts/verificar_reproducibilidad.py
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import numpy as np

from red_rlc import resultados

TOLERANCIA = 1e-9     # diferencia relativa máxima admitida

MUESTRA = [("malla", 2026, 0.1), ("malla", 2026, 3.0),
           ("anillo", 2026, 0.01), ("anillo", 2026, 1.0),
           ("mundo_pequeno", 2031, 0.1), ("mundo_pequeno", 2050, 10.0),
           ("erdos_renyi", 2026, 0.03), ("erdos_renyi", 2044, 1.0)]


def cargar_e2_script():
    spec = importlib.util.spec_from_file_location("e2", RAIZ / "scripts" / "e2_llegadas.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def dif_relativa(a: np.ndarray, b: np.ndarray) -> float:
    """Máxima diferencia relativa entre valores finitos; inf si difieren los NaN."""
    if not np.array_equal(np.isnan(a), np.isnan(b)):
        return np.inf
    ok = np.isfinite(a) & (np.abs(b) > 0)
    return float(np.max(np.abs(a[ok] - b[ok]) / np.abs(b[ok]))) if ok.any() else 0.0


def main():
    e2 = cargar_e2_script()
    peor = 0.0
    print(f"{'red':14s} {'semilla':>7s} {'κ':>5s} {'Δ t_llegada':>12s} {'Δ ⟨Eᵢ⟩':>10s}")
    for nombre, semilla, kappa in MUESTRA:
        try:
            _, x = resultados.cargar_npz(f"e2_{nombre}")
        except FileNotFoundError:
            sys.exit("Faltan datos de E2. Corre antes: python scripts/e2_llegadas.py")
        i = list(x["kappas"]).index(kappa)
        j = list(x["semillas"]).index(semilla)
        nuevo = e2.tarea(nombre, semilla, kappa)
        dt = dif_relativa(nuevo["t_llegada"], x["t_llegada"][i, j])
        de = dif_relativa(nuevo["E_media"], x["E_media"][i, j])
        peor = max(peor, dt, de)
        print(f"{nombre:14s} {semilla:7d} {kappa:5g} {dt:12.1e} {de:10.1e}")
    print(f"\nMayor diferencia relativa: {peor:.1e} (tolerancia {TOLERANCIA:.0e})")
    print("Reproducibilidad:", "OK" if peor <= TOLERANCIA else "FALLA")
    sys.exit(0 if peor <= TOLERANCIA else 1)


if __name__ == "__main__":
    main()
