# Resumen de resultados

Es el entregable «Resumen de resultados» de la Fase 4. Responde las 8
preguntas de investigación del PDF (sección 4) con los datos de los
experimentos E1 a E5 y los ajustes de la Fase 4. Es la base del informe y de
las conclusiones de la Fase 6.

## Cómo leer este documento

Cada pregunta se responde en tres niveles, separados como pide el plan (y la
sección 11 del PDF: «distinguir entre las observaciones obtenidas
directamente de las simulaciones y la interpretación física»):

| Nivel | Qué contiene |
|-------|--------------|
| **Observación numérica** | Lo que muestran los datos, con cifras y la figura que las sostiene. No incluye explicaciones. |
| **Interpretación física** | La explicación que ofrece el modelo, apoyada en la teoría de la Fase 1 o en un experimento de control. |
| **Especulación** | Ideas plausibles que los datos no prueban. Son hipótesis para el informe o para extensiones. |

**Condiciones de todos los resultados, salvo que se indique otra cosa:**

- **Circuito:** L = 1 mH, C = 1 µF, R = 1 Ω (γ = 1000 s⁻¹, ω₀ = 31 623 rad/s,
  ω₀/γ = 31.6) y Q₀ = 1 µC (E₀ = 0.5 µJ).
- **Simulación:** T = 10/γ = 10 ms (≈ 50 períodos), umbral E_th = 10⁻⁶ E₀.
- **Redes:** N = 100. Malla 10 × 10 con la fuente en el nodo interior 44;
  anillo k = 4; mundo pequeño (WS, p = 0.1) y Erdős–Rényi (ER, p = 4/99,
  conexas), cada una con 30 realizaciones (semillas 2026 a 2055).
- **Acoplamiento:** se expresa como κ = K/ω₀².

**Referencias cruzadas:**

- figuras: G1 a G10 y A1 a A3, en `resultados/figuras/`;
- datos: `resultados/datos/`;
- detalle de cada experimento: `docs/bitacora_desarrollo.md`, secciones 10 a
  18.

---

## P1. ¿Cómo se propaga una perturbación inicialmente localizada?

**Respuesta corta.** La energía avanza enlace por enlace desde la fuente: un
nodo empieza a recibirla cuando ya la tienen sus vecinos más cercanos a la
fuente. No hay un frente estricto, porque en teoría todos los nodos responden
desde t > 0. Aun así, el primer rastro medible avanza ordenado por distancia.
Mientras tanto, la energía total se disipa a un ritmo fijo, e^(−γt).

**Observación numérica.**

- **Orden de llegada** (G4): con el umbral de 10⁻⁶ E₀, el tiempo de llegada
  crece con la distancia en las cuatro redes y con todos los valores de κ.
  El frente de puntos naranjas es monótono.
- **Escalones de distancia** (G3): con κ = 0.01, cada distancia recibe un
  máximo de energía menor y más tardío. La fuente pierde energía hacia sus
  vecinos y a la vez por disipación.
- **No siempre llega a toda la red** (E1, G4): con κ = 0.01, de 99 nodos se
  alcanzan 44 en la malla, 18 en el anillo, 23 en WS y 91 en ER (realización
  de referencia).
- **Con κ = 1** el frente cruza toda la red antes de γt ≈ 0.8. Desde ahí,
  todos los nodos tienen energías del mismo orden y caen juntos.
- **Energía total** (G2a): H(t) = ΣEᵢ + U sigue H(0)e^(−γt) en todas las
  simulaciones. H(t)e^(γt)/H(0) se mantuvo entre 0.985 y 1.016.

**Interpretación física.**

- **Por qué enlace por enlace:** la ecuación (1) solo acopla vecinos
  directos. A tiempos cortos, Qᵢ(t) ≈ Q₀ Nᵢ K^d t^(2d)/(2d)! (teoría,
  punto 7): un nodo a distancia d recibe la señal en el orden d de la serie,
  así que crece como t^(2d) y tarda más en ser medible cuanto más lejos está.
- **Por qué la pérdida no depende de K ni de la red:** todos los modos
  normales decaen con la misma tasa γ/2 (teoría, punto 6). K y la topología
  reparten la energía entre los nodos, pero no cambian el ritmo con que se
  pierde.
- **Por qué no llega a toda la red con κ pequeño:** hay dos «relojes». El
  tiempo de transferencia por enlace es t_tr ≈ πω₀/K y el de decaimiento,
  1/γ. Con κ = 0.01, t_tr ≈ 10/γ: la energía se disipa antes de recorrer la
  red.

