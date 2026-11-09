# Bitácora de desarrollo

Este documento explica qué se ha construido en el proyecto, para qué sirve cada
parte y qué se ha comprobado. Se actualiza con cada avance; la sección
«Registro de cambios» al final lleva el historial.

- **Última actualización:** 8 de noviembre de 2026
- **Fase actual:** Fase 6 en curso. El informe en Word está listo (24
  páginas); faltan las diapositivas, el guion y el banco de preguntas.

## 1. Estado general

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Teoría del modelo | Documento terminado (`Fase 1 teoría del modelo RLC.pdf`) |
| 2 | Código y validación | ✅ Aprobada el 8 de noviembre tras la revisión de un integrante |
| 3 | Experimentos numéricos | ✅ Completa y regenerada de punta a punta (sección 17) |
| 4 | Análisis y ajustes | ✅ Ajustes con AICc (sección 18) y resumen de resultados (sección 19); en revisión del grupo |
| 5 | Videos y figuras finales | ✅ 6 videos y 6 figuras para proyectar (sección 20) |
| 6 | Informe, conclusiones, presentación y defensa | En curso: informe listo (sección 21); faltan diapositivas, guion y banco de preguntas |

**Fase 2 en detalle.** La fase terminaba cuando pasaran todas las pruebas de
validación del plan.

| Paso | Pieza | Estado |
|------|-------|--------|
| 0 | Entorno de trabajo (Python, entorno virtual, Git, pytest) | ✅ Listo |
| 1 | `redes.py`: topologías, laplaciano, distancias, caminos | ✅ Listo y probado (47 pruebas) |
| 2 | `modelo.py`: parámetros, DOP853, solución modal | ✅ Listo y probado |
| 3 | Energía: Eᵢ, U, H y potencia disipada (`analisis.py`) | ✅ Listo y probado |
| 4 | Pruebas de validación del modelo (las 9 del plan) | ✅ Las 9 aprobadas (ver sección 7) |
| 5 | RK4 propio y prueba de convergencia | ✅ Orden observado de 3.97 a 4.00 |
| 6 | Pseudocódigo y diagrama de flujo | ✅ `docs/pseudocodigo_y_diagrama_flujo.md` (sección 8) |
| — | Revisión de cierre por otro integrante | ✅ Aprobada (8 nov) |

**Fase 3 en detalle.** El plan pide los experimentos E1 a E5 con semillas
fijas y los gráficos base.

| Paso | Pieza | Estado |
|------|-------|--------|
| 1 | Tiempos de llegada con umbral, censura y refinamiento (`analisis.py`) | ✅ Listo y probado (sección 9) |
| 2 | Estadísticas por distancia Ē(d), σ_E(d) (`analisis.py`) | ✅ Listo y probado (sección 9) |
| 3 | E1, dinámica: Qᵢ(t), Eᵢ(t), H(t) | ✅ Datos generados y controlados (sección 10) |
| 4 | E2, tiempos de llegada frente a d, por κ, red y umbral | ✅ 434 simulaciones con las 30 realizaciones (sección 12) |
| 5 | E3, energía por distancia | ✅ Calculado con los ⟨Eᵢ⟩ de E2 (sección 14) |
| 6 | E4, efecto de la posición a igual d | ✅ Calculado con los datos de E2 (sección 15) |
| 7 | E5, sensibilidad a γ, N y posición de la fuente | ✅ 234 simulaciones (sección 16) |
| 8 | Gráficos base | ✅ G1 a G10 (secciones 10, 11 y 13 a 17) |
| 9 | Reproducibilidad y ejecución completa | ✅ `verificar_reproducibilidad.py` y `fase3_completa.py` (sección 17) |
| — | Ejecución completa de punta a punta | ✅ 920 s; controles OK; reproducibilidad exacta |

**Pruebas automáticas:** 183 en total, todas aprobadas; tardan entre 30 s y
2 min según la carga del equipo.

## 2. Entorno de trabajo

| Elemento | Detalle |
|----------|---------|
| Ubicación del proyecto | `C:\Users\juand\proyectos\proyecto_final_fisicaIII` (fuera de OneDrive) |
| Python | 3.13.17 |
| Entorno virtual | `C:\Users\juand\venvs\fisica3`, también fuera de OneDrive |
| Librerías | numpy 2.5.4, scipy 1.18.1, networkx 3.7, matplotlib 3.11.2, imageio-ffmpeg 0.8.1, pytest 9.2.0 |
| Control de versiones | Git, rama `main`, remoto `github.com/juandabettt/rlc-coupled-networks-fisicaIII` |
| IDE | IntelliJ con el intérprete del entorno `fisica3` |

**Por qué fuera de OneDrive:** OneDrive sincronizaría miles de archivos de
librerías y no ofrece control de versiones real. Git cumple esa función.

**Archivos de configuración:**

- `requirements.txt`: lista de librerías con versión mínima.
- `pytest.ini`: indica a pytest que las pruebas están en `tests/` y que
  `red_rlc` se importa desde la raíz. Así funcionan `pytest` y `python -m pytest`.
- `.gitignore`: excluye cachés, entornos, la carpeta del IDE y los resultados
  pesados (`resultados/datos`, `resultados/videos`), que se pueden regenerar.

**Cómo correr las pruebas** (con el entorno activado, desde la raíz):

```bash
python -m pytest -v
```

## 3. Estructura del código

El paquete `red_rlc/` separa el trabajo en módulos con una sola responsabilidad
cada uno. Así cada pieza se prueba por separado y el flujo de datos es claro:

```
redes.py  ──►  modelo.py  ──►  analisis.py  ──►  ajustes.py
(topología)    (dinámica)      (energía,          (modelos
 A, Λ, d, Nᵢ    Q(t), I(t)      tiempos, Ē(d))     funcionales)
                                     │
                                     ▼
                              graficos.py, videos.py
```

| Módulo | Función | Estado |
|--------|---------|--------|
| `redes.py` | Construye las redes y sus cantidades estructurales | ✅ |
| `modelo.py` | Resuelve la dinámica Q(t), I(t) | ✅ |
| `analisis.py` | Energías, tiempos de llegada, estadísticas por distancia | ✅ |
| `ajustes.py` | Ajustes funcionales y comparación con AICc | ✅ |
| `graficos.py` | Gráficos G1 a G10, con estilo y paleta comunes | ✅ |
| `resultados.py` | Rutas de resultados; guarda y carga `.npz` (con metadatos) y `.csv` | ✅ |
| `videos.py` | Animaciones de log₁₀(Eᵢ/E₀) | ✅ |

## 4. `redes.py`: topologías y distancias

**Para qué sirve:** genera las cuatro redes del estudio y calcula todo lo que
depende solo de la topología. Atiende el objetivo O3 del PDF.

### Las cuatro redes de referencia

Todas tienen N = 100 y un grado medio cercano a 4. Así las diferencias entre
redes vienen de su estructura y no de cuántos enlaces tienen.

| Función | Red | Fuente | d máxima | Notas |
|---------|-----|--------|----------|-------|
| `malla()` | Rejilla 10 × 10, borde abierto | Nodo 44, interior | 10 | `fuente="esquina"` usa el nodo 0, con d máxima 18 |
| `anillo()` | Anillo regular, k = 4 | Nodo 0 | 25 | Todos los nodos son equivalentes |
| `mundo_pequeno()` | Watts–Strogatz, k = 4, p = 0.1 | Nodo 0 | ≈ 10 | Aleatoria, conserva N·k/2 = 200 enlaces |
| `erdos_renyi()` | G(N, p), p = 4/99 | Nodo 0 | ≈ 5–6 | Aleatoria; solo se aceptan muestras conexas |

**Redes aleatorias y semillas.** Cada red aleatoria se genera con una semilla
fija (base 2026). La misma semilla siempre produce la misma red, así que los
resultados se pueden reproducir. Las redes desconexas se descartan y se genera
otra; el atributo `intentos` registra cuántas se generaron. Con p = 4/99 solo
cerca del 18 % de las redes ER son conexas, y este descarte selecciona un
subconjunto de redes: debe declararse en el informe.

### La clase `Red`

Empaqueta una red lista para simular:

| Atributo | Significado |
|----------|-------------|
| `nombre` | Topología ("malla", "anillo", ...) |
| `grafo` | Grafo de NetworkX, con nodos 0..N−1 |
| `fuente` | Nodo perturbado en t = 0 |
| `A` | Matriz de adyacencia (N × N) |
| `distancias` | d₀ᵢ, distancia topológica desde la fuente (−1 si no se alcanza) |
| `caminos` | Nᵢ, número de caminos más cortos desde la fuente |
| `semilla`, `intentos` | Reproducibilidad y sesgo de selección en ER |
| `grados`, `laplaciano`, `distancia_maxima`, `distribucion_distancias` | Propiedades calculadas |

### Funciones auxiliares

- `laplaciano(A)`: calcula Λ = D − A. Es la matriz que entra en la ecuación
  del modelo.
- `distancias_y_caminos(G, fuente)`: búsqueda en anchura. Cada nodo a
  distancia d + 1 acumula los caminos de sus vecinos a distancia d. Nᵢ sirve
  para el experimento E4: a tiempos cortos, Qᵢ ∝ Nᵢ (punto 7 de la teoría).
- `distribucion_distancias`: N_d, cuántos nodos hay a cada distancia. Se usa
  en el gráfico G1.
- `construir(nombre)`, `realizaciones(nombre, n)`, `redes_referencia()`: crean
  redes por nombre, las 30 realizaciones de una red aleatoria, o una red de
  cada tipo.

### Pruebas (`tests/test_redes.py`, 47 pruebas, todas aprobadas)

- **Matriz A:** es simétrica, binaria y sin autoenlaces.
- **Laplaciano:** es simétrico, sus filas suman 0, no tiene autovalores
  negativos y tiene un solo autovalor nulo (la red es conexa). Estas
  propiedades sostienen la solución modal.
- **d₀ᵢ y Nᵢ:** coinciden con los que calcula NetworkX en las 4 redes.
- **Valores conocidos:**
  - malla: fuente 44, d máxima 10, 180 enlaces;
  - malla desde la esquina: C(f + c, f) caminos al nodo (f, c);
  - anillo: d máxima 25.
- **Redes aleatorias:** son reproducibles, semillas distintas dan redes
  distintas y las 30 realizaciones son conexas.
- **Casos límite:** nodos inalcanzables, autoenlaces, nodos mal numerados,
  topología desconocida y k impar.

## 5. `modelo.py`: dinámica de la red

**Para qué sirve:** resuelve la ecuación del modelo y entrega las cargas Qᵢ(t)
y las corrientes Iᵢ(t) de todos los nodos.

```
Q̈ + γ Q̇ + (ω₀² 𝕀 + K Λ) Q = 0
```

En primer orden, con I = Q̇ (punto 4, paso 7 de la teoría):

```
Q̇ = I
İ = −γ I − ω₀² Q − K Λ Q
```

### Parámetros (`Parametros`)

Agrupa los valores físicos en unidades SI. El acoplamiento se elige con
κ = K/ω₀², como en el plan.

| Campo o propiedad | Valor base | Significado |
|-------------------|-----------|-------------|
| `L`, `C`, `R` | 1 mH, 1 µF, 1 Ω | Elementos de cada malla |
| `Q0` | 1 µC | Carga inicial de la fuente |
| `kappa` | 0.1 | κ = K/ω₀² |
| `gamma` | 1000 s⁻¹ | γ = R/L |
| `omega0` | 31 623 rad/s | ω₀ = 1/√(LC) |
| `K` | κ ω₀² | Constante de acoplamiento (s⁻²) |
| `Cc` | C/κ | Capacitor de acoplamiento equivalente |
| `E0` | 0.5 µJ | E₀ = Q₀²/(2C) |
| `factor_calidad` | 31.6 | ω₀/γ |
| `T` | 10 ms | Duración por defecto, 10/γ |

`p.con(kappa=1.0)` crea una copia con un solo valor cambiado. Es útil para
cumplir la regla del plan de variar un parámetro a la vez. Los valores de κ del
plan están en `KAPPAS_BASE` (0.01 a 1) y `KAPPAS_E2` (añade 3 y 10).

### Integrador principal: DOP853 (`integrar_dop853`)

- **Qué es:** un Runge–Kutta de orden 8 con paso adaptativo, tomado de SciPy.
  Su documentación lo recomienda para alta precisión.
- **Tolerancias:** rtol = 10⁻¹⁰. La tolerancia absoluta se escala por separado
  para cargas (10⁻¹² Q₀) y para corrientes (10⁻¹² ω_max Q₀), porque Q e I
  difieren en varios órdenes de magnitud. Las tolerancias por defecto de SciPy
  (10⁻³ y 10⁻⁶) darían resultados sin sentido con cargas del orden de 10⁻⁶ C.
- **Solución densa:** la opción `denso=True` devuelve una solución continua.
  Servirá para refinar los tiempos de llegada entre muestras.

### Solución de referencia: modos normales (`solucion_modal`)

Implementa el punto 6 de la teoría:

1. Diagonaliza Λ con `eigh`. Esto da los autovalores λₙ y los autovectores
   ortonormales vₙ.
2. Cada modo es un oscilador independiente con ωₙ² = ω₀² + Kλₙ y
   Ωₙ² = ωₙ² − γ²/4.
3. Cada coordenada modal aₙ(t) se resuelve con la fórmula exacta del oscilador
   amortiguado, y luego se reconstruye Q = V a.

Detalles de la implementación:

- **Regímenes:** cubre los tres. Con los parámetros base todos los modos son
  subamortiguados, pero el experimento E5 variará γ.
- **Memoria:** evalúa por bloques de tiempo.
- **Condiciones iniciales:** acepta cualquiera. Esto servirá para probar el
  modo uniforme.
- **Pesos modales:** `modos_normales()` y `Modos.pesos(fuente)` dan los pesos
  vₙ(i)vₙ(0), que el experimento E4 usará para explicar por qué nodos a igual
  distancia responden distinto.

