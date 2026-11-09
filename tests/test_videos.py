"""Pruebas de red_rlc.videos: tiempos de los cuadros, envolvente y generación."""

import numpy as np
import pytest

from red_rlc import analisis, modelo, videos
from conftest import REDES


def test_tiempos_cuadros_cubicos():
    tc = videos.tiempos_cuadros(10.0, 11)
    assert tc[0] == 0 and tc[-1] == pytest.approx(10.0)
    assert np.all(np.diff(tc) > 0)
    assert tc[5] == pytest.approx(10.0 * 0.5**3)        # mitad del video → 1/8 de T


def test_energia_por_cuadro_toma_el_maximo_entre_cuadros():
    t = np.arange(10.0)
    E = np.array([0, 1, 5, 2, 0, 0, 7, 0, 0, 3], float)[:, None]
    tc = np.array([0.0, 3.0, 6.0, 9.0])
    v = videos.energia_por_cuadro(t, E, tc)[:, 0]
    assert v.tolist() == [0.0, 5.0, 7.0, 3.0]            # máximos de (0,3], (3,6], (6,9]


def test_energia_por_cuadro_sin_muestras_en_el_intervalo():
    t = np.array([0.0, 1.0, 2.0])
    E = np.array([[1.0], [2.0], [3.0]])
    v = videos.energia_por_cuadro(t, E, np.array([0.0, 1.2, 1.4]))
    assert v[2, 0] == 3.0                                # usa la muestra más cercana posterior


def test_log_relativa_con_piso():
    v = videos.log_relativa(np.array([0.0, 1e-3, 1.0]), 1.0)
    assert v[1] == pytest.approx(-3.0) and v[2] == pytest.approx(0.0)
    assert np.isfinite(v[0]) and v[0] < videos.LOG_MIN


def test_video_y_cuadro_se_generan(tmp_path, monkeypatch):
    from red_rlc import graficos
    monkeypatch.setattr(videos, "VIDEOS", tmp_path)
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    red = REDES["anillo"]
    p = modelo.Parametros(kappa=0.3)
    sim = modelo.simular(red, p, "modal", T=1e-3, puntos_por_periodo=20)
    E = analisis.energias(sim).E
    panel = {"red": red, "t": sim.t, "E": E, "E0": p.E0, "gamma": p.gamma, "titulo": "prueba"}
    ruta = videos.video([panel, panel], "prueba", "prueba", fps=4, duracion_s=1.0, dpi=40)
    assert tmp_path.joinpath("prueba.mp4").stat().st_size > 1_000
    assert ruta.endswith("prueba.mp4")
    rutas = videos.cuadro([panel], "fijo", "prueba", [0.5])
    assert rutas[0].exists()
