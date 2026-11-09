"""Ajustes funcionales y comparación de modelos (Fase 4).

Reglas del plan («Ajustes funcionales»):

- Modelos de dos parámetros como máximo: ER ofrece pocas distancias y un modelo
  mayor quedaría mal determinado.
- Comparación con AICc y con los residuos, no solo con R².
- σ_E(d) no se usa como barra de error ni como peso: no es error experimental.
  Los ajustes se hacen sobre los datos de cada nodo.
- Ē(d) y σ_E(d) se ajustan en log₁₀, porque abarcan varias décadas.

Modelos (cada uno con su espacio de ajuste; AICc solo compara modelos que
ajustan la misma variable en el mismo espacio):

    tγ(d)   lineal      γt = a + b·d
            potencia    γt = a·d^b
            logarítmico γt = a + b·ln d
    E(d)    exponencial log₁₀E = a + b·d          (E ∝ 10^(b·d))
            potencia    log₁₀E = a + b·log₁₀d     (E ∝ d^b)
    v(κ)    potencia    log₁₀v = a + b·log₁₀κ
            por tramos  v = A·κ (κ ≤ κc), A·√(κc·κ) (κ > κc): exponentes 1 y ½
                        fijos por la teoría; parámetros A y κc
            suave       v = A·κ/√(1 + κ/κc): mismos límites, transición continua

AICc (Burnham y Anderson, 2002), con k parámetros del modelo más la varianza
del residuo:
    AICc = n·ln(RSS/n) + 2k' + 2k'(k'+1)/(n − k' − 1),   k' = k + 1
El mejor modelo tiene ΔAICc = 0; ΔAICc < 2 se considera apoyo equivalente y
ΔAICc > 10, apoyo prácticamente nulo. Los pesos de Akaike, w = e^(−Δ/2)/Σ,
resumen la evidencia relativa.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Modelo:
    """Un modelo de dos parámetros, en el espacio donde se ajusta.

    f(x, a, b) predice la variable transformada (γt, log₁₀E o log₁₀v).
    inicial(x, y) da valores de partida para el ajuste no lineal.
    """

    nombre: str
    formula: str
    f: Callable
    inicial: Callable
    parametros: tuple = ("a", "b")


def _recta(x, y):
    b, a = np.polyfit(x, y, 1)
    return a, b


# tγ(d): se ajusta en la escala original de γt.
T_LINEAL = Modelo("lineal", "γt = a + b·d", lambda d, a, b: a + b * d, _recta)
T_POTENCIA = Modelo(
    "potencia", "γt = a·d^b", lambda d, a, b: a * np.power(d, b),
    lambda d, y: (lambda a, b: (np.exp(a), b))(*_recta(np.log(d), np.log(np.maximum(y, 1e-300)))))
T_LOG = Modelo("logarítmico", "γt = a + b·ln d", lambda d, a, b: a + b * np.log(d),
               lambda d, y: _recta(np.log(d), y))
MODELOS_T = (T_LINEAL, T_POTENCIA, T_LOG)

# E(d) y σ(d): se ajustan en log₁₀.
E_EXPONENCIAL = Modelo("exponencial", "log₁₀E = a + b·d", lambda d, a, b: a + b * d, _recta)
E_POTENCIA = Modelo("potencia", "log₁₀E = a + b·log₁₀d", lambda d, a, b: a + b * np.log10(d),
                    lambda d, y: _recta(np.log10(d), y))
MODELOS_E = (E_EXPONENCIAL, E_POTENCIA)


# v(κ): se ajusta en log₁₀v; κ entra en escala original.
def _v_tramos(k, logA, logkc):
    A, kc = 10.0**logA, 10.0**logkc
    return np.log10(np.where(k <= kc, A * k, A * np.sqrt(kc * k)))


def _v_suave(k, logA, logkc):
    A, kc = 10.0**logA, 10.0**logkc
    return np.log10(A * k / np.sqrt(1 + k / kc))


def _inicial_v(k, y):
    # A ≈ v/κ en el κ más pequeño; κc ≈ 1 (transición observada en E2).
    return y[np.argmin(k)] - np.log10(k.min()), 0.0


V_POTENCIA = Modelo("potencia", "log₁₀v = a + b·log₁₀κ", lambda k, a, b: a + b * np.log10(k),
                    lambda k, y: _recta(np.log10(k), y))
V_TRAMOS = Modelo("por tramos (1 y ½)", "v = Aκ si κ ≤ κc; A√(κc κ) si κ > κc", _v_tramos,
                  _inicial_v, ("log₁₀A", "log₁₀κc"))
V_SUAVE = Modelo("transición suave", "v = Aκ/√(1 + κ/κc)", _v_suave, _inicial_v,
                 ("log₁₀A", "log₁₀κc"))
MODELOS_V = (V_POTENCIA, V_TRAMOS, V_SUAVE)


# ---------------------------------------------------------------------------
# Ajuste y comparación
# ---------------------------------------------------------------------------

def aicc(rss: float, n: int, k: int) -> float:
    """AICc para mínimos cuadrados con k parámetros (más la varianza del residuo)."""
    kk = k + 1
    if n - kk - 1 <= 0 or rss <= 0:
        return np.nan
    return n * np.log(rss / n) + 2 * kk + 2 * kk * (kk + 1) / (n - kk - 1)


@dataclass
class Ajuste:
    """Resultado de ajustar un modelo a (x, y), con y ya en el espacio del modelo."""

    modelo: Modelo
    p: np.ndarray
    error_p: np.ndarray
    n: int
    rss: float
    aicc: float
    r2: float
    residuos: np.ndarray = field(repr=False)
    x: np.ndarray = field(repr=False)
    delta: float = np.nan        # ΔAICc respecto del mejor modelo comparado
    peso: float = np.nan         # peso de Akaike

    @property
    def nombre(self) -> str:
        return self.modelo.nombre

    def predecir(self, x) -> np.ndarray:
        return self.modelo.f(np.asarray(x, float), *self.p)

    def parametros(self) -> dict:
        return {n: (float(v), float(e)) for n, v, e in
                zip(self.modelo.parametros, self.p, self.error_p)}


def ajustar(modelo: Modelo, x, y) -> Ajuste | None:
    """Ajusta por mínimos cuadrados. Devuelve None si no hay datos suficientes
    (al menos 4 puntos y 2 valores distintos de x) o si el ajuste no converge."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 4 or np.unique(x).size < 2:
        return None
    try:
        p0 = modelo.inicial(x, y)
        with warnings.catch_warnings():
            # Con residuo exactamente cero la covarianza no se puede estimar:
            # los errores de los parámetros quedan en NaN.
            warnings.simplefilter("ignore", OptimizeWarning)
            p, cov = curve_fit(modelo.f, x, y, p0=p0, maxfev=20_000)
    except (RuntimeError, ValueError, TypeError):
        return None
    pred = modelo.f(x, *p)
    if not np.all(np.isfinite(pred)):
        return None
    res = y - pred
    rss = float(res @ res)
    sst = float(((y - y.mean()) ** 2).sum())
    err = np.sqrt(np.diag(cov)) if np.all(np.isfinite(cov)) else np.full(len(p), np.nan)
    return Ajuste(modelo, np.asarray(p), err, x.size, rss, aicc(rss, x.size, len(p)),
                  1 - rss / sst if sst > 0 else np.nan, res, x)


