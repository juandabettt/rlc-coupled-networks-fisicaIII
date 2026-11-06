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
├── docs/                # Teoría (Fase 1), plan y enunciado en PDF
├── red_rlc/             # Paquete con el código del modelo (Fase 2 en adelante)
│   ├── __init__.py
│   ├── redes.py         # Generación de topologías y distancias       (listo)
│   ├── modelo.py        # Sistema de primer orden e integración        (pendiente)
│   ├── analisis.py      # Energías, tiempos de llegada, estadísticas   (pendiente)
│   ├── ajustes.py       # Ajustes funcionales                          (pendiente)
│   ├── graficos.py      # Gráficos G1 a G10                            (pendiente)
│   └── videos.py        # Animaciones de log₁₀(Eᵢ/E₀)                  (pendiente)
├── scripts/             # Un script por experimento numérico (E1, E2, …)
├── tests/               # Validación: K = 0, casos límite, convergencia
│   └── test_redes.py    # Pruebas de redes.py                          (listo)
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
python -m pytest            # pruebas de validación
python scripts/<experimento>.py
```

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
