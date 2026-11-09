"""Fase 6: informe final en Word (.docx).

Genera docs/informe/Informe_final_red_RLC.docx a partir de:
    - las figuras de resultados/figuras/ (G1 a G10, A1 a A3, cuadros de video);
    - las tablas de resultados/datos/*.csv (las cifras se leen de los datos,
      no se copian a mano: si los datos se regeneran, el informe se actualiza);
    - el texto, basado en docs/resumen_resultados.md, la bitácora y la teoría.

El índice queda como campo de Word; scripts/f6_exportar.ps1 lo actualiza y
exporta el PDF.

Requiere: requirements-docs.txt y haber corrido las Fases 3 a 5.

Uso, desde la raíz del proyecto:
    python scripts/f6_informe.py
"""

import csv
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import numpy as np
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from red_rlc import modelo, redes

FIG = RAIZ / "resultados" / "figuras"
DAT = RAIZ / "resultados" / "datos"
SALIDA = RAIZ / "docs" / "informe" / "Informe_final_red_RLC.docx"

REDES = list(redes.TOPOLOGIAS)
NOMBRE = {"malla": "Malla 10 × 10", "anillo": "Anillo (k = 4)",
          "mundo_pequeno": "Mundo pequeño (WS)", "erdos_renyi": "Erdős–Rényi (ER)"}
AZUL = RGBColor(0x1C, 0x5C, 0xAB)
GRIS = RGBColor(0x52, 0x51, 0x4E)


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

