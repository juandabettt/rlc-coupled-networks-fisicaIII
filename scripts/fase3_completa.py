"""Regenera todos los resultados de la Fase 3, en orden, y verifica la
reproducibilidad.

Orden (cada paso usa los datos del anterior cuando hace falta):

    g1_redes            G1  topologías (no simula)
    g2_validacion       G2  validación del código
    e1_dinamica         E1  dinámica (20 simulaciones)
    g3_g4_dinamica      G3, G4 con los datos de E1
    e2_llegadas         E2  tiempos de llegada (434 simulaciones, en paralelo)
    g5_g6_llegadas      G5, G6 con los datos de E2
    e3_energia_distancia E3 con los datos de E2
    g7_g8_energia       G7, G8 con los datos de E3
    e4_posicion         E4 con los datos de E2
    g9_posicion         G9 con los datos de E4
    e5_sensibilidad     E5  sensibilidad (234 simulaciones, en paralelo)
    g10_topologias      G10 con los datos de E2 y E3
    verificar_reproducibilidad

Primero corre las pruebas automáticas: si alguna falla, no genera nada (regla
del plan: ningún resultado se analiza antes de pasar las pruebas).

Uso, desde la raíz del proyecto (≈ 15 min; la última ejecución tardó 920 s):
    python scripts/fase3_completa.py
"""

import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PASOS = ["g1_redes", "g2_validacion", "e1_dinamica", "g3_g4_dinamica", "e2_llegadas",
         "g5_g6_llegadas", "e3_energia_distancia", "g7_g8_energia", "e4_posicion",
         "g9_posicion", "e5_sensibilidad", "g10_topologias", "verificar_reproducibilidad"]


def correr(args: list, nombre: str) -> float:
    inicio = time.perf_counter()
    print(f"\n=== {nombre} ===", flush=True)
    r = subprocess.run([sys.executable, *args], cwd=RAIZ)
    duracion = time.perf_counter() - inicio
    if r.returncode != 0:
        sys.exit(f"\n{nombre} falló (código {r.returncode}); se detiene la Fase 3.")
    return duracion


def main():
    tiempos = {"pruebas": correr(["-m", "pytest", "-q"], "pruebas automáticas")}
    for paso in PASOS:
        tiempos[paso] = correr([str(RAIZ / "scripts" / f"{paso}.py")], paso)
    print("\nResumen de tiempos")
    for paso, s in tiempos.items():
        print(f"  {paso:28s} {s:7.1f} s")
    print(f"  {'total':28s} {sum(tiempos.values()):7.1f} s")


if __name__ == "__main__":
    main()