### Integrador de comprobación: RK4 propio (`integrar_rk4`)

Es el Runge–Kutta clásico de orden 4, con paso fijo y escrito a mano. No
genera resultados. Cumple dos funciones:

- **Prueba de convergencia del plan:** al dividir el paso entre 2, el error
  debe bajar 2⁴ = 16 veces.
- **Explicación del algoritmo en la exposición.**

En cada paso se evalúa la pendiente cuatro veces (k₁ a k₄) y se combinan:

```
k₁ = f(yₙ)
k₂ = f(yₙ + h/2 · k₁)
k₃ = f(yₙ + h/2 · k₂)
k₄ = f(yₙ + h · k₃)
yₙ₊₁ = yₙ + h/6 · (k₁ + 2k₂ + 2k₃ + k₄)
```

Aquí y = (Q, I) y f(Q, I) = (I, −γI − MQ). El parámetro `subpasos` divide cada
intervalo de muestreo en varios pasos de RK4. Se usa con
`simular(red, p, "rk4", subpasos=...)`.

**Orden observado** (malla, κ = 1, 2 ms, frente a la solución modal):

| Paso h | Error máximo / Q₀ | Orden |
|--------|-------------------|-------|
| 6.7 µs | 1.4 × 10⁻² | — |
| 3.3 µs | 9.0 × 10⁻⁴ | 3.97 |
| 1.7 µs | 5.6 × 10⁻⁵ | 4.00 |
| 0.84 µs | 3.5 × 10⁻⁶ | 4.00 |

### Muestreo temporal (`malla_temporal`)

Los instantes guardados son equiespaciados, con **100 muestras por período del
modo más rápido**, ω_max = √(ω₀² + Kλ_max). Se usa el modo más rápido porque,
con κ grande, la red oscila hasta 9 veces más rápido que ω₀.

| κ | Muestras en T = 10/γ (ER) | Memoria Q + I |
|---|---------------------------|---------------|
| 0.01 | 5 346 | 9 MB |
| 1 | 18 676 | 30 MB |
| 10 | 57 093 | 91 MB |

### Entrada de alto nivel (`simular`)

`simular(red, p, metodo="dop853" | "modal" | "rk4")` hace tres cosas:

1. Fija las condiciones iniciales del PDF: Q₀ en la fuente, el resto en cero y
   todas las corrientes nulas.
2. Elige la malla temporal.
3. Devuelve una `Simulacion`, con `t`, `Q`, `I` (forma n_t × N; columna i =
   nodo i), el laplaciano `Lambda`, los parámetros, la fuente, el método y
   datos del cálculo. Guarda `Lambda` porque la energía de acoplamiento lo
   necesita.

`sim.t_gamma` da el tiempo adimensional γt que usan los gráficos.

### Verificación inicial

Fue la primera comprobación, hecha a mano. Ya forma parte de las pruebas
automáticas (sección 7).

| Comprobación | Resultado |
|--------------|-----------|
| K = 0 frente a la fórmula analítica del punto 2 de la teoría | Error 1.9 × 10⁻⁹ Q₀; los demás nodos quedan exactamente en 0 |
| DOP853 frente a la solución modal: 4 redes, κ = 0.01, 0.1, 1 y 10 | Error máximo 1.5 × 10⁻⁹ Q₀ en carga y en corriente |
| Régimen sobreamortiguado (R = 100 Ω) y crítico (R = 63.2 Ω) | Error ≤ 2.6 × 10⁻¹⁰ Q₀ |
| Costo de DOP853 | 0.3 a 6 s por simulación; la solución modal, de 0.02 a 1.5 s |

El criterio del plan pide un error mucho menor que 10⁻³ Q₀, que es la amplitud
del umbral. Queda superado por unos seis órdenes de magnitud.

## 6. `analisis.py`, parte de energía

**Para qué sirve:** convierte Q(t) e I(t) en energías. Atiende el objetivo O6
del PDF y aplica los puntos 2 y 5 de la teoría. Más adelante, en la Fase 3,
este módulo también tendrá los tiempos de llegada y las estadísticas por
distancia.

### Por qué hacen falta varias energías

La ecuación (13) del PDF define la energía de cada malla, Eᵢ, pero no incluye
la energía guardada en los capacitores de acoplamiento C_c. Por eso:

- **ΣEᵢ no es la energía total.** Con K ≠ 0 no se conserva aunque R = 0.
- **ΣEᵢ puede superar E₀**, porque la energía inicial real es
  H(0) = E₀(1 + k₀κ), con k₀ el grado de la fuente.
- **H es la cantidad con balance exacto:** dH/dt = −RΣIᵢ². Es la herramienta
  para validar el código.

### Funciones

| Función | Fórmula | Uso |
|---------|---------|-----|
| `energia_nodos(Q, I, p)` | Eᵢ = Qᵢ²/(2C) + LIᵢ²/2 | Umbral, gráficos y promedios exigidos por el PDF |
| `energia_acoplamiento(Q, Λ, p)` | U = (LK/2) QᵀΛQ | Energía en los C_c |
| `potencia_disipada(I, p)` | RΣIᵢ² | Calor en las resistencias |
| `potencia_intercambio(Q, I, Λ, p)` | Pᵢ = −LK Iᵢ (ΛQ)ᵢ | Potencia que la malla i recibe de sus enlaces; explica por qué Eᵢ puede subir |
| `energia_inicial(p, k₀)` | H(0) = E₀(1 + k₀κ) | Valor teórico para comprobar |
| `energias(sim)` | Todas las anteriores | Devuelve un objeto `Energias` |
| `energia_media(t, E)` | ⟨Eᵢ⟩ = (1/T)∫Eᵢ dt, ecuación (16) | Experimento E3; se integra con la regla de Simpson |
| `fraccion_energia(⟨E⟩)` | ⟨Eᵢ⟩/Σⱼ⟨Eⱼ⟩ | Apoyo que sí suma 1 |

### El objeto `Energias`

Contiene `E` (n_t × N), `U`, `P` y `E0`, y calcula:

- `H = ΣEᵢ + U`, la energía total;
- `suma_nodos = ΣEᵢ`;
- `E_rel = Eᵢ/E₀`, la normalización del PDF;
- `disipada`, la energía convertida en calor hasta cada instante;
- `residuo_balance()`.

`residuo_balance()` es la forma integrada del balance:

```
[H(t) + ∫₀ᵗ RΣIᵢ² dt' − H(0)] / H(0)   →   debe ser ≈ 0 en todo t
```

Se usa la forma integrada y no la derivada, porque derivar datos muestreados
amplifica el ruido. La integral se calcula con Simpson acumulado (error ∝ h⁴),
que es más preciso que el trapecio usado en la prueba de la Fase 1.

### Verificación inicial

Primera comprobación, hecha a mano; ya forma parte de las pruebas automáticas
(sección 7).

**Malla con fuente interior (k₀ = 4).** Se compara con la tabla del punto 5 de
la teoría.

| κ | H(0)/E₀ | Teoría | máx ΣEᵢ/E₀ | U/H en t = 0 | U/H promedio | máx \|residuo\| | H e^(γt)/H(0) |
|---|---------|--------|------------|--------------|--------------|-----------------|----------------|
| 0.01 | 1.040 | 1.04 | 1.011 | 0.038 | 0.019 | 1.3 × 10⁻⁷ | 0.985 a 1.016 |
| 0.1 | 1.400 | 1.40 | 1.346 | 0.286 | 0.143 | 7.6 × 10⁻⁸ | 0.988 a 1.013 |
| 1 | 5.000 | 5.00 | 4.694 | 0.800 | 0.400 | 2.6 × 10⁻⁸ | 0.995 a 1.007 |

Coincide con la Fase 1 en todas las columnas.

**Otras comprobaciones:**

- **Las 4 redes, con κ = 0.1 y κ = 10:** el residuo del balance es ≤ 9 × 10⁻⁸,
  y ΣEᵢ nunca supera la cota H(0).
- **Origen del residuo:** con κ = 1, al pasar de 50 a 100 y luego a 200
  muestras por período, bajó de 4.2 × 10⁻⁷ a 2.6 × 10⁻⁸ y después a
  1.7 × 10⁻⁹. Baja unas 16 veces cada vez que se duplica el muestreo, que es
  el orden h⁴ de Simpson. Por lo tanto, el residuo viene de la integral
  numérica y no del modelo ni del integrador.
- **Sin resistencia (R = 0, κ = 0.1):** H varía 1.2 × 10⁻⁹, es decir, se
  conserva. ΣEᵢ varía un 40 %, como predice la teoría.
- **Balance de una sola malla** (nodo 34, vecino de la fuente): dEᵢ/dt =
  −RIᵢ² + Pᵢ se cumple con un error de 10⁻⁶ respecto al máximo de Eᵢ.
- **Fracción ⟨Eᵢ⟩/Σ⟨Eⱼ⟩:** suma exactamente 1.

## 7. Pruebas automáticas

Hay 145 pruebas en total, que se corren con `python -m pytest`. Ningún
resultado se analiza antes de que todas pasen.

| Archivo | Pruebas | Qué cubre |
|---------|---------|-----------|
| `tests/test_redes.py` | 49 | Topologías, laplaciano, distancias, caminos, semillas, cambio de fuente y de tamaño (sección 4) |
| `tests/test_modelo.py` | 38 | Parámetros, integradores, solución modal y 6 pruebas del plan |
| `tests/test_energia.py` | 35 | Fórmulas de energía y 3 pruebas del plan |
| `tests/test_analisis.py` | 33 | Tiempos de llegada, rapidez del frente, estadísticas por distancia (también por realización), peso modal y relación a igual distancia (secciones 9, 12, 14 y 15) |
| `tests/test_videos.py` | 5 | Tiempos de los cuadros, envolvente por cuadro, escala logarítmica, generación de un video y de una imagen fija (sección 20) |
| `tests/test_resultados_graficos.py` | 14 | Guardado y carga de `.npz` y `.csv`; generación de G1 a G10 y de las figuras de ajuste; envolvente por máximos; formato de los umbrales; normalización por grupo |
| `tests/test_ajustes.py` | 14 | Fórmula de AICc; recuperación exacta de parámetros de los 8 modelos; elección del modelo verdadero con ruido; límites de la rapidez; datos insuficientes; desviación en d = 1 (sección 18) |
| `tests/conftest.py` | — | Guarda en caché las simulaciones para que las pruebas las compartan |

### Las 9 pruebas de validación del plan

| Prueba del plan | Caso | Criterio exigido | Dónde |
|-----------------|------|------------------|-------|
| Oscilador aislado | K = 0 | Coincide con la fórmula analítica con error < 10⁻⁸ Q₀; con DOP853, los demás nodos quedan exactamente en 0 | `test_oscilador_aislado` |
| Conservación | K = 0, R = 0 | E₀ constante, con variación < 10⁻⁸ | `test_conservacion_sin_acoplamiento_ni_resistencia` |
| Decaimiento | K = 0, R > 0 | E(t) igual a la fórmula del punto 2, paso 14 (error < 10⁻⁸ E₀); cae a < 10⁻⁴ E₀ en T | `test_decaimiento_sin_acoplamiento` |
| Balance general | K > 0, R > 0 | Residuo de dH/dt = −RΣIᵢ² < 10⁻⁶, en 4 redes × 3 valores de κ | `test_balance_de_H` |
| Dos nodos | N = 2 | Batidos exactos con ω₀ y √(ω₀² + 2K), error < 10⁻⁸ Q₀ | `test_dos_nodos_*` |
| Modo uniforme | Las 4 redes | ΣQᵢ(t) igual al oscilador aislado, error < 10⁻⁸ Q₀ | `test_modo_uniforme` |
| Simetría | Anillo | Nodos +d y −d iguales, error < 10⁻⁹ Q₀; también la diagonal de la malla | `test_simetria_*` |
| Convergencia | RK4 | Orden entre 3.8 y 4.2 en tres divisiones del paso | `test_rk4_orden_4` |
| Referencia | DOP853 frente a la solución modal | Error < 10⁻⁷ Q₀, en 4 redes × 3 valores de κ y con κ = 10 | `test_dop853_coincide_con_modal*` |

### Pruebas adicionales

- **Teoría, punto 5:**
  - H(0) = E₀(1 + k₀κ);
  - H nunca aumenta;
  - ΣEᵢ ≤ H(0);
  - con R = 0, H se conserva y ΣEᵢ no;
  - ΣEᵢ puede superar E₀.
- **Teoría, punto 6:** H decae como e^(−γt) para cualquier κ.
- **Balance de una malla:** dEᵢ/dt = −RIᵢ² + Pᵢ.
- **Identidades de energía:**
  - U es igual a la suma sobre los enlaces;
  - ΣPᵢ = −dU/dt.
- **Solución modal:**
  - es exacta en los regímenes crítico y sobreamortiguado;
  - funciona con condiciones iniciales arbitrarias;
  - los pesos modales suman δᵢ₀;
  - el modo uniforme pesa 1/N.

### Un caso que hubo que ajustar

En la prueba del oscilador aislado se exigía que los demás nodos quedaran
exactamente en cero. DOP853 lo cumple. La solución modal da unos 10⁻¹⁶ Q₀,
porque pasa por los autovectores y queda redondeo de punto flotante. No es un
error: para ese método el criterio quedó en < 10⁻¹³ Q₀.

## 8. Pseudocódigo y diagrama de flujo

Están en `docs/pseudocodigo_y_diagrama_flujo.md`. Es el entregable de la Fase 2
que pide el criterio «Programación y lógica» (10 % de la nota). Contiene:

| Sección | Contenido |
|---------|-----------|
| 1 | Tabla que relaciona cada ecuación de la teoría y del PDF con la función que la implementa |
| 2 | Diagrama de flujo general de un experimento. Incluye las decisiones (red aleatoria conexa, elección del método, control del balance de H) y marca con borde punteado lo que es de la Fase 3 |
| 3 | Pseudocódigo de cada pieza: construcción de redes, BFS de distancias y caminos, sistema de ecuaciones, DOP853, RK4, solución modal, `simular`, energía y balance, y validación. RK4 y la solución modal tienen además su propio diagrama |
| 4 | Diagrama de módulos: qué módulo entrega datos a cuál |
| 5 | Cómo usar el material en el informe, la exposición y la defensa |

