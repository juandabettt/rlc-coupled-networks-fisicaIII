"""Análisis de las simulaciones: energía, tiempos de llegada y estadísticas por
distancia.

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

Tiempo de llegada, ecuación (20) del PDF: primer instante tᵢ en que
Eᵢ(t) ≥ E_th = u · E₀ (u = 10⁻⁶ por defecto). No mide un frente físico exacto
(teoría, punto 7): depende del umbral, y un nodo puede no alcanzarlo nunca por
el amortiguamiento. Esos nodos se marcan como no alcanzados (NaN), sin
asignarles T ni cero.

Estadísticas por distancia, ecuaciones (21)–(23) del PDF: para cada d,
Ē(d) es la media de ⟨Eᵢ⟩ sobre los N_d nodos a esa distancia, y σ_E(d) su
desviación estándar con ddof = 1, que no está definida si N_d = 1.

Convención: los arreglos por nodo tienen forma (n_t, N); los totales, (n_t,).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import cumulative_simpson, simpson
from scipy.optimize import brentq
from scipy.stats import spearmanr

from .modelo import Modos, Parametros, Simulacion, modos_normales, solucion_modal


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


# ---------------------------------------------------------------------------
# Tiempos de llegada
# ---------------------------------------------------------------------------

# Umbrales relativos E_th/E₀ del experimento E2; 10⁻⁶ es el del PDF.
UMBRAL_BASE = 1e-6
UMBRALES = (1e-4, 1e-6, 1e-8)


def indice_primer_cruce(E: np.ndarray, E_th: float) -> np.ndarray:
    """Primer índice temporal con Eᵢ ≥ E_th para cada nodo; −1 si no lo cruza.

    E tiene forma (n_t, N); devuelve un arreglo de enteros (N,).
    """
    cruza = E >= E_th
    idx = np.argmax(cruza, axis=0)
    idx[~cruza.any(axis=0)] = -1
    return idx


def _interpolar_cruce(t0, t1, E0, E1, E_th):
    """Instante en que E cruza E_th entre dos muestras.

    Si ambas muestras son positivas (t₀ > 0, E₀ > 0) interpola en log–log:
    es exacto si E ∝ tᵖ, que es el comportamiento a tiempos cortos (teoría,
    punto 7: Eᵢ ∝ t^(4d−2) mientras domina la corriente). Si no, interpola
    linealmente.
    """
    if t0 > 0 and E0 > 0:
        lt0, lt1 = np.log(t0), np.log(t1)
        f = (np.log(E_th) - np.log(E0)) / (np.log(E1) - np.log(E0))
        return float(np.exp(lt0 + f * (lt1 - lt0)))
    f = (E_th - E0) / (E1 - E0)
    return float(t0 + f * (t1 - t0))


def tiempos_llegada(t: np.ndarray, E: np.ndarray, E_th: float,
                    energia_en=None) -> np.ndarray:
    """Tiempo de llegada tᵢ de cada nodo (s); NaN si no cruza el umbral en [0, T].

    Parámetros
    ----------
    t : instantes (n_t,).
    E : energías Eᵢ(t), forma (n_t, N).
    E_th : umbral absoluto (J).
    energia_en : opcional, función t ↦ E(t) de forma (N,). Si se da, el cruce
        se refina con `brentq` entre las dos muestras que lo encierran (ver
        `evaluador_modal`). Si no, se interpola entre ellas.

    Un nodo que ya supera el umbral en t[0] (la fuente) tiene tᵢ = t[0].
    """
    idx = indice_primer_cruce(E, E_th)
    tl = np.full(E.shape[1], np.nan)
    for i, k in enumerate(idx):
        if k < 0:
            continue
        if k == 0:
            tl[i] = t[0]
            continue
        if energia_en is None:
            tl[i] = _interpolar_cruce(t[k - 1], t[k], E[k - 1, i], E[k, i], E_th)
        else:
            tl[i] = brentq(lambda s: energia_en(s)[i] - E_th, t[k - 1], t[k],
                           xtol=1e-15, rtol=1e-12)
    return tl


def evaluador_modal(sim: Simulacion, modos: Modos | None = None):
    """Devuelve E(t) exacta (por modos normales) para refinar tiempos de llegada.

    Usa el estado inicial de la simulación, así que vale para cualquier método.
    """
    p = sim.parametros
    if modos is None:
        modos = modos_normales(sim.Lambda, p)
    Q0, I0 = sim.Q[0], sim.I[0]

    def energia_en(s: float) -> np.ndarray:
        Q, I = solucion_modal(sim.Lambda, p, np.array([s]), Q0, I0, modos=modos)
        return energia_nodos(Q[0], I[0], p)

    return energia_en


def evaluador_denso(sim: Simulacion):
    """E(t) a partir de la solución continua de DOP853 (`simular(..., denso=True)`)."""
    if "solucion_densa" not in sim.info:
        raise ValueError("La simulación no guardó la solución densa: usa denso=True.")
    sol, N, p = sim.info["solucion_densa"], sim.N, sim.parametros

    def energia_en(s: float) -> np.ndarray:
        y = sol(s)
        return energia_nodos(y[:N], y[N:], p)

    return energia_en


@dataclass
class Llegadas:
    """Tiempos de llegada de una simulación para un umbral.

    Atributos
    ---------
    t : tᵢ en segundos (NaN si el nodo no se alcanzó).
    gamma : γ, para expresar el tiempo como γtᵢ.
    umbral : umbral relativo E_th/E₀.
    """

    t: np.ndarray = field(repr=False)
    gamma: float
    umbral: float

    @property
    def t_gamma(self) -> np.ndarray:
        """γ(tᵢ − t₀) con t₀ = 0, la variable de los gráficos del PDF."""
        return self.gamma * self.t

    @property
    def alcanzado(self) -> np.ndarray:
        return ~np.isnan(self.t)

    @property
    def n_no_alcanzados(self) -> int:
        return int(np.sum(~self.alcanzado))


def llegadas(sim: Simulacion, en: Energias | None = None,
             umbral: float = UMBRAL_BASE, refinar: str = "auto") -> Llegadas:
    """Tiempos de llegada de la simulación con E_th = umbral · E₀.

    refinar:
        "auto" (por defecto) — "denso" si la simulación guardó la solución
            continua (`simular(..., denso=True)`), si no "modal".
        "denso" — raíz con la solución continua de DOP853.
        "modal" — raíz exacta con la solución por modos normales.
        "interpolar" — solo entre muestras. Rápido, pero falla en los vecinos
            de la fuente: con κ ≳ 0.1 cruzan el umbral antes de la primera
            muestra, donde E ∝ t² y la interpolación lineal desde E = 0 da
            errores de hasta 99 %.
    """
    if en is None:
        en = energias(sim)
    if refinar == "auto":
        refinar = "denso" if "solucion_densa" in sim.info else "modal"
    evaluadores = {"interpolar": lambda: None,
                   "modal": lambda: evaluador_modal(sim),
                   "denso": lambda: evaluador_denso(sim)}
    if refinar not in evaluadores:
        raise ValueError(f"refinar debe ser uno de {tuple(evaluadores) + ('auto',)}")
    tl = tiempos_llegada(sim.t, en.E, umbral * en.E0, evaluadores[refinar]())
    return Llegadas(tl, sim.parametros.gamma, umbral)


def rapidez_frente(t_llegada: np.ndarray, distancias: np.ndarray, d_min: int = 1):
    """Rapidez media del frente: ajuste lineal tᵢ = a + b·dᵢ por mínimos cuadrados.

    Usa los nodos alcanzados con d ≥ d_min (por defecto se excluye la fuente).
    Devuelve (v, b, a) con v = 1/b en nodos por segundo. Si hay menos de dos
    distancias distintas, o b ≤ 0, devuelve NaN.

    Es una medida resumen para comparar κ y redes (G6). La teoría (punto 7)
    muestra que t frente a d es curvo para d pequeño, así que la comparación
    de modelos funcionales se hace aparte, en la Fase 4.
    """
    ok = np.isfinite(t_llegada) & (distancias >= d_min)
    d, t = distancias[ok].astype(float), t_llegada[ok]
    if np.unique(d).size < 2:
        return np.nan, np.nan, np.nan
    b, a = np.polyfit(d, t, 1)
    v = 1.0 / b if b > 0 else np.nan
    return float(v), float(b), float(a)


# ---------------------------------------------------------------------------
# Estadísticas por distancia
# ---------------------------------------------------------------------------

@dataclass
class PorDistancia:
    """Resumen de una cantidad por nodo, agrupada por distancia a la fuente.

    Atributos (todos con una entrada por distancia d)
    ---------
    d : distancias presentes (0, 1, …, d_max).
    N_d : nodos a esa distancia.
    n_validos : nodos con valor finito (difiere de N_d si hay no alcanzados).
    media : media sobre los nodos válidos, ecuación (21).
    sigma : desviación estándar con ddof = 1, ecuación (23); NaN si hay
        menos de 2 nodos válidos.
    minimo, maximo : extremos, útiles para ver la dispersión a igual d.
    """

    d: np.ndarray
    N_d: np.ndarray
    n_validos: np.ndarray
    media: np.ndarray
    sigma: np.ndarray
    minimo: np.ndarray
    maximo: np.ndarray

    @property
    def sigma_relativa(self) -> np.ndarray:
        """σ(d)/media(d): heterogeneidad relativa (gráfico G8)."""
        with np.errstate(invalid="ignore", divide="ignore"):
            return self.sigma / self.media


def por_distancia(valores: np.ndarray, distancias: np.ndarray) -> PorDistancia:
    """Agrupa un valor por nodo (⟨Eᵢ⟩, tᵢ, …) según la distancia a la fuente.

    Ignora los nodos inalcanzables en la red (d = −1) y los valores NaN (nodos
    que no cruzaron el umbral), que se cuentan aparte en `n_validos`.
    """
    validos_red = distancias >= 0
    ds = np.unique(distancias[validos_red])
    filas = {k: [] for k in ("N_d", "n_validos", "media", "sigma", "minimo", "maximo")}
    for d in ds:
        v = valores[distancias == d]
        finitos = v[np.isfinite(v)]
        n = finitos.size
        filas["N_d"].append(v.size)
        filas["n_validos"].append(n)
        filas["media"].append(finitos.mean() if n else np.nan)
        filas["sigma"].append(finitos.std(ddof=1) if n >= 2 else np.nan)
        filas["minimo"].append(finitos.min() if n else np.nan)
        filas["maximo"].append(finitos.max() if n else np.nan)
    return PorDistancia(ds, *(np.array(filas[k]) for k in
                              ("N_d", "n_validos", "media", "sigma", "minimo", "maximo")))


def por_distancia_realizaciones(valores: np.ndarray, distancias: np.ndarray) -> dict:
    """`por_distancia` aplicado a cada realización, con un eje d común.

    valores, distancias : forma (realizaciones, N).

    Devuelve un diccionario con arreglos de forma (realizaciones, d_max + 1),
    rellenos con NaN donde una realización no tiene nodos a esa distancia:
    "d", "N_d", "media" (Ē(d)) y "sigma" (σ(d), ddof = 1).

    Así se separan las dos variabilidades del plan: σ mide las diferencias
    entre nodos dentro de una red; la dispersión de "media" a lo largo del
    eje 0 mide las diferencias entre realizaciones.
    """
    nr = valores.shape[0]
    dmax = int(distancias.max())
    d = np.arange(dmax + 1)
    N_d = np.zeros((nr, dmax + 1), int)
    media = np.full((nr, dmax + 1), np.nan)
    sigma = np.full((nr, dmax + 1), np.nan)
    for j in range(nr):
        r = por_distancia(valores[j], distancias[j])
        N_d[j, r.d] = r.N_d
        media[j, r.d] = r.media
        sigma[j, r.d] = r.sigma
    return {"d": d, "N_d": N_d, "media": media, "sigma": sigma}


# ---------------------------------------------------------------------------
# Nodos a igual distancia (experimento E4)
# ---------------------------------------------------------------------------

def peso_modal_incoherente(Lambda: np.ndarray, fuente: int, tol: float = 1e-8) -> np.ndarray:
    """Wᵢ = Σ_λ (Π_λ)ᵢ₀²: peso de la fuente en el nodo i, sumado sin interferencia.

    Π_λ es el proyector sobre el subespacio de autovalor λ de Λ. Con modos de
    frecuencias distintas, el promedio temporal de Qᵢ² sin amortiguamiento es
    ½ Q₀² Wᵢ (los términos cruzados promedian a cero). Usar proyectores, y no
    autovectores sueltos, hace que Wᵢ no dependa de la base elegida cuando hay
    autovalores repetidos (malla y anillo, por simetría).

    No depende de K: los autovectores de Λ son los mismos para todo κ.
    """
    lam, V = np.linalg.eigh(Lambda)
    W = np.zeros(Lambda.shape[0])
    inicio = 0
    for k in range(1, lam.size + 1):
        if k == lam.size or lam[k] - lam[k - 1] > tol * max(1.0, abs(lam[k])):
            Vb = V[:, inicio:k]
            W += (Vb @ Vb[fuente]) ** 2           # columna de Π_λ en la fuente
            inicio = k
    return W


def relacion_a_igual_distancia(y: np.ndarray, x: np.ndarray, distancias: np.ndarray,
                               minimo: int = 3) -> dict:
    """Cuánto explica x la variación de y entre nodos a la misma distancia.

    y, x, distancias : forma (realizaciones, N). Cada grupo es un par
    (realización, d) con d ≥ 1. Se usan los nodos con y, x finitos y positivos.

    Devuelve:
        rho_mediana  — mediana de la correlación de Spearman dentro de los
                       grupos con al menos `minimo` nodos y valores distintos;
        frac_positiva — fracción de esos grupos con ρ > 0;
        n_grupos     — grupos usados;
        pendiente, R2 — regresión de log y sobre log x tras restar la media de
                       cada grupo (efectos fijos por distancia y realización):
                       R2 es la parte de la variación a igual d que explica x.
    """
    rhos, lx_all, ly_all = [], [], []
    for r in range(y.shape[0]):
        for d in np.unique(distancias[r]):
            if d < 1:
                continue
            g = (distancias[r] == d) & np.isfinite(y[r]) & np.isfinite(x[r]) \
                & (y[r] > 0) & (x[r] > 0)
            if g.sum() < 2:
                continue
            ly, lx = np.log(y[r, g]), np.log(x[r, g])
            lx_all.append(lx - lx.mean())
            ly_all.append(ly - ly.mean())
            if g.sum() >= minimo and np.unique(x[r, g]).size > 1 and np.unique(y[r, g]).size > 1:
                rhos.append(spearmanr(x[r, g], y[r, g])[0])
    lx, ly = (np.concatenate(lx_all), np.concatenate(ly_all)) if lx_all else (np.array([]),) * 2
    sxx, syy = float(lx @ lx), float(ly @ ly)
    if sxx > 0 and syy > 0:
        b = float(lx @ ly) / sxx
        R2 = 1 - float(((ly - b * lx) ** 2).sum()) / syy
    else:
        b, R2 = np.nan, np.nan
    rhos = np.array(rhos)
    return {"rho_mediana": float(np.median(rhos)) if rhos.size else np.nan,
            "frac_positiva": float(np.mean(rhos > 0)) if rhos.size else np.nan,
            "n_grupos": int(rhos.size), "pendiente": b, "R2": R2}
