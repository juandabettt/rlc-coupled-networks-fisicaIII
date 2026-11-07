# Bitácora de desarrollo

Este documento explica qué se ha construido en el proyecto, para qué sirve cada
parte y qué se ha comprobado. Se actualiza con cada avance; la sección
«Registro de cambios» al final lleva el historial.

- **Última actualización:** 6 de noviembre de 2026
- **Fase actual:** Fase 2, código y validación (avance ≈ 55 %)

## 1. Estado general

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Teoría del modelo | Documento terminado (`Fase 1 teoría del modelo RLC.pdf`); falta la revisión del grupo |
| 2 | Código y validación | En curso: ver la tabla siguiente |
| 3 a 6 | Experimentos, análisis, gráficos y videos, cierre | Sin iniciar |

**Fase 2 en detalle.** La fase termina cuando pasan todas las pruebas de
validación del plan.

| Paso | Pieza | Estado |
|------|-------|--------|
| 0 | Entorno de trabajo (Python, entorno virtual, Git, pytest) | ✅ Listo |
| 1 | `redes.py`: topologías, laplaciano, distancias, caminos | ✅ Listo y probado (47 pruebas) |
| 2 | `modelo.py`: parámetros, DOP853, solución modal | ✅ Implementado y verificado a mano; faltan sus pruebas automáticas |
| 3 | Energía: Eᵢ, U, H y potencia disipada (`analisis.py`) | ✅ Implementado y verificado a mano; faltan sus pruebas automáticas |
| 4 | Pruebas de validación del modelo (9 del plan) | ⏳ Pendiente |
| 5 | RK4 propio y prueba de convergencia | ⏳ Pendiente |
| 6 | Pseudocódigo y diagrama de flujo | ⏳ Pendiente |

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
| `modelo.py` | Resuelve la dinámica Q(t), I(t) | ✅ (sin pruebas aún) |
| `analisis.py` | Energías, tiempos de llegada, estadísticas por distancia | 🟡 Parte de energía lista; faltan tiempos de llegada y estadísticas (Fase 3) |
| `ajustes.py` | Ajustes funcionales y comparación con AICc | ⏳ |
| `graficos.py` | Gráficos G1 a G10 | ⏳ |
| `videos.py` | Animaciones de log₁₀(Eᵢ/E₀) | ⏳ |

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

`simular(red, p, metodo="dop853" | "modal")` hace tres cosas:

1. Fija las condiciones iniciales del PDF: Q₀ en la fuente, el resto en cero y
   todas las corrientes nulas.
2. Elige la malla temporal.
3. Devuelve una `Simulacion`, con `t`, `Q`, `I` (forma n_t × N; columna i =
   nodo i), el laplaciano `Lambda`, los parámetros, la fuente, el método y
   datos del cálculo. Guarda `Lambda` porque la energía de acoplamiento lo
   necesita.

`sim.t_gamma` da el tiempo adimensional γt que usan los gráficos.

### Verificación hecha a mano

Es una comprobación previa. Pasará a pruebas automáticas en el paso 4.

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

### Verificación hecha a mano

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

## 7. Hallazgos y decisiones

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

## 8. Próximos pasos

1. **Pruebas del modelo:**
   - oscilador aislado;
   - conservación con R = 0;
   - decaimiento e^(−γt);
   - balance dH/dt = −RΣIᵢ²;
   - dos nodos;
   - modo uniforme;
   - simetría del anillo;
   - comparación con la solución modal.
2. **RK4 propio** y su prueba de convergencia de orden 4.
3. **Pseudocódigo y diagrama de flujo** del código.

## Registro de cambios

| Fecha | Cambio |
|-------|--------|
| 6 nov 2026 | Estructura del proyecto, `redes.py`, primer commit y subida a GitHub |
| 6 nov 2026 | Proyecto movido fuera de OneDrive; IDE con el intérprete `fisica3` |
| 6 nov 2026 | `pytest.ini` y `tests/test_redes.py` (47 pruebas); enunciado copiado a `docs/` |
| 6 nov 2026 | `modelo.py`: parámetros, DOP853, solución modal y `simular`, verificados frente a la solución exacta; se crea esta bitácora |
| 6 nov 2026 | `analisis.py`, parte de energía: Eᵢ, U, H, potencias, balance integrado, ⟨Eᵢ⟩ y fracción de energía. `Simulacion` ahora guarda Λ. Resultados verificados frente a la teoría |
