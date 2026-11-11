import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "laudos_paciente_janaina")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class FrischmannCanvas(canvas.Canvas):
    """Canvas com cabeçalho de marca e numeração de página Frischmann Aisengart / DASA."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        w, h = A4
        
        # Barra superior laranja de detalhe
        self.setFillColor(colors.HexColor("#E65100"))
        self.rect(28, h - 22, w - 56, 3, fill=True, stroke=False)
        
        # Linha fina no rodapé
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(28, 45, w - 28, 45)
        
        # Textos de rodapé oficial Frischmann / DASA
        self.setFont("Helvetica", 6.5)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(28, 35, "Laboratório registrado no CRM/PR 4128 | Responsável Técnico: Dr. Emilio Salvador Granato CRM 1313")
        self.drawString(28, 25, "A interpretação dos resultados deste(s) exame(s) e a conclusão diagnóstica são atos médicos dependentes de correlação clínica.")
        
        # Paginação à direita
        atend_txt = getattr(self, "atendimento_codigo", "8081.0150.7702")
        self.drawRightString(w - 28, 35, f"{atend_txt}  •  PG {self._pageNumber} de {page_count}")
        self.drawRightString(w - 28, 25, "Controle de Qualidade: Controllab / PALC - SBPC/ML")
        
        self.restoreState()


def criar_laudo_pdf(dados_laudo, caminho_saida):
    """Gera o arquivo PDF de um laudo clínico completo."""
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=32,
        bottomMargin=52
    )

    styles = getSampleStyleSheet()
    
    titulo_lab = ParagraphStyle(
        'TituloLab',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=17,
        textColor=colors.HexColor("#0284C7")
    )
    subtitulo_lab = ParagraphStyle(
        'SubLab',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#475569"),
        alignment=2
    )
    header_box_style = ParagraphStyle(
        'HBoxVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )
    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    nome_exame_style = ParagraphStyle(
        'NomeExame',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=9.5,
        textColor=colors.HexColor("#0F172A")
    )
    metodo_style = ParagraphStyle(
        'MetodoStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#475569")
    )
    resultado_normal = ParagraphStyle(
        'ResNormal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=9.5,
        textColor=colors.HexColor("#0F172A")
    )
    resultado_alterado = ParagraphStyle(
        'ResAlterado',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=9.5,
        textColor=colors.HexColor("#B91C1C")
    )
    referencia_style = ParagraphStyle(
        'RefStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # Cabeçalho da marca / Laboratório
    lab_table_data = [
        [
            Paragraph("FRISCHMANN<br/><font size=6.5 color='#E65100'><b>AISENGART MEDICINA DIAGNÓSTICA</b></font>", titulo_lab),
            Paragraph("Laboratório Frischmann Aisengart Curitiba<br/>Atendimento ao Cliente: <b>(41) 4004-0103</b> • www.labfa.com.br", subtitulo_lab)
        ]
    ]
    t_lab = Table(lab_table_data, colWidths=[280, 259])
    t_lab.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_lab)
    story.append(Spacer(1, 4))

    # Box de Dados do Paciente e Protocolo (Compatível com regex de extrator_local.py e Gemini)
    atend = dados_laudo['atendimento']
    cip = dados_laudo['cip']
    paciente_nome = dados_laudo['paciente']
    dn = dados_laudo['data_nascimento']
    idade = dados_laudo['idade']
    sexo = dados_laudo['sexo']
    solicitante = dados_laudo['solicitante']
    data_coleta = dados_laudo['data_coleta']
    hora_coleta = dados_laudo['hora_coleta']
    data_liberacao = dados_laudo['data_liberacao']

    box_data = [
        [
            Paragraph(f"<b>Protocolo:</b> {atend} &nbsp;|&nbsp; <b>CIP:</b> {cip}", header_box_style),
            Paragraph(f"<b>Data da Coleta:</b> {data_coleta} ({hora_coleta})", header_box_style)
        ],
        [
            Paragraph(f"<b>Paciente:</b> {paciente_nome} &nbsp;|&nbsp; <b>Sexo:</b> {sexo}", header_box_style),
            Paragraph(f"<b>Data de Nascimento:</b> {dn} ({idade} Anos)", header_box_style)
        ],
        [
            Paragraph(f"<b>Médico Solicitante:</b> {solicitante}", header_box_style),
            Paragraph(f"<b>Liberação:</b> {data_liberacao}", header_box_style)
        ]
    ]
    t_box = Table(box_data, colWidths=[330, 209])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 6))

    # Montagem da Tabela Única de Exames com Header repetível
    # Colunas: Exame / Analito | Material / Método | Resultado | Valores de Referência
    col_widths = [165, 115, 110, 149]
    table_rows = [
        [
            Paragraph("<b>Exame / Analito</b>", th_style),
            Paragraph("<b>Material / Método</b>", th_style),
            Paragraph("<b>Resultado</b>", th_style),
            Paragraph("<b>Valores de Referência</b>", th_style)
        ]
    ]

    for ex in dados_laudo['exames']:
        nome = ex['nome']
        detalhe = ex.get('detalhe', 'Soro / Quimioluminescência')
        resultado = ex['resultado']
        referencia = ex.get('referencia', '')
        alterado = ex.get('alterado', False)

        res_p = Paragraph(f"<b>{resultado}</b>", resultado_alterado if alterado else resultado_normal)
        nome_p = Paragraph(f"<b>{nome}</b>", nome_exame_style)
        det_p = Paragraph(detalhe, metodo_style)
        ref_p = Paragraph(referencia, referencia_style)

        table_rows.append([nome_p, det_p, res_p, ref_p])

        # Se tiver subitens (ex: frações do hemograma ou cálculos como HOMA-IR)
        for sub in ex.get('subitens', []):
            sub_res_p = Paragraph(sub['resultado'], resultado_alterado if sub.get('alterado', False) else resultado_normal)
            sub_nome_p = Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• {sub['nome']}", nome_exame_style)
            sub_ref_p = Paragraph(sub.get('referencia', ''), referencia_style)
            table_rows.append([sub_nome_p, det_p, sub_res_p, sub_ref_p])

    t_exames = Table(table_rows, colWidths=col_widths, repeatRows=1)
    t_exames.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_exames)

    def set_canvas_atend(c_obj, d_obj):
        c_obj.atendimento_codigo = atend

    doc.build(story, canvasmaker=FrischmannCanvas)
    return caminho_saida