Los diagramas están escritos en Mermaid. GitHub los muestra como imagen
dentro del Markdown. Para pasarlos a Word o a las diapositivas, cada bloque se
puede exportar a PNG o SVG desde mermaid.live.

## 9. Fase 3: tiempos de llegada y estadísticas por distancia

**Para qué sirve:** convierte la energía de cada nodo en las dos cantidades
que estudian los experimentos E2 a E4. Está en `analisis.py`.

- **Tiempo de llegada tᵢ**, ecuación (20) del PDF: primer instante en que
  Eᵢ ≥ E_th = u · E₀. Responde P3 y P5.
- **Estadísticas por distancia**, ecuaciones (21) a (23): Ē(d) y σ_E(d).
  Responden P4 y P8.

### Tiempos de llegada

| Función | Qué hace |
|---------|----------|
| `indice_primer_cruce(E, E_th)` | Primera muestra con Eᵢ ≥ E_th en cada nodo; −1 si no la hay |
| `tiempos_llegada(t, E, E_th, energia_en)` | Ubica el cruce entre las dos muestras que lo encierran. Usa interpolación, o la raíz exacta si recibe una función E(t) |
| `evaluador_modal(sim)` | E(t) exacta en cualquier instante, por modos normales |
| `evaluador_denso(sim)` | E(t) a partir de la solución continua de DOP853 |
| `llegadas(sim, umbral, refinar)` | Entrada principal; devuelve un objeto `Llegadas` |
| `Llegadas` | `t` (s), `t_gamma` (γtᵢ), `alcanzado`, `n_no_alcanzados`, `umbral` |
| `UMBRALES` | 10⁻⁴, 10⁻⁶ y 10⁻⁸, para la sensibilidad al umbral del experimento E2 |

**Nodos no alcanzados.** Un nodo puede no cruzar nunca el umbral, porque el
amortiguamiento apaga la señal antes de que llegue. Su tiempo queda en NaN, sin
asignarle T ni cero, como pide el plan. La fuente, que empieza con E₀, tiene
tᵢ = 0.

**Cómo se ubica el cruce (`refinar`):**

- `"auto"` (por defecto): usa `"denso"` si la simulación se hizo con
  `denso=True`; si no, `"modal"`.
- `"denso"` y `"modal"`: encuentran la raíz de Eᵢ(t) − E_th con `brentq`
  dentro del intervalo entre muestras. Cuestan menos de 0.1 s por simulación.
- `"interpolar"`: más rápido, pero no sirve para los vecinos de la fuente
  (ver hallazgo abajo).

**Hallazgo: la interpolación falla en los vecinos de la fuente.** Con
κ ≳ 0.1, los nodos a d = 1 cruzan 10⁻⁶ E₀ en menos de 1 µs, antes de la
primera muestra. En ese tramo E ∝ t², y la interpolación lineal desde E = 0 dio
errores de hasta 99 %. Con DOP853 continuo, el resultado coincide con la
solución exacta con diferencias de 10⁻⁹. Por eso el valor por defecto refina
la raíz.

### Estadísticas por distancia

`por_distancia(valores, distancias)` agrupa cualquier valor por nodo (⟨Eᵢ⟩,
tᵢ, …) según d₀ᵢ y devuelve un objeto `PorDistancia` con estos campos:

- `d` y `N_d`;
- `n_validos`: los nodos con valor finito. Si hay nodos no alcanzados, es
  menor que N_d;
- `media`: ecuación (21);
- `sigma`: ecuación (23), con ddof = 1. Es NaN si hay menos de 2 valores,
  porque no está definida con N_d = 1;
- `minimo` y `maximo`;
- `sigma_relativa = σ/media`, para el gráfico G8.

Esta σ_E(d) mide las diferencias entre nodos dentro de una red. La dispersión
entre las 30 realizaciones de una red aleatoria se calculará aparte, como
exige el plan.

### Verificación frente a la teoría (punto 7, malla con fuente interior)

| κ | Nodo | d | Nᵢ | tᵢ teoría (µs) | tᵢ ahora (µs) |
|---|------|---|----|----------------|---------------|
| 0.01 | 45 | 1 | 1 | 3.18 | 3.17 |
| 0.01 | 46 | 2 | 1 | 323 | 322.9 |
| 0.1 | 46 | 2 | 1 | 28.3 | 28.11 |
| 0.1 | 49 | 5 | 1 | 587 | 586.7 |
| 1 | 46 | 2 | 1 | 5.80 | 5.80 |
| 1 | 49 | 5 | 1 | 71.7 | 71.46 |
| 10 | 49 | 5 | 1 | 18.5 | 18.41 |

Las diferencias son de 0.7 % o menos. Los valores actuales son más precisos,
porque refinan la raíz y la prueba de la Fase 1 trabajó solo con muestras.

| Comprobación | Teoría | Ahora |
|--------------|--------|-------|
| Nodos alcanzados con T = 10/γ (κ = 0.003, 0.01, 0.03) | 12, 44, 99 | 12, 44, 99 |
| t(Nᵢ = 2)/t(Nᵢ = 1) a d = 2 (κ = 0.01, 0.1, 1, 10) | 0.70, 0.79, 0.81, 0.82 | 0.70, 0.78, 0.79, 0.79 |

La razón entre tiempos cae dentro del rango que predicen las fórmulas de la
teoría, de 2^(−1/2) = 0.71 a 2^(−1/3) = 0.79. Las pequeñas diferencias con
κ ≥ 1 vienen del muestreo más grueso de la Fase 1.

### Pruebas (`tests/test_analisis.py`, 25)

- **Detección del cruce:**
  - interpolación exacta para leyes de potencia;
  - la fuente llega en t = 0;
  - los nodos no alcanzados quedan en NaN;
  - refinamiento con una función exacta.
- **Tablas de la teoría:**
  - nodos alcanzados;
  - siete tiempos de llegada;
  - efecto de Nᵢ.
- **Consistencia:**
  - el resultado con DOP853 continuo coincide con el modal;
  - un umbral más bajo da llegadas más tempranas;
  - las llegadas son simétricas en el anillo.
- **Estadísticas:**
  - caso sintético con NaN, ddof = 1 y N_d = 1;
  - N_d coincide con `redes` en las 4 redes.

**Un caso que hubo que ajustar:** la prueba de los umbrales falló al
principio porque comparaba tiempos NaN. En NumPy, cualquier comparación con
NaN da falso. Se reescribió para comparar solo los nodos alcanzados y
comprobar, además, que todo nodo que cruza un umbral alto también cruza los
más bajos.

## 10. Fase 3: gráfico G1 y experimento E1

### Infraestructura común

- **`red_rlc/resultados.py`:** define dónde va cada salida (`resultados/datos`,
  `resultados/figuras`, `resultados/videos`).
  - `guardar_npz` escribe los arreglos comprimidos junto con un campo `meta`
    en JSON: experimento, red, semilla, intentos, parámetros, método, umbral y
    fecha. Así cada archivo dice cómo se generó.
  - `cargar_npz` devuelve `(meta, arreglos)`.
  - `guardar_csv` guarda las tablas resumen.
- **`red_rlc/graficos.py`:** estilo común para todas las figuras, con fondo
  claro, rejilla tenue, trazos finos y títulos con unidades. Tiene dos
  paletas:
  - **categórica**, en orden fijo y validada para daltonismo. Cada topología
    tiene su color fijo en todas las figuras: malla azul, anillo naranja,
    mundo pequeño verde agua, ER amarillo;
  - **secuencial azul**, de claro a oscuro, para magnitudes como la distancia.

  `guardar(fig, nombre)` escribe el PNG (200 dpi) y el PDF.
- **Scripts (`scripts/`):** cada uno se corre desde la raíz con
  `python scripts/<nombre>.py`. Agregan la raíz del proyecto al `sys.path`, así
  que no hace falta instalar el paquete.

### G1: topologías y distribución de distancias (`scripts/g1_redes.py`)

Archivos: `resultados/figuras/g1_redes.png` y `.pdf`; datos en
`resultados/datos/g1_distancias.csv`. Sostiene el «diseño del estudio».

- **Fila superior:** cada red dibujada con los nodos coloreados por distancia
  a la fuente (azul claro = cerca, oscuro = lejos) y la fuente en naranja.
  - malla: en su rejilla;
  - anillo y mundo pequeño: en círculo, así los atajos de WS se ven como
    cuerdas;
  - ER: en disposición de resortes, con semilla fija.
- **Fila inferior:** N_d de la realización de referencia, en barras. Para las
  redes aleatorias se superpone la mediana de las 30 realizaciones con el
  rango entre los percentiles 10 y 90.

**Ajustes de diseño tras revisar la figura:**

- **Rango en vez de ± σ:** ± σ hacía que algunas barras de error bajaran de 0,
  y N_d no puede ser negativo. Se usa el rango entre percentiles.
- **Mediana en vez de media:** la media puede caer fuera de ese rango cuando la
  distribución es asimétrica.
- **Leyenda única:** estaba tapando los datos; ahora hay una sola, debajo de
  la figura.
- **Ejes enteros:** se fuerzan marcas enteras.
- **Distancias raras omitidas:** las que casi ninguna realización alcanza no
  se dibujan.

**Datos estructurales:**

| Red | Enlaces | ⟨k⟩ | d máx (referencia) | d máx medio (30) | ⟨k⟩ medio (30) |
|-----|---------|-----|---------------------|-------------------|----------------|
| Malla | 180 | 3.60 | 10 | — | — |
| Anillo | 200 | 4.00 | 25 | — | — |
| Mundo pequeño | 200 | 4.00 | 10 | 8.50 | 4.00 |
| Erdős–Rényi | 222 | 4.44 | 5 | 5.43 | 4.19 |

Las 30 redes ER conexas requirieron 164 intentos, es decir, un 18.3 % de
muestras conexas, como estimó el plan. El ⟨k⟩ medio de ER, 4.19, supera el
valor esperado sin condicionar (4), tal como anticipó la teoría: exigir
conexidad favorece redes con más enlaces.

### E1: dinámica (`scripts/e1_dinamica.py`)

**Diseño:**

- 4 redes de referencia (semilla 2026) × κ ∈ {0.01, 0.03, 0.1, 0.3, 1}; el
  resto de los parámetros queda fijo, con T = 10/γ;
- integración con DOP853 y solución densa;
- tiempos de llegada con umbral 10⁻⁶ E₀, refinados con la solución densa.

**Salidas en `resultados/datos/`** (64 MB en total, no se versionan):

- `e1_<red>_k<κ>.npz`, uno por simulación, con:
  - t;
  - Eᵢ(t) de todos los nodos, en float32;
  - Qᵢ(t) de un **nodo representativo por distancia**: el de más caminos
    más cortos, o el de menor índice si hay empate;
  - H, U y RΣIᵢ²;
  - ⟨Eᵢ⟩ y tᵢ;
  - d₀ᵢ, Nᵢ, grados, fuente y A.
- `e1_resumen.csv`: una fila por simulación, con los controles de calidad y
  las cifras principales.

**Controles de calidad.** Las 20 simulaciones pasan los tres:

- residuo del balance ≤ 1.3 × 10⁻⁷;
- H(0) igual a E₀(1 + k₀κ);
- ΣEᵢ nunca supera H(0).

Las 20 tardan unos 35 s en total.

**Observación numérica** (solo los datos; la interpretación física va en la
Fase 4):

| Red | κ | Alcanzados (de 99) | γt de la última llegada | ⟨E_fuente⟩/Σ⟨Eⱼ⟩ |
|-----|---|--------------------|--------------------------|-------------------|
| Malla | 0.01 | 44 | 4.29 | 0.87 |
| Malla | 0.1 | 99 | 1.05 | 0.27 |
| Malla | 1 | 99 | 0.16 | 0.07 |
| Anillo | 0.01 | 18 | 5.88 | 0.87 |
| Anillo | 0.1 | 99 | 5.53 | 0.32 |
| Anillo | 1 | 99 | 0.77 | 0.11 |
| Mundo pequeño | 0.01 | 23 | 6.14 | 0.89 |
| Mundo pequeño | 0.1 | 99 | 1.61 | 0.31 |
| Mundo pequeño | 1 | 99 | 0.23 | 0.10 |
| Erdős–Rényi | 0.01 | 91 | 5.22 | 0.83 |
| Erdős–Rényi | 0.1 | 99 | 0.42 | 0.31 |
| Erdős–Rényi | 1 | 99 | 0.06 | 0.14 |

- **κ = 0.01:** el número de nodos alcanzados ordena las redes según su
  distancia máxima: ER (91) > malla (44) > mundo pequeño (23) > anillo (18).
- **κ ≥ 0.1:** todas las redes se alcanzan por completo. La última llegada
  ocurre antes al subir κ, y lo más tarde es en el anillo y lo más temprano
  en ER.
- **Energía retenida en la fuente:** la fracción de la energía media que
  queda en la fuente baja de ≈ 0.85 a ≈ 0.1 al pasar de κ = 0.01 a κ = 1.
- **Cotas:** H(0)/E₀ va de 1.03 a 7.00 y ΣEᵢ/E₀ llega a 6.6 (ER con κ = 1,
  fuente de grado 6). Ninguna supera su cota.

## 11. Fase 3: gráficos G3 y G4 (datos de E1)

Los genera `scripts/g3_g4_dinamica.py`, que lee los `.npz` de E1, así que
antes hay que haber corrido E1. Las dos figuras usan la misma rejilla: las 4
redes en columnas y κ = 0.01, 0.1 y 1 en filas. Así una sola figura muestra
el efecto de la topología (horizontal) y del acoplamiento (vertical).

### G3: energía de un nodo representativo por distancia

