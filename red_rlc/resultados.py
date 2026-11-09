"""Rutas de resultados y guardado de datos de los experimentos.

- Datos numéricos: `resultados/datos/` (.npz y .csv; no se versionan).
- Figuras: `resultados/figuras/` (.png y .pdf).
- Videos: `resultados/videos/` (.mp4; no se versionan).

Cada .npz guarda, además de los arreglos, un campo `meta` con un JSON que
describe cómo se generó (experimento, parámetros, semillas, fecha), para que
cada resultado se pueda reproducir.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "resultados" / "datos"
FIGURAS = RAIZ / "resultados" / "figuras"
VIDEOS = RAIZ / "resultados" / "videos"


def _a_json(valor):
    if is_dataclass(valor):
        return asdict(valor)
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        return float(valor)
    if isinstance(valor, np.ndarray):
        return valor.tolist()
    return str(valor)


def guardar_npz(nombre: str, meta: dict, **arreglos) -> Path:
    """Guarda arreglos comprimidos en resultados/datos/<nombre>.npz con su `meta`."""
    DATOS.mkdir(parents=True, exist_ok=True)
    meta = {"generado": datetime.now().isoformat(timespec="seconds"), **meta}
    ruta = DATOS / f"{nombre}.npz"
    np.savez_compressed(ruta, meta=json.dumps(meta, default=_a_json, ensure_ascii=False),
                        **arreglos)
    return ruta


def cargar_npz(nombre: str) -> tuple[dict, dict]:
    """Devuelve (meta, arreglos) de resultados/datos/<nombre>.npz."""
    with np.load(DATOS / f"{nombre}.npz", allow_pickle=False) as f:
        arreglos = {k: f[k] for k in f.files if k != "meta"}
        meta = json.loads(str(f["meta"]))
    return meta, arreglos


def guardar_csv(nombre: str, filas: list[dict]) -> Path:
    """Guarda una tabla (lista de diccionarios) en resultados/datos/<nombre>.csv."""
    DATOS.mkdir(parents=True, exist_ok=True)
    ruta = DATOS / f"{nombre}.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    return ruta
