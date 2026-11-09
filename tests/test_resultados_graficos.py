"""Pruebas del guardado de resultados y de la generación de figuras."""

import numpy as np

from red_rlc import analisis, graficos, modelo, resultados
from conftest import REDES


def test_guardar_y_cargar_npz(tmp_path, monkeypatch):
    monkeypatch.setattr(resultados, "DATOS", tmp_path)
    p = modelo.Parametros(kappa=0.3)
    resultados.guardar_npz("prueba", {"experimento": "X", "parametros": p},
                           a=np.arange(3), b=np.eye(2, dtype=np.float32))
    meta, arr = resultados.cargar_npz("prueba")
    assert meta["experimento"] == "X"
    assert meta["parametros"]["kappa"] == 0.3        # dataclass convertido a dict
    assert "generado" in meta
    assert arr["a"].tolist() == [0, 1, 2]
    assert arr["b"].dtype == np.float32


def test_guardar_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(resultados, "DATOS", tmp_path)
    ruta = resultados.guardar_csv("tabla", [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}])
    assert ruta.read_text(encoding="utf-8").splitlines() == ["x,y", "1,a", "2,b"]


def test_colores_fijos_por_red():
    assert len(set(graficos.COLOR_RED.values())) == 4


def test_g3_g4_se_generan(tmp_path, monkeypatch):
    """G3 y G4 con el mismo formato de datos que guarda E1 (simulación corta)."""
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    red = REDES["anillo"]
    p = modelo.Parametros(kappa=0.3)
    sim = modelo.simular(red, p, "modal", T=2e-3, puntos_por_periodo=20)
    en = analisis.energias(sim)
    repr_ = np.array([np.flatnonzero(red.distancias == d)[0]
                      for d in range(red.distancia_maxima + 1)])
    x = {"t": sim.t, "E": en.E, "H": en.H, "nodos_repr": repr_,
         "distancias": red.distancias, "caminos": red.caminos,
         "t_llegada": analisis.llegadas(sim, en).t, "fuente": np.array(red.fuente),
         "gamma": p.gamma, "E0": p.E0}
    datos = {("anillo", 0.3): x}
    for fig, nombre in ((graficos.g3_energia_por_distancia(datos, ["anillo"], [0.3]), "g3"),
                        (graficos.g4_mapa_nodo_tiempo(datos, ["anillo"], [0.3]), "g4")):
        ruta = graficos.guardar(fig, nombre, formatos=("png",), dpi=50)[0]
        assert ruta.stat().st_size > 5_000


def test_texto_umbral():
    assert graficos._texto_umbral(1e-6) == "10⁻⁶"
    assert graficos._texto_umbral(1e-10) == "10⁻¹⁰"


def test_g5_g6_se_generan(tmp_path, monkeypatch):
    """G5 y G6 con el mismo formato de datos que guarda E2 (2 κ, 2 realizaciones)."""
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    p = modelo.Parametros()
    datos = {}
    for nombre in ("malla", "anillo"):
        red = REDES[nombre]
        kappas, umbrales = (0.1, 1.0), analisis.UMBRALES
        tl = np.empty((2, 2, 3, red.N))
        for i, k in enumerate(kappas):
            sim = modelo.simular(red, p.con(kappa=k), "modal", T=3e-3, puntos_por_periodo=20)
            en = analisis.energias(sim)
            for u, um in enumerate(umbrales):
                tl[i, :, u] = analisis.llegadas(sim, en, umbral=um).t
        datos[nombre] = {"kappas": np.array(kappas), "umbrales": np.array(umbrales),
                         "t_llegada": tl, "distancias": np.tile(red.distancias, (2, 1)),
                         "semillas": np.array([1, 2]), "gamma": p.gamma, "omega0": p.omega0}
        datos[nombre]["_rapidez"] = graficos.rapideces(datos[nombre])
        assert np.all(np.isfinite(datos[nombre]["_rapidez"]))
    for fig, nombre in ((graficos.g5_llegada_vs_distancia(datos, list(datos), [0.1, 1.0]), "g5"),
                        (graficos.g6_rapidez_vs_kappa(datos, list(datos)), "g6")):
        ruta = graficos.guardar(fig, nombre, formatos=("png",), dpi=50)[0]
        assert ruta.stat().st_size > 5_000


def test_g7_g8_se_generan(tmp_path, monkeypatch):
    """G7 y G8 con el mismo formato de datos que guarda E3 (2 κ, 2 realizaciones)."""
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    p = modelo.Parametros()
    datos = {}
    for nombre in ("malla", "anillo"):
        red = REDES[nombre]
        kappas = (0.1, 1.0)
        dist = np.tile(red.distancias, (2, 1))
        E_rel = np.empty((2, 2, red.N))
        media = np.empty((2, 2, red.distancia_maxima + 1))
        sigma = np.empty_like(media)
        for i, k in enumerate(kappas):
            sim = modelo.simular(red, p.con(kappa=k), "modal", T=3e-3, puntos_por_periodo=20)
            Em = analisis.energia_media(sim.t, analisis.energias(sim).E) / p.E0
            E_rel[i] = Em
            r = analisis.por_distancia_realizaciones(E_rel[i], dist)
            media[i], sigma[i] = r["media"], r["sigma"]
        datos[nombre] = {"kappas": np.array(kappas), "d": r["d"], "N_d": r["N_d"],
                         "media": media, "sigma": sigma, "E_rel": E_rel, "distancias": dist}
    for fig, nombre in ((graficos.g7_energia_media_vs_distancia(datos, list(datos), [0.1, 1.0]), "g7"),
                        (graficos.g8_heterogeneidad(datos, list(datos), [0.1, 1.0]), "g8")):
        ruta = graficos.guardar(fig, nombre, formatos=("png",), dpi=50)[0]
        assert ruta.stat().st_size > 5_000


