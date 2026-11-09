# Red de osciladores RLC acoplados — Proyecto final de Física III

Estudio numérico de la propagación de una perturbación y de la distribución de
energía en una red de N = 100 osciladores RLC acoplados, sobre cuatro
topologías: malla 10 × 10, anillo regular (k = 4), mundo pequeño
(Watts–Strogatz, p = 0.1) y aleatoria de Erdős–Rényi conexa (p = 4/99).

## Modelo

Para cada oscilador i:

    Q̈ᵢ + γ Q̇ᵢ + ω₀² Qᵢ = K Σⱼ Aᵢⱼ (Qⱼ − Qᵢ)

con γ = R/L, ω₀² = 1/(LC), acoplamiento K y matriz de adyacencia A (no dirigida,
sin autoenlaces). En forma vectorial: Q̈ + γQ̇ + (ω₀²𝕀 + KΛ)Q = 0, con Λ = D − A.

- Condiciones iniciales: Q₀(0) = Q₀, Qᵢ(0) = 0 para i > 0, Iᵢ(0) = 0.
- Energía por nodo: Eᵢ = Qᵢ²/(2C) + L Iᵢ²/2.
- Tiempo de llegada: primer instante en que Eᵢ ≥ E_th = 10⁻⁶ E₀; se compara
  γ(tᵢ − t₀) frente a la distancia topológica d₀ᵢ.

Parámetros base: L = 1 mH, C = 1 µF, R = 1 Ω, Q₀ = 1 µC, T = 10/γ, κ = K/ω₀².

## Estructura del repositorio

```
proyecto_final_fisicaIII/
├── README.md            # Este archivo
├── requirements.txt     # Dependencias de Python
├── pytest.ini           # Configuración de las pruebas
├── .gitignore
├── docs/                # Teoría (Fase 1), plan, enunciado y bitácora de desarrollo
├── red_rlc/             # Paquete con el código del modelo (Fase 2 en adelante)
│   ├── __init__.py
│   ├── redes.py         # Generación de topologías y distancias       (listo)
│   ├── modelo.py        # Sistema de primer orden e integración        (listo)
│   ├── analisis.py      # Energías, tiempos de llegada, estadísticas   (listo)
│   ├── ajustes.py       # Ajustes funcionales y comparación con AICc   (listo)
│   ├── graficos.py      # Gráficos G1 a G10                            (listo)
│   ├── resultados.py    # Rutas y guardado de datos (.npz, .csv)       (listo)
│   └── videos.py        # Animaciones de log₁₀(Eᵢ/E₀)                  (listo)
├── scripts/             # Un script por experimento numérico (E1, E2, …)
│   ├── fase3_completa.py # Regenera toda la Fase 3 en orden            (listo)
│   ├── verificar_reproducibilidad.py # Repite una muestra de E2        (listo)
│   ├── g1_redes.py      # G1: topologías y distribución de distancias  (listo)
│   ├── g2_validacion.py # G2: validación del código                     (listo)
│   ├── e1_dinamica.py   # E1: Qᵢ(t), Eᵢ(t), H(t) por red y κ           (listo)
│   ├── g3_g4_dinamica.py # G3 y G4 con los datos de E1                 (listo)
│   ├── e2_llegadas.py   # E2: tiempos de llegada, 30 realizaciones      (listo)
│   ├── g5_g6_llegadas.py # G5 y G6 con los datos de E2                 (listo)
│   ├── e3_energia_distancia.py # E3: Ē(d), σ_E(d) con los datos de E2  (listo)
│   ├── g7_g8_energia.py # G7 y G8 con los datos de E3                   (listo)
│   ├── e4_posicion.py   # E4: nodos a igual d frente a Nᵢ, kᵢ y Wᵢ      (listo)
│   ├── g9_posicion.py   # G9 con los datos de E4                        (listo)
│   ├── e5_sensibilidad.py # E5: sensibilidad a γ, N y fuente           (listo)
│   ├── g10_topologias.py # G10: comparación de topologías              (listo)
│   ├── f4_ajustes.py    # Fase 4: ajustes de tγ(d), E(d), σ(d), v(κ)    (listo)
│   ├── f4_figuras.py    # Fase 4: figuras A1 a A3 (modelos y residuos)  (listo)
│   ├── f5_videos.py     # Fase 5: 6 videos e imágenes fijas            (listo)
│   ├── f5_figuras_presentacion.py # Fase 5: figuras para proyectar     (listo)
│   ├── f6_informe.py    # Fase 6: informe en Word (.docx)              (listo)
│   └── f6_exportar.ps1  # Fase 6: actualiza el índice y exporta a PDF  (listo)
├── tests/               # Validación: K = 0, casos límite, convergencia
│   ├── conftest.py      # Caché de simulaciones compartida
│   ├── test_redes.py    # Pruebas de redes.py                          (listo)
│   ├── test_modelo.py   # Pruebas del modelo y validación del plan     (listo)
│   ├── test_energia.py  # Pruebas de energía y balance de H            (listo)
│   ├── test_analisis.py # Pruebas de tiempos de llegada y Ē(d), σ_E(d)  (listo)
│   ├── test_ajustes.py  # Pruebas de modelos, AICc y comparación       (listo)
│   ├── test_videos.py   # Pruebas de los videos                        (listo)
│   └── test_resultados_graficos.py # Guardado de datos y figuras       (listo)
└── resultados/
    ├── datos/           # Resultados numéricos (.npz, .csv) — no se versionan
    ├── figuras/         # Gráficos finales (.png, .pdf)
    └── videos/          # Animaciones (.mp4) — no se versionan
```