**Especulación.** El frente tiene un ancho que crece con la distancia, por
la dispersión de los modos (ver P3). Un umbral más alto vería un frente más
compacto y más tardío.

**Evidencia:** G2, G3, G4; `e1_resumen.csv`.

---

## P2. ¿Cómo influye K en la propagación y en la distribución de energía según la distancia?

**Respuesta corta.** K acelera la propagación, con dos regímenes. Con
acoplamiento débil la rapidez crece como K, y con acoplamiento fuerte, como
√K. El cambio ocurre cerca de K ≈ ω₀². Además, al aumentar K la energía sale
más de la fuente y se reparte de forma más pareja por distancia: el perfil
pasa de caer exponencialmente a ser casi plano.

**Observación numérica.**

- **Rapidez del frente** (E2, G6, A3; v/ω₀ con umbral 10⁻⁶, mediana de las
  realizaciones):

| κ | Malla | Anillo | Mundo pequeño | ER |
|---|-------|--------|---------------|----|
| 0.01 | 0.028 | 0.023 | 0.022 | 0.025 |
| 0.1 | 0.26 | 0.13 | 0.17 | 0.30 |
| 1 | 1.76 | 0.94 | 1.32 | 2.04 |
| 10 | 6.34 | 4.09 | 5.23 | 7.67 |

- **Exponente de v frente a κ:** 0.95–1.04 con κ entre 0.03 y 0.3, y
  0.56–0.64 con κ entre 1 y 10, en las cuatro redes.
- **Mejor modelo de v(κ)** (A3): v = Aκ/√(1 + κ/κ_c) o su versión por tramos
  con exponentes 1 y ½. El cambio de régimen está en κ_c = 0.62 (malla), 0.55
  (anillo), 0.91 (WS) y 0.75 (ER).
- **Energía que se queda en la fuente** (⟨E_fuente⟩/Σ⟨Eⱼ⟩, E3): ≈ 0.87 con
  κ = 0.01, ≈ 0.3 con κ = 0.1 y ≈ 0.1 con κ = 1, casi igual en las cuatro
  redes.
- **Perfil de energía por distancia** (G7, A2):
  - con κ = 0.01, Ē(d) cae de forma exponencial, entre −0.8 y −1.2 décadas
    por enlace;
  - con κ ≥ 1 gana una ley de potencia con un exponente pequeño, y en la
    malla y el anillo el perfil es casi plano (−0.03 a −0.04 décadas por
    enlace).
- **Alcance:** con κ ≥ 0.1 se alcanzan los 99 nodos en todas las redes; con
  κ = 0.01, entre el 18 % y el 90 %.

**Interpretación física.**

- **Acoplamiento débil (K ≪ ω₀²):** dos osciladores vecinos intercambian
  energía con una frecuencia de batido Δ ≈ K/ω₀ (teoría, punto 3). Por eso
  la rapidez es proporcional a K/ω₀.
- **Acoplamiento fuerte (K ≫ ω₀²):** el término de acoplamiento domina sobre
  ω₀². Las frecuencias de los modos se separan como √(Kλ), y la velocidad de
  grupo máxima crece como √K. En la cadena es exactamente v_max ≈ √K (teoría,
  punto 7, paso 13).
- **El cambio de régimen** ocurre cuando las dos escalas son comparables,
  K ~ ω₀², de acuerdo con κ_c ≈ 0.55–0.9.
- **El reparto de la energía** depende de la competencia con γ:
  - con κ pequeño, cada enlace transfiere poca energía antes de que se
    disipe, así que la energía cae un factor casi constante por enlace (perfil
    exponencial);
  - con κ grande, la transferencia es más rápida que la disipación y la
    energía alcanza a repartirse por toda la red antes de perderse (perfil
    plano).

**Especulación.** El prefactor A de la rapidez parece depender de cuántos
caminos cortos hay hacia cada nodo; κ_c depende menos de la red. Podría
existir una relación entre A y propiedades espectrales de Λ (ancho del
espectro, λ₂), pero solo hay cuatro redes para comprobarlo.

**Evidencia:** G6, G7, A2, A3; `e2_resumen.csv`, `e3_resumen.csv`,
`f4_ajustes_v.csv`.

---

## P3. ¿Hay relación entre el tiempo de llegada y la distancia topológica?