Archivos: `resultados/figuras/g3_energia_por_distancia.png` y `.pdf`. Responde
P1.

- **Curvas:** Eᵢ(t)/E₀ en escala logarítmica para la fuente (naranja) y hasta
  6 distancias repartidas entre 1 y d máx (azul, más oscuro cuanto más
  lejos). El nodo de cada distancia es el representativo que guardó E1.
- **Referencias:** H(t)/E₀ en punteado y el umbral de 10⁻⁶ E₀ en línea
  discontinua.
- **Envolvente:** cada curva es el máximo de Eᵢ en 400 intervalos de tiempo.
  Con κ = 1, Eᵢ oscila tan rápido que la curva completa se volvía una mancha
  ilegible; la envolvente conserva la tendencia y los picos.
- **Leyendas:** van debajo de cada columna, porque cada red muestra distancias
  distintas. Dentro de los paneles tapaban las curvas.

### G4: mapa de energía por nodo y tiempo

Archivos: `resultados/figuras/g4_mapa_nodo_tiempo.png` y `.pdf`. Responde P1
y P2.

- **Filas del mapa:** los nodos, ordenados por distancia a la fuente (arriba
  d = 0). A igual d, primero los de más caminos más cortos.
- **Color:** log₁₀(Eᵢ/E₀) en la escala azul secuencial, entre −12 y 0, con una
  barra de colores común. El tiempo se agrupa en 600 intervalos y se toma el
  máximo de cada uno.
- **Frente de llegada:** puntos naranjas en el tiempo de llegada de cada nodo,
  con el umbral de 10⁻⁶ E₀.
- **No alcanzados:** se indica cuántos nodos no llegan.
- **Ajuste tras revisar la figura:** las etiquetas de distancia de los grupos
  pequeños, cerca de la fuente, se encimaban. Ahora solo se muestran las que
  tienen espacio.

### Observación numérica en las figuras

La interpretación va en la Fase 4.

- **κ = 0.01:** la energía avanza por escalones de distancia, y cada nodo
  alcanza un máximo cada vez más bajo.
  - Faltan por llegar 55 nodos en la malla, 81 en el anillo, 76 en el mundo
    pequeño y 8 en ER.
  - En la malla, la fuente cae por debajo de sus vecinos hacia γt ≈ 5.
- **κ = 0.1, anillo:** el frente es una recta en el mapa, es decir, la
  llegada crece en proporción a d, de γt ≈ 0 a ≈ 5.5 en d = 25. En las otras
  redes el frente es más corto y curvo.
- **κ = 1:** el frente cruza toda la red antes de γt ≈ 0.8. Desde entonces,
  todos los nodos tienen energías del mismo orden y siguen la caída de H.
- **H(t):** en todos los paneles decae como e^(−γt), como predice la teoría.

## 12. Fase 3: experimento E2, tiempos de llegada

Lo genera `scripts/e2_llegadas.py`. Responde P2, P3 y P5.

### Diseño

| Qué se varía | Valores |
|--------------|---------|
| κ | 0.01, 0.03, 0.1, 0.3, 1, 3 y 10 (`KAPPAS_E2`) |
| Red | Malla y anillo, 1 realización. Mundo pequeño y ER, **30 realizaciones** (semillas 2026 a 2055) |
| Umbral E_th/E₀ | 10⁻⁴, 10⁻⁶ y 10⁻⁸ |

En total son 434 simulaciones con DOP853 y solución densa. El tiempo de
llegada se refina con la raíz exacta en los tres umbrales.

- **Ejecución en paralelo:** 6 procesos, cada uno con un solo hilo de álgebra
  lineal. Las simulaciones más costosas (κ grande) se lanzan primero para
  repartir mejor la carga.
- **Costo:** **4 min 19 s** en total. El caso más pesado (ER, κ = 10) usa unos
  330 MB y tarda unos 8 s.
- **Medida resumen:** se agregó `analisis.rapidez_frente(t, d)`, que ajusta
  tᵢ = a + b·dᵢ por mínimos cuadrados sobre los nodos alcanzados con d ≥ 1 y
  da v = 1/b en nodos por segundo. Se reporta como v/ω₀.
- **Datos para E3:** de paso se guarda ⟨Eᵢ⟩ de cada nodo. E3 usa
  exactamente estas redes y valores de κ, así que no hay que repetir las
  integraciones.

**Salidas:**

- `e2_<red>.npz`, con ejes [κ, realización, umbral, nodo] para `t_llegada`
  (en s), [κ, realización, nodo] para `E_media`, y la estructura de cada
  realización (distancias, caminos, grados, fuente, intentos);
- `e2_resumen.csv`, una fila por (red, κ, umbral), con la mediana y los
  percentiles 10–90 entre realizaciones.

Todo ocupa 1.2 MB.

**Controles de calidad** (las 434 simulaciones): el residuo del balance de H
es ≤ 1.3 × 10⁻⁷ y el error relativo de H(0) ≤ 3.3 × 10⁻¹⁶. El script no
guarda nada si algún control falla.

### Resultados, umbral 10⁻⁶ (medianas sobre realizaciones)

Rapidez del frente v/ω₀ y nodos alcanzados (de 99):

| κ | Malla | Anillo | Mundo pequeño | Erdős–Rényi |
|---|-------|--------|---------------|-------------|
| 0.01 | 0.028 · 44 | 0.023 · 18 | 0.022 · 30 | 0.025 · 89 |
| 0.03 | 0.073 · 99 | 0.041 · 46 | 0.043 · 96 | 0.088 · 99 |
| 0.1 | 0.258 · 99 | 0.130 · 99 | 0.174 · 99 | 0.300 · 99 |
| 0.3 | 0.666 · 99 | 0.368 · 99 | 0.470 · 99 | 0.864 · 99 |
| 1 | 1.759 · 99 | 0.937 · 99 | 1.322 · 99 | 2.037 · 99 |
| 3 | 3.296 · 99 | 1.972 · 99 | 2.676 · 99 | 3.868 · 99 |
| 10 | 6.337 · 99 | 4.088 · 99 | 5.232 · 99 | 7.667 · 99 |

**Exponente de v frente a κ** (pendiente log–log):

| Red | Acoplamiento débil (κ = 0.03 a 0.3) | Acoplamiento fuerte (κ = 1 a 10) |
|-----|--------------------------------------|-----------------------------------|
| Malla | 0.96 | 0.56 |
| Anillo | 0.95 | 0.64 |
| Mundo pequeño | 1.04 | 0.60 |
| Erdős–Rényi | 0.99 | 0.58 |

La hipótesis del plan (punto 7 de la teoría) era que la rapidez crece como
K/ω₀ con acoplamiento débil (exponente 1) y como √K con acoplamiento fuerte
(exponente 1/2). Los datos la respaldan en las cuatro redes: el exponente débil
queda entre 0.95 y 1.04, y el fuerte entre 0.56 y 0.64. El tramo fuerte se
acerca a 1/2 sin llegar, lo que es coherente con que κ = 10 todavía no sea un
límite asintótico. Esto se confirmará con ajustes en la Fase 4.

**Variabilidad entre las 30 realizaciones** (v/ω₀, percentiles 10–90):

| Red | κ = 0.1 | κ = 1 | κ = 10 | Alcanzados con κ = 0.01 (mín–máx) |
|-----|---------|-------|--------|-------------------------------------|
| Mundo pequeño | 0.156–0.207 | 1.17–1.57 | 4.90–5.86 | 14–48 |
| Erdős–Rényi | 0.216–0.348 | 1.61–2.25 | 5.95–8.60 | 20–98 |

**Sensibilidad al umbral** (v/ω₀ con umbral 10⁻⁴ / 10⁻⁶ / 10⁻⁸):

| Red | κ = 0.1 | κ = 1 |
|-----|---------|-------|
| Malla | 0.19 / 0.26 / 0.35 | 1.20 / 1.76 / 2.11 |
| Anillo | 0.11 / 0.13 / 0.15 | 0.83 / 0.94 / 1.06 |
| Mundo pequeño | 0.10 / 0.17 / 0.25 | 0.82 / 1.32 / 1.74 |
| Erdős–Rényi | 0.15 / 0.30 / 0.53 | 1.22 / 2.04 / 2.76 |

### Observación numérica

La interpretación va en la Fase 4.

- **Orden de las redes:** para κ ≥ 0.03 la rapidez sigue el mismo orden en
  todos los valores de κ: ER > malla > mundo pequeño > anillo. El anillo es
  el más lento: entre 1.5 y 2.2 veces más lento que ER.
- **Nodos alcanzados con κ ≤ 0.03:** dependen mucho de la red y, en las
  aleatorias, de la realización. Con κ = 0.01, ER llega a entre 20 y 98 nodos
  según la semilla.
- **El umbral importa:** al bajar el umbral de 10⁻⁴ a 10⁻⁸, la rapidez
  aparente aumenta entre un 30 % (anillo) y un 250 % (ER, κ = 0.1). El tiempo
  de llegada mide el primer rastro de energía, no un frente físico único,
  como advirtió la teoría. El anillo es el menos sensible.
- **Dispersión entre realizaciones:** en las redes aleatorias es moderada
  para κ ≥ 0.1 (≈ ±15 % en WS, ≈ ±20 % en ER) y grande en el número de nodos
  alcanzados con κ pequeño.

## 13. Fase 3: gráficos G5 y G6 (datos de E2)

Los genera `scripts/g5_g6_llegadas.py`, que lee los `.npz` de E2. También
guarda `resultados/datos/g6_rapidez.csv`, con v/ω₀ por red, κ, umbral y
realización.

### G5: tiempo de llegada frente a la distancia

Archivos: `resultados/figuras/g5_llegada_vs_distancia.png` y `.pdf`.
Responde P2, P3 y P5.

- **Rejilla:** las 4 redes en columnas y κ = 0.01, 0.1, 1 y 10 en filas.
- **Puntos:** cada nodo alcanzado con el umbral 10⁻⁶ E₀. En las redes
  aleatorias aparecen los nodos de las 30 realizaciones, semitransparentes y
  con un pequeño desplazamiento horizontal para que no se tapen.
- **Líneas negras:** la mediana por distancia con cada umbral (continua 10⁻⁶,
  discontinua 10⁻⁴, punteada 10⁻⁸). La mediana se omite donde llega menos de
  la mitad de los nodos.
- **Texto:** cuántos nodos no llegan, en promedio por realización.

**Ajustes tras revisar la figura:**

- **Escala vertical propia:** con el eje vertical compartido por fila, la
  curva del anillo, que tarda hasta 5 veces más, quedaba cortada. Ahora cada
  panel tiene su propia escala.
- **Leyenda:** se movió debajo de la figura, porque chocaba con el texto de
  los nodos no alcanzados.

### G6: rapidez del frente frente al acoplamiento

Archivos: `resultados/figuras/g6_rapidez_vs_kappa.png` y `.pdf`. Responde P2
y P7.

- **Paneles:** uno por umbral, en escala log–log.
- **Curvas:** una línea por red con su color fijo, que une las medianas
  entre realizaciones; las franjas son los percentiles 10–90 de las 30
  realizaciones.
- **Referencias grises:** los límites de la teoría para la cadena, v = K/ω₀
  (pendiente 1) y v = √K (pendiente ½).
- **Etiquetas:** cada red se nombra al final de su línea.

**Ajustes tras revisar la figura:**

- **Etiquetas al final de las líneas:** se encimaban en el panel de 10⁻⁴.
  Ahora se separan al menos 0.12 décadas.
- **Rectas de referencia:** sus textos caían sobre los datos. Pasaron a la
  leyenda común.
- **Eje vertical:** se simplificó su etiqueta a v/ω₀.
- **Superíndices de los umbrales:** una función auxiliar ponía también en
  superíndice el «10» de la base. Se corrigió y se agregó una prueba.

### Observación numérica en las figuras

- **G6:**
  - las cuatro redes siguen la pendiente 1 con κ ≤ 0.3 y se doblan hacia la
    pendiente ½ con κ ≥ 1, en los tres umbrales;
  - las curvas de las redes son casi paralelas entre sí;
  - el orden ER > malla > mundo pequeño > anillo se mantiene.
- **G5:**
  - **Anillo:** γt crece casi en línea recta con d en todos los valores de κ.
  - **Malla:** también casi lineal.
  - **Mundo pequeño:** se dobla hacia arriba a partir de d ≈ 10. A esas
    distancias solo llegan pocas realizaciones, así que el tramo final es
    menos confiable.
  - **ER:** los nodos de una misma distancia se agrupan en franjas
    horizontales bien separadas. Es la huella de nodos con distinto número de
    caminos Nᵢ, la pregunta P5 que estudiará E4.
- **Umbral:** el umbral más bajo (10⁻⁸) siempre da llegadas más tempranas, y
  la separación entre las tres medianas crece con d.

## 14. Fase 3: experimento E3 y gráficos G7 y G8

### E3: energía por distancia (`scripts/e3_energia_distancia.py`)

Responde P2, P4 y P8. **No simula:** usa los ⟨Eᵢ⟩ que E2 ya calculó, con
T = 10/γ en todos los casos, así que las comparaciones son válidas. Tarda
unos segundos.

**Qué calcula,** para cada red, cada κ (los 7 de E2) y cada realización:

- ⟨Eᵢ⟩/E₀ de cada nodo, ecuación (18);
- Ē(d)/E₀, ecuación (21), y σ_E(d)/E₀ con ddof = 1, ecuación (23);
- la fracción ⟨Eᵢ⟩/Σ⟨Eⱼ⟩.

**Las dos variabilidades del plan quedan separadas:**

- **σ_E(d):** diferencias entre nodos dentro de una misma red. Se calcula
  por realización con la función nueva
  `analisis.por_distancia_realizaciones`, que usa un eje d común y pone NaN
  donde una realización no tiene nodos a esa distancia.
- **Entre realizaciones:** mediana y percentiles 10–90 de Ē(d) sobre las 30
  realizaciones.

**Salidas:**

