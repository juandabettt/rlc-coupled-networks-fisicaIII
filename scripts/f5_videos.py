"""Fase 5: videos de la propagación (objetivo O11) e imágenes fijas para el informe.

Usa los datos de E1 (Eᵢ(t) de todos los nodos); no simula.

Videos (resultados/videos/, 1920×1080, 24 cuadros/s, 16 s; se generan en
paralelo, un proceso por video):
    v1_kappa_malla.mp4, v1_kappa_anillo.mp4, v1_kappa_mundo_pequeno.mp4,
    v1_kappa_erdos_renyi.mp4
        una red, κ = 0.01, 0.1 y 1 lado a lado (efecto del acoplamiento)
    v2_topologias_k0p1.mp4, v2_topologias_k1.mp4
        las 4 redes lado a lado con el mismo κ (efecto de la topología)

Imágenes fijas (resultados/figuras/): instantes elegidos de los videos v2,
para el informe en PDF y como respaldo en la presentación.

Requiere haber corrido antes:
    python scripts/e1_dinamica.py   (o scripts/fase3_completa.py)

Uso, desde la raíz del proyecto (≈ 4 min):
    python scripts/f5_videos.py            todos los videos e imágenes
    python scripts/f5_videos.py --rapido   solo las imágenes fijas
"""

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from red_rlc import graficos, redes, resultados, videos

KAPPAS = (0.01, 0.1, 1.0)
FPS, DURACION_S = 24, 16.0
NOMBRE_CORTO = {"malla": "Malla 10 × 10", "anillo": "Anillo (k = 4)",
                "mundo_pequeno": "Mundo pequeño", "erdos_renyi": "Erdős–Rényi"}


def panel(red, kappa: float, titulo: str) -> dict:
    meta, x = resultados.cargar_npz(f"e1_{red.nombre}_k{kappa:g}")
    if not np.array_equal(x["distancias"], red.distancias):
        sys.exit(f"La red {red.nombre} no coincide con la de E1: vuelve a correr E1.")
    p = meta["parametros"]
    return {"red": red, "t": x["t"], "E": x["E"].astype(float),
            "E0": p["Q0"] ** 2 / (2 * p["C"]), "gamma": p["R"] / p["L"], "titulo": titulo}


def paneles_de(especificacion: list) -> list:
    """[(red, κ, título), ...] → paneles con los datos de E1."""
    referencia = redes.redes_referencia()
    return [panel(referencia[r], k, titulo) for r, k, titulo in especificacion]


def hacer_video(especificacion: list, nombre: str, titulo: str) -> tuple:
    """Tarea de un proceso: carga sus datos y genera un video."""
    inicio = time.perf_counter()
    ruta = videos.video(paneles_de(especificacion), nombre, titulo, fps=FPS,
                        duracion_s=DURACION_S)
    return ruta, time.perf_counter() - inicio


def main():
    rapido = "--rapido" in sys.argv
    try:
        por_red = {r: paneles_de([(r, k, f"κ = {k:g}") for k in KAPPAS])
                   for r in redes.TOPOLOGIAS}
    except FileNotFoundError:
        sys.exit("Faltan datos de E1. Corre antes: python scripts/e1_dinamica.py")

    def topologias(k):
        return [{**por_red[r][KAPPAS.index(k)], "titulo": NOMBRE_CORTO[r]}
                for r in redes.TOPOLOGIAS]

    rutas = []
    # Imágenes fijas: el frente a mitad de camino y la red ya repartida.
    rutas += videos.cuadro(topologias(0.1), "v2_topologias_k0p1",
                           "Propagación de la energía, κ = 0.1", [0.2, 0.6, 2.0])
    rutas += videos.cuadro(topologias(1.0), "v2_topologias_k1",
                           "Propagación de la energía, κ = 1", [0.05, 0.15])
    rutas += videos.cuadro(por_red["malla"], "v1_kappa_malla",
                           "Malla 10 × 10: efecto del acoplamiento", [0.5, 2.0])

    if not rapido:
        trabajos = [([(r, k, f"κ = {k:g}") for k in KAPPAS], f"v1_kappa_{r}",
                     f"{NOMBRE_CORTO[r]}: efecto del acoplamiento κ = K/ω₀²")
                    for r in redes.TOPOLOGIAS]
        for k, sufijo in ((0.1, "k0p1"), (1.0, "k1")):
            trabajos.append(([(r, k, NOMBRE_CORTO[r]) for r in redes.TOPOLOGIAS],
                             f"v2_topologias_{sufijo}", f"Efecto de la topología, κ = {k:g}"))
        procesos = max(1, min(len(trabajos), (os.cpu_count() or 2) - 2))
        print(f"Generando {len(trabajos)} videos en {procesos} procesos...", flush=True)
        with ProcessPoolExecutor(max_workers=procesos) as pool:
            futuros = [pool.submit(hacer_video, *t) for t in trabajos]
            for fut in as_completed(futuros):
                ruta, s = fut.result()
                rutas.append(ruta)
                print(f"  {Path(ruta).name} ({s:.0f} s)", flush=True)

    print("Guardado:", *rutas, sep="\n  ")


if __name__ == "__main__":
    main()