**Respuesta corta.** Sí. El tiempo de llegada crece con la distancia según
una ley de potencia, γt = a·dᵇ, con **b > 1**: el frente se desacelera a
medida que se aleja. La relación depende del umbral elegido.

**Observación numérica.**

- **Mejor modelo** (A1, `f4_ajustes_t.csv`): la ley de potencia gana a los
  modelos lineal y logarítmico en todas las redes y valores de κ (29 o 30 de
  30 realizaciones en WS y ER).
  - El ΔAICc del segundo modelo va de 10 a 131.
  - Los residuos de la potencia quedan cerca de cero en todas las
    distancias; los otros dos modelos dejan curvaturas sistemáticas.
- **Exponente b** (mediana):

| Red | κ = 0.01 | κ = 0.1 | κ = 1 | κ = 10 |
|-----|----------|---------|-------|--------|
| Malla | 2.63 | 1.70 | 1.62 | 1.68 |
| Anillo | 2.93 | 1.47 | 1.44 | 1.35 |
| Mundo pequeño | 2.91 | 1.99 | 1.91 | 1.82 |
| Erdős–Rényi | 2.77 | 2.31 | 2.12 | 2.26 |

- **d = 1 no se aparta de la tendencia:** con el mejor modelo ajustado sin
  d = 1, el residuo en d = 1 está entre −0.2 y −0.8 desviaciones estándar.
- **Dependencia del umbral** (E2, G5, G6): al bajar el umbral de 10⁻⁴ a 10⁻⁸
  la rapidez aparente aumenta entre un 30 % (anillo) y un 250 % (ER con
  κ = 0.1). El orden entre redes y la forma de las curvas se mantienen.
- **Consecuencia práctica** (E5): una «rapidez» lineal única depende del
  rango de distancias usado. En la malla baja de 0.37 a 0.19 (κ = 0.1) al
  pasar de N = 36 a N = 400.

**Interpretación física.**

- **Qué es el tiempo de llegada:** el primer instante en que un nodo acumula
  energía por encima de un nivel fijo. A tiempos cortos la señal crece como
  t^(2d) (teoría, punto 7), y entre tanto la energía total decae como
  e^(−γt). Por eso cada distancia extra cuesta más tiempo, y con κ pequeño
  el exponente es grande (b ≈ 2.6–2.9): el sistema está cerca de no
  alcanzar a los nodos lejanos.
- **Dilución de la energía:** el orden de b entre redes coincide con el
  crecimiento de N_d (G1). El anillo, con N_d constante (= 4), tiene el b
  más bajo (≈ 1.4), el más parecido a una onda de velocidad constante. La
  malla, con N_d que crece linealmente, queda en medio (≈ 1.65). WS y ER,
  donde N_d crece rápido, tienen b ≈ 2. Cuando la energía del frente se
  reparte entre más nodos, a cada uno le llega menos y tarda más en cruzar
  el umbral.
- **Dependencia del umbral:** el tiempo de llegada mide el primer rastro, no
  el paso del grueso de la energía (teoría, punto 7). Por eso conviene
  reportar siempre el umbral usado.

**Especulación.** El argumento de dilución es coherente con el orden de los
exponentes, pero no está demostrado. Se podría probar en redes con N_d
controlado, por ejemplo árboles regulares con distinto número de ramas.

**Evidencia:** G5, G6, A1; `f4_ajustes_t.csv`, `e5_resumen.csv`.

---

## P4. ¿Cómo varía la energía media con la distancia a la fuente?

**Respuesta corta.** Disminuye con la distancia en todas las redes. La forma
de la caída depende de κ: es exponencial con acoplamiento débil y una ley de
potencia suave, casi plana, con acoplamiento fuerte.

**Observación numérica.**

- **Caída de Ē(d)** (G7, E3; pendiente de log₁₀Ē por enlace):

| Red | κ = 0.01 | κ = 0.1 | κ = 1 |
|-----|----------|---------|-------|
| Malla | −0.85 | −0.10 | −0.03 |
| Anillo | −1.70 | −0.14 | −0.04 |
| Mundo pequeño | −1.13 | −0.32 | −0.14 |
| Erdős–Rényi | −1.04 | −0.39 | −0.21 |

- **Mejor modelo** (A2):
  - exponencial con κ = 0.01 en malla, anillo y WS (30/30), con ΔAICc de 27
    a 82;
  - potencia con κ ≥ 0.1 (≥ 1 en el anillo).