def leer(nombre: str) -> list:
    with open(DAT / f"{nombre}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def mediana(filas, campo, **filtro):
    v = [num(f[campo]) for f in filas
         if all((num(f[k]) == v_ if isinstance(v_, float) else f[k] == v_)
                for k, v_ in filtro.items())]
    v = [x for x in v if np.isfinite(x)]
    return float(np.median(v)) if v else np.nan


def ganadores(filas, **filtro):
    """Cuántas realizaciones gana cada modelo (ΔAICc = 0)."""
    g = [f for f in filas if num(f["delta_aicc"]) == 0 and
         all((num(f[k]) == v if isinstance(v, float) else f[k] == v) for k, v in filtro.items())]
    return Counter(f["modelo"] for f in g)


def fmt(x, d=2):
    if x is None or not np.isfinite(x):
        return "—"
    return f"{x:.{d}f}".replace("-", "−")


def fmt_sci(x, d=1):
    if not np.isfinite(x):
        return "—"
    m, e = f"{x:.{d}e}".split("e")
    sup = str(int(e)).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{m} × 10{sup}"


# ---------------------------------------------------------------------------
# Ayudas de formato
# ---------------------------------------------------------------------------

class Informe:
    def __init__(self):
        self.doc = Document()
        self.n_fig = 0
        self.n_tab = 0
        self.n_eq = 0
        self._estilos()

    def _estilos(self):
        d = self.doc
        sec = d.sections[0]
        sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)     # carta
        sec.left_margin = sec.right_margin = Cm(2.5)
        sec.top_margin = sec.bottom_margin = Cm(2.5)
        st = d.styles
        normal = st["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(11)
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.15
        for nivel, tam in ((1, 16), (2, 13), (3, 11.5)):
            h = st[f"Heading {nivel}"]
            h.font.name = "Calibri"
            h.font.size = Pt(tam)
            h.font.bold = True
            h.font.color.rgb = AZUL if nivel < 3 else GRIS
            # Quitar las fuentes del tema, que tienen prioridad sobre font.name.
            rfonts = h.element.rPr.rFonts
            for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                rfonts.attrib.pop(qn(attr), None)
            h.paragraph_format.space_before = Pt(14 if nivel == 1 else 10)
            h.paragraph_format.space_after = Pt(6)
            h.paragraph_format.keep_with_next = True
        cap = st["Caption"]
        cap.font.size = Pt(9.5)
        cap.font.italic = False
        cap.font.color.rgb = GRIS
        # Pie de página con número
        pie = sec.footer.paragraphs[0]
        pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._campo(pie, "PAGE")

    @staticmethod
    def _campo(parrafo, instruccion: str, texto: str = "1"):
        r = parrafo.add_run()
        for tipo, contenido in (("begin", None), ("instr", instruccion), ("separate", None),
                                ("texto", texto), ("end", None)):
            if tipo == "instr":
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = contenido
            elif tipo == "texto":
                el = OxmlElement("w:t")
                el.text = contenido
            else:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), tipo)
            r._r.append(el)

    # Bloques
    def titulo(self, texto, nivel=1):
        return self.doc.add_heading(texto, level=nivel)

    def p(self, *partes, estilo=None, alinear=None, cursiva=False):
        """Párrafo con partes de texto; una parte "**x**" va en negrita."""
        par = self.doc.add_paragraph(style=estilo)
        for parte in partes:
            limpia = parte.strip()
            negrita = len(limpia) > 4 and limpia.startswith("**") and limpia.endswith("**")
            if negrita:     # conserva los espacios de alrededor
                parte = parte.replace("**", "")
            r = par.add_run(parte)
            r.bold = negrita
            r.italic = cursiva
        if alinear:
            par.alignment = alinear
        else:
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return par

    def nivel(self, etiqueta, texto):
        """Párrafo de los tres niveles: «Observación numérica.», etc."""
        return self.p(f"**{etiqueta}.** ", texto)

    def vinetas(self, items, numeradas=False):
        for it in items:
            par = self.doc.add_paragraph(style="List Number" if numeradas else "List Bullet")
            if isinstance(it, tuple):
                r = par.add_run(it[0])
                r.bold = True
                par.add_run(it[1])
            else:
                par.add_run(it)
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def ecuacion(self, texto):
        self.n_eq += 1
        par = self.doc.add_paragraph()
        ancho = self.doc.sections[0].page_width - self.doc.sections[0].left_margin \
            - self.doc.sections[0].right_margin
        par.paragraph_format.tab_stops.add_tab_stop(int(ancho / 2), WD_TAB_ALIGNMENT.CENTER)
        par.paragraph_format.tab_stops.add_tab_stop(ancho, WD_TAB_ALIGNMENT.RIGHT)
        r = par.add_run("\t" + texto)
        r.font.name = "Cambria Math"
        r.font.size = Pt(11.5)
        par.add_run(f"\t({self.n_eq})")
        return self.n_eq

    def figura(self, nombre, pie, ancho_cm=16.5):
        ruta = FIG / nombre
        if not ruta.exists():
            raise FileNotFoundError(f"Falta la figura {ruta}; corre antes las Fases 3 a 5.")
        self.n_fig += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        c = self.doc.add_paragraph(style="Caption")
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(f"Figura {self.n_fig}. ")
        r.bold = True
        c.add_run(pie)
        return self.n_fig

    def tabla(self, encabezado, filas, titulo, anchos_cm=None, tam=9.5):
        self.n_tab += 1
        c = self.doc.add_paragraph(style="Caption")
        c.paragraph_format.keep_with_next = True
        r = c.add_run(f"Tabla {self.n_tab}. ")
        r.bold = True
        c.add_run(titulo)
        t = self.doc.add_table(rows=1, cols=len(encabezado))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, texto in enumerate(encabezado):
            celda = t.rows[0].cells[i]
            celda.text = ""
            run = celda.paragraphs[0].add_run(str(texto))
            run.bold = True
            run.font.size = Pt(tam)
            sombra = OxmlElement("w:shd")
            sombra.set(qn("w:val"), "clear")
            sombra.set(qn("w:color"), "auto")
            sombra.set(qn("w:fill"), "DCE8F7")
            celda._tc.get_or_add_tcPr().append(sombra)
        for fila in filas:
            celdas = t.add_row().cells
            for i, texto in enumerate(fila):
                celdas[i].text = ""
                run = celdas[i].paragraphs[0].add_run(str(texto))
                run.font.size = Pt(tam)
        # Repetir encabezado en cada página
        trPr = t.rows[0]._tr.get_or_add_trPr()
        rep = OxmlElement("w:tblHeader")
        rep.set(qn("w:val"), "true")
        trPr.append(rep)
        if anchos_cm:
            for fila in t.rows:
                for i, w in enumerate(anchos_cm):
                    fila.cells[i].width = Cm(w)
        self.doc.add_paragraph()
        return self.n_tab

    def salto(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def indice(self):
        par = self.doc.add_paragraph()
        self._campo(par, 'TOC \\o "1-2" \\h \\z \\u',
                    "Haga clic derecho aquí y elija «Actualizar campo» para ver el índice.")


# ---------------------------------------------------------------------------
# Contenido
# ---------------------------------------------------------------------------

def portada(inf: Informe):
    d = inf.doc
    def centrado(texto, tam=12, negrita=False, espacio=6, color=None):
        par = d.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_after = Pt(espacio)
        r = par.add_run(texto)
        r.font.size = Pt(tam)
        r.bold = negrita
        if color:
            r.font.color.rgb = color
    centrado("UNIVERSIDAD COOPERATIVA DE COLOMBIA", 14, True)
    centrado("Facultad de Ingeniería")
    centrado("Programa de Ingeniería de Software")
    centrado("Física 3 (Electricidad y Magnetismo)", espacio=60)
    centrado("Dinámica y propagación de energía en una red de osciladores RLC acoplados",
             20, True, 12, AZUL)
    centrado("Informe del proyecto final", 14, espacio=70)
    centrado("Integrantes", 12, True)
    for k in range(1, 5):
        centrado(f"[Nombre completo del integrante {k}]", 12, espacio=2)
    centrado("", espacio=30)
    centrado("Docente", 12, True)
    centrado("Miguel Alejandro Molina Ceron", 12, espacio=80)
    centrado("San Juan de Pasto, Nariño")
    centrado("Noviembre de 2026")
    inf.salto()
    # «Contenido» no es un título de Word, para que no aparezca dentro del índice.
    par = d.add_paragraph()
    r = par.add_run("Contenido")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = AZUL
    inf.indice()
    inf.salto()


def resumen(inf: Informe, v):
    inf.titulo("Resumen", 1)
    inf.p("Este trabajo estudia numéricamente cómo se propaga una perturbación localizada en una "
          "red de N = 100 osciladores RLC acoplados y cómo se reparte su energía según la "
          "distancia topológica a la fuente. Se compararon cuatro topologías con grado medio "
          "cercano a 4 (malla 10 × 10, anillo regular, mundo pequeño de Watts–Strogatz y "
          "Erdős–Rényi conexa, estas dos con 30 realizaciones) y valores del acoplamiento "
          "κ = K/ω₀² entre 0.01 y 10. El sistema se integró con DOP853 y se validó contra la "
          "solución exacta por modos normales, con un error menor que "
          f"{fmt_sci(v['err_modal'])} Q₀, y contra el balance de energía total, con un residuo "
          f"menor que {fmt_sci(v['res_balance'])}.")
    inf.p("El tiempo de llegada crece con la distancia según una ley de potencia t_γ = a·dᵇ con "
          f"b entre {fmt(v['b_min'], 1)} y {fmt(v['b_max'], 1)} (κ ≥ 0.1): el frente se "
          "desacelera. La rapidez de propagación crece como κ con acoplamiento débil y como √κ "
          f"con acoplamiento fuerte, con la transición en κ_c ≈ {fmt(v['kc_min'], 2)}–"
          f"{fmt(v['kc_max'], 2)}, es decir, K ≈ ω₀². La energía media cae de forma exponencial "
          "con la distancia cuando el acoplamiento es débil y se reparte de forma casi uniforme "
          "cuando es fuerte. Los nodos a igual distancia no responden igual: el número de "
          "caminos más cortos explica su tiempo de llegada y su peso en los modos normales "
          "explica su energía con acoplamiento fuerte. Erdős–Rényi es la red más rápida y de "
          "mayor alcance, y el anillo la más lenta.")
    inf.p("**Palabras clave:** ", "circuitos RLC, osciladores acoplados, redes complejas, "
          "laplaciano de grafos, modos normales, propagación de energía, métodos numéricos.")


def introduccion(inf: Informe):
    inf.titulo("1. Introducción", 1)
    inf.p("Un circuito RLC es el sistema básico para estudiar oscilaciones eléctricas: la carga y "
          "la corriente intercambian energía entre el capacitor y el inductor, mientras la "
          "resistencia la disipa. Cuando muchos circuitos se acoplan, la red se convierte en un "
          "medio por el que puede viajar una perturbación. Este proyecto estudia ese problema "
          "con el modelo del enunciado (Molina Ceron, 2026):")
    inf.ecuacion("Q̈ᵢ + γ Q̇ᵢ + ω₀² Qᵢ = K Σⱼ Aᵢⱼ (Qⱼ − Qᵢ)")
    inf.p("donde Qᵢ es la carga del oscilador i, γ = R/L, ω₀² = 1/(LC), K es la intensidad del "
          "acoplamiento y A es la matriz de adyacencia de la red (no dirigida, sin autoenlaces).")
    inf.titulo("1.1 Objetivo general", 2)
    inf.p("Analizar numéricamente la dinámica de una red de osciladores RLC acoplados, "
          "estudiando la influencia de la intensidad del acoplamiento K y de la topología de la "
          "red sobre la propagación de perturbaciones y la distribución de energía.")
    inf.titulo("1.2 Objetivos específicos", 2)
    inf.vinetas([
        "Derivar, con las leyes de Kirchhoff, la ecuación de un oscilador RLC.",
        "Extender el modelo a N osciladores acoplados y justificar el término de acoplamiento.",
        "Construir redes de malla, regulares, de mundo pequeño y de Erdős–Rényi mediante su "
        "matriz de adyacencia.",
        "Analizar la propagación de una perturbación aplicada sobre un único oscilador.",
        "Determinar el tiempo de propagación y su relación con la distancia topológica.",
        "Calcular la energía de cada oscilador.",
        "Determinar la energía media y su distribución en función de la distancia.",
        "Comparar valores de K en la rapidez de propagación y la distribución energética.",
        "Analizar la influencia de la topología, incluida la diferencia entre nodos a igual "
        "distancia.",
        "Ajustar modelos matemáticos a los datos, con medidas de dispersión.",
        "Generar videos de la propagación para distintos K y topologías."], numeradas=True)
    inf.titulo("1.3 Preguntas de investigación", 2)
    inf.tabla(["N.º", "Pregunta"], [
        ["P1", "¿Cómo se propaga una perturbación inicialmente localizada hacia los demás "
               "osciladores?"],
        ["P2", "¿Cómo influye K en la propagación y en la distribución de energía según la "
               "distancia a la fuente?"],
        ["P3", "¿Existe una relación entre el tiempo de llegada y la distancia topológica?"],
        ["P4", "¿Cómo varía la energía media de los osciladores con su distancia a la fuente?"],
        ["P5", "¿Los osciladores a igual distancia presentan la misma respuesta energética y el "
               "mismo tiempo de propagación?"],
        ["P6", "¿Cómo influye la topología (malla, regular, mundo pequeño, Erdős–Rényi)?"],
        ["P7", "¿Qué interpretación física tiene el efecto del acoplamiento?"],
        ["P8", "¿Cómo cambia la heterogeneidad energética, σ(d), con la distancia?"]],
        "Preguntas de investigación del enunciado.", [1.4, 15])


def marco(inf: Informe):
    inf.titulo("2. Marco teórico", 1)
    inf.titulo("2.1 Oscilador RLC", 2)
    inf.p("En un circuito RLC en serie sin fuente, la ley de mallas de Kirchhoff establece que la "
          "suma de las caídas de voltaje es cero. Con I = dQ/dt:")
    inf.ecuacion("L dI/dt + R I + Q/C = 0   ⇒   Q̈ + γ Q̇ + ω₀² Q = 0")
    inf.p("El inductor aporta inercia, el capacitor la fuerza de restitución y el resistor el "
          "rozamiento (Young, Freedman y Ford, 2020; French, 1971). Con R = 1 Ω, L = 1 mH y "
          "C = 1 µF el circuito es subamortiguado (γ < 2ω₀) y, para Q(0) = Q₀ e I(0) = 0,")
    inf.ecuacion("Q(t) = Q₀ e^(−γt/2) [cos Ωt + (γ/2Ω) sen Ωt],    Ω² = ω₀² − γ²/4")
    inf.p("La energía E = Q²/(2C) + LI²/2 cumple dE/dt = −RI²: solo R la disipa. Para γ ≪ ω₀, "
          "E(t) ≈ E₀e^(−γt), por lo que t_γ = γt mide el tiempo en unidades de decaimiento.")
    inf.titulo("2.2 Justificación del acoplamiento", 2)
    inf.p("El enunciado pide justificar el término de acoplamiento sin fijar un circuito. Se "
          "propone que dos mallas vecinas compartan un capacitor C_c. Por esa rama circula "
          "Iᵢ − Iⱼ, su carga es Qᵢ − Qⱼ y su voltaje (Qᵢ − Qⱼ)/C_c. La ley de mallas en la malla i "
          "es")
    inf.ecuacion("L Q̈ᵢ + R Q̇ᵢ + Qᵢ/C + Σⱼ Aᵢⱼ (Qᵢ − Qⱼ)/C_c = 0,     K = 1/(L C_c)")
    inf.p("y al dividir entre L se recupera la ecuación (1). K tiene unidades de s⁻², como ω₀²; "
          "un C_c grande produce poco voltaje y un acoplamiento débil. La construcción es "
          "directa en circuitos planos como la malla; en redes arbitrarias es una idealización. "
          "Con dos mallas, la suma y la diferencia de cargas se desacoplan y oscilan con ω₀ y "
          "√(ω₀² + 2K): la energía pasa de una malla a otra en un tiempo t_tr ≈ πω₀/K cuando "
          "K ≪ ω₀² (French, 1971).")
    inf.titulo("2.3 Forma matricial y laplaciano", 2)
    inf.p("Con el grado kᵢ = Σⱼ Aᵢⱼ y el laplaciano Λ = D − A (D, matriz diagonal de grados), la "
          "red se escribe en forma vectorial y de primer orden, como en las ecuaciones (8) a "
          "(10) del enunciado:")
    inf.ecuacion("Q̇ = I,     İ = −γ I − (ω₀² 𝕀 + K Λ) Q")
    inf.p("Λ es simétrica, semidefinida positiva y sus filas suman cero; el número de autovalores "
          "nulos es el número de componentes conexas (von Luxburg, 2007). Por eso las redes de "
          "Erdős–Rényi se restringieron a muestras conexas.")
    inf.titulo("2.4 Energía total del sistema", 2)
    inf.p("La energía de cada malla, Eᵢ = Qᵢ²/(2C) + LIᵢ²/2 (ecuación 13 del enunciado), no "
          "incluye la energía guardada en los capacitores de acoplamiento. La cantidad con "
          "balance exacto es")
    inf.ecuacion("H = Σᵢ Eᵢ + (LK/2) Qᵀ Λ Q,     dH/dt = −R Σᵢ Iᵢ²")
    inf.p("Con la condición inicial del enunciado, H(0) = E₀(1 + k₀κ), con k₀ el grado de la "
          "fuente. Como H no aumenta, Σᵢ Eᵢ(t) ≤ E₀(1 + k₀κ): la suma de energías puede superar "
          "E₀ y ⟨Eᵢ⟩/E₀ no es una fracción de la energía total. Se usan Eᵢ y E₀ como pide el "
          "enunciado, y H como diagnóstico.")
    inf.titulo("2.5 Modos normales", 2)
    inf.p("Los autovectores ortonormales vₙ de Λ, con autovalores λₙ, desacoplan la red en N "
          "osciladores independientes de frecuencia ωₙ² = ω₀² + Kλₙ. Con las condiciones "
          "iniciales del enunciado,")
    inf.ecuacion("Qᵢ(t) = Q₀ Σₙ vₙ(i) vₙ(0) e^(−γt/2) [cos Ωₙt + (γ/2Ωₙ) sen Ωₙt]")
    inf.p("K entra por las frecuencias y la topología por los pesos vₙ(i)vₙ(0). Como todos los "
          "modos decaen con la misma tasa, H(t) ≈ H(0)e^(−γt) para cualquier K y red. Esta "
          "solución exacta es la referencia para validar el integrador. Dos nodos a igual "
          "distancia solo responden igual si una simetría de la red los intercambia.")
    inf.titulo("2.6 Tiempos cortos y rapidez de propagación", 2)
    inf.p("Con R = 0, el desarrollo de Taylor de la ecuación (5) muestra que el primer término no "
          "nulo en un nodo a distancia d es")
    inf.ecuacion("Qᵢ(t) ≈ Q₀ Nᵢ K^d t^(2d) / (2d)!")
    inf.p("donde Nᵢ es el número de caminos más cortos entre la fuente y el nodo i. El exponente "
          "2d hace que los nodos lejanos tarden en alcanzar una energía medible, y un Nᵢ mayor "
          "adelanta el cruce del umbral. En una cadena, los modos son ondas con "
          "ω²(q) = ω₀² + 2K(1 − cos q) y velocidad de grupo máxima K/ω₀ si K ≪ ω₀² y √K si "
          "K ≫ ω₀²: se espera que la rapidez crezca como κ con acoplamiento débil y como √κ con "
          "acoplamiento fuerte.")
    inf.titulo("2.7 Topologías", 2)
    inf.tabla(["Red", "Construcción", "Propiedad relevante"], [
        ["Malla 10 × 10", "Rejilla cuadrada con borde abierto; fuente en el nodo interior (4,4)",
         "Muchos caminos más cortos a cada distancia"],
        ["Anillo regular", "Cada nodo unido a sus 2 vecinos de cada lado (k = 4)",
         "Distancia máxima grande (25); alta simetría"],
        ["Mundo pequeño", "Watts–Strogatz, k = 4, recableado p = 0.1",
         "Pocos atajos reducen mucho las distancias (Watts y Strogatz, 1998)"],
        ["Erdős–Rényi", "Enlaces al azar con p = 4/99; solo muestras conexas",
         "Distancias cortas y grados variados (Erdős y Rényi, 1959)"]],
        "Topologías estudiadas (Newman, 2003). Todas tienen N = 100 y grado medio cercano a 4.",
        [3.2, 7, 6.3])


def metodologia(inf: Informe, v):
    p = modelo.Parametros()
    inf.titulo("3. Metodología", 1)
    inf.titulo("3.1 Parámetros", 2)
    inf.tabla(["Parámetro", "Valor", "Comentario"], [
        ["L", "1 mH", ""],
        ["C", "1 µF", f"f₀ = {p.omega0 / (2 * np.pi) / 1e3:.2f} kHz; período T₀ = "
                      f"{p.periodo * 1e6:.0f} µs"],
        ["R", "1 Ω", f"γ = {p.gamma:.0f} s⁻¹; factor de calidad ω₀/γ = {p.factor_calidad:.1f}"],
        ["Q₀", "1 µC", f"E₀ = Q₀²/(2C) = {p.E0 * 1e6:.1f} µJ"],
        ["κ = K/ω₀²", "0.01, 0.03, 0.1, 0.3, 1, 3, 10", "Del régimen débil al fuerte"],
        ["T", "10/γ = 10 ms", "≈ 50 períodos; la energía cae un factor e⁻¹⁰"],
        ["N", "100", "Por red"],
        ["Umbral", "E_th = 10⁻⁶ E₀", "También 10⁻⁴ y 10⁻⁸ E₀ para la sensibilidad"]],
        "Parámetros de referencia.", [3, 5, 8.5])
    inf.p("Como el sistema es lineal, Q₀ solo fija la escala, y los resultados dependen de dos "
          "números adimensionales: κ y ω₀/γ.")
    inf.titulo("3.2 Redes y realizaciones", 2)
    inf.p("La malla y el anillo son deterministas. Para Watts–Strogatz y Erdős–Rényi se generaron "
          "30 realizaciones con semillas fijas (2026 a 2055), lo que permite reproducir cada red. "
          f"Las redes de Erdős–Rényi desconexas se descartaron: se necesitaron {v['er_intentos']} "
          f"intentos para obtener 30 conexas ({v['er_frac']:.0f} % de muestras conexas), y las "
          f"aceptadas tienen grado medio {fmt(v['er_k'], 2)} en lugar de 4. Este sesgo de "
          "selección se declara como limitación. La Figura 1 muestra las redes y la cantidad de "
          "nodos a cada distancia de la fuente.")
    inf.figura("g1_redes.png", "Topologías estudiadas, coloreadas por distancia a la fuente "
               "(naranja), y número de nodos N_d a cada distancia. En las redes aleatorias se "
               "superpone la mediana de 30 realizaciones con los percentiles 10–90.")
    inf.titulo("3.3 Método numérico", 2)
    inf.p("El sistema de primer orden, con 2N = 200 incógnitas, se integró con DOP853, el "
          "Runge–Kutta explícito de orden 8 de SciPy, recomendado para alta precisión (Dormand y "
          "Prince, 1980; Virtanen et al., 2020). Se usaron rtol = 10⁻¹⁰ y una tolerancia "
          "absoluta escalada por variable: 10⁻¹² Q₀ para las cargas y 10⁻¹² ω_max Q₀ para las "
          "corrientes. Las tolerancias por defecto (10⁻³ y 10⁻⁶) no sirven para cargas del "
          "orden de 10⁻⁶ C.")
    inf.p("La salida se muestreó con 100 puntos por período del modo más rápido, "
          "ω_max = √(ω₀² + Kλ_max), que con κ grande oscila hasta 9 veces más rápido que ω₀. "
          "Como referencia se programó la solución exacta por modos normales (ecuación 7) y, "
          "para verificar el orden de convergencia y explicar el algoritmo, un Runge–Kutta "
          "clásico de orden 4 propio.")
    inf.titulo("3.4 Cantidades medidas", 2)
    inf.vinetas([
        ("Energía: ", "Eᵢ(t) con la ecuación (13) del enunciado, y H(t) con la ecuación (6)."),
        ("Energía media: ", "⟨Eᵢ⟩ = (1/T)∫Eᵢ dt, integrada con la regla de Simpson."),
        ("Tiempo de llegada: ", "primer t con Eᵢ(t) ≥ E_th. El cruce se ubica con la raíz de "
         "Eᵢ(t) − E_th entre las dos muestras que lo encierran, usando la solución continua de "
         "DOP853; la interpolación entre muestras fallaba en los vecinos de la fuente, que "
         "cruzan el umbral antes de la primera muestra. Un nodo que nunca cruza el umbral se "
         "reporta como no alcanzado, sin asignarle un valor."),
        ("Estadística por distancia: ", "Ē(d) y σ_E(d) con las ecuaciones (22) y (23) del "
         "enunciado (denominador N_d − 1; σ no definida si N_d = 1). En las redes aleatorias se "
         "calculan por realización, y la dispersión entre realizaciones se reporta aparte con "
         "percentiles 10–90."),
        ("Rapidez del frente: ", "inverso de la pendiente del ajuste lineal de tᵢ contra d "
         "(d ≥ 1). Es un resumen comparativo; la sección 4.2 muestra que t(d) es curvo."),
        ("Predictores a igual distancia: ", "número de caminos más cortos Nᵢ, grado kᵢ y peso "
         "modal Wᵢ = Σ_λ (Π_λ)ᵢ₀², calculado con proyectores sobre cada autovalor para que no "
         "dependa de la base cuando hay autovalores repetidos.")])
    inf.titulo("3.5 Ajustes funcionales", 2)
    inf.p("Se compararon modelos de dos parámetros como máximo, porque Erdős–Rényi ofrece pocas "
          "distancias. Los modelos se ajustaron sobre los datos de cada nodo (σ_E no se usó como "
          "peso, porque no es error experimental) y se compararon con el criterio de información "
          "de Akaike corregido, AICc (Akaike, 1974; Burnham y Anderson, 2002), y con gráficos de "
          "residuos. ΔAICc > 10 indica que el modelo peor no tiene apoyo. En las redes aleatorias "
          "cada realización se ajustó por separado.")
    inf.tabla(["Datos", "Modelos", "Espacio del ajuste"], [
        ["t_γ(d)", "lineal a + b·d; potencia a·dᵇ; logarítmico a + b·ln d", "t_γ"],
        ["⟨Eᵢ⟩(d), σ_E(d)", "exponencial (log₁₀E = a + b·d); potencia (log₁₀E = a + b·log₁₀d)",
         "log₁₀"],
        ["v(κ)", "potencia; por tramos con exponentes 1 y ½; transición suave Aκ/√(1 + κ/κ_c)",
         "log₁₀v"]],
        "Modelos comparados.", [3.3, 9.5, 3.7])
    inf.titulo("3.6 Experimentos", 2)
    inf.tabla(["Experimento", "Qué se varía", "Qué se mide", "Simulaciones", "Preguntas"], [
        ["E1. Dinámica", "κ (5 valores), red", "Eᵢ(t), H(t)", "20", "P1"],
        ["E2. Tiempo de llegada", "κ (7), red, umbral (3), 30 realizaciones",
         "t_γ vs d, rapidez, nodos no alcanzados", "434", "P2, P3, P5"],
        ["E3. Energía por distancia", "κ, red", "⟨Eᵢ⟩, Ē(d), σ_E(d)", "(datos de E2)", "P2, P4, P8"],
        ["E4. Posición a igual d", "nodos con igual d", "relación con Nᵢ, kᵢ y Wᵢ",
         "(datos de E2)", "P5, P6"],
        ["E5. Sensibilidad", "γ, N, posición de la fuente", "rapidez, alcance, Ē(d)", "234",
         "Limitaciones, P7"]],
        "Diseño experimental. Se varió un parámetro a la vez.", [3.4, 4.1, 4.1, 2.2, 2.7], 9)
    inf.titulo("3.7 Estructura del programa", 2)
    inf.p("El código es un paquete de Python (red_rlc) con un módulo por responsabilidad y un "
          "script por experimento; el pseudocódigo y los diagramas de flujo están en "
          "docs/pseudocodigo_y_diagrama_flujo.md.")
    inf.tabla(["Módulo", "Responsabilidad"], [
        ["redes.py", "Topologías, A, Λ, distancias y número de caminos (búsqueda en anchura)"],
        ["modelo.py", "Parámetros, DOP853, solución modal, RK4 propio"],
        ["analisis.py", "Energías, balance de H, tiempos de llegada, estadísticas, peso modal"],
        ["ajustes.py", "Modelos funcionales, AICc y pesos de Akaike"],
        ["graficos.py, videos.py", "Figuras G1–G10 y videos"],
        ["resultados.py", "Guardado de datos con metadatos (semillas, parámetros)"],
        ["tests/", f"{v['n_pruebas']} pruebas automáticas"]],
        "Módulos del programa.", [4, 12.5])
    inf.titulo("3.8 Validación", 2)
    inf.p(f"Antes de analizar resultados, el código superó {v['n_pruebas']} pruebas automáticas, "
          "entre ellas las nueve del plan (Tabla 7). Los experimentos además comprobaron en cada "
          "simulación el balance de H y el valor de H(0). Toda la Fase 3 se regeneró de punta a "
          "punta y una muestra de simulaciones repetida dio diferencias exactamente nulas.")
    inf.tabla(["Prueba", "Caso", "Criterio", "Resultado"], [
        ["Oscilador aislado", "K = 0", "Coincide con la ecuación (3)", "Error < 10⁻⁸ Q₀"],
        ["Conservación", "K = 0, R = 0", "E₀ constante", "Variación < 10⁻⁸"],
        ["Decaimiento", "K = 0, R > 0", "E(t) exacta", "Error < 10⁻⁸ E₀"],
        ["Balance general", "K > 0, R > 0", "dH/dt = −RΣIᵢ²", f"Residuo ≤ {fmt_sci(v['res_balance'])}"],
        ["Dos nodos", "N = 2", "Batidos con ω₀ y √(ω₀² + 2K)", "Error < 10⁻⁸ Q₀"],
        ["Modo uniforme", "4 redes", "ΣQᵢ = oscilador aislado", "Error < 10⁻⁸ Q₀"],
        ["Simetría", "Anillo", "Nodos +d y −d iguales", "Error < 10⁻⁹ Q₀"],
        ["Convergencia", "RK4", "Orden 4", f"Órdenes {v['ordenes_rk4']}"],
        ["Referencia", "DOP853 vs modal", "≪ 10⁻³ Q₀", f"Error ≤ {fmt_sci(v['err_modal'])} Q₀"]],
        "Pruebas de validación del plan.", [3.3, 2.9, 4.8, 5.5])
    inf.figura("g2_validacion.png", "Validación: (a) H(t) sigue H(0)e^(−γt) y ΣEᵢ no es la "
               "energía total; (b) residuo del balance de H; (c) error de DOP853 frente a la "
               "solución modal; (d) convergencia de orden 4 del RK4 propio.")


def resultados(inf: Informe, v, T):
    inf.titulo("4. Resultados", 1)
    inf.p("Cada resultado se presenta en tres niveles: lo que muestra la simulación "
          "(observación numérica), su explicación física (interpretación) y las ideas que aún no "
          "se comprobaron (especulación), como pide la sección 11 del enunciado.")

    # 4.1
    inf.titulo("4.1 Propagación de la perturbación (P1)", 2)
    inf.figura("g3_energia_por_distancia.png", "Energía (envolvente) de un nodo representativo "
               "por distancia, con H(t) y el umbral. Columnas: redes; filas: κ = 0.01, 0.1 y 1.")
    inf.figura("g4_mapa_nodo_tiempo.png", "Mapa nodo-tiempo de log₁₀(Eᵢ/E₀), con los nodos "
               "ordenados por distancia; los puntos naranjas marcan la llegada con umbral "
               "10⁻⁶ E₀.")
    inf.nivel("Observación numérica",
              "La energía sale de la fuente y alcanza primero a los vecinos y después a los "
              "nodos lejanos (Figuras 3 y 4). Con κ = 0.01 la perturbación no llega a toda la "
              f"red en T = 10/γ: se alcanzan {T['alc_e1']}. Con κ = 1 el frente cruza toda la red "
              "antes de γt ≈ 0.8 y luego todos los nodos tienen energías del mismo orden. En "
              "todos los casos, H(t) decae como H(0)e^(−γt).")
    inf.nivel("Interpretación física",
              "La perturbación avanza enlace por enlace porque el acoplamiento solo une vecinos. "
              "No hay un frente nítido: por la ecuación (8), cada nodo responde desde t > 0, pero "
              "su amplitud crece como t^(2d). La pérdida de energía no depende de K ni de la red, "
              "porque todos los modos decaen con la misma tasa. Con κ pequeño el tiempo de "
              "transferencia por enlace, ≈ πω₀/K, es del orden de 10/γ, y la energía se disipa "
              "antes de recorrer la red.")
    inf.nivel("Especulación",
              "El frente se ensancha con la distancia por la dispersión de los modos; un umbral "
              "más alto vería un frente más compacto y más tardío.")

    # 4.2
    inf.titulo("4.2 Tiempo de llegada y distancia (P3)", 2)
    inf.figura("g5_llegada_vs_distancia.png", "Tiempo de llegada contra distancia. Puntos: "
               "nodos (umbral 10⁻⁶ E₀; en redes aleatorias, 30 realizaciones). Líneas: medianas "
               "con umbrales 10⁻⁴, 10⁻⁶ y 10⁻⁸ E₀.")
    inf.figura("a1_ajuste_llegada.png", "Ajustes de t_γ(d) con κ = 0.1 y κ = 1: modelos y "
               "residuos por distancia. Los residuos de la ley de potencia quedan cerca de cero; "
               "los de los modelos lineal y logarítmico son sistemáticos.")
    inf.tabla(["Red"] + [f"κ = {k:g}" for k in (0.01, 0.1, 1, 10)], T["tabla_b"],
              "Exponente b de t_γ = a·dᵇ (mediana; en redes aleatorias, percentiles 10–90) y "
              "ΔAICc mediano del segundo mejor modelo.", [3.6, 3.2, 3.2, 3.2, 3.2], 9)
    inf.nivel("Observación numérica",
              "El tiempo de llegada crece con la distancia en las cuatro redes. La ley de "
              f"potencia es el mejor modelo en todas las redes y valores de κ, con ΔAICc del "
              f"segundo modelo entre {fmt(v['daicc_min'], 0)} y {fmt(v['daicc_max'], 0)}. "
              f"El exponente es b > 1 siempre. El nodo a d = 1 no se aparta de la tendencia: su "
              f"residuo, con el modelo ajustado sin d = 1, está entre {fmt(v['d1_min'], 1)} y "
              f"{fmt(v['d1_max'], 1)} desviaciones estándar.")
    inf.nivel("Interpretación física",
              "Que b > 1 significa que el frente se desacelera. El tiempo de llegada es el primer "
              "instante en que un nodo acumula energía sobre un nivel fijo, mientras la energía "
              "total decae como e^(−γt): cada distancia extra cuesta más tiempo, y con κ pequeño "
              "(b ≈ 2.6–2.9) el sistema está cerca de no alcanzar a los nodos lejanos. El orden "
              "de b entre redes coincide con el crecimiento de N_d (Figura 1): el anillo, con N_d "
              "constante, tiene el b más bajo (≈ 1.4, el más parecido a una onda de velocidad "
              "constante); las redes aleatorias, donde N_d crece rápido, tienen b ≈ 2. Es "
              "coherente con una dilución de la energía del frente entre más nodos.")
    inf.nivel("Especulación",
              "El argumento de dilución no está demostrado; podría probarse en árboles regulares "
              "con distinto número de ramas.")

    # 4.3
    inf.titulo("4.3 Efecto de K en la rapidez de propagación (P2, P7)", 2)
    inf.figura("g6_rapidez_vs_kappa.png", "Rapidez del frente v/ω₀ contra κ (log–log), un "
               "panel por umbral, con los límites de la cadena v = K/ω₀ y v = √K.")
    inf.figura("a3_ajuste_rapidez.png", "Ajustes de v(κ): potencia, por tramos con exponentes "
               "1 y ½, y transición suave v = Aκ/√(1 + κ/κ_c), con sus residuos.")
    inf.tabla(["Red"] + [f"κ = {k:g}" for k in (0.01, 0.1, 1, 10)] +
              ["Exp. débil", "Exp. fuerte", "κ_c"], T["tabla_v"],
              "Rapidez v/ω₀ (umbral 10⁻⁶ E₀, mediana), exponentes log–log en régimen débil "
              "(κ = 0.03–0.3) y fuerte (κ = 1–10), y κ_c del modelo de transición suave.",
              [3.2, 1.7, 1.7, 1.7, 1.7, 2, 2, 2.4], 8.5)
    inf.nivel("Observación numérica",
              "La rapidez crece con κ en las cuatro redes, en más de dos órdenes de magnitud "
              "entre κ = 0.01 y κ = 10. Los exponentes son cercanos a 1 en el régimen débil y "
              f"a 0.6 en el fuerte. El modelo de transición suave o el de tramos ganan en tres "
              f"redes (el anillo queda empatado con ΔAICc ≈ 2), con κ_c = "
              f"{fmt(v['kc_min'], 2)}–{fmt(v['kc_max'], 2)}. Al bajar el umbral de 10⁻⁴ a "
              f"10⁻⁸ E₀ la rapidez aparente aumenta entre {T['umbral_min']:.0f} % y "
              f"{T['umbral_max']:.0f} %; el orden entre redes se mantiene.")
    inf.nivel("Interpretación física",
              "Con K ≪ ω₀², dos vecinos intercambian energía con una frecuencia de batido "
              "≈ K/ω₀; con K ≫ ω₀² el acoplamiento domina y la escala es √K, como la velocidad "
              "de grupo de la cadena (sección 2.6). El cambio ocurre donde ambas escalas son "
              "comparables, K ≈ ω₀². La dependencia del umbral muestra que el tiempo de llegada "
              "mide el primer rastro de energía, no el paso de la mayor parte: es una medida "
              "operativa ligada a la ecuación (20) del enunciado.")
    inf.nivel("Especulación",
              "La topología cambia sobre todo el prefactor A (ER > malla > WS > anillo) más que "
              "κ_c; podría relacionarse con propiedades espectrales de Λ.")

    # 4.4
    inf.titulo("4.4 Energía media y distancia (P2, P4)", 2)
    inf.figura("g7_energia_media_vs_distancia.png", "Energía media por distancia: puntos por "
               "nodo, Ē(d) (mediana entre realizaciones), barras ±σ_E(d) entre nodos y franja de "
               "percentiles 10–90 entre realizaciones.")
    inf.figura("a2_ajuste_energia.png", "Ajustes de log₁₀⟨Eᵢ⟩(d) con κ = 0.01 y κ = 1: modelo "
               "exponencial frente a potencia, con residuos.")
    inf.tabla(["Red", "κ = 0.01", "κ = 0.1", "κ = 1"], T["tabla_E"],
              "Modelo ganador para log₁₀⟨Eᵢ⟩(d) (realizaciones ganadas), pendiente del modelo "
              "exponencial (décadas por enlace) y fracción de la energía media que queda en la "
              "fuente.", [3.6, 4.3, 4.3, 4.3], 9)
    inf.nivel("Observación numérica",
              "La energía media decae con la distancia en todas las redes. Con κ = 0.01 el mejor "
              "modelo es exponencial (salvo ER, donde las 4–5 distancias por realización no "
              "separan los modelos) y la fuente conserva cerca del 87 % de la energía media. Con "
              "κ ≥ 0.1 gana la ley de potencia y el perfil se aplana; con κ = 1 la fuente "
              "conserva ≈ 10 %. La fracción que queda en la fuente es casi igual en las cuatro "
              "redes. En la malla, Ē(d) sube en los bordes.")
    inf.nivel("Interpretación física",
              "Con acoplamiento débil cada enlace transmite poca energía antes de que se disipe, "
              "así que la energía cae un factor casi constante por enlace. Con acoplamiento "
              "fuerte la energía recorre la red antes de perderse y se reparte entre los modos "
              "normales. Con κ = 10 la energía media de la fuente vuelve a subir porque "
              "H(0) = E₀(1 + k₀κ): los capacitores de acoplamiento devuelven a las mallas la "
              "energía guardada al inicio.")
    inf.nivel("Especulación",
              "La subida en los bordes de la malla podría deberse a reflexiones en el borde "
              "abierto; se podría comprobar con una malla periódica.")

    # 4.5
    inf.titulo("4.5 Heterogeneidad energética (P8)", 2)
    inf.figura("g8_heterogeneidad.png", "σ_E(d)/E₀ (arriba) y σ_E/Ē (abajo) contra la distancia, "
               "una línea por κ; solo distancias con al menos 2 nodos y Ē > 10⁻¹² E₀.")
    inf.nivel("Observación numérica",
              "La heterogeneidad absoluta σ_E(d) disminuye con la distancia, siguiendo a Ē(d); en "
              "las redes aleatorias cae de forma exponencial en la mayoría de las realizaciones. "
              "La heterogeneidad relativa σ_E/Ē no tiene una tendencia clara con d: en WS y ER "
              "llega a 1.0–1.3 con κ = 0.01 y baja a ≈ 0.4–0.65 con κ grande, mientras en la "
              "malla y el anillo es menor e irregular.")
    inf.nivel("Interpretación física",
              "σ_E es una propiedad del modelo, no un error. Proviene de las diferencias entre "
              "nodos a igual distancia (sección 4.6): en las redes aleatorias esas diferencias son "
              "grandes; en las regulares, la simetría las reduce. Con κ pequeño, diferencias "
              "modestas en el número de caminos se vuelven grandes en energía.")

    # 4.6
    inf.titulo("4.6 Nodos a igual distancia (P5)", 2)
    inf.figura("g9_posicion.png", "Nodos a igual distancia: respuesta relativa al promedio de "
               "su distancia frente al número de caminos más cortos, el grado y el peso modal. "
               "Cada panel indica la correlación de Spearman ρ dentro de grupos y el R² "
               "explicado.")
    inf.tabla(["Red", "t vs Nᵢ (κ = 0.1)", "E vs Nᵢ (κ = 0.01)", "E vs Nᵢ (κ = 1)",
               "E vs kᵢ (κ = 1)", "E vs Wᵢ (κ = 1)"], T["tabla_E4"],
              "Parte de la variación a igual distancia explicada por cada predictor (R²) y "
              "correlación de Spearman mediana dentro de grupos (ρ).",
              [3.2, 2.7, 2.7, 2.7, 2.6, 2.6], 8.5)
    inf.nivel("Observación numérica",
              "Los nodos a igual distancia no responden igual: su energía media puede diferir en "
              "más de un factor 10 y su tiempo de llegada en 30–50 %. El número de caminos más "
              "cortos Nᵢ explica el tiempo de llegada en todas las redes y la energía con κ "
              "pequeño; con κ grande la energía la explica el peso modal Wᵢ. El grado explica "
              "poco. En el anillo los nodos simétricos (+d y −d) responden exactamente igual.")
    inf.nivel("Interpretación física",
              "A tiempos cortos, las contribuciones de los caminos más cortos se suman "
              "(Qᵢ ∝ Nᵢ): más caminos significa llegar antes. Con κ grande la energía se reparte "
              "entre los modos normales y la respuesta de cada nodo depende de cuánto participa "
              "en los modos que excita la fuente (ecuación 7). El grado solo describe el entorno "
              "inmediato del nodo, no su conexión con la fuente.")

    # 4.7
    inf.titulo("4.7 Influencia de la topología (P6)", 2)
    inf.figura("g10_topologias.png", "Comparación de topologías: rapidez, alcance con κ = 0.01, "
               "caída de la energía, heterogeneidad, energía que queda en la fuente y "
               "conectividad algebraica λ₂.")
    inf.tabla(["Métrica"] + [NOMBRE[r] for r in REDES], T["tabla_top"],
              "Medianas por red (en redes aleatorias, sobre 30 realizaciones).",
              [4.6, 3, 3, 3, 3], 8.5)
    inf.nivel("Observación numérica",
              "Erdős–Rényi es la red más rápida y de mayor alcance, y el anillo la más lenta y de "
              "menor alcance, en todas las métricas de propagación. La caída de la energía con d "
              "y la heterogeneidad son mayores en las redes aleatorias. En cambio, la energía que "
              "sale de la fuente es casi la misma en las cuatro redes. λ₂ ordena bien los "
              "extremos, pero el mundo pequeño tiene un λ₂ algo mayor que la malla y es más "
              "lento.")
    inf.nivel("Interpretación física",
              "Las distancias cortas de Erdős–Rényi llevan la energía a más nodos en menos enlaces "
              "antes de que se disipe; el anillo, con distancia máxima 25, es el caso más lento. "
              "La energía que sale de la fuente depende del acoplamiento local (κ y su grado); la "
              "red decide hacia dónde va y a qué velocidad.")
    inf.nivel("Especulación",
              "λ₂ por sí solo no basta para predecir la rapidez; una combinación de N_d con "
              "propiedades espectrales podría ordenar las redes, pero hacen falta más topologías.")

    # 4.8
    inf.titulo("4.8 Sensibilidad (E5)", 2)
    inf.tabla(["Estudio", "Variante", "v/ω₀ (κ = 0.1)", "v/ω₀ (κ = 1)", "Alcance (κ = 0.1)"],
              T["tabla_E5"], "Sensibilidad en la malla y en Erdős–Rényi (medianas).",
              [2.6, 4, 3.3, 3.3, 3.3], 9)
    inf.nivel("Observación numérica",
              "Al multiplicar R por 33, la rapidez cambia poco (menos de 10 % con κ = 1 en malla "
              "y ER), pero con R = 10 Ω y κ = 0.1 el alcance cae y la fuente retiene casi toda la "
              "energía. La rapidez medida baja al aumentar N, porque el ajuste lineal abarca más "
              "distancias de una curva t(d) que no es recta. La posición de la fuente importa: en "
              "la malla, desde el borde o la esquina la rapidez es 20–30 % menor; en ER, desde el "
              "nodo de mayor grado el frente es ≈ 75 % más rápido que desde el de menor grado.")
    inf.nivel("Interpretación física",
              "K fija la rapidez y γ fija hasta dónde llega la energía: son los «dos relojes», el "
              "tiempo de transferencia por enlace frente al tiempo de decaimiento 1/γ. t_γ y ⟨Eᵢ⟩ "
              "solo son comparables con el mismo γ y el mismo T.")

    # 4.9
    inf.titulo("4.9 Videos", 2)
    inf.p("Se generaron seis videos de la evolución de log₁₀(Eᵢ/E₀): cuatro comparan κ = 0.01, "
          "0.1 y 1 en cada red, y dos comparan las cuatro topologías con κ = 0.1 y κ = 1. El "
          "tiempo avanza de forma no lineal (más lento al inicio) para que el frente sea visible, "
          "y un reloj muestra el valor real de γt. Los archivos están en resultados/videos. La "
          "Figura 14 muestra un cuadro.")
    inf.figura("v2_topologias_k0p1_gt0p6.png", "Cuadro del video de topologías con κ = 0.1 en "
               "γt = 0.6: el anillo solo se ha excitado cerca de la fuente, mientras Erdős–Rényi "
               "ya está casi completo.")


def discusion(inf: Informe):
    inf.titulo("5. Discusión: respuesta a las preguntas de investigación", 1)
    inf.tabla(["N.º", "Respuesta", "Evidencia"], [
        ["P1", "Avanza enlace por enlace; la energía total decae como e^(−γt) sin depender de K "
               "ni de la red; con K débil no alcanza a toda la red.", "Fig. 3, 4, 14; sec. 4.1"],
        ["P2", "K acelera el frente (∝ κ débil, ∝ √κ fuerte, cambio en K ≈ ω₀²) y aplana el "
               "perfil de energía.", "Fig. 7, 8, 9, 10; Tablas 9, 10"],
        ["P3", "Sí: t_γ = a·dᵇ con b > 1; el frente se desacelera. Depende del umbral.",
         "Fig. 5, 6; Tabla 8"],
        ["P4", "Decrece: exponencial con K débil, potencia suave con K fuerte.", "Fig. 9, 10; Tabla 10"],
        ["P5", "No. Nᵢ decide la llegada; el peso modal decide la energía con K fuerte.",
         "Fig. 12; Tabla 11"],
        ["P6", "ER es la más rápida y de mayor alcance; el anillo, la más lenta. La energía que "
               "sale de la fuente no depende de la red.", "Fig. 13; Tabla 12"],
        ["P7", "K = 1/(LC_c): un capacitor compartido que almacena y devuelve energía; K decide "
               "qué tan rápido y lejos se reparte, γ cuánto dura.", "Fig. 2; sec. 2.2, 4.3, 4.8"],
        ["P8", "σ_E disminuye con d; σ_E/Ē es alta con K débil y en las redes aleatorias.",
         "Fig. 11"]],
        "Respuestas a las preguntas de investigación.", [1.3, 10.5, 4.7], 9)
    inf.p("Los once objetivos específicos del enunciado quedaron cubiertos: la derivación y la "
          "justificación del acoplamiento (sección 2), la construcción de las redes (3.2), el "
          "análisis de propagación, tiempos y energía (4.1–4.6), la comparación de K y "
          "topologías (4.3, 4.7), los ajustes con medidas de dispersión (3.5, 4.2–4.4) y los "
          "videos (4.9).")


def conclusiones(inf: Informe, v):
    inf.titulo("6. Conclusiones", 1)
    inf.vinetas([
        ("Efecto de K sobre la propagación. ",
         "El acoplamiento acelera la propagación en más de dos órdenes de magnitud entre "
         "κ = 0.01 y κ = 10. La rapidez crece como κ con acoplamiento débil y como √κ con "
         f"acoplamiento fuerte, con la transición en κ_c ≈ {fmt(v['kc_min'], 2)}–"
         f"{fmt(v['kc_max'], 2)} (K ≈ ω₀²). K no cambia el ritmo con que se pierde la "
         "energía, que solo depende de R."),
        ("Energía y distancia topológica. ",
         "La energía media decae con la distancia: exponencialmente con acoplamiento débil "
         "(≈ 1 década por enlace con κ = 0.01) y de forma suave y casi plana con acoplamiento "
         "fuerte. El tiempo de llegada crece como dᵇ con b > 1."),
        ("Influencia de la estructura de la red. ",
         "Las redes con distancias cortas (Erdős–Rényi) propagan más rápido y más lejos que las "
         "de distancias largas (anillo). A igual distancia, la respuesta depende del número de "
         "caminos más cortos y del peso en los modos normales, no del grado."),
        ("Limitaciones. ",
         "El modelo es lineal, con componentes ideales e iguales; el capacitor compartido es "
         "una idealización en redes no planas; el tiempo de llegada depende del umbral; ⟨Eᵢ⟩ "
         "depende de T y E₀ no incluye la energía inicial de los enlaces; las redes ER se "
         "restringieron a muestras conexas (sesgo de selección); con N = 100, ER tiene solo 4–5 "
         "distancias; una rapidez lineal única depende del rango de distancias."),
        ("Extensiones. ",
         "Elementos no uniformes o no lineales; pérdidas en los capacitores de acoplamiento; "
         "redes más grandes y otras topologías para probar la hipótesis de dilución y el papel de "
         "λ₂; mallas periódicas para separar el efecto de borde; excitación continua; y medición "
         "en un circuito real de pocas mallas.")])


def referencias(inf: Informe):
    inf.titulo("Referencias", 1)
    refs = [
        "Akaike, H. (1974). A new look at the statistical model identification. IEEE "
        "Transactions on Automatic Control, 19(6), 716–723. https://doi.org/10.1109/TAC.1974.1100705",
        "Burnham, K. P. y Anderson, D. R. (2002). Model Selection and Multimodel Inference: A "
        "Practical Information-Theoretic Approach (2.ª ed.). Springer.",
        "Dormand, J. R. y Prince, P. J. (1980). A family of embedded Runge-Kutta formulae. "
        "Journal of Computational and Applied Mathematics, 6(1), 19–26.",
        "Erdős, P. y Rényi, A. (1959). On random graphs I. Publicationes Mathematicae, 6(3–4), "
        "290–297.",
        "French, A. P. (1971). Vibrations and Waves. W. W. Norton.",
        "Hagberg, A. A., Schult, D. A. y Swart, P. J. (2008). Exploring network structure, "
        "dynamics, and function using NetworkX. En Proceedings of the 7th Python in Science "
        "Conference (pp. 11–15).",
        "Hairer, E., Nørsett, S. P. y Wanner, G. (1993). Solving Ordinary Differential "
        "Equations I: Nonstiff Problems (2.ª ed.). Springer.",
        "Molina Ceron, M. A. (2026). Dinámica y propagación de energía en una red de osciladores "
        "RLC acoplados [Enunciado del proyecto final de Física 3]. Universidad Cooperativa de "
        "Colombia.",
        "Newman, M. E. J. (2003). The structure and function of complex networks. SIAM Review, "
        "45(2), 167–256.",
        "Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing "
        "in Python. Nature Methods, 17(3), 261–272.",
        "von Luxburg, U. (2007). A tutorial on spectral clustering. Statistics and Computing, "
        "17(4), 395–416.",
        "Watts, D. J. y Strogatz, S. H. (1998). Collective dynamics of 'small-world' networks. "
        "Nature, 393(6684), 440–442.",
        "Young, H. D., Freedman, R. A. y Ford, A. L. (2020). Sears and Zemansky's University "
        "Physics with Modern Physics (15.ª ed.). Pearson."]
    for r in refs:
        par = inf.doc.add_paragraph(r)
        par.paragraph_format.left_indent = Cm(1)
        par.paragraph_format.first_line_indent = Cm(-1)


def anexos(inf: Informe):
    inf.titulo("Anexo A. Reproducción de los resultados", 1)
    inf.p("Desde la carpeta del proyecto, con Python 3.10 o superior y las librerías de "
          "requirements.txt (NumPy, SciPy, NetworkX, Matplotlib, imageio-ffmpeg y pytest):")
    for cmd in ["pip install -r requirements.txt",
                "python -m pytest                          # pruebas de validación",
                "python scripts/fase3_completa.py          # Fase 3 completa (~15 min)",
                "python scripts/f4_ajustes.py              # ajustes con AICc",
                "python scripts/f4_figuras.py              # figuras de ajuste",
                "python scripts/f5_videos.py               # videos (~4 min)",
                "python scripts/f5_figuras_presentacion.py # figuras para proyectar",
                "pip install -r requirements-docs.txt",
                "python scripts/f6_informe.py              # este informe"]:
        par = inf.doc.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        r = par.add_run(cmd)
        r.font.name = "Consolas"
        r.font.size = Pt(9.5)
    inf.p("")
    inf.p("Las redes aleatorias usan semillas fijas (2026 a 2055) y cada archivo de datos guarda "
          "sus parámetros y semillas, por lo que los resultados se reproducen exactamente. El "
          "detalle de cada paso está en docs/bitacora_desarrollo.md.")


# ---------------------------------------------------------------------------
# Cifras para el texto y las tablas
# ---------------------------------------------------------------------------

def cifras():
    v, T = {}, {}
    e1 = leer("e1_resumen")
    e2 = leer("e2_resumen")
    e4 = leer("e4_resumen")
    e5 = leer("e5_resumen")
    g2 = leer("g2_validacion")
    g10 = leer("g10_metricas")
    ft, fE, fv = leer("f4_ajustes_t"), leer("f4_ajustes_E"), leer("f4_ajustes_v")

    v["res_balance"] = max(num(f["residuo_balance_max"]) for f in e1)
    v["err_modal"] = max(num(f["error_Q_sobre_Q0"]) for f in g2 if f["prueba"] == "referencia_modal")
    errs = [num(f["error_Q_sobre_Q0"]) for f in g2 if f["prueba"] == "convergencia_rk4"]
    v["ordenes_rk4"] = ", ".join(f"{np.log2(a / b):.2f}" for a, b in zip(errs[:-1], errs[1:]))

    import subprocess
    salida = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"],
                            cwd=RAIZ, capture_output=True, text=True).stdout
    v["n_pruebas"] = next((ln.split()[0] for ln in salida.splitlines() if "collected" in ln), "—")

    reals = redes.realizaciones("erdos_renyi")
    v["er_intentos"] = sum(r.intentos for r in reals)
    v["er_frac"] = 100 * len(reals) / v["er_intentos"]
    v["er_k"] = float(np.mean([r.grados.mean() for r in reals]))

    alc = {f["red"]: f["alcanzados"] for f in e1 if num(f["kappa"]) == 0.01}
    en_red = {"malla": "la malla", "anillo": "el anillo", "mundo_pequeno": "el mundo pequeño",
              "erdos_renyi": "Erdős–Rényi"}
    T["alc_e1"] = ", ".join(f"{alc[r]} de 99 nodos en {en_red[r]}" for r in REDES)

    # Exponentes b de t ∝ d^b
    filas, bs, d1, dmins = [], [], [], []
    for r in REDES:
        fila = [NOMBRE[r]]
        for k in (0.01, 0.1, 1.0, 10.0):
            b = [num(f["p_b"]) for f in ft if f["red"] == r and num(f["kappa"]) == k
                 and f["modelo"] == "potencia"]
            por_real = {}
            for f in ft:
                if f["red"] == r and num(f["kappa"]) == k:
                    por_real.setdefault(f["realizacion"], []).append(num(f["delta_aicc"]))
            seg = [sorted(x)[1] for x in por_real.values() if len(x) > 1]
            texto = fmt(np.median(b))
            if len(b) > 1:
                texto += f" [{fmt(np.percentile(b, 10))}, {fmt(np.percentile(b, 90))}]"
            fila.append(f"{texto}; ΔAICc {fmt(np.median(seg), 0)}")
            if k >= 0.1:
                bs.append(np.median(b))
            dmins.append(np.median(seg))
            dd = [num(f["desviacion_d1_sigmas"]) for f in ft if f["red"] == r
                  and num(f["kappa"]) == k and num(f["delta_aicc"]) == 0]
            dd = [x for x in dd if np.isfinite(x)]
            if dd and k >= 0.1:
                d1.append(np.median(dd))
        filas.append(fila)
    T["tabla_b"] = filas
    v["b_min"], v["b_max"] = min(bs), max(bs)
    v["daicc_min"], v["daicc_max"] = min(dmins), max(dmins)
    v["d1_min"], v["d1_max"] = min(d1), max(d1)

    # Rapidez
    filas, kcs = [], []
    for r in REDES:
        vk = {k: mediana(e2, "rapidez_sobre_w0_mediana", red=r, kappa=k, umbral=1e-6)
              for k in (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)}
        deb = np.polyfit(np.log([0.03, 0.1, 0.3]), np.log([vk[0.03], vk[0.1], vk[0.3]]), 1)[0]
        fue = np.polyfit(np.log([1, 3, 10]), np.log([vk[1.0], vk[3.0], vk[10.0]]), 1)[0]
        kc = [10 ** num(f["p_log₁₀κc"]) for f in fv if f["red"] == r
              and f["modelo"] == "transición suave"]
        kcs.append(np.median(kc))
        filas.append([NOMBRE[r]] + [fmt(vk[k], 3 if k < 1 else 2) for k in (0.01, 0.1, 1.0, 10.0)]
                     + [fmt(deb), fmt(fue), fmt(np.median(kc))])
    T["tabla_v"] = filas
    v["kc_min"], v["kc_max"] = min(kcs), max(kcs)
    cambios = []
    for r in REDES:
        for k in (0.1, 1.0):
            a = mediana(e2, "rapidez_sobre_w0_mediana", red=r, kappa=k, umbral=1e-4)
            b = mediana(e2, "rapidez_sobre_w0_mediana", red=r, kappa=k, umbral=1e-8)
            cambios.append(100 * (b / a - 1))
    T["umbral_min"], T["umbral_max"] = min(cambios), max(cambios)

    # Energía por distancia
    filas = []
    for r in REDES:
        fila = [NOMBRE[r]]
        for k in (0.01, 0.1, 1.0):
            gan = ganadores(fE, red=r, kappa=k)
            m, c = gan.most_common(1)[0]
            n = sum(gan.values())
            pend = mediana(fE, "p_b", red=r, kappa=k, modelo="exponencial")
            frac = np.median([num(f["valor"]) for f in g10 if f["red"] == r
                              and f["metrica"] == "fuente" and f["serie"] == f"κ = {k:g}"]) \
                if k in (0.1, 1.0) else np.nan
            texto = f"{m} ({c}/{n}); {fmt(pend)} déc./enlace"
            if np.isfinite(frac):
                texto += f"; fuente {100 * frac:.0f} %"
            fila.append(texto)
        filas.append(fila)
    T["tabla_E"] = filas

    # E4
    def celda(r, k, resp, pred):
        f = next(x for x in e4 if x["red"] == r and num(x["kappa"]) == k
                 and x["respuesta"] == resp and x["predictor"] == pred)
        R2, rho = num(f["R2"]), num(f["rho_mediana"])
        return "—" if not np.isfinite(R2) else f"R² {fmt(R2)}; ρ {fmt(rho)}"
    T["tabla_E4"] = [[NOMBRE[r], celda(r, 0.1, "t_llegada", "N_caminos"),
                      celda(r, 0.01, "E_media", "N_caminos"), celda(r, 1.0, "E_media", "N_caminos"),
                      celda(r, 1.0, "E_media", "grado"), celda(r, 1.0, "E_media", "peso_modal")]
                     for r in REDES]

    # Topologías
    def met(m, serie, d=2):
        return [fmt(np.median([num(f["valor"]) for f in g10 if f["red"] == r
                               and f["metrica"] == m and f["serie"] == serie]), d) for r in REDES]
    T["tabla_top"] = [["Rapidez v/ω₀, κ = 0.1"] + met("rapidez", "κ = 0.1"),
                      ["Rapidez v/ω₀, κ = 1"] + met("rapidez", "κ = 1"),
                      ["Alcance, κ = 0.01"] + met("alcance", "κ = 0.01"),
                      ["Pendiente log₁₀Ē, κ = 0.1"] + met("pendiente", "κ = 0.1"),
                      ["σ_E/Ē, κ = 0.1"] + met("heterogeneidad", "κ = 0.1"),
                      ["Energía en la fuente, κ = 0.1"] + met("fuente", "κ = 0.1"),
                      ["λ₂"] + met("lambda2", "estructura", 3)]

    # E5
    def e5m(campo, **f):
        return mediana(e5, campo, **f)
    filas = []
    for R in (0.3, 1.0, 10.0):
        filas.append(["γ (malla)", f"R = {R:g} Ω",
                      fmt(e5m("v_sobre_w0", estudio="gamma", red="malla", variante=str(R), kappa=0.1)),
                      fmt(e5m("v_sobre_w0", estudio="gamma", red="malla", variante=str(R), kappa=1.0)),
                      fmt(e5m("fraccion_alcanzada", estudio="gamma", red="malla", variante=str(R),
                              kappa=0.1))])
    for L in ("6", "10", "20"):
        filas.append(["N (malla)", f"{L} × {L}",
                      fmt(e5m("v_sobre_w0", estudio="N", red="malla", variante=L, kappa=0.1)),
                      fmt(e5m("v_sobre_w0", estudio="N", red="malla", variante=L, kappa=1.0)),
                      fmt(e5m("fraccion_alcanzada", estudio="N", red="malla", variante=L, kappa=0.1))])
    for red, variantes in (("malla", ("interior", "borde", "esquina")),
                           ("erdos_renyi", ("mayor grado", "nodo 0", "menor grado"))):
        for var in variantes:
            filas.append([f"Fuente ({'malla' if red == 'malla' else 'ER'})", var,
                          fmt(e5m("v_sobre_w0", estudio="fuente", red=red, variante=var, kappa=0.1)),
                          fmt(e5m("v_sobre_w0", estudio="fuente", red=red, variante=var, kappa=1.0)),
                          fmt(e5m("fraccion_alcanzada", estudio="fuente", red=red, variante=var,
                                  kappa=0.1))])
    T["tabla_E5"] = filas
    return v, T


def main():
    try:
        v, T = cifras()
    except FileNotFoundError as e:
        sys.exit(f"Faltan datos ({e.filename}). Corre antes las Fases 3 a 5.")
    inf = Informe()
    portada(inf)
    resumen(inf, v)
    introduccion(inf)
    marco(inf)
    metodologia(inf, v)
    resultados(inf, v, T)
    discusion(inf)
    conclusiones(inf, v)
    referencias(inf)
    anexos(inf)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    inf.doc.save(SALIDA)
    print(f"Informe: {SALIDA}  ({inf.n_fig} figuras, {inf.n_tab} tablas, {inf.n_eq} ecuaciones)")


if __name__ == "__main__":
    main()