- `e3_<red>.npz`, con ejes [κ, realización, d] para Ē y σ, y
  [κ, realización, nodo] para ⟨Eᵢ⟩/E₀ y la fracción;
- `e3_resumen.csv`, una fila por (red, κ, d).

**Resultados** (medianas entre realizaciones). La «pendiente» es la de
log₁₀ Ē frente a d en d ≥ 1, una medida resumen de qué tan rápido cae la
energía con la distancia. Los modelos funcionales se comparan en la Fase 4.

| Red | κ | Ē(1)/E₀ | pendiente log₁₀Ē por d | máx σ/Ē | fracción en la fuente |
|-----|---|---------|------------------------|---------|-----------------------|
| Malla | 0.01 | 2.7 × 10⁻³ | −0.85 | 0.86 | 0.87 |
| Malla | 0.1 | 4.1 × 10⁻³ | −0.10 | 0.68 | 0.27 |
| Malla | 1 | 4.7 × 10⁻³ | −0.03 | 0.49 | 0.07 |
| Anillo | 0.01 | 3.0 × 10⁻³ | −1.70 | 1.01 | 0.87 |
| Anillo | 0.1 | 7.4 × 10⁻³ | −0.14 | 0.67 | 0.32 |
| Anillo | 1 | 9.0 × 10⁻³ | −0.04 | 0.68 | 0.11 |
| Mundo pequeño | 0.01 | 3.0 × 10⁻³ | −1.13 | 1.27 | 0.87 |
| Mundo pequeño | 0.1 | 7.6 × 10⁻³ | −0.31 | 0.87 | 0.32 |
| Mundo pequeño | 1 | 1.1 × 10⁻² | −0.14 | 0.61 | 0.11 |
| Erdős–Rényi | 0.01 | 2.7 × 10⁻³ | −1.04 | 1.02 | 0.87 |
| Erdős–Rényi | 0.1 | 6.2 × 10⁻³ | −0.39 | 0.87 | 0.32 |
| Erdős–Rényi | 1 | 9.2 × 10⁻³ | −0.21 | 0.69 | 0.12 |

### G7: energía media por distancia

Archivos: `resultados/figuras/g7_energia_media_vs_distancia.png` y `.pdf`.

- **Rejilla:** las 4 redes en columnas y κ = 0.01, 0.1, 1 y 10 en filas, con
  el eje y logarítmico.
- **Puntos:** ⟨Eᵢ⟩/E₀ de cada nodo (en redes aleatorias, los de las 30
  realizaciones).
- **Línea negra:** Ē(d), la mediana entre realizaciones.
- **Barras:** Ē ± σ_E(d), la dispersión entre nodos.
- **Franja de color:** percentiles 10–90 de Ē(d) entre realizaciones.

**Ajustes tras revisar la figura:**

- **Escala por fila:** con el eje y común a todos los paneles, las filas de
  κ ≥ 0.1 ocupaban solo la parte de arriba de 10 décadas. Ahora cada fila
  (mismo κ) comparte su propia escala y el piso queda una década por debajo
  del menor Ē(d) de la fila. El primer intento usaba el percentil 2 de los
  nodos y cortaba la cola del anillo.
- **Barras bajo el piso:** se quitaron las de las distancias cuyo Ē queda
  bajo el borde inferior, porque saturaban el borde.
- **Barras que llegan al borde:** cuando Ē − σ ≤ 0 (pasa en el mundo
  pequeño con κ = 0.01), la barra llega al borde inferior. Indica que σ es
  comparable a Ē.

### G8: heterogeneidad por distancia

Archivos: `resultados/figuras/g8_heterogeneidad.png` y `.pdf`.

- **Fila superior:** σ_E(d)/E₀, en escala logarítmica.
- **Fila inferior:** σ_E/Ē, en escala lineal.
- **Curvas:** una línea por κ, en azul de claro (κ pequeño) a oscuro.
- **Distancias incluidas:** solo las que tienen al menos 2 nodos y
  Ē(d) > 10⁻¹² E₀.

**Hallazgo: energías por debajo de toda escala física.** En la primera
versión, la σ del anillo con κ = 0.01 llegaba a 10⁻⁴⁴ E₀. Esas energías están
más de 30 órdenes por debajo del umbral más bajo (10⁻⁸) y se acercan a la
precisión del integrador: atol = 10⁻¹² Q₀ equivale a unos 10⁻²⁴ E₀. Su
dispersión no es interpretable, así que G8 usa un piso de 10⁻¹² E₀ para Ē(d),
documentado en la figura.

### Observación numérica

La interpretación va en la Fase 4.

- **Ē(d) decae con d en todas las redes.**
  - Con κ = 0.01 la caída es fuerte, entre 0.85 y 1.7 décadas por paso de
    distancia, y la más pronunciada es la del anillo.
  - Al subir κ la caída se suaviza mucho. Con κ ≥ 1, Ē(d) es casi plana en la
    malla y el anillo, y sigue decreciente en WS y ER.
- **En la malla, Ē(d) deja de decrecer** a partir de d ≈ 5 con κ ≥ 0.1, e
  incluso sube en los bordes (d = 9 y 10). Puede ser un efecto de borde
  (nodos de esquina con grado 2); se revisará en la Fase 4.
- **Energía que queda en la fuente:** es casi idéntica en las cuatro redes
  para el mismo κ (≈ 0.87, 0.3 y 0.1 con κ = 0.01, 0.1 y 1). La cantidad que
  se va depende de κ y casi nada de la topología. La forma en que se reparte
  por distancia, en cambio, sí depende de la red.
- **Ē(0)/E₀ no es monótona en κ:** baja de 0.088 a ≈ 0.02 hasta κ ≈ 0.3–1 y
  vuelve a subir, hasta 0.09–0.13 con κ = 10. Es coherente con
  H(0) = E₀(1 + k₀κ): con κ grande hay mucha más energía inicial en los
  enlaces, que vuelve a las mallas. Es otra muestra de que ⟨Eᵢ⟩/E₀ no es una
  fracción de energía.
- **Heterogeneidad relativa σ/Ē:**
  - en WS y ER es alta con κ pequeño (hasta 1.0–1.3) y baja con κ grande
    (≈ 0.4–0.65), casi sin depender de d;
  - en la malla y el anillo es irregular por distancia, porque tienen pocos
    nodos por d y simetrías (los nodos simétricos tienen la misma energía).

## 15. Fase 3: experimento E4 y gráfico G9

### E4: efecto de la posición a igual distancia (`scripts/e4_posicion.py`)

Responde P5 («¿igual distancia implica igual respuesta?»), P6 y P8. **No
simula:** usa tᵢ (umbral 10⁻⁶ E₀) y ⟨Eᵢ⟩ de cada nodo que E2 ya calculó.

**Tres predictores,** que el plan pide relacionar con la respuesta de cada
nodo:

| Predictor | Qué es | Origen |
|-----------|--------|--------|
| Nᵢ | número de caminos más cortos desde la fuente | teoría, punto 7: a tiempos cortos Qᵢ ∝ Nᵢ |
| kᵢ | grado del nodo | estructura local |
| Wᵢ | peso modal incoherente Σ_λ (Π_λ)ᵢ₀² | teoría, punto 6: la amplitud media que llegaría al nodo si los modos no interfirieran |

**Dos funciones nuevas en `analisis.py`:**

- `peso_modal_incoherente(Λ, fuente)` calcula Wᵢ con los **proyectores**
  Π_λ sobre cada autovalor, no con autovectores sueltos. La malla y el anillo
  tienen autovalores repetidos por simetría, y con autovectores sueltos Wᵢ
  dependería de una elección arbitraria de base. Una prueba comprueba que los
  nodos simétricos del anillo reciben el mismo Wᵢ.
- `relacion_a_igual_distancia(y, x, d)` compara solo nodos de un mismo grupo
  (misma realización y distancia), así que la distancia no influye. Da dos
  medidas:
  - **ρ:** correlación de Spearman dentro de cada grupo, mediana entre grupos;
  - **R²:** regresión de log y sobre log x tras restar la media de cada
    grupo. Es la parte de la variación a igual d que explica el predictor.

**Verificación:** el script reconstruye cada red con su semilla y comprueba
que las distancias coincidan con las guardadas por E2 antes de calcular Wᵢ.

**Salidas:** `e4_<red>.npz` (por nodo) y `e4_resumen.csv` (una fila por red,
κ, respuesta y predictor).

**Resultados** (ρ mediana / R²):

*Tiempo de llegada* (se espera ρ < 0: más caminos, llegada más temprana):

| Red | κ | Nᵢ | kᵢ | Wᵢ |
|-----|---|----|----|----|
| Malla | 0.1 | −0.91 / 0.88 | −0.21 / 0.11 | −0.30 / 0.03 |
| Malla | 1 | −0.89 / 0.93 | −0.21 / 0.12 | −0.38 / 0.01 |
| Anillo | 0.1 | −0.94 / 0.20 | — | −0.32 / 0.01 |
| Mundo pequeño | 0.1 | −0.88 / 0.66 | +0.11 / 0.00 | −0.23 / 0.04 |
| Mundo pequeño | 1 | −0.89 / 0.73 | +0.11 / 0.00 | −0.22 / 0.03 |
| Erdős–Rényi | 0.1 | −0.92 / 0.80 | −0.15 / 0.09 | −0.17 / 0.01 |
| Erdős–Rényi | 1 | −0.92 / 0.93 | −0.01 / 0.12 | −0.26 / 0.01 |

*Energía media* (se espera ρ > 0):

| Red | κ | Nᵢ | kᵢ | Wᵢ |
|-----|---|----|----|----|
| Malla | 0.01 | +0.88 / 1.00 | +0.20 / 0.19 | +0.43 / 0.02 |
| Malla | 1 | +0.61 / 0.24 | +0.43 / 0.11 | +0.79 / 0.50 |
| Malla | 10 | +0.41 / 0.04 | +0.48 / 0.17 | +0.75 / 0.74 |
| Mundo pequeño | 0.01 | +0.86 / 0.77 | −0.11 / 0.00 | +0.25 / 0.04 |
| Mundo pequeño | 1 | +0.33 / 0.07 | −0.11 / 0.01 | +0.73 / 0.58 |
| Mundo pequeño | 10 | +0.26 / 0.04 | +0.00 / 0.00 | +0.85 / 0.78 |
| Erdős–Rényi | 0.01 | +0.80 / 0.64 | +0.11 / 0.08 | +0.25 / 0.04 |
| Erdős–Rényi | 1 | +0.29 / 0.05 | +0.28 / 0.11 | +0.86 / 0.78 |
| Erdős–Rényi | 10 | +0.25 / 0.05 | +0.48 / 0.20 | +0.88 / 0.79 |

En el anillo todos los nodos tienen grado 4, así que kᵢ no puede explicar
nada. Por su simetría, la energía a igual d varía poco y ningún predictor
supera R² = 0.14 con κ ≥ 0.1. El CSV tiene los 7 valores de κ.

### G9: nodos a igual distancia (`scripts/g9_posicion.py`)

Archivos: `resultados/figuras/g9_posicion.png` y `.pdf`.

- **Paneles:** 4 filas por 4 redes:
  - γtᵢ frente a Nᵢ (κ = 0.1);
  - ⟨Eᵢ⟩ frente a Nᵢ (κ = 0.01);
  - ⟨Eᵢ⟩ frente a kᵢ (κ = 1);
  - ⟨Eᵢ⟩ frente a Wᵢ (κ = 1).
- **Normalización:** respuesta y predictor se dividen por la media
  geométrica de su grupo. Así 1 significa «como el promedio de su distancia»
  y se pueden juntar todas las distancias en un mismo panel. Es la misma
  normalización que usa la regresión de E4.
- **Elementos:** puntos por nodo, mediana por intervalos (línea negra) y, en
  cada panel, su ρ y su R².

**Ajustes tras revisar la figura:**

- **Predictor normalizado:** en la primera versión, Nᵢ y kᵢ iban en valor
  absoluto. Como Nᵢ crece con d, las tendencias salían en zigzag al mezclar
  distancias. Ahora el predictor también se normaliza por grupo.
- **Marcas de los ejes:** las logarítmicas («2×10⁰») pasaron a números
  simples.
- **Predictor constante:** el panel del grado en el anillo muestra un aviso
  en lugar de puntos dispersos artificialmente.

### Observación numérica

La interpretación va en la Fase 4.

- **El tiempo de llegada lo explica Nᵢ.** En todas las redes y valores de κ,
  ρ está entre −0.82 y −0.94, con R² de 0.66 a 0.99 (salvo el anillo,
  R² = 0.20–0.35). Es lo que predice la teoría para el primer rastro de
  energía. kᵢ y Wᵢ casi no aportan (R² ≤ 0.12).
- **La energía media cambia de predictor según κ:**
  - con κ = 0.01 la explica Nᵢ (R² de 0.64 a 1.0), porque la energía apenas
    sale del frente y depende de cuántos caminos llegan;
  - con κ ≥ 1 la explica el peso modal Wᵢ (R² de 0.50 a 0.79 en malla, WS y
    ER), y Nᵢ cae a R² ≤ 0.24.
- **Respuesta a P5:** igual distancia **no** implica igual respuesta. Las
  diferencias en energía superan un factor 10 entre nodos de la misma
  distancia (WS y ER con κ = 0.01, entre ≈ 0.05 y ≈ 20 veces el promedio de
  su distancia). En el tiempo de llegada son de hasta ±30–50 %. En ambos
  casos tienen causas identificables.
- **El grado importa poco:** como mucho R² = 0.20 (ER con κ = 10).

## 16. Fase 3: experimento E5 y gráfico G10

### E5: sensibilidad (`scripts/e5_sensibilidad.py`)

Sirve para las limitaciones del estudio y para P7. Cambia un parámetro a la
vez respecto del caso base, con κ = 0.1 y κ = 1.