- **ER con κ = 0.01** queda indeciso: la potencia gana en 17 de 30
  realizaciones con ΔAICc = 8, porque cada realización tiene solo 4 o 5
  distancias.
- **R² bajo con κ grande** (0.15–0.5): la variación entre nodos a la misma
  distancia es comparable a la variación con la distancia.
- **Bordes de la malla:** Ē(d) deja de decrecer desde d ≈ 5 y sube en d = 9
  y 10 con κ ≥ 0.1.
- **Ē(0)/E₀ no es monótona en κ:** baja de 0.088 (κ = 0.01) a ≈ 0.02
  (κ ≈ 0.3–1) y vuelve a subir, hasta 0.09–0.13 con κ = 10.

**Interpretación física.**

- **Caída exponencial con κ pequeño:** cada enlace solo transmite una
  fracción pequeña de la energía antes de que se disipe, así que la energía
  cae un factor casi constante por enlace.
- **Perfil casi plano con κ grande:** la energía llega a todos los nodos en
  menos de 1/γ y se reparte entre los modos normales. El promedio temporal
  ve entonces una distribución casi uniforme, modulada por la estructura de
  la red (ver P5).
- **Por qué Ē(0) vuelve a subir:** la energía inicial real es
  H(0) = E₀(1 + k₀κ). Con κ grande, los capacitores de acoplamiento guardan
  mucha energía al inicio y la devuelven a las mallas. Por eso ⟨Eᵢ⟩/E₀ no es
  una fracción de la energía disponible. Para comparar repartos se usa
  ⟨Eᵢ⟩/Σ⟨Eⱼ⟩.

**Especulación.** La subida en los bordes de la malla podría deberse a
reflexiones en el borde abierto: los nodos de esquina, con grado 2, acumulan
la energía que vuelve. Habría que compararlo con una malla con condiciones
periódicas (un toro).

**Evidencia:** G7, A2; `e3_resumen.csv`, `f4_ajustes_E.csv`.

---

## P5. ¿Los nodos a la misma distancia responden igual?

**Respuesta corta.** **No.** A la misma distancia, la energía media puede
diferir en más de un factor 10, y el tiempo de llegada en un 30–50 %. Las
diferencias tienen causas identificables:

- el **número de caminos más cortos Nᵢ** explica el tiempo de llegada, y la
  energía con κ pequeño;
- el **peso modal Wᵢ** explica la energía con κ grande;
- el **grado** casi no importa.

**Observación numérica** (E4, G9; R² es la parte de la variación a igual d
explicada por cada predictor):

| Respuesta | Nᵢ | kᵢ (grado) | Wᵢ (peso modal) |
|-----------|----|------------|-----------------|
| Tiempo de llegada (todos los κ) | ρ ≈ −0.9; R² = 0.66–0.99 (anillo 0.20–0.35) | R² ≤ 0.12 | R² ≤ 0.06 (anillo con κ = 0.01: 0.32) |
| Energía media, κ = 0.01 | ρ ≈ +0.85; R² = 0.64–1.0 | R² ≤ 0.19 | R² ≤ 0.04 |
| Energía media, κ ≥ 1 | R² ≤ 0.24 | R² ≤ 0.20 | ρ ≈ +0.8; R² = 0.50–0.79 (anillo ≤ 0.14) |

- **Tamaño de las diferencias:** en WS y ER con κ = 0.01, nodos a la misma
  distancia tienen entre ≈ 0.05 y ≈ 20 veces la energía media de su
  distancia (G9).
- **Simetría** (G5, G9): en el anillo, los nodos simétricos (+d y −d)
  responden exactamente igual, por la simetría de la red.

**Interpretación física.**

- **Por qué Nᵢ fija el tiempo de llegada:** a tiempos cortos, la amplitud
  que llega es proporcional a Nᵢ (Qᵢ ∝ Nᵢ K^d t^(2d)), porque las
  contribuciones de los caminos más cortos se suman (teoría, punto 7). Más
  caminos significa llegar antes.
- **Por qué Nᵢ también fija la energía con κ pequeño:** la energía casi no
  pasa del frente, así que depende de cuánto llega por esos caminos.
- **Por qué con κ grande manda Wᵢ:** la energía se reparte entre todos los
  modos normales, y la respuesta de cada nodo queda determinada por cuánto
  participa en los modos que excita la fuente: Wᵢ = Σ_λ (Π_λ)ᵢ₀² (teoría,
  punto 6).
