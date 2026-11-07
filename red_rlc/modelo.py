"""Modelo dinámico de la red RLC: parámetros, integración numérica y solución modal.

Ecuación del modelo (punto 4 de la teoría, Fase 1):

    Q̈ + γ Q̇ + (ω₀² 𝕀 + K Λ) Q = 0,      γ = R/L,  ω₀² = 1/(LC),  K = 1/(L C_c)

En primer orden, con I = Q̇ (2N incógnitas):

    Q̇ = I
    İ = −γ I − ω₀² Q − K Λ Q

Este módulo ofrece dos formas de resolverla:

- `integrar_dop853`: integración numérica con DOP853 (Runge–Kutta de orden 8 de
  SciPy) y tolerancias estrictas. Es el método que genera los resultados.
- `solucion_modal`: solución exacta por modos normales (punto 6 de la teoría).
  Sirve de referencia para validar el integrador.

`simular` es la entrada de alto nivel: recibe una `Red` y unos `Parametros`,
fija las condiciones iniciales del PDF (Q₀ en la fuente, el resto en reposo) y
devuelve una `Simulacion`.

Convenciones:

- Los arreglos de la simulación tienen forma (n_t, N): fila = instante,
  columna = nodo. Así `sim.Q[:, i]` es la historia del nodo i.
- Todo se trabaja en unidades SI (s, C, A). La normalización (tγ, E/E₀) se
  hace en el análisis.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace

import numpy as np
from scipy.integrate import solve_ivp

# Valores de κ = K/ω₀² del plan («Parámetros y redes de referencia»).
KAPPAS_BASE = (0.01, 0.03, 0.1, 0.3, 1.0)
KAPPAS_E2 = KAPPAS_BASE + (3.0, 10.0)

# Opciones numéricas por defecto. Las tolerancias por defecto de solve_ivp
# (rtol = 1e−3, atol = 1e−6) no sirven aquí: las cargas son del orden de 1e−6 C
# y los umbrales de energía llegan a 1e−8 E₀.
RTOL = 1e-10
ATOL_RELATIVA = 1e-12          # atol = ATOL_RELATIVA × escala de cada variable
# Muestras por período del modo más rápido. El plan observó que unas 40 por
# período discretizan visiblemente los tiempos de llegada; con 100, T = 10/γ
# (≈ 50 períodos de ω₀) da unas 5000 muestras con κ pequeño.
PUNTOS_POR_PERIODO = 100


# ---------------------------------------------------------------------------
# Parámetros físicos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Parametros:
    """Parámetros físicos de una simulación (unidades SI).

    El acoplamiento se fija con κ = K/ω₀² (adimensional), como en el plan; K y
    el capacitor de acoplamiento C_c = C/κ se derivan de él.

    Atributos
    ---------
    L : inductancia (H).
    C : capacidad de cada malla (F).
    R : resistencia (Ω).
    Q0 : carga inicial del nodo fuente (C).
    kappa : κ = K/ω₀².
    n_decaimientos : duración por defecto T = n_decaimientos / γ.
    """

    L: float = 1e-3
    C: float = 1e-6
    R: float = 1.0
    Q0: float = 1e-6
    kappa: float = 0.1
    n_decaimientos: float = 10.0

    def __post_init__(self):
        if self.L <= 0 or self.C <= 0:
            raise ValueError("L y C deben ser positivos.")
        if self.R < 0 or self.kappa < 0:
            raise ValueError("R y κ no pueden ser negativos.")

    def con(self, **cambios) -> Parametros:
        """Copia con algunos valores cambiados, p. ej. `p.con(kappa=1.0)`."""
        return replace(self, **cambios)

    @property
    def gamma(self) -> float:
        """γ = R/L (s⁻¹): tasa de decaimiento de la energía."""
        return self.R / self.L

    @property
    def omega0(self) -> float:
        """ω₀ = 1/√(LC) (rad/s): frecuencia natural sin resistencia."""
        return 1.0 / np.sqrt(self.L * self.C)

    @property
    def K(self) -> float:
        """K = κ ω₀² (s⁻²)."""
        return self.kappa * self.omega0**2

    @property
    def Cc(self) -> float:
        """Capacitor de acoplamiento C_c = 1/(LK) = C/κ (F); infinito si κ = 0."""
        return np.inf if self.kappa == 0 else self.C / self.kappa

    @property
    def E0(self) -> float:
        """E₀ = Q₀²/(2C) (J): energía inicial del oscilador fuente."""
        return self.Q0**2 / (2 * self.C)

    @property
    def periodo(self) -> float:
        """T₀ = 2π/ω₀ (s)."""
        return 2 * np.pi / self.omega0

    @property
    def factor_calidad(self) -> float:
        """ω₀/γ; infinito si R = 0."""
        return np.inf if self.R == 0 else self.omega0 / self.gamma

    @property
    def T(self) -> float:
        """Duración por defecto, n_decaimientos/γ (s). Con R = 0 no existe."""
        if self.R == 0:
            raise ValueError("Con R = 0 no hay escala 1/γ: indica T explícitamente.")
        return self.n_decaimientos / self.gamma


# ---------------------------------------------------------------------------
# Piezas del sistema
# ---------------------------------------------------------------------------

def matriz_rigidez(Lambda: np.ndarray, p: Parametros) -> np.ndarray:
    """M = ω₀² 𝕀 + K Λ, de modo que Q̈ + γ Q̇ + M Q = 0."""
    N = Lambda.shape[0]
    return p.omega0**2 * np.eye(N) + p.K * Lambda


def condiciones_iniciales(N: int, fuente: int, Q0: float) -> tuple[np.ndarray, np.ndarray]:
    """Condiciones del PDF: Q_fuente(0) = Q₀, demás cargas nulas, corrientes nulas."""
    Q = np.zeros(N)
    Q[fuente] = Q0
    return Q, np.zeros(N)


def omega_maxima(Lambda: np.ndarray, p: Parametros) -> float:
    """Frecuencia del modo más rápido, √(ω₀² + K λ_max) (rad/s).

    Fija el muestreo: con κ grande la red oscila varias veces más rápido que ω₀.
    """
    lam_max = np.linalg.eigvalsh(Lambda)[-1]
    return float(np.sqrt(p.omega0**2 + p.K * max(lam_max, 0.0)))


def malla_temporal(T: float, omega_max: float,
                   puntos_por_periodo: int = PUNTOS_POR_PERIODO) -> np.ndarray:
    """Instantes equiespaciados en [0, T], con `puntos_por_periodo` muestras por
    período del modo más rápido."""
    n = int(np.ceil(T * omega_max / (2 * np.pi) * puntos_por_periodo))
    return np.linspace(0.0, T, max(n, 2) + 1)


# ---------------------------------------------------------------------------
# Integración numérica con DOP853
# ---------------------------------------------------------------------------

def integrar_dop853(Lambda: np.ndarray, p: Parametros, t: np.ndarray,
                    Q_ini: np.ndarray, I_ini: np.ndarray,
                    rtol: float = RTOL, atol_relativa: float = ATOL_RELATIVA,
                    denso: bool = False):
    """Integra el sistema de primer orden con DOP853.

    Parámetros
    ----------
    Lambda : laplaciano Λ (N × N).
    p : parámetros físicos.
    t : instantes donde se guarda la solución (creciente, empieza en t[0]).
    Q_ini, I_ini : estado inicial.
    rtol : tolerancia relativa.
    atol_relativa : la tolerancia absoluta se escala con cada tipo de variable:
        atol_Q = atol_relativa · Q₀ y atol_I = atol_relativa · ω_max · Q₀,
        porque Q e I tienen unidades y órdenes de magnitud distintos.
    denso : si es True, devuelve también la solución continua (`OdeSolution`),
        útil para refinar tiempos de cruce entre muestras.

    Devuelve
    --------
    Q, I : arreglos (n_t, N).
    info : diccionario con el número de evaluaciones, el tiempo de cómputo y,
        si se pidió, la solución densa.
    """
    N = Lambda.shape[0]
    M = matriz_rigidez(Lambda, p)
    gamma = p.gamma

    def derivadas(_t, y):
        Q, I = y[:N], y[N:]
        return np.concatenate((I, -gamma * I - M @ Q))

    escala_Q = p.Q0
    escala_I = omega_maxima(Lambda, p) * p.Q0
    atol = np.concatenate((np.full(N, atol_relativa * escala_Q),
                           np.full(N, atol_relativa * escala_I)))

    inicio = time.perf_counter()
    sol = solve_ivp(derivadas, (t[0], t[-1]), np.concatenate((Q_ini, I_ini)),
                    method="DOP853", t_eval=t, rtol=rtol, atol=atol,
                    dense_output=denso)
    duracion = time.perf_counter() - inicio
    if not sol.success:
        raise RuntimeError(f"DOP853 falló: {sol.message}")

    Y = sol.y.T
    info = {"nfev": sol.nfev, "tiempo_s": duracion, "rtol": rtol, "atol": atol}
    if denso:
        info["solucion_densa"] = sol.sol
    return Y[:, :N], Y[:, N:], info


# ---------------------------------------------------------------------------
# Solución exacta por modos normales
# ---------------------------------------------------------------------------

@dataclass
class Modos:
    """Modos normales de la red para unos parámetros dados (punto 6 de la teoría).

    Atributos
    ---------
    lam : autovalores λₙ de Λ, en orden creciente.
    V : autovectores ortonormales; la columna n es vₙ y V[i, n] = vₙ(i).
    omega2 : ωₙ² = ω₀² + K λₙ.
    Omega2 : Ωₙ² = ωₙ² − γ²/4 (positivo si el modo es subamortiguado).
    gamma : γ usado.
    """

    lam: np.ndarray
    V: np.ndarray = field(repr=False)
    omega2: np.ndarray = field(repr=False)
    Omega2: np.ndarray = field(repr=False)
    gamma: float

    def pesos(self, fuente: int) -> np.ndarray:
        """Pesos vₙ(i) vₙ(fuente), forma (N, N): fila = nodo i, columna = modo n.

        Con las condiciones del PDF, Qᵢ(t) = Q₀ Σₙ vₙ(i) vₙ(0) gₙ(t).
        """
        return self.V * self.V[fuente, :]


def modos_normales(Lambda: np.ndarray, p: Parametros) -> Modos:
    """Diagonaliza Λ (simétrica) con `eigh` y calcula las frecuencias de cada modo."""
    lam, V = np.linalg.eigh(Lambda)
    lam = np.where(np.abs(lam) < 1e-12, 0.0, lam)   # el modo uniforme vale 0 exacto
    omega2 = p.omega0**2 + p.K * lam
    Omega2 = omega2 - p.gamma**2 / 4
    return Modos(lam, V, omega2, Omega2, p.gamma)


def _funciones_modales(t: np.ndarray, Omega2: np.ndarray, gamma: float):
    """C(t) = e^(−γt/2) cos Ωt y S(t) = e^(−γt/2) sen(Ωt)/Ω para cada modo.

    Con Ω² < 0 (sobreamortiguado) se usan cosh y senh, y con Ω² = 0 (crítico)
    C = e^(−γt/2) y S = t e^(−γt/2). En los modos sobreamortiguados se combinan
    las exponenciales para no multiplicar números enormes por diminutos.
    Devuelve dos arreglos (n_t, n_modos).
    """
    a = gamma / 2
    tt = t[:, None]
    C = np.empty((t.size, Omega2.size))
    S = np.empty_like(C)
    escala = np.maximum(np.abs(Omega2), 1.0)
    sub = Omega2 > 1e-12 * escala
    sobre = Omega2 < -1e-12 * escala
    crit = ~(sub | sobre)

    env = np.exp(-a * tt)
    if sub.any():
        W = np.sqrt(Omega2[sub])
        C[:, sub] = env * np.cos(W * tt)
        S[:, sub] = env * np.sin(W * tt) / W
    if sobre.any():
        b = np.sqrt(-Omega2[sobre])
        lento = np.exp(-(a - b) * tt)
        rapido = np.exp(-(a + b) * tt)
        C[:, sobre] = (lento + rapido) / 2
        S[:, sobre] = (lento - rapido) / (2 * b)
    if crit.any():
        C[:, crit] = env
        S[:, crit] = env * tt
    return C, S


def solucion_modal(Lambda: np.ndarray, p: Parametros, t: np.ndarray,
                   Q_ini: np.ndarray, I_ini: np.ndarray,
                   modos: Modos | None = None, bloque: int = 20_000):
    """Solución exacta Q(t), I(t) por modos normales.

    Cada coordenada modal aₙ = vₙᵀ Q cumple äₙ + γ ȧₙ + ωₙ² aₙ = 0, cuya
    solución (punto 2 de la teoría, con ω₀ → ωₙ) es:

        aₙ(t) = aₙ(0) C(t) + [ȧₙ(0) + (γ/2) aₙ(0)] S(t)
        ȧₙ(t) = ȧₙ(0) C(t) − [(γ/2) ȧₙ(0) + ωₙ² aₙ(0)] S(t)

    y luego Q = V a, I = V ȧ. Admite estados iniciales arbitrarios. Se evalúa
    por bloques de tiempo para acotar la memoria.

    Devuelve Q, I con forma (n_t, N).
    """
    if modos is None:
        modos = modos_normales(Lambda, p)
    V = modos.V
    a0 = V.T @ Q_ini
    b0 = V.T @ I_ini
    alfa = p.gamma / 2
    coef_S_a = b0 + alfa * a0
    coef_S_b = alfa * b0 + modos.omega2 * a0

    N = V.shape[0]
    Q = np.empty((t.size, N))
    I = np.empty((t.size, N))
    for ini in range(0, t.size, bloque):
        tb = t[ini:ini + bloque]
        C, S = _funciones_modales(tb, modos.Omega2, p.gamma)
        a = a0 * C + coef_S_a * S
        da = b0 * C - coef_S_b * S
        Q[ini:ini + bloque] = a @ V.T
        I[ini:ini + bloque] = da @ V.T
    return Q, I


# ---------------------------------------------------------------------------
# Entrada de alto nivel
# ---------------------------------------------------------------------------

@dataclass
class Simulacion:
    """Resultado de simular una red.

    Atributos
    ---------
    t : instantes (s), forma (n_t,).
    Q, I : cargas (C) y corrientes (A), forma (n_t, N).
    Lambda : laplaciano de la red simulada (lo necesita la energía H).
    parametros : `Parametros` usados.
    fuente : nodo perturbado.
    red : nombre de la topología.
    metodo : "dop853" o "modal".
    info : datos del cálculo (evaluaciones, tiempo de cómputo, ...).
    """

    t: np.ndarray = field(repr=False)
    Q: np.ndarray = field(repr=False)
    I: np.ndarray = field(repr=False)
    Lambda: np.ndarray = field(repr=False)
    parametros: Parametros
    fuente: int
    red: str
    metodo: str
    info: dict = field(default_factory=dict, repr=False)

    @property
    def N(self) -> int:
        return self.Q.shape[1]

    @property
    def t_gamma(self) -> np.ndarray:
        """Tiempo adimensional γt (eje de los gráficos del PDF)."""
        return self.parametros.gamma * self.t


METODOS = ("dop853", "modal")


def simular(red, p: Parametros, metodo: str = "dop853", T: float | None = None,
            puntos_por_periodo: int = PUNTOS_POR_PERIODO,
            t: np.ndarray | None = None, **opciones) -> Simulacion:
    """Simula la red con las condiciones iniciales del PDF.

    Parámetros
    ----------
    red : `redes.Red` (usa su laplaciano, su fuente y su nombre).
    p : parámetros físicos.
    metodo : "dop853" (resultados) o "modal" (referencia exacta).
    T : duración (s); por defecto p.T = n_decaimientos/γ.
    puntos_por_periodo : muestras por período del modo más rápido.
    t : instantes explícitos; si se dan, ignora T y puntos_por_periodo.
    opciones : se pasan a `integrar_dop853` (rtol, atol_relativa, denso).
    """
    if metodo not in METODOS:
        raise ValueError(f"Método desconocido {metodo!r}; opciones: {METODOS}")
    Lambda = red.laplaciano
    if t is None:
        T = p.T if T is None else T
        t = malla_temporal(T, omega_maxima(Lambda, p), puntos_por_periodo)
    Q_ini, I_ini = condiciones_iniciales(red.N, red.fuente, p.Q0)

    if metodo == "dop853":
        Q, I, info = integrar_dop853(Lambda, p, t, Q_ini, I_ini, **opciones)
    else:
        inicio = time.perf_counter()
        Q, I = solucion_modal(Lambda, p, t, Q_ini, I_ini)
        info = {"tiempo_s": time.perf_counter() - inicio}
    info["n_t"] = t.size
    return Simulacion(t, Q, I, Lambda, p, red.fuente, red.nombre, metodo, info)