## Instalación

Se requiere Python 3.10 o superior. Se recomienda tener el proyecto y el
entorno virtual **fuera de carpetas sincronizadas como OneDrive**, para que no
se sincronicen miles de archivos de librerías (el versionado lo hace Git):

```bash
# Windows (PowerShell)
python -m venv C:\Users\<usuario>\venvs\fisica3
C:\Users\<usuario>\venvs\fisica3\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

Todos los comandos se ejecutan desde la raíz del proyecto:

```bash
python -m pytest                              # pruebas de validación (~30 s)
python scripts/<experimento>.py               # un experimento o gráfico
python scripts/fase3_completa.py              # toda la Fase 3 en orden (~15 min)
python scripts/verificar_reproducibilidad.py  # comprueba que E2 se reproduce
python scripts/f4_ajustes.py                  # Fase 4: ajustes con AICc (~1 min)
python scripts/f4_figuras.py                  # Fase 4: figuras A1 a A3
python scripts/f5_videos.py                   # Fase 5: 6 videos .mp4 (~4 min, en paralelo)
python scripts/f5_figuras_presentacion.py     # Fase 5: figuras para proyectar
```

Los videos quedan en `resultados/videos/` (no se versionan) y las figuras para
la presentación en `resultados/figuras/presentacion/`.

Informe final (requiere `pip install -r requirements-docs.txt` y Microsoft Word
para el PDF):

```bash
python scripts/f6_informe.py                                   # docs/informe/*.docx
powershell -ExecutionPolicy Bypass -File scripts/f6_exportar.ps1   # índice y PDF
```

`fase3_completa.py` corre primero las pruebas y se detiene si alguna falla.
Los datos quedan en `resultados/datos/` (no se versionan) y las figuras G1 a
G10 en `resultados/figuras/`. Las redes aleatorias usan semillas fijas
(2026 a 2055), así que los resultados se reproducen exactamente.

## Fases

| Fase | Contenido | Fechas |
|------|-----------|--------|
| 1 | Teoría del modelo | 6–8 nov |
| 2 | Código y validación | 8–10 nov |
| 3 | Experimentos numéricos | 10–12 nov |
| 4 | Análisis y ajustes | 12–14 nov |
| 5 | Gráficos finales y videos | 14–15 nov |
| 6 | Informe, conclusiones y presentación | 15–18 nov |

Entrega: 24 de noviembre de 2026.
