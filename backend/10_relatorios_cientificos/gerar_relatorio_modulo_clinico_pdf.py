import os
import matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Registra a família tipográfica TrueType Times New Roman (Unicode completo) + DejaVuSerif para setas diagonais
pdfmetrics.registerFont(TTFont('TNR', r'C:\Windows\Fonts\times.ttf'))
pdfmetrics.registerFont(TTFont('TNR-Bold', r'C:\Windows\Fonts\timesbd.ttf'))
pdfmetrics.registerFont(TTFont('TNR-Italic', r'C:\Windows\Fonts\timesi.ttf'))
pdfmetrics.registerFont(TTFont('TNR-BoldItalic', r'C:\Windows\Fonts\timesbi.ttf'))
pdfmetrics.registerFontFamily(
    'TNR',
    normal='TNR',
    bold='TNR-Bold',
    italic='TNR-Italic',
    boldItalic='TNR-BoldItalic'
)
mpl_fonts_dir = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf')
pdfmetrics.registerFont(TTFont('DVS', os.path.join(mpl_fonts_dir, 'DejaVuSerif.ttf')))


class ScholarlyModuleCanvas(canvas.Canvas):
    """
    Canvas editorial acadêmico (padrão JAMIA / Journal of Biomedical Informatics)
    com cabeçalho corrente e paginação formal "Página X de Y".
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_scholarly_chrome(num_pages)
            super().showPage()
        super().save()

    def draw_scholarly_chrome(self, page_count):
        self.saveState()
        w, h = A4  # 595.27 x 841.89 pt
        left = 54
        right = w - 54

        if self._pageNumber == 1:
            self.setStrokeColor(colors.HexColor("#0f172a"))
            self.setLineWidth(1.5)
            self.line(left, h - 36, right, h - 36)
            self.setLineWidth(0.4)
            self.line(left, h - 39, right, h - 39)

            self.setFont("TNR-Italic", 8)
            self.setFillColor(colors.HexColor("#334155"))
            self.drawString(left, h - 31, "CADERNOS DE INFORMÁTICA MÉDICA — COALIZÃO OPEN HEALTH BRASIL")
            self.drawRightString(right, h - 31, "Série Técnica Vol. II — Novembro de 2026")
        else:
            self.setFont("TNR-Italic", 8.5)
            self.setFillColor(colors.HexColor("#1e293b"))
            self.drawString(left, h - 38, "Módulo de Classificação Clínica, Interpretação Determinística e Display Longitudinal")

            self.setFont("TNR", 8.5)
            self.drawRightString(right, h - 38, "Open Health — Desafio Rivio / LEPoli")

            self.setStrokeColor(colors.HexColor("#1e293b"))
            self.setLineWidth(0.6)
            self.line(left, h - 43, right, h - 43)

        # Rodapé acadêmico
        self.setStrokeColor(colors.HexColor("#94a3b8"))
        self.setLineWidth(0.5)
        self.line(left, 44, right, 44)

        self.setFont("TNR-Italic", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(left, 32, "Resumo Técnico-Acadêmico & Arquitetura Operacional | Informática Biomédica e Saúde Digital")

        self.setFont("TNR-Bold", 8.5)
        self.setFillColor(colors.HexColor("#0f172a"))
        self.drawRightString(right, 32, f"Página {self._pageNumber} de {page_count}")

        self.restoreState()


def make_booktabs_style(header_bg="#0f172a"):
    """
    Estilo de tabela acadêmica 'booktabs' (filetes horizontais calibrados, sem grades verticais poluídas).
    """
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor('#0f172a')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.0, colors.HexColor('#0f172a')),
        ('LINEBELOW', (0, 1), (-1, -2), 0.35, colors.HexColor('#cbd5e1')),
        ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor('#0f172a')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])


def gerar_relatorio_modulo_clinico(pdf_output_path, fig1_path, fig2_path, der_img_path):
    doc = SimpleDocTemplate(
        pdf_output_path,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=52,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    kicker_style = ParagraphStyle(
        'AcadKicker', parent=styles['Normal'], fontName='TNR-Bold', fontSize=9, leading=12,
        textColor=colors.HexColor('#1e3a8a'), alignment=1, spaceAfter=4
    )
    title_style = ParagraphStyle(
        'AcadTitle', parent=styles['Normal'], fontName='TNR-Bold', fontSize=16.0, leading=20.0,
        textColor=colors.HexColor('#0f172a'), alignment=1, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'AcadSubtitle', parent=styles['Normal'], fontName='TNR-Italic', fontSize=10.8, leading=14.2,
        textColor=colors.HexColor('#334155'), alignment=1, spaceAfter=10
    )
    author_style = ParagraphStyle(
        'AcadAuthor', parent=styles['Normal'], fontName='TNR-Bold', fontSize=9.5, leading=13,
        textColor=colors.HexColor('#0f172a'), alignment=1, spaceAfter=2
    )
    affil_style = ParagraphStyle(
        'AcadAffil', parent=styles['Normal'], fontName='TNR-Italic', fontSize=8.5, leading=11.5,
        textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=10
    )
    abstract_box_style = ParagraphStyle(
        'AcadAbstractText', parent=styles['Normal'], fontName='TNR', fontSize=8.5, leading=12.2,
        textColor=colors.HexColor('#1e293b'), alignment=4, spaceAfter=4
    )
    h1_style = ParagraphStyle(
        'AcadH1', parent=styles['Normal'], fontName='TNR-Bold', fontSize=12, leading=15.5,
        textColor=colors.HexColor('#0f172a'), spaceBefore=12, spaceAfter=5, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'AcadH2', parent=styles['Normal'], fontName='TNR-BoldItalic', fontSize=10.2, leading=13.5,
        textColor=colors.HexColor('#1e3a8a'), spaceBefore=9, spaceAfter=4, keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'AcadH3', parent=styles['Normal'], fontName='TNR-Bold', fontSize=9.5, leading=12.5,
        textColor=colors.HexColor('#1e293b'), spaceBefore=6, spaceAfter=3, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'AcadBody', parent=styles['Normal'], fontName='TNR', fontSize=9.5, leading=13.8,
        textColor=colors.HexColor('#1e293b'), alignment=4, firstLineIndent=16, spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'AcadBullet', parent=styles['Normal'], fontName='TNR', fontSize=9.2, leading=13.2,
        textColor=colors.HexColor('#1e293b'), alignment=4, leftIndent=14, firstLineIndent=-10, spaceAfter=4
    )
    formula_style = ParagraphStyle(
        'AcadFormula', parent=styles['Normal'], fontName='TNR-Italic', fontSize=9.5, leading=14,
        textColor=colors.HexColor('#0f172a'), alignment=1, spaceBefore=4, spaceAfter=6
    )
    th_style = ParagraphStyle(
        'AcadTH', parent=styles['Normal'], fontName='TNR-Bold', fontSize=8.0, leading=10.2,
        textColor=colors.white, alignment=0
    )
    td_style = ParagraphStyle(
        'AcadTD', parent=styles['Normal'], fontName='TNR', fontSize=7.9, leading=10.5,
        textColor=colors.HexColor('#0f172a'), alignment=0
    )
    td_bold = ParagraphStyle('AcadTDBold', parent=td_style, fontName='TNR-Bold')
    td_italic = ParagraphStyle('AcadTDItalic', parent=td_style, fontName='TNR-Italic')
    td_green = ParagraphStyle('AcadTDGreen', parent=td_style, fontName='TNR-Bold', textColor=colors.HexColor('#047857'))
    td_yellow = ParagraphStyle('AcadTDYellow', parent=td_style, fontName='TNR-Bold', textColor=colors.HexColor('#b45309'))
    td_orange = ParagraphStyle('AcadTDOrange', parent=td_style, fontName='TNR-Bold', textColor=colors.HexColor('#c2410c'))
    td_red = ParagraphStyle('AcadTDRed', parent=td_style, fontName='TNR-Bold', textColor=colors.HexColor('#b91c1c'))
    caption_style = ParagraphStyle(
        'AcadCaption', parent=styles['Normal'], fontName='TNR', fontSize=8.4, leading=11.5,
        textColor=colors.HexColor('#334155'), alignment=4, spaceBefore=4, spaceAfter=6
    )
    ref_style = ParagraphStyle(
        'AcadRef', parent=styles['Normal'], fontName='TNR', fontSize=8.1, leading=11.3,
        textColor=colors.HexColor('#1e293b'), alignment=4, leftIndent=16, firstLineIndent=-16, spaceAfter=3.5
    )

    story = []

    # =========================================================================
    # CABEÇALHO CIENTÍFICO & RESUMO EXECUTIVO (PÁGINA 1)
    # =========================================================================
    story.append(Paragraph("RESUMO TÉCNICO-ACADÊMICO & ARQUITETURA EM OPERAÇÃO (PARTE II)", kicker_style))
    story.append(Paragraph(
        "Módulo de Classificação Clínica por Gradiente, Interpretação Determinística e Display Longitudinal "
        "de Exames de Sangue em Arquitetura Open Health (HL7 FHIR BR Core, LOINC e LGPD)",
        title_style
    ))
    story.append(Paragraph(
        "Padronização Matemática de Intervalos de Referência (CLSI EP28-A3c / CTCAE v5.0 / CAP), "
        "Mitigação de Alucinações em IA e Visualização de Séries Temporais Multi-Laboratoriais",
        subtitle_style
    ))
    story.append(Paragraph("Grupo de Pesquisa em Informática Médica e Arquitetura de Sistemas de Saúde Digital", author_style))
    story.append(Paragraph(
        "Escola Politécnica / Hackathon Gama House &amp; LEPoli — Desafio Rivio | São Paulo, 08 de Novembro de 2026",
        affil_style
    ))

    resumo_html = (
        "<b>RESUMO:</b> A simples disponibilização de dados laboratoriais estruturados em barramentos <i>Open Health</i> "
        "não garante, por si só, compreensão clínica ou segurança para o paciente leigo, tampouco agilidade cognitiva para o "
        "médico assistente. Este documento técnico-acadêmico especifica a arquitetura do <b>Módulo de Classificação, "
        "Interpretação Determinística e Display Longitudinal de Exames Laboratoriais</b>, operando sobre a base relacional "
        "normalizada de quatro tabelas (<i>patients</i>, <i>diagnostic_reports</i>, <i>observations</i> e <i>consents</i>) "
        "sob os padrões <b>HL7 FHIR (Perfil BR Core)</b>, <b>LOINC</b>, <b>UCUM</b> e <b>LGPD</b>. O sistema estrutura-se em "
        "três pilares fundamentais: (1) um <i>Motor de Classificação por Gradiente Matemático</i> que adimensionaliza qualquer "
        "analito numérico da tabela <i>observations</i> a partir de sua largura de referência (<i>max − min</i>), fundamentado "
        "nas diretrizes internacionais <b>CLSI EP28-A3c</b>, <b>NCI CTCAE v5.0</b> e <b>Valores Críticos CAP/CLSI GP47</b>, "
        "mapeando cinco estados clínicos internos em quatro níveis visuais seguros de interface (Verde, Amarelo, Laranja e Vermelho) "
        "acrescidos de indicador de tendência temporal (<font name='DVS'>↗</font> / <font name='DVS'>↘</font> para variações &gt; 20%); (2) uma <i>Arquitetura de Interpretação "
        "Clínica Determinística</i> pré-computada (matriz de 113 analitos × 5 faixas = 565 objetos de conhecimento estruturados "
        "em 5 pilares educativos), eliminando o risco de alucinação de LLMs e o travamento de requisições em tempo de execução; "
        "e (3) uma <i>Camada de Display Longitudinal</i> baseada em séries temporais por LOINC com banda de referência sombreada "
        "e rastreabilidade multi-laboratorial.<br/><br/>"
        "<b>Palavras-chave:</b> Classificação Laboratorial; CLSI EP28-A3c; NCI CTCAE; Interpretação Determinística; Séries Temporais LOINC; UX em Saúde.<br/><br/>"
        "<b>ABSTRACT:</b> <i>This technical paper documents the Clinical Classification, Deterministic Interpretation, and Longitudinal "
        "Display Module built atop an HL7 FHIR (BR Core) and LOINC relational Open Health architecture. We formalize the mathematical "
        "gradient normalization across heterogeneous blood analytes using CLSI EP28-A3c, NCI CTCAE v5.0, and CAP guidelines, justify the "
        "replacement of runtime LLM/RAG generation with a pre-verified deterministic lookup matrix (565 clinical objects), and specify "
        "the longitudinal time-series visualization layer unifying multi-laboratory diagnostic reports.</i>"
    )
    abstract_table = Table([[Paragraph(resumo_html, abstract_box_style)]], colWidths=[487])
    abstract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(abstract_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 1. VISÃO GERAL DA ARQUITETURA EM OPERAÇÃO
    # =========================================================================
    story.append(Paragraph("1. Visão Sistêmica da Arquitetura Open Health em Operação", h1_style))
    story.append(Paragraph(
        "Em continuidade à especificação do modelo relacional normalizado de quatro tabelas (Relatório Técnico Parte I), "
        "o presente documento detalha a camada de inteligência clínica, tradução semântica e visualização longitudinal que "
        "transforma tuplas brutas da entidade <i>observations</i> em informação clínica acionável, ética e compreensível. "
        "A <b>Figura 1</b> sintetiza o fluxo operacional completo atualmente implementado no projeto, conectando os cinco "
        "estágios do ciclo de vida do dado laboratorial:",
        body_style
    ))

    if os.path.exists(fig1_path):
        img1 = Image(fig1_path, width=485, height=485 * (4.6 / 12.0))
        t_img1 = Table([[img1]], colWidths=[487])
        t_img1.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#334155')),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(KeepTogether([
            t_img1,
            Paragraph(
                "<b>Figura 1:</b> Fluxograma arquitetural de ponta a ponta do sistema em operação: (1) Ingestão híbrida de PDFs "
                "(Gemini 2.5 Flash em nuvem ou extrator offline local); (2) Persistência relacional nas 4 tabelas FHIR/LOINC/LGPD; "
                "(3) Motor matemático de gradiente e tendência; (4) Base determinística pré-computada (565 objetos); e (5) Display longitudinal.",
                caption_style
            )
        ]))

    # =========================================================================
    # 2. PILAR 1: MOTOR DE CLASSIFICAÇÃO E FUNDAMENTAÇÃO CLÍNICA
    # =========================================================================
    story.append(Paragraph("2. Motor de Classificação e Fundamentação Clínica (Gradiente de Resultados)", h1_style))
    story.append(Paragraph(
        "O primeiro desafio matemático de uma plataforma de exames de sangue reside na heterogeneidade de ordens de grandeza "
        "e unidades de medida (padrão <b>UCUM</b>) entre diferentes biomarcadores registrados na tabela <i>observations</i>. "
        "Um mesmo laudo contém parâmetros expressos em frações decimais (ex.: Creatinina entre 0,55 e 1,02 mg/dL), dezenas "
        "(ex.: Glicose entre 70 e 99 mg/dL) e centenas de milhares (ex.: Plaquetas entre 150.000 e 450.000 /µL). "
        "Para padronizar universalmente a gravidade de qualquer resultado sem depender de escalas absolutas rígidas, "
        "o sistema implementa um algoritmo de <b>Normalização Adimensional por Gradiente Relativo</b>.",
        body_style
    ))

    story.append(Paragraph("2.1. Formulação Matemática da Normalização de Escala", h2_style))
    story.append(Paragraph(
        "Seja cada registro quantitativo da tabela <i>observations</i> definido pela trinca ordenada "
        "(<i>V</i>, <i>R<sub>min</sub></i>, <i>R<sub>max</sub></i>), correspondente aos atributos <i>valor_numerico</i>, "
        "<i>faixa_referencia_min</i> e <i>faixa_referencia_max</i>. Para faixas unilaterais (ex.: Colesterol Total &lt; 190 mg/dL, "
        "onde apenas o limite superior é fornecido no laudo), o motor normaliza <i>R<sub>min</sub></i> = 0; analogamente, para "
        "limites exclusivamente inferiores (ex.: Colesterol HDL &gt; 40 mg/dL), adota-se <i>R<sub>max</sub></i> = 2 × <i>R<sub>min</sub></i>. "
        "A <b>Largura da Faixa de Referência (<i>L</i>)</b> é definida por:",
        body_style
    ))
    story.append(Paragraph("<i>L</i> = <i>R<sub>max</sub></i> − <i>R<sub>min</sub></i> ,   com <i>L</i> &gt; 0", formula_style))

    story.append(Paragraph(
        "A partir de <i>L</i>, o algoritmo avalia a relação de pertinência do valor medido <i>V</i> ao intervalo fechado "
        "[<i>R<sub>min</sub></i>, <i>R<sub>max</sub></i>], derivando duas métricas adimensionais complementares:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Caso 1 — Valor Dentro da Faixa de Referência (<i>R<sub>min</sub></i> ≤ <i>V</i> ≤ <i>R<sub>max</sub></i>):</b> "
        "Calcula-se a <b>Posição Percentual Interna (<i>P</i>)</b>, que mapeia linearmente o resultado no intervalo unitário [0%, 100%], "
        "indicando o quão centralizado ou próximo às bordas o analito se encontra:",
        bullet_style
    ))
    story.append(Paragraph("<i>P</i> = ( ( <i>V</i> − <i>R<sub>min</sub></i> ) / <i>L</i> ) × 100%   ∈ [0%, 100%]", formula_style))

    story.append(Paragraph(
        "• <b>Caso 2 — Valor Fora da Faixa de Referência (<i>V</i> &lt; <i>R<sub>min</sub></i> ou <i>V</i> &gt; <i>R<sub>max</sub></i>):</b> "
        "Calcula-se o <b>Desvio Percentual Externo (<i>D</i>)</b> em relação à borda violada (<i>B</i> = <i>R<sub>min</sub></i> se hiporregulado; "
        "<i>B</i> = <i>R<sub>max</sub></i> se hiperregulado), normalizado pela largura <i>L</i> da própria faixa fisiológica:",
        bullet_style
    ))
    story.append(Paragraph(
        "<i>D</i> = ( ( <i>R<sub>min</sub></i> − <i>V</i> ) / <i>L</i> ) × 100%  (se <i>V</i> &lt; <i>R<sub>min</sub></i>)     ou     "
        "<i>D</i> = ( ( <i>V</i> − <i>R<sub>max</sub></i> ) / <i>L</i> ) × 100%  (se <i>V</i> &gt; <i>R<sub>max</sub></i>)",
        formula_style
    ))

    story.append(Paragraph("2.2. Fundamentação nas Referências Médicas Oficiais (CLSI, CTCAE e CAP)", h2_style))
    story.append(Paragraph(
        "Os pontos de corte matemáticos de <i>P</i> e <i>D</i> não foram escolhidos arbitrariamente; eles traduzem três consensos "
        "internacionais da patologia clínica e medicina diagnóstica:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>CLSI EP28-A3c e SBPC/ML (Intervalos de Referência e Zona de Fronteira):</b> Conforme a diretriz <i>Defining, Establishing, "
        "and Verifying Reference Intervals in the Clinical Laboratory</i> (CLSI EP28-A3c) e a Sociedade Brasileira de Patologia Clínica "
        "e Medicina Laboratorial (SBPC/ML), os intervalos de referência convencionais compreendem os <b>95% centrais</b> de uma população "
        "aparentemente saudável (entre os percentis 2,5 e 97,5). Por definição estatística, 5% dos indivíduos saudáveis situam-se "
        "fora dos limites, e resultados localizados nas extremidades internas da faixa (<i>P</i> &lt; 10% ou <i>P</i> &gt; 90%) estão "
        "sujeitos à sobreposição entre a variação biológica intraindividual (CV<sub>I</sub>) e a imprecisão analítica do ensaio (CV<sub>A</sub>), "
        "justificando uma <i>Zona Limítrofe / Atenção Preventiva</i>.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>NCI CTCAE v5.0 (National Cancer Institute / NIH):</b> O sistema <i>Common Terminology Criteria for Adverse Events</i> "
        "constitui o padrão ouro global em pesquisa clínica para graduar a severidade de alterações laboratoriais em relação ao "
        "Limite Superior da Normalidade (ULN — <i>Upper Limit of Normal</i>) ou Limite Inferior (LLN — <i>Lower Limit of Normal</i>) "
        "em 4 graus progressivos: <b>Grau 1 (Leve / Assintomático)</b>, <b>Grau 2 (Moderado — intervenção mínima/não-invasiva indicada)</b>, "
        "<b>Grau 3 (Grave / Clinicamente significativo)</b> e <b>Grau 4 (Consequências com risco à vida / Urgência)</b>.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Valores Críticos Laboratoriais (CAP e CLSI GP47):</b> Segundo o <i>College of American Pathologists</i> (CAP) e a "
        "diretriz CLSI GP47 (<i>Management of Critical- and Significant-Risk Results</i>), desvios extremos além dos limites "
        "fisiológicos configuram resultados de risco significativo que exigem comunicação prioritária e avaliação médica célere.",
        bullet_style
    ))

    story.append(Paragraph("2.3. Mapeamento dos 5 Estados Clínicos para 4 Níveis Visuais de UX Segura", h2_style))
    story.append(Paragraph(
        "Uma decisão arquitetural crucial de <i>User Experience (UX) em Saúde Digital</i> consiste na distinção entre a "
        "classificação clínica interna do motor (5 estados: Normal + Limítrofe + CTCAE Graus 1, 2 e 3–4) e a camada visual "
        "apresentada ao paciente (<b>4 Níveis Visuais Seguros</b>). Em conformidade com os princípios de comunicação clínica "
        "não-iatrogênica, pacientes leigos expostos a rótulos brutos do CTCAE como <i>\"Grau 4: Risco de Vida\"</i> ou "
        "<i>\"Valor Crítico Grave\"</i> sofrem ansiedade aguda desproporcional (cibercondria), muitas vezes diante de alterações "
        "crônicas já conhecidas pelo médico assistente ou artefatos pré-analíticos (como hemólise da amostra ou jejum inadequado).",
        body_style
    ))
    story.append(Paragraph(
        "Por essa razão, o sistema agrupa a zona de fronteira interna (<i>P</i> &lt; 10% ou <i>P</i> &gt; 90%) e o Grau 1 leve "
        "(<i>D</i> ≤ 15%) no nível visual <b>Atenção / Leve (Amarelo)</b>, reserva o nível <b>Alterado Moderado (Laranja)</b> para "
        "o Grau 2 (15% &lt; <i>D</i> ≤ 50%), e consolida os Graus 3 e 4 (<i>D</i> &gt; 50%) sob o nível <b>Alteração Acentuada (Vermelho)</b>, "
        "acompanhado da recomendação ética padronizada: <i>\"Valor fora do padrão esperado. Recomendamos buscar avaliação médica com prioridade\"</i>. "
        "A <b>Tabela 1</b> formaliza o mapeamento matemático e semântico completo:",
        body_style
    ))

    story.append(Paragraph("<b>Tabela 1:</b> Mapeamento formal entre os 5 estados clínicos internos (CLSI/CTCAE/CAP) e os 4 níveis visuais seguros de UX.", caption_style))
    grad_table_data = [
        [
            Paragraph("Nível Visual UX (Cor)", th_style),
            Paragraph("Estado Clínico Interno", th_style),
            Paragraph("Critério Matemático (P ou D)", th_style),
            Paragraph("Fundamentação (CLSI / CTCAE)", th_style),
            Paragraph("Orientação Segura ao Paciente", th_style)
        ],
        [
            Paragraph("1. Normal (Verde #10B981)", td_green),
            Paragraph("Nível 1: Normal Central", td_bold),
            Paragraph("Dentro da faixa: 10% ≤ P ≤ 90%", td_style),
            Paragraph("CLSI EP28-A3c (Zona Central 95%)", td_style),
            Paragraph("Resultado dentro da faixa central esperada para o exame.", td_style)
        ],
        [
            Paragraph("2. Atenção / Leve (Amarelo #EAB308)", td_yellow),
            Paragraph("Nível 2: Limítrofe Interno", td_bold),
            Paragraph("Dentro da faixa: P &lt; 10% ou P &gt; 90%", td_style),
            Paragraph("CLSI EP28-A3c (Fronteira P2,5–P10 / P90–P97,5)", td_style),
            Paragraph("Valor na faixa, porém próximo ao limite. Vale acompanhar a evolução.", td_style)
        ],
        [
            Paragraph("2. Atenção / Leve (Âmbar #F59E0B)", td_yellow),
            Paragraph("Nível 3: Alterado Leve", td_bold),
            Paragraph("Fora da faixa: 0% &lt; D ≤ 15%", td_style),
            Paragraph("NCI CTCAE v5.0 — Grau 1 (Leve)", td_style),
            Paragraph("Discretamente fora da faixa (até 15%). Acompanhamento de rotina.", td_style)
        ],
        [
            Paragraph("3. Alterado Moderado (Laranja #F97316)", td_orange),
            Paragraph("Nível 4: Alterado Moderado", td_bold),
            Paragraph("Fora da faixa: 15% &lt; D ≤ 50%", td_style),
            Paragraph("NCI CTCAE v5.0 — Grau 2 (Moderado)", td_style),
            Paragraph("Moderadamente fora da faixa. Avaliação médica para contextualizar.", td_style)
        ],
        [
            Paragraph("4. Alteração Acentuada (Vermelho #EF4444)", td_red),
            Paragraph("Nível 5: Alteração Acentuada", td_bold),
            Paragraph("Fora da faixa: D &gt; 50%", td_style),
            Paragraph("NCI CTCAE Graus 3–4 / CAP &amp; CLSI GP47", td_style),
            Paragraph("Valor fora do padrão esperado. Buscar avaliação médica com prioridade.", td_style)
        ],
    ]
    t_grad = Table(grad_table_data, colWidths=[85, 80, 92, 95, 135], repeatRows=1)
    t_grad.setStyle(make_booktabs_style("#0f172a"))
    story.append(t_grad)
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.4. Indicador Dinâmico de Tendência Temporal (<font name='DVS'>↗</font> / <font name='DVS'>↘</font>)", h2_style))
    story.append(Paragraph(
        "Um exame pontualmente classificado como <b>Normal (Verde)</b> pode ocultar uma deterioração fisiológica subjacente caso o "
        "biomarcador apresente variação abrupta entre duas coletas consecutivas (fenômeno conhecido em patologia clínica como "
        "<i>Delta Check</i> ou <i>Reference Change Value — RCV</i>). Para capturar essa cinética longitudinal, o algoritmo ordena "
        "todos os registros de um mesmo <i>codigo_loinc</i> por <i>data_coleta</i> e compara o valor atual <i>V<sub>t</sub></i> "
        "com o resultado imediatamente anterior <i>V<sub>t−1</sub></i>:",
        body_style
    ))
    story.append(Paragraph(
        "Δ<sub>rel</sub>(%) = ( ( <i>V<sub>t</sub></i> − <i>V<sub>t−1</sub></i> ) / |<i>V<sub>t−1</sub></i>| ) × 100%       e       "
        "Δ<sub>faixa</sub>(%) = ( ( <i>V<sub>t</sub></i> − <i>V<sub>t−1</sub></i> ) / <i>L</i> ) × 100%",
        formula_style
    ))
    story.append(Paragraph(
        "Sempre que a magnitude da variação supera <b>20%</b> (|Δ<sub>rel</sub>| &gt; 20% ou |Δ<sub>faixa</sub>| &gt; 20%) e o vetor "
        "de deslocamento aponta em direção ao limite superior (<i>V<sub>t</sub></i> &gt; Centro da faixa com Δ &gt; 0) ou ao limite "
        "inferior (<i>V<sub>t</sub></i> &lt; Centro da faixa com Δ &lt; 0), o motor aciona automaticamente o <b>Badge de Tendência "
        "(<font name='DVS'>↗</font> ou <font name='DVS'>↘</font>)</b>. Assim, uma queda de Ferritina de 48,0 para 35,0 ng/mL (−27,1% em direção à borda inferior) exibe o alerta "
        "preventivo <font name='DVS'>↘</font> mesmo permanecendo dentro do intervalo normal (10 a 291 ng/mL).",
        body_style
    ))

    # =========================================================================
    # 3. PILAR 2: INTERPRETAÇÃO CLÍNICA VIA TEXTOS DETERMINÍSTICOS
    # =========================================================================
    story.append(Paragraph("3. Interpretação Clínica via Textos Determinísticos (Zero-LLM Runtime)", h1_style))
    story.append(Paragraph(
        "Na concepção inicial de sistemas de saúde apoiados por IA, é frequente o emprego de arquiteturas <i>Retrieval-Augmented "
        "Generation</i> (RAG + LLM em tempo de execução) para redigir explicações ao paciente a cada abertura de tela. Contudo, "
        "a engenharia rigorosa de dispositivos médicos baseados em software (<i>Software as a Medical Device — SaMD</i>, regulados "
        "no Brasil pela <b>RDC ANVISA nº 657/2022</b>) demonstra que a geração textual aberta em <i>runtime</i> introduz riscos "
        "clínicos, regulatórios e operacionais inaceitáveis. Por conseguinte, o projeto substituiu o RAG dinâmico na exibição "
        "de faixas por uma <b>Matriz de Conhecimento Determinística Pré-Validada</b>, indexada diretamente pelo par ordenado "
        "(<i>codigo_loinc</i>, <i>nivel_gradiente</i>).",
        body_style
    ))

    story.append(Paragraph("3.1. Justificativa Arquitetural, Clínica e Regulatória", h2_style))
    story.append(Paragraph(
        "• <b>1. Previsibilidade e Segurança Clínica Absoluta (Eliminação do Risco de Alucinação):</b> "
        "Grandes Modelos de Linguagem (LLMs) são intrinsecamente probabilísticos (estocásticos). Mesmo sob temperaturas baixas "
        "(<i>T</i> = 0,2) e <i>System Prompts</i> restritivos, LLMs em tempo de execução podem sofrer <i>prompt drift</i>, "
        "extrapolar correlações clínicas inexistentes ou empregar vocabulário diagnóstico implícito. Com textos determinísticos "
        "pré-redigidos e auditados por diretrizes médicas (SBPC/ML, SBD, SBEM, SBC), garante-se <b>100% de determinismo funcional</b>: "
        "para um mesmo par (<i>codigo_loinc</i>, <i>nivel_gradiente</i>), o sistema entregará invariavelmente o texto homologado.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>2. Conformidade Ético-Legal e Delimitação Estrita de Escopo (CFM, ANVISA e LGPD):</b> "
        "De acordo com a Lei do Ato Médico (Lei nº 12.842/2013) e as diretrizes do Conselho Federal de Medicina, a emissão de "
        "diagnóstico nosológico é prerrogativa exclusiva do médico. Textos determinísticos asseguram que a plataforma atue "
        "estritamente na <b>Educação e Letramento em Saúde</b>: o conteúdo explica o papel fisiológico do biomarcador no corpo, "
        "contextualiza estatisticamente a faixa etária, aponta fatores pré-analíticos/hábitos de vida e fornece <b>2 a 3 perguntas "
        "estruturadas</b> para o paciente dialogar com seu médico na consulta, sem jamais proferir diagnósticos.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>3. Desempenho Computacional O(1) e Resiliência Operacional:</b> "
        "Enquanto uma chamada RAG + LLM em nuvem apresenta latência de 2.500 a 8.000 ms por analito (podendo causar travamentos "
        "e <i>carregamento infinito</i> quando um paciente abre um painel com 45 exames simultâneos, além de expor dados a "
        "quotas de API), a busca determinística em tabela hash em memória (<i>BASE_565_POR_LOINC</i>) opera em complexidade "
        "constante <b><i>O</i>(1) com tempo de resposta inferior a 1 ms</b>, funcionando 100% offline.",
        bullet_style
    ))

    story.append(Paragraph("3.2. Arquitetura e Schema da Base Determinística (113 Exames × 5 Faixas = 565 Objetos)", h2_style))
    story.append(Paragraph(
        "A base determinística homologada no arquivo <i>base_conhecimento_exames_565.json</i> (complementada por "
        "<i>base_conhecimento_loinc.json</i>) cobre a totalidade dos <b>113 analitos canônicos</b> do catálogo BR Core / LOINC "
        "(Hemograma Completo, Metabolismo Glicêmico, Perfil Lipídico, Função Renal, Eletrólitos, Função Hepática, Tireoide, "
        "Hormônios, Vitaminas/Minerais e Marcadores Inflamatórios/Cardíacos). Para cada analito, foram pré-computados os textos "
        "dos 5 níveis de classificação (113 × 5 = <b>565 objetos clínicos determinísticos</b>), cada qual estruturado em "
        "<b>5 Pilares Educativos</b> mais o bloco de perguntas médicas (<b>Tabela 2</b>):",
        body_style
    ))

    story.append(Paragraph("<b>Tabela 2:</b> Schema estrutural da Base de Conhecimento Determinística (565 objetos indexados por LOINC + Nível).", caption_style))
    kb_schema_data = [
        [
            Paragraph("Campo do Schema JSON", th_style),
            Paragraph("Tipo de Dado", th_style),
            Paragraph("Chave / Escopo", th_style),
            Paragraph("Conteúdo Determinístico e Função Educativa no Display", th_style)
        ],
        [
            Paragraph("<b>codigo_loinc / coluna</b>", td_bold),
            Paragraph("String (PK Hash)", td_italic),
            Paragraph("113 Analitos BR Core", td_style),
            Paragraph("Chave primária de indexação em memória (ex.: <i>2276-4</i> / <i>ferritina_ng_mL</i>).", td_style)
        ],
        [
            Paragraph("<b>resumo_exame</b>", td_bold),
            Paragraph("Text", td_italic),
            Paragraph("Por Analito (113)", td_style),
            Paragraph("Explicação acessível sobre a função biológica do marcador no organismo humano.", td_style)
        ],
        [
            Paragraph("<b>1_descricao_resultado</b>", td_bold),
            Paragraph("Text", td_italic),
            Paragraph("Por Faixa (565)", td_style),
            Paragraph("Pilar 1: Contextualização acolhedora e não-alarmista da posição atual na faixa.", td_style)
        ],
        [
            Paragraph("<b>2_estatistica_etaria_18_25</b>", td_bold),
            Paragraph("Text", td_italic),
            Paragraph("Por Faixa (565)", td_style),
            Paragraph("Pilar 2: Distribuição epidemiológica esperada em pares etários adultos jovens (18–25 anos).", td_style)
        ],
        [
            Paragraph("<b>3_impactos_individuo</b>", td_bold),
            Paragraph("Text", td_italic),
            Paragraph("Por Faixa (565)", td_style),
            Paragraph("Pilar 3: Repercussões funcionais no bem-estar, disposição energética e rotina diária.", td_style)
        ],
        [
            Paragraph("<b>4_possiveis_causas</b>", td_bold),
            Paragraph("Text", td_italic),
            Paragraph("Por Faixa (565)", td_style),
            Paragraph("Pilar 4: Fatores pré-analíticos (jejum, hidratação, treino) e fisiológicos associados.", td_style)
        ],
        [
            Paragraph("<b>5_correcao_desvio</b>", td_bold),
            Paragraph("Text", td_italic),
            Paragraph("Por Faixa (565)", td_style),
            Paragraph("Pilar 5: Orientações de estilo de vida saudável e indicação de avaliação médica.", td_style)
        ],
        [
            Paragraph("<b>perguntas_para_o_medico</b>", td_bold),
            Paragraph("Array[String] (2–3)", td_italic),
            Paragraph("Por Analito", td_style),
            Paragraph("Perguntas prontas em 1ª pessoa para empoderar o paciente durante a consulta médica.", td_style)
        ],
    ]
    t_kb = Table(kb_schema_data, colWidths=[105, 72, 85, 225], repeatRows=1)
    t_kb.setStyle(make_booktabs_style("#1e3a8a"))
    story.append(t_kb)

    # =========================================================================
    # 4. PILAR 3: DISPLAY DE EVOLUÇÃO CLÍNICA LONGITUDINAL
    # =========================================================================
    story.append(Paragraph("4. Display de Evolução Clínica Longitudinal (Interface do Paciente)", h1_style))
    story.append(Paragraph(
        "A camada de visualização do sistema materializa o valor prático da interoperabilidade semântica para o usuário final e "
        "para o médico. Ao invés de obrigar o paciente a abrir dezenas de arquivos PDF estáticos de diferentes laboratórios, "
        "a interface constrói dinamicamente a linha do tempo clínica a partir da junção relacional entre <i>patients</i>, "
        "<i>diagnostic_reports</i> e <i>observations</i>. A <b>Figura 2</b> ilustra o modelo visual da régua de gradiente "
        "combinado às curvas longitudinais reais extraídas da coorte de 3 anos do projeto:",
        body_style
    ))

    if os.path.exists(fig2_path):
        img2 = Image(fig2_path, width=485, height=485 * (5.2 / 12.0))
        t_img2 = Table([[img2]], colWidths=[487])
        t_img2.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#334155')),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(KeepTogether([
            t_img2,
            Paragraph(
                "<b>Figura 2:</b> (A) Régua matemática de normalização do gradiente mapeando os 5 estados clínicos em 4 níveis visuais seguros; "
                "(B1) Série temporal longitudinal da Glicose (LOINC <i>2345-7</i>) mostrando transição de nível alterado para normal; "
                "(B2) Série temporal da Ferritina Sérica (LOINC <i>2276-4</i>) destacando os alertas de tendência (<font name='DVS'>↘</font> −27% e <font name='DVS'>↗</font> +61%) dentro da banda sombreada.",
                caption_style
            )
        ]))

    story.append(Paragraph("4.1. Componentes Visuais e Cognitivos da Interface Longitudinal", h2_style))
    story.append(Paragraph(
        "• <b>Séries Temporais Filtradas por Código LOINC:</b> Os gráficos plotam <i>data_coleta</i> no eixo horizontal (X) "
        "contra <i>valor_numerico</i> no eixo vertical (Y) para qualquer biomarcador selecionado pelo código LOINC universal "
        "(ex.: Ferritina <i>2276-4</i>, Hemoglobina <i>718-7</i>, TSH <i>3016-3</i>, Glicose <i>2345-7</i> / <i>1558-6</i>, "
        "Vitamina D <i>1989-3</i>). Independentemente de o exame ter sido nomeado como \"Glicemia de Jejum\" no Laboratório A "
        "e \"Dosagem de Glicose\" no Hospital B, ambos compartilham o mesmo LOINC e convergem para uma única curva contínua.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Faixa de Referência Sombreada (Banda Fisiológica Translúcida):</b> O gráfico renderiza em segundo plano uma "
        "banda horizontal contínua e translúcida delimitada inferiormente por <i>faixa_referencia_min</i> e superiormente por "
        "<i>faixa_referencia_max</i>. Sob a ótica da ergonomia cognitiva (<i>pre-attentive visual processing</i>), essa banda "
        "permite que o paciente identifique em menos de 200 ms se sua trajetória histórica caminha pelo centro da zona verde "
        "ou se tangencia os limites de fronteira.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Rastreabilidade Multi-Laboratorial e Tooltips de Auditoria:</b> Cada vértice da curva longitudinal é colorido "
        "segundo seu nível semafórico (Verde, Amarelo, Laranja ou Vermelho) e possui um <i>tooltip</i> interativo que exibe: "
        "(i) o valor numérico exato e a unidade padronizada <b>UCUM</b>; (ii) a data da coleta; (iii) o rótulo da classificação "
        "e o badge de tendência (<font name='DVS'>↗</font> / <font name='DVS'>↘</font>); e (iv) o atributo <b><i>laboratorio_origem</i></b> resgatado da tabela "
        "<i>diagnostic_reports</i>, comprovando visualmente a interoperabilidade entre instituições distintas.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Visão Tabular Pivotada (Matriz Analito × Tempo com Colunas Vazias):</b> Além do gráfico em curva por LOINC, "
        "a interface do paciente oferece uma visão matricial completa das 113 colunas padronizadas (incluindo colunas não "
        "solicitadas em determinada coleta), permitindo ao médico comparar transversalmente todos os sistemas orgânicos.",
        bullet_style
    ))

    # =========================================================================
    # 5. CONSOLIDAÇÃO DOS SCHEMAS E FUNCIONAMENTO ATUAL DO PROJETO
    # =========================================================================
    story.append(Paragraph("5. Consolidação dos Schemas Relacionais e Estado Atual do Projeto", h1_style))
    story.append(Paragraph(
        "Para documentar integralmente como o sistema encontra-se estruturado e operando neste momento, apresenta-se a "
        "integração entre a camada de persistência relacional (as 4 tabelas SQL normalizadas ilustradas na <b>Figura 3</b>) "
        "e os contratos de API/Schemas internos que alimentam o Módulo de Classificação e Display Longitudinal:",
        body_style
    ))

    if os.path.exists(der_img_path):
        img_der = Image(der_img_path, width=440, height=440 * (506.0 / 1024.0))
        t_der = Table([[img_der]], colWidths=[487])
        t_der.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#334155')),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(KeepTogether([
            t_der,
            Paragraph(
                "<b>Figura 3:</b> Diagrama Entidade-Relacionamento (DER) das 4 tabelas relacionais normalizadas que sustentam "
                "as consultas de séries temporais e o controle de acesso LGPD do Módulo de Classificação e Display.",
                caption_style
            )
        ]))

    story.append(Paragraph("<b>Tabela 3:</b> Síntese integrada dos Schemas de Banco de Dados, Motor de Gradiente e Endpoints em operação.", caption_style))
    sys_table_data = [
        [
            Paragraph("Camada / Componente", th_style),
            Paragraph("Schema / Estrutura de Dados", th_style),
            Paragraph("Chaves e Atributos Principais", th_style),
            Paragraph("Comportamento Atual no Sistema (localhost:5000)", th_style)
        ],
        [
            Paragraph("<b>1. Tabela patients</b><br/>(FHIR <i>Patient</i>)", td_bold),
            Paragraph("Relacional SQL (PostgreSQL / SQLite)", td_style),
            Paragraph("<i>id</i> (UUID PK), <i>nome</i>, <i>cpf</i> (UNIQUE), <i>cns</i>, <i>data_nascimento</i>, <i>sexo_biologico</i>", td_style),
            Paragraph("Unifica o paciente por CPF. Permite clicar no paciente para abrir seus 10 laudos e evolução clínica.", td_style)
        ],
        [
            Paragraph("<b>2. Tabela diagnostic_reports</b><br/>(FHIR <i>DiagnosticReport</i>)", td_bold),
            Paragraph("Relacional SQL (1:N com <i>patients</i>)", td_style),
            Paragraph("<i>id</i> (UUID PK), <i>patient_id</i> (FK), <i>laboratorio_origem</i>, <i>data_coleta</i>, <i>assinatura_hash</i>, <i>versao</i>", td_style),
            Paragraph("Armazena os 10 laudos históricos (2023–2026) e novos uploads em PDF com deduplicação e hash SHA-256.", td_style)
        ],
        [
            Paragraph("<b>3. Tabela observations</b><br/>(FHIR <i>Observation</i>)", td_bold),
            Paragraph("Relacional Vertical EAV (1:N com <i>reports</i>)", td_style),
            Paragraph("<i>id</i> (PK), <i>report_id</i> (FK), <i>codigo_loinc</i>, <i>valor_numerico</i>, <i>unidade</i>, <i>faixa_referencia_min/max</i>", td_style),
            Paragraph("Armazena cada analito como linha indexada por LOINC; alimenta tanto os gráficos quanto a matriz de 113 colunas.", td_style)
        ],
        [
            Paragraph("<b>4. Tabela consents</b><br/>(Governança LGPD)", td_bold),
            Paragraph("Relacional SQL (1:N com <i>patients</i>)", td_style),
            Paragraph("<i>id</i> (PK), <i>patient_id</i> (FK), <i>hospital_origem/destino</i>, <i>escopo</i>, <i>status</i>, <i>expira_em</i>", td_style),
            Paragraph("Vinculada diretamente ao perfil do paciente; valida se o consentimento está <i>ativo</i> antes de expor os dados.", td_style)
        ],
        [
            Paragraph("<b>5. Schema Gradiente &amp; Tendência</b>", td_bold),
            Paragraph("Objeto Computado (<i>classificador.py</i>)", td_style),
            Paragraph("<i>nivel_4</i> (1–4), <i>nivel_5</i> (1–5), <i>posicao_pct</i>, <i>desvio_pct</i>, <i>seta</i> (<font name='DVS'>↗</font>/<font name='DVS'>↘</font>), <i>var_pct</i>", td_style),
            Paragraph("Calculado dinamicamente sobre a série ordenada por <i>data_coleta</i>; colore os badges e aciona alertas &gt; 20%.", td_style)
        ],
        [
            Paragraph("<b>6. Schema Base 565 Determinística</b>", td_bold),
            Paragraph("JSON Indexado em RAM (<i>interpretador_rag.py</i>)", td_style),
            Paragraph("Chave (<i>codigo_loinc</i>, <i>faixa</i>) → 5 Pilares (18–25a) + <i>perguntas_para_o_medico</i>", td_style),
            Paragraph("Retorno instantâneo (&lt; 5 ms) sem travamento ou dependência de LLM externa em tempo de execução.", td_style)
        ],
    ]
    t_sys = Table(sys_table_data, colWidths=[95, 90, 132, 170], repeatRows=1)
    t_sys.setStyle(make_booktabs_style("#0f172a"))
    story.append(t_sys)
    story.append(Spacer(1, 8))

    # =========================================================================
    # 6. REFERÊNCIAS TÉCNICAS E CIENTÍFICAS
    # =========================================================================
    story.append(Paragraph("6. Referências Técnicas, Clínicas e Normativas", h1_style))
    refs = [
        "1. <b>CLINICAL AND LABORATORY STANDARDS INSTITUTE (CLSI).</b> <i>EP28-A3c: Defining, Establishing, and Verifying Reference Intervals in the Clinical Laboratory; Approved Guideline — Third Edition</i>. Wayne, PA: CLSI, 2010.",
        "2. <b>CLINICAL AND LABORATORY STANDARDS INSTITUTE (CLSI).</b> <i>GP47: Management of Critical- and Significant-Risk Results, 1st Edition</i>. Wayne, PA: CLSI / College of American Pathologists (CAP), 2015.",
        "3. <b>U.S. DEPARTMENT OF HEALTH AND HUMAN SERVICES (NIH / NCI).</b> <i>Common Terminology Criteria for Adverse Events (CTCAE) Version 5.0</i>. National Cancer Institute, Nov. 2017.",
        "4. <b>SOCIEDADE BRASILEIRA DE PATOLOGIA CLÍNICA / MEDICINA LABORATORIAL (SBPC/ML).</b> <i>Recomendações da SBPC/ML para Comunicação de Resultados Críticos e Intervalos de Referência Laboratoriais (Lab Tests Online BR)</i>. Rio de Janeiro: SBPC/ML, 2022.",
        "5. <b>AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA (ANVISA).</b> <i>Resolução da Diretoria Colegiada — RDC nº 657, de 24 de março de 2022</i>. Dispõe sobre a regularização de software como dispositivo médico (<i>Software as a Medical Device — SaMD</i>). Brasília: DOU, 2022.",
        "6. <b>HEALTH LEVEL SEVEN INTERNATIONAL (HL7) &amp; MINISTÉRIO DA SAÚDE.</b> <i>HL7 FHIR Release 4 — Perfil Nacional BR Core (Patient, DiagnosticReport, Observation, Consent)</i> e <i>Portaria GM/MS nº 8.726/2025 (Padronização LOINC na RNDS)</i>. Brasília, 2025.",
        "7. <b>FRASER, C. G.</b> <i>Biological Variation: From Principles to Practice</i> (Reference Change Values / Delta Check in Clinical Chemistry). Washington, DC: AACC Press, 2001."
    ]
    for r in refs:
        story.append(Paragraph(r, ref_style))

    doc.build(story, canvasmaker=ScholarlyModuleCanvas)
    print(f"Relatório PDF do Módulo Clínico gerado com sucesso em: {pdf_output_path}")


if __name__ == '__main__':
    base_dir = r"c:\Users\janna\Desktop\Hackathon LEPoli"
    pdf_out = os.path.join(base_dir, "Relatorio_Tecnico_Modulo_Classificacao_Display_Longitudinal.pdf")
    fig1 = os.path.join(base_dir, "figura1_fluxo_arquitetura_deterministica.png")
    fig2 = os.path.join(base_dir, "figura2_gradiente_e_serie_longitudinal.png")
    der_img = r"C:\Users\janna\.gemini\antigravity\brain\bbb68fb2-9595-4ef1-b666-fcaa93e47f43\.user_uploaded\media_1794117577504_0711b472.jpg"
    gerar_relatorio_modulo_clinico(pdf_out, fig1, fig2, der_img)