| Estudio | Qué se varía | Redes |
|---------|--------------|-------|
| γ | R = 0.3, 1, 3 y 10 Ω (factor de calidad ω₀/γ = 105, 31.6, 10.5 y 3.2), con T = 10/γ en cada caso | las 4 de referencia |
| N | malla de lado 6, 10, 14 y 20 (N = 36 a 400); anillo de 50 a 400 nodos | malla y anillo |
| Fuente | malla: interior (4,4), borde (0,4) y esquina (0,0). ER: nodo 0, el de mayor grado y el de menor grado de cada realización | malla y ER (30 realizaciones) |

- **Por qué N solo en redes deterministas:** en WS y ER, cambiar N obliga a
  cambiar también p para conservar el grado medio, y serían dos cambios a la
  vez.
- **Función nueva:** se agregó `redes.con_fuente(red, fuente)` (misma red,
  otra fuente) con su prueba.
- **Costo:** 234 simulaciones en 6 procesos, **86 s**.
- **Control de calidad:** residuo del balance de H ≤ 8.7 × 10⁻⁷.
- **Salida:** `e5_resumen.csv`, una fila por simulación.

**Resultados** (medianas; v/ω₀ con umbral 10⁻⁶; «alcance» = fracción de
nodos alcanzados; «fuente» = ⟨E_fuente⟩/Σ⟨Eⱼ⟩):

*Amortiguamiento, κ = 0.1:*

| Red | R = 0.3 Ω | R = 1 Ω | R = 3 Ω | R = 10 Ω |
|-----|-----------|---------|---------|----------|
| Malla: v/ω₀ · alcance · fuente | 0.27 · 1.00 · 0.10 | 0.26 · 1.00 · 0.27 | 0.22 · 1.00 · 0.57 | 0.21 · 0.44 · 0.89 |
| Anillo | 0.15 · 1.00 · 0.14 | 0.13 · 1.00 · 0.32 | 0.13 · 0.48 · 0.61 | 0.25 · 0.16 · 0.89 |
| Mundo pequeño | 0.17 · 1.00 · 0.14 | 0.16 · 1.00 · 0.31 | 0.12 · 0.89 · 0.61 | 0.19 · 0.18 · 0.90 |
| Erdős–Rényi | 0.34 · 1.00 · 0.16 | 0.33 · 1.00 · 0.31 | 0.30 · 1.00 · 0.56 | 0.25 · 0.90 · 0.87 |

*Amortiguamiento, κ = 1* (v/ω₀ con R = 0.3 → 10 Ω): malla 1.77 → 1.66;
anillo 0.96 → 0.73; mundo pequeño 1.18 → 0.97; ER 2.16 → 2.08. Todas las
redes llegan a todos los nodos, salvo el anillo con R = 10 Ω (94 %).

*Tamaño* (v/ω₀ con κ = 0.1 / κ = 1):

| Malla | N = 36 | 100 | 196 | 400 |
|-------|--------|-----|-----|-----|
| v/ω₀ | 0.37 / 2.31 | 0.26 / 1.76 | 0.22 / 1.48 | 0.19 / 1.26 |

| Anillo | N = 50 | 100 | 200 | 400 |
|--------|--------|-----|-----|-----|
| v/ω₀ | 0.17 / 1.18 | 0.13 / 0.94 | 0.12 / 0.83 | 0.12 / 0.77 |
| alcance con κ = 0.1 | 1.00 | 1.00 | 0.69 | 0.35 |

*Posición de la fuente:*

| Red | Fuente (grado k₀) | v/ω₀ κ = 0.1 | v/ω₀ κ = 1 | fuente κ = 0.1 |
|-----|-------------------|--------------|------------|----------------|
| Malla | interior (4) | 0.26 | 1.76 | 0.27 |
| Malla | borde (3) | 0.18 | 1.29 | 0.29 |
| Malla | esquina (2) | 0.20 | 1.32 | 0.34 |
| ER | nodo 0 (4) | 0.30 | 2.04 | 0.32 |
| ER | mayor grado (10) | 0.35 | 2.32 | 0.56 |
| ER | menor grado (1) | 0.20 | 1.55 | 0.72 |

**Observación numérica** (la interpretación va en la Fase 4):

- **γ casi no cambia la rapidez, pero sí el alcance.**
  - Al multiplicar R por 33, v/ω₀ cambia menos de un 25 % en la mayoría de
    los casos, y menos de un 10 % con κ = 1 en malla y ER.
  - Con R = 10 Ω el frente se apaga antes de recorrer la red: con κ = 0.1 el
    alcance baja a 16–44 % en anillo, WS y malla.
  - La energía que se queda en la fuente sube de ≈ 0.1 a ≈ 0.9.
  - En resumen, K fija la rapidez y γ fija hasta dónde llega la señal. Es
    coherente con los «dos relojes» de la teoría (t_tr frente a 1/γ).
  - Con R = 10 Ω y alcance bajo, la rapidez se calcula con pocos nodos
    cercanos y es menos confiable (por ejemplo, en el anillo sube a 0.25).
- **La rapidez medida baja con N.**
  - En la malla pasa de 0.37 a 0.19 (κ = 0.1); en el anillo, de 0.17 a 0.12.
  - El ajuste lineal de t frente a d incluye nodos más lejanos en las redes
    grandes. Como t frente a d es curvo (teoría, punto 7; se ve en G5), la
    pendiente media cambia con el rango de d.
  - Es una limitación de usar una sola «rapidez». En la Fase 4 conviene
    ajustar t(d) con modelos no lineales, o medir la rapidez en un rango
    fijo de d.
- **La fracción en la fuente no depende de N** (0.324 en el anillo con 50 a
  400 nodos): la energía que sale de la fuente en T depende de su entorno,
  no del tamaño total.
- **El alcance de los anillos grandes:** con κ = 0.1 cae a 69 % (N = 200) y
  35 % (N = 400), porque d máx crece con N y el amortiguamiento corta el
  frente.
- **La posición de la fuente importa:**
  - **Malla:** con la fuente en el borde o la esquina la rapidez es entre
    un 20 y un 30 % menor que en el interior.
  - **ER, rapidez:** el frente es un 75 % más rápido desde el nodo de mayor
    grado que desde el de menor grado (0.35 frente a 0.20 con κ = 0.1).
  - **ER, energía retenida:** las dos fuentes extremas retienen más energía
    que la típica (0.56 y 0.72 frente a 0.32).
    - Con k₀ = 1 la salida tiene un solo enlace, que hace de cuello de
      botella.
    - Con k₀ = 10, H(0) = E₀(1 + 10κ) es grande y los enlaces devuelven
      energía a la fuente.

### G10: comparación de topologías (`scripts/g10_topologias.py`)

Archivos: `resultados/figuras/g10_topologias.png` y `.pdf`; datos en
`resultados/datos/g10_metricas.csv`. Responde P6.

- **Paneles:** una métrica por panel, con las cuatro redes lado a lado. Cada
  red lleva su color; κ = 0.1 va como círculo y κ = 1 como rombo. En las
  redes aleatorias, una barra marca los percentiles 10–90 de las 30
  realizaciones.
- **Métricas:**
  - rapidez del frente;
  - alcance con κ = 0.01;
  - caída de Ē(d);
  - heterogeneidad σ/Ē;
  - energía que queda en la fuente;
  - λ₂, la conectividad algebraica de la red. Es la hipótesis de la teoría
    (punto 4): un λ₂ mayor podría asociarse a un reparto más rápido de la
    energía.

**Ajustes tras revisar la figura:**

- **Nombres del eje x:** se encimaban; ahora son nombres cortos.
- **Leyenda:** usaba el círculo para tres cosas a la vez (κ = 0.1, κ = 0.01
  y estructura). Ahora solo muestra las series de los paneles con dos κ; en
  los paneles de una sola serie, el título ya dice cuál es.
- **Ejes logarítmicos:** se pasaron a números simples.

**Medianas:**

| Métrica | Malla | Anillo | Mundo pequeño | ER |
|---------|-------|--------|---------------|----|
| v/ω₀, κ = 0.1 | 0.26 | 0.13 | 0.17 | 0.30 |
| v/ω₀, κ = 1 | 1.76 | 0.94 | 1.32 | 2.04 |
| alcance, κ = 0.01 | 0.44 | 0.18 | 0.31 | 0.90 |
| pendiente log₁₀Ē por d, κ = 0.1 | −0.10 | −0.14 | −0.32 | −0.38 |
| σ/Ē, κ = 0.1 | 0.42 | 0.09 | 0.70 | 0.70 |
| fracción en la fuente, κ = 0.1 | 0.27 | 0.32 | 0.32 | 0.31 |
| λ₂ | 0.098 | 0.020 | 0.123 | 0.450 |

**Observación numérica:**

- **ER y anillo, en los extremos:** ER es la red más rápida y de mayor
  alcance, y el anillo la más lenta y de menor alcance, en todas las
  métricas de propagación.
- **λ₂ ordena bien los extremos, pero no todo:**
  - ER tiene el λ₂ más alto (0.45) y el anillo el más bajo (0.02);
  - WS tiene un λ₂ algo mayor que la malla (0.12 frente a 0.10), pero la
    malla es más rápida. λ₂ no basta para predecir la rapidez. La hipótesis
    se cumple solo en parte y se discutirá en la Fase 4.
- **Caída de la energía con d:** es más pronunciada en las redes aleatorias
  (WS y ER), donde la energía se concentra cerca de la fuente. En la malla
  y el anillo el perfil es más plano.
- **Heterogeneidad:** mucho mayor en las redes aleatorias (σ/Ē ≈ 0.7) que en
  las regulares (0.09–0.42), por la variedad de Nᵢ y de pesos modales que
  mostró E4.
- **Energía que sale de la fuente:** es casi la misma en las cuatro redes
  (≈ 0.3 con κ = 0.1). La topología decide hacia dónde va y a qué velocidad,
  no cuánta sale.

## 17. Cierre de la Fase 3: G2, reproducibilidad y ejecución completa

### G2: validación del código (`scripts/g2_validacion.py`)

Archivos: `resultados/figuras/g2_validacion.png` y `.pdf`; datos en
`resultados/datos/g2_validacion.csv`. Sostiene la «confianza en el código».
Genera sus propias simulaciones en ≈ 1 min.

| Panel | Qué muestra | Resultado |
|-------|-------------|-----------|
| (a) | H(t) frente a H(0)e^(−γt) y ΣEᵢ(t) (malla, κ = 1) | H coincide con la exponencial; ΣEᵢ queda por debajo y no es la energía total |
| (b) | Residuo del balance de H en las 4 redes (κ = 0.1), envolvente | ≤ 9.1 × 10⁻⁸; el criterio de las pruebas es 10⁻⁶ |
| (c) | Error de DOP853 frente a la solución modal, 4 redes × 7 valores de κ | ≤ 1.5 × 10⁻⁹ Q₀; el criterio del plan es ≪ 10⁻³ Q₀ |
| (d) | Convergencia de RK4 (5 tamaños de paso) | Orden 3.97, 4.00, 4.00, 4.00 |

**Ajustes tras revisar la figura:**

- **Panel (a):** la recta teórica quedaba tapada por H(t), porque coinciden.
  Ahora va encima, en trazo discontinuo.
- **Panel (b):** el residuo oscilaba tanto que formaba una mancha. Se dibuja
  su envolvente.
- **Panel (d):** las marcas del eje x se encimaban; se pasaron a números
  simples.

### Reproducibilidad (`scripts/verificar_reproducibilidad.py`)

El script vuelve a correr 8 simulaciones de E2 con la misma función que usó
E2: las 4 redes, κ de 0.01 a 10 y semillas distintas en WS y ER. Luego
compara los tiempos de llegada y las energías medias con los guardados.

**Resultado:** la diferencia es **exactamente 0** en las 8. Los resultados se
reproducen bit a bit, gracias a las semillas fijas, al integrador y las
tolerancias fijas, y a un hilo de álgebra lineal por proceso.

### Ejecución completa (`scripts/fase3_completa.py`)

Regenera toda la Fase 3 en orden:

1. corre las pruebas automáticas y se detiene si alguna falla;
2. G1, G2 y E1 a E5, con sus gráficos, en el orden en que dependen unos de
   otros;
3. la verificación de reproducibilidad.

Imprime el tiempo de cada paso. Es el comando para la revisión del grupo y
para regenerar los resultados en otro equipo.

### Ejecución de punta a punta (8 de noviembre)

| Paso | Tiempo | Control |
|------|--------|---------|
| Pruebas automáticas | 122 s | 168 aprobadas |
| G1, G2 | 114 s | — |
| E1 + G3, G4 | 147 s | controles de calidad OK |
| E2 + G5, G6 | 320 s | residuo ≤ 1.3 × 10⁻⁷; error de H(0) ≤ 3.3 × 10⁻¹⁶ |
| E3 + G7, G8 | 27 s | — |
| E4 + G9 | 42 s | — |
| E5 + G10 | 126 s | residuo ≤ 8.7 × 10⁻⁷ |
| Reproducibilidad | 23 s | diferencia relativa **0.0** |
| **Total** | **920 s (15 min 20 s)** | |

Los tiempos son mayores que los de cada experimento por separado porque las
pruebas y los procesos en paralelo compiten por el procesador.

**Para revisar en otro equipo:**

- correr `python scripts/fase3_completa.py` y comprobar que termina con
  «Reproducibilidad: OK»;
- revisar que cada figura G1 a G10 sostenga una conclusión, como pide el plan.

## 18. Fase 4: ajustes funcionales (`ajustes.py`, `scripts/f4_ajustes.py`)

### Reglas del plan

- **Tamaño de los modelos:** como máximo 2 parámetros.
- **Comparación:** con AICc y gráficos de residuos, no solo con R².
- **Datos:** el ajuste se hace sobre los datos de cada nodo, y σ_E no se usa
  como peso.

### `red_rlc/ajustes.py`

Define 8 modelos de 2 parámetros. AICc solo compara modelos que ajustan la
misma variable en el mismo espacio.