- **Por qué no importa el grado:** describe solo el entorno inmediato del
  nodo, no cómo está conectado con la fuente.

**Especulación.** Debería existir un predictor único que combine los dos
regímenes, por ejemplo un peso modal amortiguado y ponderado por el tiempo de
transferencia. Explicaría el R² intermedio con κ = 0.1.

**Evidencia:** G9; `e4_resumen.csv`.

---

## P6. ¿Cómo influye la topología?

**Respuesta corta.** La topología fija la rapidez, el alcance y la forma del
reparto. **ER es la red más rápida y de mayor alcance, y el anillo la más
lenta y de menor alcance.** En cambio, la cantidad de energía que sale de la
fuente casi no depende de la red.

**Observación numérica** (G10, medianas):

| Métrica | Malla | Anillo | Mundo pequeño | ER |
|---------|-------|--------|---------------|----|
| v/ω₀, κ = 0.1 / κ = 1 | 0.26 / 1.76 | 0.13 / 0.94 | 0.17 / 1.32 | 0.30 / 2.04 |
| Alcance con κ = 0.01 | 0.44 | 0.18 | 0.31 | 0.90 |
| Exponente b de t(d), κ = 1 | 1.62 | 1.44 | 1.91 | 2.12 |
| Caída de Ē por enlace, κ = 0.1 | −0.10 | −0.14 | −0.32 | −0.38 |
| Heterogeneidad σ/Ē, κ = 0.1 | 0.42 | 0.09 | 0.70 | 0.70 |
| Energía que queda en la fuente, κ = 0.1 | 0.27 | 0.32 | 0.32 | 0.31 |
| λ₂ (conectividad algebraica) | 0.098 | 0.020 | 0.123 | 0.450 |

- **Orden de rapidez:** ER > malla > WS > anillo, igual para todo κ ≥ 0.03.
- **λ₂:** ordena bien los extremos (ER y anillo), pero WS tiene un λ₂ algo
  mayor que la malla y es más lento.
- **Posición de la fuente** (E5):
  - **malla:** con la fuente en el borde o la esquina, la rapidez es un 20 a
    30 % menor;
  - **ER:** el frente es un 75 % más rápido desde el nodo de mayor grado que
    desde el de menor grado.

**Interpretación física.**

- **Distancias cortas, frente rápido:** la red con distancias más cortas (ER:
  d máx ≈ 5) lleva la energía a más nodos en menos enlaces. El anillo, con
  d máx = 25 y un solo camino «de ida», es el caso más lento.
- **Por qué el reparto es más desigual en las redes aleatorias:** tienen
  mucha variedad de Nᵢ y de pesos modales entre nodos a la misma distancia
  (P5). Las regulares, por su simetría, reparten la energía de forma pareja.
- **Por qué sale lo mismo de la fuente en todas las redes:** depende sobre
  todo del acoplamiento local (κ y el grado de la fuente). La red decide
  hacia dónde va esa energía y a qué velocidad, no cuánta sale.

**Especulación.** λ₂ por sí solo no basta para predecir la rapidez. Una
combinación de la distribución de distancias (N_d) con propiedades
espectrales podría ordenar las cuatro redes, pero hacen falta más
topologías para probarlo.

**Evidencia:** G1, G5, G6, G10; `g10_metricas.csv`, `e5_resumen.csv`.

---

## P7. ¿Qué interpretación física tiene el efecto del acoplamiento?

**Respuesta corta.** K representa un capacitor compartido entre mallas
vecinas, con K = 1/(LC_c). Transforma la diferencia de carga entre dos
mallas en un voltaje que empuja corriente de una a la otra. Un K mayor (un
C_c menor) intercambia energía más rápido. **K decide qué tan rápido y qué
tan lejos se reparte la energía; γ decide cuánto tiempo dura.**

**Observación numérica.**

- **K casi no cambia la pérdida de energía:** H(t) decae como H(0)e^(−γt)
  con cualquier κ (G2a).
- **Energía guardada en los enlaces:** con κ = 1, la suma ΣEᵢ llega a 4.7 E₀
  en la malla, y el 80 % de la energía inicial está en los capacitores de
  acoplamiento (H(0) = E₀(1 + k₀κ), E1).