def comparar(modelos, x, y) -> list[Ajuste]:
    """Ajusta todos los modelos y los ordena por AICc, con ΔAICc y pesos de Akaike."""
    ajustes = [a for a in (ajustar(m, x, y) for m in modelos) if a is not None
               and np.isfinite(a.aicc)]
    if not ajustes:
        return []
    ajustes.sort(key=lambda a: a.aicc)
    mejor = ajustes[0].aicc
    for a in ajustes:
        a.delta = a.aicc - mejor
    w = np.exp(-0.5 * np.array([a.delta for a in ajustes]))
    for a, wi in zip(ajustes, w / w.sum()):
        a.peso = float(wi)
    return ajustes


def desviacion_en_d1(ajuste_sin_d1: Ajuste, d, y) -> float:
    """Cuánto se aparta d = 1 de la tendencia ajustada sin d = 1.

    Devuelve el residuo medio en d = 1 dividido por la desviación estándar de
    los residuos del ajuste (en unidades de esa dispersión). El plan pide
    «revisar si d = 1 se desvía de la tendencia» en tγ(d).
    """
    d, y = np.asarray(d, float), np.asarray(y, float)
    m = (d == 1) & np.isfinite(y)
    if not m.any() or ajuste_sin_d1.n < 3:
        return np.nan
    s = np.sqrt(ajuste_sin_d1.rss / (ajuste_sin_d1.n - 2))
    return float(np.mean(y[m] - ajuste_sin_d1.predecir(d[m])) / s) if s > 0 else np.nan