def test_g9_se_genera(tmp_path, monkeypatch):
    """G9 con el formato de E4, incluido un predictor constante (grado del anillo)."""
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    p = modelo.Parametros()
    datos = {}
    for nombre in ("malla", "anillo"):
        red = REDES[nombre]
        kappas = (0.01, 0.1, 1.0)
        tg = np.empty((3, 1, red.N))
        E = np.empty((3, 1, red.N))
        for i, k in enumerate(kappas):
            sim = modelo.simular(red, p.con(kappa=k), "modal", T=3e-3, puntos_por_periodo=20)
            en = analisis.energias(sim)
            tg[i, 0] = p.gamma * analisis.llegadas(sim, en).t
            E[i, 0] = analisis.energia_media(sim.t, en.E) / p.E0
        datos[nombre] = {"kappas": np.array(kappas), "t_gamma": tg, "E_rel": E,
                         "distancias": red.distancias[None], "caminos": red.caminos[None],
                         "grados": red.grados[None],
                         "peso_modal": analisis.peso_modal_incoherente(red.laplaciano,
                                                                       red.fuente)[None]}
    fig = graficos.g9_posicion(datos, ["malla", "anillo"])
    ruta = graficos.guardar(fig, "g9", formatos=("png",), dpi=50)[0]
    assert ruta.stat().st_size > 5_000


def test_g2_se_genera(tmp_path, monkeypatch):
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    tg = np.linspace(0, 10, 200)
    energia = {"tg": tg, "H": 5 * np.exp(-tg), "suma_E": 4 * np.exp(-tg),
               "H_teo": 5 * np.exp(-tg), "titulo": "prueba"}
    balance = {"malla": (tg, 1e-8 * np.sin(tg))}
    referencia = {"malla": (np.array([0.1, 1.0]), np.array([1e-9, 2e-9]))}
    convergencia = {"h": [4e-6, 2e-6, 1e-6], "error": [1.6e-3, 1e-4, 6.25e-6]}
    fig = graficos.g2_validacion(balance, energia, referencia, convergencia)
    ruta = graficos.guardar(fig, "g2", formatos=("png",), dpi=50)[0]
    assert ruta.stat().st_size > 5_000


def test_figura_ajustes_se_genera(tmp_path, monkeypatch):
    from red_rlc import ajustes
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    d = np.repeat(np.arange(1, 9), 6).astype(float)
    y = 0.05 * d**1.5 + np.random.default_rng(6).normal(0, 0.01, d.size)
    curvas, residuos = {}, {}
    for a in ajustes.comparar(ajustes.MODELOS_T, d, y):
        curvas[a.nombre] = (np.linspace(1, 8, 50), a.predecir(np.linspace(1, 8, 50)))
        ux = np.unique(a.x)
        residuos[a.nombre] = (ux, np.array([np.median(a.residuos[a.x == v]) for v in ux]))
    panel = {"x": d, "y": y, "color": graficos.CATEGORICA[0], "curvas": curvas,
             "residuos": residuos, "texto": "prueba", "etiqueta": "κ = 0.1"}
    fig = graficos.figura_ajustes([[panel, panel]], ["a", "b"], "prueba", ["y"], "r", "d",
                                  orden_modelos=["potencia", "lineal", "logarítmico"])
    ruta = graficos.guardar(fig, "fa", formatos=("png",), dpi=50)[0]
    assert ruta.stat().st_size > 5_000


def test_g10_se_genera(tmp_path, monkeypatch):
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    redes_ = ["malla", "erdos_renyi"]
    metricas = [
        {"titulo": "dos series", "ylabel": "y", "log": True,
         "valores": {"malla": {"κ = 0.1": [0.2], "κ = 1": [1.7]},
                     "erdos_renyi": {"κ = 0.1": [0.2, 0.3, 0.4], "κ = 1": [1.5, 2.0, 2.4]}}},
        {"titulo": "una serie", "ylabel": "y",
         "valores": {"malla": {"κ = 0.01": [0.4]}, "erdos_renyi": {"κ = 0.01": [0.5, 0.9]}}},
    ]
    fig = graficos.g10_topologias(metricas, redes_, columnas=2)
    ruta = graficos.guardar(fig, "g10", formatos=("png",), dpi=50)[0]
    assert ruta.stat().st_size > 5_000


def test_relativo_al_grupo():
    dist = np.array([[0, 1, 1, 2, 2]])
    V = np.array([[5.0, 1.0, 4.0, 3.0, 3.0]])
    R = graficos._relativo_al_grupo(V, dist)
    assert np.isnan(R[0, 0])                               # la fuente no entra
    assert np.allclose(R[0, 1:], [0.5, 2.0, 1.0, 1.0])     # media geométrica de 1 y 4 = 2


def test_agrupar_maximo_conserva_picos():
    t = np.arange(10.0)
    M = np.array([0, 5, 0, 0, 7, 0, 0, 0, 9, 0], dtype=float)[:, None]
    tb, Mb = graficos._agrupar_maximo(t, M, 5)
    assert Mb[:, 0].tolist() == [5, 0, 7, 0, 9]
    assert tb.tolist() == [0, 2, 4, 6, 8]


def test_g1_se_genera(tmp_path, monkeypatch):
    monkeypatch.setattr(graficos, "FIGURAS", tmp_path)
    fig = graficos.g1_redes(REDES)
    rutas = graficos.guardar(fig, "g1_prueba", formatos=("png",), dpi=60)
    assert rutas[0].exists() and rutas[0].stat().st_size > 10_000