| Datos | Modelos | Espacio del ajuste |
|-------|---------|--------------------|
| tγ(d) | lineal a + b·d; potencia a·dᵇ; logarítmico a + b·ln d | γt |
| ⟨Eᵢ⟩(d) y σ_E(d) | exponencial (log₁₀E = a + b·d); potencia (log₁₀E = a + b·log₁₀d) | log₁₀ |
| v(κ) | potencia; por tramos con exponentes 1 y ½ fijos (A, κ_c); transición suave v = Aκ/√(1 + κ/κ_c) | log₁₀v |

- **De dónde salen los modelos de v(κ):** los dos últimos tienen los límites
  de la teoría de la cadena (v ∝ κ con κ pequeño y v ∝ √κ con κ grande), con
  un único κ_c que marca el cambio de régimen. Así se prueba la hipótesis
  del plan con 2 parámetros.
- **`comparar`:** ordena los modelos por AICc y da ΔAICc y los pesos de
  Akaike. ΔAICc < 2 indica un apoyo equivalente; ΔAICc > 10, un apoyo
  prácticamente nulo para el modelo peor.
- **`desviacion_en_d1`:** el plan pide «revisar si d = 1 se desvía de la
  tendencia». La función ajusta el mejor modelo sin d = 1 y mide cuánto se
  aparta d = 1, en desviaciones estándar del ajuste.
- **Pruebas:** 14, incluida la recuperación exacta de los parámetros de los
  8 modelos.

### `scripts/f4_ajustes.py`

- **Datos:** usa los de E2 y E3; no simula.
- **Ajustes:** uno por cada red, κ y realización. En WS y ER se reporta
  cuántas de las 30 realizaciones gana cada modelo.
- **Salidas:** `f4_ajustes_{t,E,sigma,v}.csv`.

`scripts/f4_figuras.py` genera las figuras de ajuste, con los datos y los
modelos arriba y los residuos por distancia abajo:

- **A1:** tγ(d) con κ = 0.1 y 1;
- **A2:** E(d) con κ = 0.01 y 1;
- **A3:** v(κ).

Cada modelo tiene un estilo de línea propio dentro de la figura (continuo,
discontinuo, punteado), porque los colores identifican a las redes. En la
primera versión dos modelos compartían estilo; se corrigió.

### Resultados

**1. El tiempo de llegada sigue una ley de potencia, no una recta.**

- **Quién gana:** la potencia gana en todas las redes y valores de κ (en 29
  o 30 de 30 realizaciones en WS y ER).
- **Margen:** ΔAICc del segundo modelo de 10 a 131 y peso de Akaike ≈ 1.
- **Residuos:** los de la potencia quedan cerca de cero en todas las
  distancias; los modelos lineal y logarítmico dejan curvaturas
  sistemáticas (A1).

Exponente b de tγ = a·dᵇ (mediana, con p10–p90 en las redes aleatorias):

| Red | κ = 0.01 | κ = 0.1 | κ = 1 | κ = 10 |
|-----|----------|---------|-------|--------|
| Malla | 2.63 | 1.70 | 1.62 | 1.68 |
| Anillo | 2.93 | 1.47 | 1.44 | 1.35 |
| Mundo pequeño | 2.91 [2.66, 3.47] | 1.99 [1.87, 2.17] | 1.91 [1.74, 2.01] | 1.82 [1.73, 1.98] |
| Erdős–Rényi | 2.77 [2.60, 3.26] | 2.31 [2.11, 2.53] | 2.12 [1.95, 2.31] | 2.26 [2.05, 2.47] |

Lo que se ve:

- **b > 1 en todos los casos:** el frente se desacelera con la distancia.
  Esto explica la limitación que encontró E5, donde la «rapidez» lineal
  bajaba con N.
- **El anillo tiene el b más cercano a 1** (1.35–1.47), es decir, el frente
  más parecido a una onda de velocidad constante.
- **Las redes aleatorias tienen el b mayor** (≈ 2).
- **Con κ = 0.01, b ≈ 2.6–2.9 en todas las redes:** es el régimen en que el
  amortiguamiento compite con la transferencia.

**2. d = 1 no se aparta de la tendencia.** El residuo medio en d = 1, con el
mejor modelo ajustado sin d = 1, está entre −0.2 y −0.8 desviaciones estándar
del ajuste. Es siempre algo adelantado, pero dentro de la dispersión normal.

**3. E(d) cambia de forma con κ.**

- **Con κ pequeño gana la exponencial** (log₁₀E = a + b·d):
  - en malla, anillo y WS gana en 1/1, 1/1 y 30/30 realizaciones, con ΔAICc
    de 27 a 82;
  - la pendiente es de −0.8 a −1.2 décadas por enlace con κ = 0.01.
- **Con κ ≥ 0.1 (≥ 1 en el anillo) gana la potencia** (E ∝ dᵇ), con
  exponentes de −0.4 a −1.2 con κ = 1.
- **Con κ grande el perfil es casi plano.** R² baja (0.15–0.5), porque la
  variación entre nodos a igual d (E4) es comparable a la variación con d.
- **ER con κ = 0.01 es un caso límite:** la potencia gana en 17 de 30
  realizaciones, con ΔAICc de 8. Con solo 4 o 5 distancias por realización,
  la evidencia es débil.

**4. σ_E(d):** en WS y ER gana la exponencial en la mayoría de las
realizaciones, con R² de 0.46 a 0.99. En la malla R² es muy bajo (< 0.42),
porque σ_E(d) no es monótona: depende de pocos nodos por distancia y de las
simetrías de la red.

**5. La rapidez v(κ) confirma la transición de la teoría.**

- **Ganadores:**
  - malla y WS: la transición suave, en 1/1 y 28/30 realizaciones;
  - ER: el modelo por tramos con exponentes 1 y ½, en 27/30;
  - anillo: la potencia simple, con ΔAICc = 2, es decir, empate.
- **Parámetros de la transición suave** v = Aκ/√(1 + κ/κ_c), mediana
  [p10, p90]:

| Red | A | κ_c |
|-----|---|-----|
| Malla | 2.70 | 0.62 |
| Anillo | 1.65 | 0.55 |
| Mundo pequeño | 1.84 [1.62, 2.22] | 0.91 [0.81, 1.02] |
| Erdős–Rényi | 3.05 [2.04, 3.56] | 0.75 [0.64, 1.03] |

- **Dónde cambia el régimen:** κ_c ≈ 0.55–0.9 en las cuatro redes, es
  decir, K ≈ ω₀². Coincide con la escala en que la teoría predice el paso de
  v ∝ K/ω₀ a v ∝ √K.
- **Qué fija la topología:** sobre todo el prefactor A (ER > malla > WS >
  anillo), más que κ_c.

## 19. Fase 4: resumen de resultados (`docs/resumen_resultados.md`)

Es el entregable «Resumen de resultados» del plan. Contiene:

- **Las 8 preguntas del PDF,** cada una con una respuesta corta y los tres
  niveles que pide el plan: observación numérica (con cifras y figura),
  interpretación física (apoyada en la teoría o en un experimento) y
  especulación (hipótesis que los datos no prueban). Así se cumple también
  la sección 11 del PDF.
- **La cobertura de los 11 objetivos del PDF:** 10 cumplidos; el O11
  (videos) queda para la Fase 5.
- **Un borrador de las conclusiones,** con los cinco puntos de la sección 12
  del PDF: efecto de K, energía y distancia, estructura de la red,
  limitaciones y extensiones.
- **La revisión de la fase:** una tabla con la figura, el dato y el archivo
  que sostienen cada pregunta.

**Interpretación nueva que surgió al redactar:** el exponente b de
t ∝ dᵇ sigue el mismo orden que el crecimiento de N_d en cada red. El anillo,
con N_d constante, tiene el b más bajo; la malla, con N_d lineal, va después;
WS y ER, con N_d de crecimiento rápido, tienen b ≈ 2. Es coherente con una
«dilución» de la energía del frente entre más nodos. Queda como
interpretación por confirmar; el resumen propone cómo probarla (árboles con
distinto número de ramas).

**Corrección al verificar las cifras:** en la tabla de P5, el peso modal sí
explica algo del tiempo de llegada en el anillo con κ = 0.01 (R² = 0.32), y
no explica la energía del anillo con κ ≥ 1 (R² ≤ 0.14). Se corrigió la tabla.

## 20. Fase 5: videos y figuras finales

### Videos (`red_rlc/videos.py`, `scripts/f5_videos.py`)

Cumplen el objetivo O11 del PDF: «comparando diferentes valores de K y
diferentes topologías». Usan los datos de E1 y no simulan.

| Video | Contenido |
|-------|-----------|
| `v1_kappa_malla.mp4`, `v1_kappa_anillo.mp4`, `v1_kappa_mundo_pequeno.mp4`, `v1_kappa_erdos_renyi.mp4` | Una red, con κ = 0.01, 0.1 y 1 lado a lado: efecto del acoplamiento |
| `v2_topologias_k0p1.mp4`, `v2_topologias_k1.mp4` | Las 4 redes lado a lado con el mismo κ: efecto de la topología |

**Formato:** 1920×1080, 24 cuadros/s, 16 s y entre 2.8 y 6.1 MB cada uno, en
`resultados/videos/` (no se versionan).

- **Nodos:** cada nodo se colorea según log₁₀(Eᵢ/E₀), con la misma escala
  azul de G4 (−12 a 0).
- **Fuente:** un anillo naranja.
- **Enlaces:** líneas grises tenues.
- **Información en pantalla:** un reloj con γt y una barra de colores.

**Decisiones de diseño:**

- **Tiempo no lineal:** los cuadros se reparten como t = T·(k/n)³. Con
  κ = 1 el frente cruza la red en γt < 0.2, un 2 % de la simulación, y a
  velocidad constante pasaría en un instante. Así el video va lento al
  principio y rápido al final. El reloj muestra siempre el γt real.
- **Envolvente:** Eᵢ oscila al doble de la frecuencia natural; mostrada tal
  cual, los nodos parpadearían. Cada cuadro muestra el máximo de Eᵢ desde el
  cuadro anterior, el mismo criterio de G3 y G4.
- **Generación en paralelo:** un proceso por video. Cada cuadro tarda
  ≈ 0.4 s en dibujarse; los 6 videos tardaron unos 4 min en total, en lugar
  de ≈ 26 min uno tras otro.

**Imágenes fijas.** El informe en PDF no puede llevar videos, así que
`videos.cuadro` genera imágenes de instantes elegidos (`v1_*_gt*.png` y
`v2_*_gt*.png` en `resultados/figuras/`). Cada una muestra la envolvente en
una ventana de un período (200 µs) antes del instante. Sirven también como
respaldo en la presentación.

**Verificación:** se extrajo un cuadro de cada tipo de video con ffmpeg y se
revisó. Por ejemplo, en `v2_topologias_k0p1` con γt = 0.84, en el anillo la
energía solo cubre el lado de la fuente, mientras ER ya está lleno. Los
metadatos del video son correctos: 16 s, 1920×1080 y 24 cuadros/s.

### Figuras para proyectar (`scripts/f5_figuras_presentacion.py`)

Las figuras G1 a G10 son rejillas densas, adecuadas para el informe. Para la
presentación se generaron versiones con **una idea por diapositiva**, un
título que dice la conclusión y letra más grande (base 14 en vez de 9.5).
Están en `resultados/figuras/presentacion/`.

| Figura | Diapositiva del plan | Contenido |
|--------|----------------------|-----------|
| `p1_validacion` | Validación | G2 completa |
| `p2_llegada_k0p1` | Propagación (P1, P3) | γt frente a d, 4 redes, κ = 0.1 |
| `p3_rapidez` | Efecto de K (P2, P7) | v/ω₀ frente a κ, umbral 10⁻⁶, un panel |
| `p4_energia_distancia` | Energía y distancia (P4) | Ē(d) con κ = 0.01 y κ = 1 |
| `p5_igual_distancia` | Igual distancia (P5) | γt frente a Nᵢ (κ = 0.1); ⟨Eᵢ⟩ frente a Wᵢ (κ = 1) |
| `p6_topologias` | Topologías (P6) | rapidez, alcance, caída de energía y heterogeneidad |

**Cambios en `graficos.py`:**

- **Tamaños de letra:** varias funciones tenían tamaños fijos (8 a 10
  puntos) que no crecían con el estilo de presentación. Los 33 casos pasaron
  a `fontsize=_fs(x)`, que escala con el tamaño base del estilo vigente. Las
  figuras normales no cambian (razón 1) y las de presentación crecen ≈ 1.5
  veces.
- **`g6_rapidez_vs_kappa`** ahora funciona con un solo umbral; fallaba porque
  matplotlib devuelve un eje suelto en vez de una lista.
- **`guardar`** crea las subcarpetas que hagan falta.

**Ajustes tras revisar las figuras:**

- **Rótulo de fila «κ = …»:** se encimaba con la etiqueta del eje y al
  agrandar la letra. Se integra en la etiqueta del eje (P4) o se quita
  cuando el título ya dice κ (P2).
- **Distribución:** al cambiar el tamaño de una figura ya armada se
  recalcula su distribución con el mismo margen que usa la función original.

## 21. Fase 6: informe final en Word

### Decisiones

- **Informe nuevo:** en `docs/` había un borrador de informe en Word
  (`Informe_final_red_RLC.docx`, del 7 de noviembre) que describía otra
  versión del código:
  - otro paquete (`rlc/`) y otros comandos;
  - 12 pruebas y 446 simulaciones;
  - atol = 10⁻¹⁰, 40 puntos por período y regla del trapecio;
  - otros archivos de datos y algunas cifras distintas.

  Por decisión del grupo se escribió un informe nuevo. El borrador queda
  intacto como referencia.
- **Formato:** Word (.docx) y PDF.
- **Herramientas:** en el equipo no hay Node.js ni LibreOffice. Con permiso
  del grupo se instalaron `python-docx`, `python-pptx` y `PyMuPDF`, anotadas
  en `requirements-docs.txt` (aparte de las del cálculo). PyMuPDF arrastró
  dependencias adicionales (onnxruntime, entre otras) que el proyecto no usa.