- **γ casi no cambia la rapidez, pero sí el alcance** (E5): al multiplicar R
  por 33 (de 0.3 a 10 Ω), v/ω₀ cambia menos de un 10 % con κ = 1 en malla y
  ER. En cambio, con R = 10 Ω y κ = 0.1 el alcance baja al 16–44 % en
  anillo, WS y malla, y la fuente retiene el 90 % de la energía.
- **El cambio de régimen de la rapidez** ocurre en κ_c ≈ 0.55–0.9, es
  decir, K ≈ ω₀² (P2).

**Interpretación física.**

- **Los capacitores de acoplamiento almacenan y devuelven energía, pero no
  la disipan:** solo las resistencias convierten energía en calor
  (dH/dt = −RΣIᵢ²). Por eso K cambia el reparto y no el ritmo de pérdida.
- **Dos relojes:** el tiempo de transferencia por enlace (≈ πω₀/K con
  acoplamiento débil) y el de decaimiento (1/γ). Si la transferencia es más
  lenta que el decaimiento, la energía se pierde antes de llegar.
- **K ≈ ω₀² como escala:** cuando la «rigidez» del acoplamiento iguala la de
  cada malla, el intercambio deja de ser una perturbación lenta (batidos) y
  pasa a ser una onda que se propaga por toda la red.

**Especulación.** En un circuito real, C_c no sería ideal (tendría pérdidas
propias). Eso añadiría disipación en los enlaces y haría que κ grande
también acelerara la pérdida de energía.

**Evidencia:** G2, G3, G6, A3; `e1_resumen.csv`, `e5_resumen.csv`; teoría,
puntos 3, 5 y 6.

---

## P8. ¿Cómo cambia la heterogeneidad energética con la distancia?

**Respuesta corta.**

- **En términos absolutos,** σ_E(d) disminuye con la distancia, siguiendo a
  Ē(d).
- **En términos relativos,** σ/Ē es alta con acoplamiento débil y moderada
  con acoplamiento fuerte, sin una tendencia clara con d.
- **Por tipo de red,** es mucho mayor en las redes aleatorias que en las
  regulares.

**Observación numérica** (E3, G8, `f4_ajustes_sigma.csv`):

- **σ absoluta:**
  - en WS y ER cae con d de forma exponencial en la mayoría de las
    realizaciones (R² de 0.46 a 0.99);
  - en la malla no es monótona (R² < 0.42).
- **σ relativa (σ/Ē):**
  - en WS y ER llega a 1.0–1.3 con κ = 0.01 y baja a ≈ 0.4–0.65 con κ grande,
    casi sin depender de d;
  - en la malla y el anillo es más baja y cambia de forma irregular entre
    distancias.
- **Por red** (mediana sobre d ≥ 1, κ = 0.1; G10): anillo 0.09, malla 0.42,
  WS 0.70 y ER 0.70.

**Interpretación física.**

- **Por qué hay heterogeneidad:** la heterogeneidad a igual distancia es la
  huella de P5. Viene de las diferencias en Nᵢ (κ pequeño) y en los pesos
  modales (κ grande) entre nodos a la misma distancia. En las redes
  aleatorias esas diferencias son grandes; en las regulares, la simetría las
  reduce o elimina.
- **Por qué es mayor con κ pequeño:** la energía depende casi
  exponencialmente de cuántos caminos llegan, así que diferencias modestas en
  Nᵢ se vuelven diferencias grandes en energía.

**Especulación.** En la malla y el anillo, la forma irregular de σ/Ē por
distancia podría seguir un patrón de interferencia entre caminos de igual
longitud. Haría falta una malla mayor para confirmarlo.

**Evidencia:** G8, G10; `e3_resumen.csv`, `f4_ajustes_sigma.csv`.

---

## Objetivos del PDF y dónde se cumplen

| Objetivo | Estado | Evidencia |
|----------|--------|-----------|
| O1. Derivar la ecuación RLC con Kirchhoff | ✅ | Teoría, punto 1 |
| O2. Extender a N osciladores y justificar el acoplamiento | ✅ | Teoría, puntos 3 y 4 (capacitor compartido) |
| O3. Construir mallas, regulares, mundo pequeño y ER | ✅ | `redes.py`, G1 |
| O4. Analizar la perturbación localizada | ✅ | E1, G3, G4 (P1) |
| O5. Relacionar el tiempo y la distancia topológica | ✅ | E2, G5, A1 (P3, P5) |
| O6. Calcular la energía de cada oscilador | ✅ | `analisis.py`, E1 |
| O7. Estudiar la energía media por distancia | ✅ | E3, G7, G8, A2 (P4, P8) |
| O8. Comparar valores de K | ✅ | E2, E3, G6, G7, A3 (P2, P7) |
| O9. Topología y posición de los nodos | ✅ | E4, E5, G9, G10 (P5, P6) |
| O10. Ajustes con medidas de dispersión | ✅ | Fase 4: AICc, residuos, σ_E(d) y percentiles entre realizaciones (A1 a A3) |
| O11. Videos | ✅ | Fase 5: 6 videos (4 de κ por red, 2 de topologías por κ), `resultados/videos/` |

