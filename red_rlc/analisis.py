"""Análisis de las simulaciones: energía (Fase 2) y, más adelante, tiempos de
llegada y estadísticas por distancia (Fase 3).

Energía (puntos 2 y 5 de la teoría, Fase 1):

- Energía de cada malla, ecuación (13) del PDF:
      Eᵢ = Qᵢ²/(2C) + L Iᵢ²/2
- Energía guardada en los capacitores de acoplamiento C_c:
      U = (LK/2) Σ_{i<j} Aᵢⱼ (Qᵢ − Qⱼ)² = (LK/2) Qᵀ Λ Q
- Energía total, la única con balance exacto:
      H = Σᵢ Eᵢ + U,      dH/dt = −R Σᵢ Iᵢ²
- Balance de cada malla:
      dEᵢ/dt = −R Iᵢ² + Pᵢ,   Pᵢ = LK Iᵢ Σⱼ Aᵢⱼ (Qⱼ − Qᵢ) = −LK Iᵢ (ΛQ)ᵢ
  Pᵢ es la potencia que la malla i intercambia con sus enlaces (cualquier signo).

ΣEᵢ no es la energía total: con K ≠ 0 no se conserva aunque R = 0, y puede
superar E₀, porque la energía inicial real es H(0) = E₀ (1 + k₀ κ).

Convención: los arreglos por nodo tienen forma (n_t, N); los totales, (n_t,).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import cumulative_simpson, simpson

from .modelo import Parametros, Simulacion


# ---------------------------------------------------------------------------
# Cantidades de energía
# ---------------------------------------------------------------------------

def energia_nodos(Q: np.ndarray, I: np.ndarray, p: Parametros) -> np.ndarray:
    """Eᵢ(t) = Qᵢ²/(2C) + L Iᵢ²/2 (J), ecuación (13) del PDF. Forma (n_t, N)."""
    return Q**2 / (2 * p.C) + p.L * I**2 / 2


def energia_acoplamiento(Q: np.ndarray, Lambda: np.ndarray, p: Parametros) -> np.ndarray:
    """U(t) = (LK/2) Qᵀ Λ Q (J): energía en los capacitores C_c. Forma (n_t,)."""
    return p.L * p.K / 2 * np.einsum("ti,ti->t", Q @ Lambda, Q)


def potencia_disipada(I: np.ndarray, p: Parametros) -> np.ndarray:
    """R Σᵢ Iᵢ² (W): calor generado en las resistencias. Forma (n_t,)."""
    return p.R * np.sum(I**2, axis=1)


def potencia_intercambio(Q: np.ndarray, I: np.ndarray, Lambda: np.ndarray,
                         p: Parametros) -> np.ndarray:
    """Pᵢ = −LK Iᵢ (ΛQ)ᵢ (W): potencia que cada malla recibe de sus enlaces.

    Positiva cuando la malla gana energía del acoplamiento. Forma (n_t, N).
    """
    return -p.L * p.K * I * (Q @ Lambda)


def energia_inicial(p: Parametros, grado_fuente: int) -> float:
    """H(0) = E₀ (1 + k₀ κ) con las condiciones del PDF (punto 5, paso 12)."""
    return p.E0 * (1 + grado_fuente * p.kappa)


# ---------------------------------------------------------------------------
# Paquete de energías de una simulación
# ---------------------------------------------------------------------------

@dataclass
class Energias:
    """Todas las energías de una simulación, en joules.

    Atributos
    ---------
    t : instantes (s).
    E : Eᵢ(t), forma (n_t, N).
    U : energía de acoplamiento, forma (n_t,).
    P : potencia disipada R Σ Iᵢ², forma (n_t,).
    E0 : energía de referencia del PDF, Q₀²/(2C).
    """

    t: np.ndarray = field(repr=False)
    E: np.ndarray = field(repr=False)
    U: np.ndarray = field(repr=False)
    P: np.ndarray = field(repr=False)
    E0: float

    @property
    def suma_nodos(self) -> np.ndarray:
        """Σᵢ Eᵢ(t). No es la energía total."""
        return self.E.sum(axis=1)

    @property
    def H(self) -> np.ndarray:
        """H(t) = Σᵢ Eᵢ + U: energía total."""
        return self.suma_nodos + self.U

    @property
    def E_rel(self) -> np.ndarray:
        """Eᵢ/E₀, la normalización del PDF."""
        return self.E / self.E0

    @property
    def disipada(self) -> np.ndarray:
        """Energía acumulada convertida en calor, ∫₀ᵗ R Σ Iᵢ² dt' (J).

        Usa la regla de Simpson acumulada (error ∝ h⁴), más precisa que el
        trapecio que se usó en la prueba de la Fase 1.
        """
        return cumulative_simpson(self.P, x=self.t, initial=0.0)

    def residuo_balance(self) -> np.ndarray:
        """[H(t) + ∫₀ᵗ R Σ Iᵢ² − H(0)] / H(0).

        Es la forma integrada de dH/dt = −R Σ Iᵢ²: debe ser ≈ 0 en todo t.
        """
        H = self.H
        return (H + self.disipada - H[0]) / H[0]


def energias(sim: Simulacion) -> Energias:
    """Calcula todas las energías de una simulación."""
    p = sim.parametros
    return Energias(
        t=sim.t,
        E=energia_nodos(sim.Q, sim.I, p),
        U=energia_acoplamiento(sim.Q, sim.Lambda, p),
        P=potencia_disipada(sim.I, p),
        E0=p.E0,
    )


# ---------------------------------------------------------------------------
# Promedios temporales
# ---------------------------------------------------------------------------

def energia_media(t: np.ndarray, E: np.ndarray) -> np.ndarray:
    """⟨Eᵢ⟩ = (1/T) ∫₀ᵀ Eᵢ dt, ecuación (16) del PDF, con la regla de Simpson.

    Depende de T, así que T debe ser igual en todas las comparaciones.
    Para E de forma (n_t, N) devuelve un arreglo (N,).
    """
    T = t[-1] - t[0]
    return simpson(E, x=t, axis=0) / T


def fraccion_energia(E_media: np.ndarray) -> np.ndarray:
    """⟨Eᵢ⟩ / Σⱼ ⟨Eⱼ⟩: reparto relativo entre nodos (sí suma 1).

    Es el apoyo que propone la teoría (punto 5), porque ⟨Eᵢ⟩/E₀ no es una
    fracción de energía.
    """
    return E_media / E_media.sum()