### Generación (`scripts/f6_informe.py` y `scripts/f6_exportar.ps1`)

- **`f6_informe.py`:** arma el documento en carta, con fuente Calibri 11 y
  números de página. **Las tablas de resultados se llenan leyendo los CSV**
  de los experimentos y no se copian a mano, así que si se regeneran los
  datos el informe se actualiza. El texto parte de `resumen_resultados.md`,
  la bitácora y la teoría.
- **`f6_exportar.ps1`:** abre el documento en Microsoft Word sin mostrar la
  ventana, actualiza el índice y los números de página, lo guarda y lo
  exporta a PDF.
- **Revisión:** las 24 páginas se convirtieron en imágenes con PyMuPDF y se
  revisaron en hojas de contacto.

**Resultado:** `docs/informe/Informe_final_red_RLC.docx` y `.pdf`, con 24
páginas, 14 figuras, 14 tablas y 8 ecuaciones.

| Sección | Contenido |
|---------|-----------|
| Portada | Datos de la universidad; los nombres de los integrantes quedan como marcadores para completar |
| Índice | Campo de Word, actualizado al exportar |
| Resumen | Con las cifras principales y palabras clave |
| 1. Introducción | Modelo, objetivos y tabla de las 8 preguntas |
| 2. Marco teórico | Oscilador, capacitor compartido, laplaciano, H, modos normales, tiempos cortos, topologías |
| 3. Metodología | Parámetros, redes, método numérico, cantidades, ajustes, experimentos, programa y validación (G1, G2) |
| 4. Resultados | 4.1 a 4.9, cada una con observación, interpretación y especulación; figuras G3–G10, A1–A3 y un cuadro de video |
| 5. Discusión | Tabla de respuestas a P1–P8 con su evidencia; cobertura de los 11 objetivos |
| 6. Conclusiones | Los 5 puntos de la sección 12 del PDF |
| Referencias y Anexo A | 13 referencias; comandos para reproducir todo |

**Correcciones tras revisar el PDF:**

- **Referencias cruzadas:** varias citas a tablas y una a una ecuación no
  coincidían con la numeración real; se corrigieron.
- **Negritas:** las marcas «\*\*…\*\*» salían como asteriscos literales en
  los tres niveles y en las palabras clave.
- **Índice:** «Contenido» aparecía dentro del propio índice.
- **Nombres propios:** se habían pasado a minúscula («erdős–rényi»).
- **Mensaje de consola:** el `.ps1` mostraba «PÃ¡ginas», porque Windows
  PowerShell 5.1 lee los `.ps1` sin BOM como ANSI. Ahora el script no usa
  tildes.

## 22. Hallazgos y decisiones

| Tema | Hallazgo o decisión |
|------|---------------------|
| Duración T = 10/γ | Son **≈ 50 períodos** de ω₀ (10 ms × 5.03 kHz), no 503 como dice la tabla de parámetros del plan. Hay que corregir ese dato en el plan y en el informe. |
| Muestreo | Se usan 100 muestras por período del modo más rápido, no 40, para que los tiempos de llegada no salgan discretizados. |
| ER conexa | El descarte de redes desconexas se registra en `Red.intentos` y debe declararse como sesgo de selección. |
| Numeración | Nodos de 0 a N − 1. La fuente de la malla es el nodo 44. |
| Forma de los arreglos | (n_t, N) en toda la simulación. |
| Energía total | Se reportan Eᵢ y E₀ como exige el PDF. H se usa como diagnóstico, y ⟨Eᵢ⟩/Σ⟨Eⱼ⟩ como apoyo. |
| Balance de energía | Se verifica en forma integrada con Simpson, no derivando datos muestreados. |
| H decae como e^(−γt) | Se confirmó en la malla: H e^(γt)/H(0) se mantiene entre 0.985 y 1.016 para cualquier κ. K y la topología reparten la energía, pero no cambian el ritmo con que se pierde. |
| Ubicación del cruce | Por defecto se refina la raíz con DOP853 continuo o con la solución modal. La interpolación entre muestras falla en los vecinos de la fuente. |
| Nodos no alcanzados | Su tiempo es NaN; se cuentan aparte (`n_no_alcanzados`, `n_validos`) y no entran en las medias. |
| d máx de las redes de referencia | Con la semilla 2026, WS tiene d máx = 10 y ER d máx = 5. El plan citaba 8 y 6, que venían de otra realización; las medias de las 30 son 8.5 y 5.4. Hay que actualizar la tabla del plan. |
| Datos de cada experimento | Se guardan en `.npz` con metadatos y en float32 para Eᵢ y Qᵢ (≈ 3 MB por simulación). Qᵢ(t) se guarda solo para un nodo por distancia. |
| Dispersión entre realizaciones en G1 | Se muestra con mediana y percentiles 10–90, no con media ± σ, porque N_d no puede ser negativo. |
| Curvas de energía | En G3 y G4 se dibuja la envolvente (máximo por intervalo), porque Eᵢ oscila más rápido de lo que una figura puede mostrar. Se aclara en cada figura. |
| Rapidez del frente | Medida resumen: 1/pendiente del ajuste lineal de t frente a d, con d ≥ 1. Se usa para comparar κ y redes; los modelos funcionales se comparan en la Fase 4. |
| Paralelismo | E2 corre en 6 procesos con un hilo de álgebra lineal cada uno: 434 simulaciones en 4 min 19 s. |
| Reutilizar simulaciones | E2 guarda ⟨Eᵢ⟩ para que E3 no repita las integraciones. |
| Escalas en rejillas | Cuando las redes difieren mucho en magnitud (G5), cada panel lleva su propio eje vertical; se comparan formas, no alturas entre columnas. En G7, los paneles con el mismo κ comparten escala. |
| Energías no interpretables | Por debajo de ~10⁻¹² E₀ la dispersión de ⟨Eᵢ⟩ se acerca a la precisión numérica y no tiene relevancia física; G8 la excluye. |
| Dos variabilidades | σ_E(d) (entre nodos) y percentiles 10–90 entre realizaciones se calculan y dibujan por separado, como pide el plan. |
| Peso modal con proyectores | Wᵢ se calcula con proyectores sobre cada autovalor, para que no dependa de la base cuando hay autovalores repetidos (malla, anillo). |
| Comparar a igual distancia | E4 resta la media de cada grupo (realización, d) antes de medir el efecto de un predictor; G9 usa la misma normalización. |
| Sensibilidad con T = 10/γ | En E5 cada valor de R usa T = 10/γ, para comparar el mismo número de tiempos de decaimiento. |
| Limitación de la rapidez lineal | La rapidez del ajuste lineal depende del rango de d (baja con N), porque t(d) es curvo. En la Fase 4 hay que comparar modelos o fijar el rango de d. |
| Reproducibilidad | Semillas fijas, tolerancias fijas y un hilo de álgebra lineal por proceso: las simulaciones se repiten bit a bit. |
| Ajustes por realización | En WS y ER cada realización se ajusta por separado y se reporta cuántas gana cada modelo; los ajustes conjuntos solo se usan para dibujar. |
| Rapidez como resumen | La rapidez lineal se conserva solo como resumen comparativo. La descripción correcta de t(d) es la ley de potencia, con b > 1. |
| Tiempo de los videos | Cuadros repartidos como t ∝ (cuadro)³, para que el frente rápido sea visible; el reloj muestra el γt real. |
| Letra escalable | Los tamaños de letra de `graficos.py` escalan con el estilo; las mismas funciones sirven para el informe y para proyectar. |

## 23. Próximos pasos

1. **Corregir el plan:**
   - T = 10/γ son unos 50 períodos, no 503;
   - las d máx de referencia de WS y ER son 10 y 5.
2. **Revisión de la Fase 4 por el grupo** (en curso).
3. **Revisión de la Fase 5:** ver los 6 videos y las figuras de
   `resultados/figuras/presentacion/` en el proyector o pantalla que se usará,
   y confirmar que se leen desde el fondo del salón.
4. **Fase 6, lo que falta:**
   - completar los nombres de los integrantes en la portada del informe;
   - diapositivas en PowerPoint (.pptx) y guion por integrante;
   - banco de preguntas de defensa.

## Registro de cambios

| Fecha | Cambio |
|-------|--------|
| 6 nov 2026 | Estructura del proyecto, `redes.py`, primer commit y subida a GitHub |
| 6 nov 2026 | Proyecto movido fuera de OneDrive; IDE con el intérprete `fisica3` |
| 6 nov 2026 | `pytest.ini` y `tests/test_redes.py` (47 pruebas); enunciado copiado a `docs/` |
| 6 nov 2026 | `modelo.py`: parámetros, DOP853, solución modal y `simular`, verificados frente a la solución exacta; se crea esta bitácora |
| 6 nov 2026 | `analisis.py`, parte de energía: Eᵢ, U, H, potencias, balance integrado, ⟨Eᵢ⟩ y fracción de energía. `Simulacion` ahora guarda Λ. Resultados verificados frente a la teoría |
| 6 nov 2026 | RK4 propio en `modelo.py` (método "rk4"). `tests/test_modelo.py`, `tests/test_energia.py` y `tests/conftest.py`: las 9 pruebas de validación del plan y otras más; 120 pruebas aprobadas |
| 8 nov 2026 | Commits confirmados en GitHub (último: `0587d9e`). `docs/pseudocodigo_y_diagrama_flujo.md`: tabla de ecuaciones y código, diagrama de flujo general, pseudocódigo de cada módulo y diagrama de módulos. Fase 2 lista para revisión |
| 8 nov 2026 | Fase 2 aprobada por un integrante. Inicio de la Fase 3: tiempos de llegada (umbral, nodos no alcanzados, refinamiento de la raíz) y estadísticas por distancia en `analisis.py`. `tests/test_analisis.py` (25 pruebas); 145 pruebas aprobadas |
| 8 nov 2026 | `resultados.py` (rutas y guardado con metadatos), `graficos.py` (estilo, paleta y G1), `scripts/g1_redes.py` y `scripts/e1_dinamica.py`. G1 generado y revisado; E1 con 20 simulaciones que pasan todos los controles. `tests/test_resultados_graficos.py`; 149 pruebas aprobadas |
| 8 nov 2026 | G3 (energía por distancia) y G4 (mapa nodo × tiempo con el frente) en `graficos.py` y `scripts/g3_g4_dinamica.py`, generados con los datos de E1 y revisados (leyendas fuera de los paneles, envolvente y etiquetas sin encimarse). 151 pruebas aprobadas |
| 8 nov 2026 | E2 (`scripts/e2_llegadas.py`): 434 simulaciones en paralelo, con 7 valores de κ, 3 umbrales y 30 realizaciones de WS y ER; controles OK. `analisis.rapidez_frente`. Los exponentes de la rapidez (≈ 1 débil, ≈ 0.6 fuerte) respaldan la hipótesis de la teoría. 154 pruebas aprobadas |
| 8 nov 2026 | G5 (llegada frente a distancia) y G6 (rapidez frente a κ) en `graficos.py` y `scripts/g5_g6_llegadas.py`, revisados (escala propia por panel, etiquetas separadas, referencias en la leyenda). `g6_rapidez.csv`. 156 pruebas aprobadas |
| 8 nov 2026 | E3 (`scripts/e3_energia_distancia.py`) con los datos de E2, sin simular; `analisis.por_distancia_realizaciones`. G7 y G8 (`scripts/g7_g8_energia.py`), revisados (escala por fila, piso de 10⁻¹² E₀ en G8). 158 pruebas aprobadas |
| 8 nov 2026 | E4 (`scripts/e4_posicion.py`) con los datos de E2; `analisis.peso_modal_incoherente` y `analisis.relacion_a_igual_distancia`. G9 (`scripts/g9_posicion.py`), revisado (predictor normalizado por grupo, ejes legibles). Nᵢ explica el tiempo de llegada; Wᵢ, la energía con κ grande. 164 pruebas aprobadas |
| 8 nov 2026 | E5 (`scripts/e5_sensibilidad.py`): 234 simulaciones con γ, N y posición de la fuente; `redes.con_fuente`. G10 (`scripts/g10_topologias.py`), revisado (nombres cortos, leyenda sin ambigüedad). Todos los experimentos de la Fase 3 listos. 167 pruebas aprobadas |
| 8 nov 2026 | G2 (`scripts/g2_validacion.py`). `verificar_reproducibilidad.py`: diferencia 0 en 8 simulaciones de E2. `fase3_completa.py` regenera toda la fase. Diagramas y README actualizados. Fase 3 lista para la revisión del grupo. 168 pruebas aprobadas |
| 8 nov 2026 | Fase 3 regenerada de punta a punta con `fase3_completa.py` (920 s, controles OK, reproducibilidad exacta). Inicio de la Fase 4: `ajustes.py` (8 modelos, AICc, pesos de Akaike), `f4_ajustes.py` y figuras A1 a A3 (`f4_figuras.py`). Resultados: t ∝ dᵇ con b > 1; E(d) pasa de exponencial a potencia al subir κ; v(κ) con κ_c ≈ 0.6–0.9. 183 pruebas aprobadas |
| 8 nov 2026 | `docs/resumen_resultados.md`: las 8 preguntas en tres niveles, la cobertura de los objetivos, un borrador de conclusiones y la tabla de evidencias. Fase 4 completa |
| 8 nov 2026 | Fase 5: `videos.py` y `scripts/f5_videos.py` (6 videos 1080p en paralelo, imágenes fijas para el informe); `scripts/f5_figuras_presentacion.py` (6 figuras para proyectar); tamaños de letra escalables en `graficos.py`; `tests/test_videos.py`. 188 pruebas aprobadas |
| 8 nov 2026 | Fase 6: informe nuevo en Word (`scripts/f6_informe.py`, `scripts/f6_exportar.ps1`), 24 páginas, con tablas leídas de los datos; exportado a PDF y revisado página por página. `requirements-docs.txt` |