## Borrador de conclusiones (sección 12 del PDF)

Es un borrador para la Fase 6. Cada punto resume las respuestas anteriores.

1. **Efecto de K sobre la propagación.** K acelera el frente y amplía su
   alcance. La rapidez crece como K con acoplamiento débil y como √K con
   acoplamiento fuerte, con el cambio cerca de K ≈ ω₀². K no cambia el ritmo
   con que se pierde la energía (e^(−γt)), que solo depende de R.
2. **Energía y distancia.** La energía media disminuye con la distancia:
   exponencialmente con acoplamiento débil (≈ 1 década por enlace) y de forma
   suave y casi plana con acoplamiento fuerte. El tiempo de llegada crece
   como dᵇ con b > 1.
3. **Influencia de la estructura de la red.** Las redes con distancias cortas
   (ER) propagan más rápido y más lejos que las de distancias largas
   (anillo). A la misma distancia, la respuesta de cada nodo depende del
   número de caminos más cortos (llegada, energía con K débil) y de su peso en
   los modos normales (energía con K fuerte), no de su grado.
4. **Limitaciones.**
   - El modelo es lineal e ideal: R, L y C son iguales en todas las mallas y
     constantes.
   - El acoplamiento por capacitor compartido es exacto en redes planas
     (malla), pero una idealización en ER y WS.
   - El tiempo de llegada depende del umbral elegido.
   - ⟨Eᵢ⟩ depende de T, y ⟨Eᵢ⟩/E₀ no es una fracción de energía.
   - Las redes ER se limitaron a muestras conexas, lo que introduce un sesgo
     de selección (⟨k⟩ = 4.19 en lugar de 4).
   - Con N = 100, ER solo tiene 4 o 5 distancias, lo que limita los ajustes.
   - Una «rapidez» lineal única depende del rango de distancias.
5. **Extensiones.**
   - Elementos no uniformes o no lineales.
   - Pérdidas en los capacitores de acoplamiento.
   - Redes más grandes y más topologías, para probar la hipótesis de dilución
     (P3) y el papel de λ₂ (P6).
   - Mallas periódicas (toro), para separar el efecto de borde (P4).
   - Excitación continua en lugar de un pulso inicial.
   - Comprobación con un circuito real de pocas mallas.

## Revisión de la Fase 4: cada pregunta tiene evidencia

| Pregunta | Figura principal | Dato principal | Archivo |
|----------|------------------|----------------|---------|
| P1 | G4 | alcance y última llegada por red y κ | `e1_resumen.csv` |
| P2 | G6, A3 | exponentes ≈ 1 y ≈ 0.6; κ_c ≈ 0.55–0.9 | `e2_resumen.csv`, `f4_ajustes_v.csv` |
| P3 | G5, A1 | t ∝ dᵇ, b = 1.4–2.3 (κ ≥ 0.1) | `f4_ajustes_t.csv` |
| P4 | G7, A2 | exponencial (κ pequeño) frente a potencia (κ grande) | `e3_resumen.csv`, `f4_ajustes_E.csv` |
| P5 | G9 | R² de Nᵢ y Wᵢ | `e4_resumen.csv` |
| P6 | G10 | métricas por red | `g10_metricas.csv` |
| P7 | G2, A3 | H ∝ e^(−γt); efecto de γ sobre la rapidez y el alcance | `e5_resumen.csv` |
| P8 | G8 | σ/Ē por red y κ | `e3_resumen.csv`, `f4_ajustes_sigma.csv` |

Todas las preguntas tienen al menos una figura y un archivo de datos que las
sostienen. Todos los resultados se regeneran con
`python scripts/fase3_completa.py`, `python scripts/f4_ajustes.py` y
`python scripts/f4_figuras.py`.
