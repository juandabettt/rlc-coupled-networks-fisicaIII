"""Utilidades compartidas por las pruebas.

`simulacion` guarda en caché cada simulación, para que varias pruebas reutilicen
el mismo resultado sin volver a integrar.
"""

from functools import lru_cache

import pytest

from red_rlc import modelo, redes

REDES = redes.redes_referencia()
P_BASE = modelo.Parametros()


@lru_cache(maxsize=None)
def _simular(nombre: str, kappa: float, R: float, metodo: str, T: float | None):
    p = P_BASE.con(kappa=kappa, R=R)
    return modelo.simular(REDES[nombre], p, metodo=metodo, T=T)


@pytest.fixture(scope="session")
def simulacion():
    """simulacion(nombre, kappa, R=1.0, metodo="dop853", T=None) → Simulacion."""
    def _f(nombre, kappa, R=1.0, metodo="dop853", T=None):
        return _simular(nombre, float(kappa), float(R), metodo, T)
    return _f
