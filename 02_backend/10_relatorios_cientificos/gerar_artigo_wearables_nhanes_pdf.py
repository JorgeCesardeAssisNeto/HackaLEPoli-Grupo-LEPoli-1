# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
"""Gera o Artigo Tecnico-Academico (Parte III): Wearables x Hemograma x NHANES."""
import os, json
import matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

pdfmetrics.registerFont(TTFont('TNR', r'C:\Windows\Fonts\times.ttf'))
pdfmetrics.registerFont(TTFont('TNR-Bold', r'C:\Windows\Fonts\timesbd.ttf'))
pdfmetrics.registerFont(TTFont('TNR-Italic', r'C:\Windows\Fonts\timesi.ttf'))
pdfmetrics.registerFont(TTFont('TNR-BoldItalic', r'C:\Windows\Fonts\timesbi.ttf'))
pdfmetrics.registerFontFamily('TNR', normal='TNR', bold='TNR-Bold', italic='TNR-Italic', boldItalic='TNR-BoldItalic')
pdfmetrics.registerFont(TTFont('DVS', os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf', 'DejaVuSerif.ttf')))

ROOT = _paths.FIGURAS_DIR
VAL = r"C:\Users\janna\.gemini\antigravity\brain\bbb68fb2-9595-4ef1-b666-fcaa93e47f43\scratch\validacao_cv.json"
V = json.load(open(VAL, encoding="utf-8"))
UP = "<font name='DVS'>↑</font>"
DN = "<font name='DVS'>↓</font>"
LR = "<font name='DVS'>↔</font>"
AR = "<font name='DVS'>→</font>"


def f(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


class ScholarlyCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self._states = []

    def showPage(self):
        self._states.append(dict(self.__dict__)); self._startPage()

    def save(self):
        n = len(self._states)
        for s in self._states:
            self.__dict__.update(s); self.chrome(n); super().showPage()
        super().save()

    def chrome(self, n):
        self.saveState(); w, h = A4; l, r = 54, w - 54
        if self._pageNumber == 1:
            self.setStrokeColor(colors.HexColor("#0f172a")); self.setLineWidth(1.5); self.line(l, h - 36, r, h - 36)
            self.setLineWidth(0.4); self.line(l, h - 39, r, h - 39)
            self.setFont("TNR-Italic", 8); self.setFillColor(colors.HexColor("#334155"))
            self.drawString(l, h - 31, "CADERNOS DE INFORMÁTICA MÉDICA — COALIZÃO OPEN HEALTH BRASIL")
            self.drawRightString(r, h - 31, "Série Técnica Vol. III — Novembro de 2026")
        else:
            self.setFont("TNR-Italic", 8.5); self.setFillColor(colors.HexColor("#1e293b"))
            self.drawString(l, h - 38, "Wearables, Hemograma e Modelagem Preditiva Cruzada (NHANES)")
            self.setFont("TNR", 8.5); self.drawRightString(r, h - 38, "Open Health — Desafio Rivio / LEPoli")
            self.setStrokeColor(colors.HexColor("#1e293b")); self.setLineWidth(0.6); self.line(l, h - 43, r, h - 43)
        self.setStrokeColor(colors.HexColor("#94a3b8")); self.setLineWidth(0.5); self.line(l, 44, r, 44)
        self.setFont("TNR-Italic", 8); self.setFillColor(colors.HexColor("#475569"))
        self.drawString(l, 32, "Artigo Técnico-Acadêmico | Ciência de Dados Aplicada à Saúde")
        self.setFont("TNR-Bold", 8.5); self.setFillColor(colors.HexColor("#0f172a"))
        self.drawRightString(r, 32, f"Página {self._pageNumber} de {n}")
        self.restoreState()


def booktabs(header_bg="#0f172a"):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor('#0f172a')), ('LINEBELOW', (0, 0), (-1, 0), 1.0, colors.HexColor('#0f172a')),
        ('LINEBELOW', (0, 1), (-1, -2), 0.35, colors.HexColor('#cbd5e1')), ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor('#0f172a')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ])


ss = getSampleStyleSheet()
def S(name, **kw):
    parent = kw.pop('parent', ss['Normal'])
    return ParagraphStyle(name, parent=parent, **kw)

kicker = S('k', fontName='TNR-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#1e3a8a'), alignment=1, spaceAfter=4)
title = S('t', fontName='TNR-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#0f172a'), alignment=1, spaceAfter=6)
subtitle = S('st', fontName='TNR-Italic', fontSize=10.8, leading=14.2, textColor=colors.HexColor('#334155'), alignment=1, spaceAfter=10)
author = S('au', fontName='TNR-Bold', fontSize=9.5, leading=13, alignment=1, spaceAfter=2)
affil = S('af', fontName='TNR-Italic', fontSize=8.5, leading=11.5, textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=10)
absx = S('ab', fontName='TNR', fontSize=8.5, leading=12.2, textColor=colors.HexColor('#1e293b'), alignment=4)
h1 = S('h1', fontName='TNR-Bold', fontSize=11.8, leading=15.0, spaceBefore=10, spaceAfter=4, keepWithNext=True)
h2 = S('h2', fontName='TNR-BoldItalic', fontSize=10.0, leading=13.0, textColor=colors.HexColor('#1e3a8a'), spaceBefore=7, spaceAfter=3.5, keepWithNext=True)
body = S('b', fontName='TNR', fontSize=9.4, leading=13.3, textColor=colors.HexColor('#1e293b'), alignment=4, firstLineIndent=16, spaceAfter=4.2)
bullet = S('bl', fontName='TNR', fontSize=9.1, leading=12.8, textColor=colors.HexColor('#1e293b'), alignment=4, leftIndent=14, firstLineIndent=-10, spaceAfter=3.2)
formula = S('fo', fontName='TNR-Italic', fontSize=9.6, leading=14, alignment=1, spaceBefore=3, spaceAfter=6)
th = S('th', fontName='TNR-Bold', fontSize=7.9, leading=10, textColor=colors.white)
td = S('td', fontName='TNR', fontSize=7.8, leading=10.2)
tdb = S('tdb', parent=td, fontName='TNR-Bold')
cap = S('cap', fontName='TNR', fontSize=8.4, leading=11.5, textColor=colors.HexColor('#334155'), alignment=4, spaceBefore=4, spaceAfter=7)
ref = S('ref', fontName='TNR', fontSize=8.1, leading=11.2, alignment=4, leftIndent=16, firstLineIndent=-16, spaceAfter=3)
note = S('note', fontName='TNR', fontSize=8.8, leading=12.6, textColor=colors.HexColor('#7c2d12'), alignment=4)

P = lambda t, s=body: Paragraph(t, s)


def table(rows, widths, bold_first=True, header_bg="#0f172a"):
    data = [[Paragraph(c, th) for c in rows[0]]]
    for r in rows[1:]:
        data.append([Paragraph(c, tdb if (i == 0 and bold_first) else td) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1); t.setStyle(booktabs(header_bg)); return t


def figure(path, caption, width=487):
    if not os.path.exists(path):
        return []
    w, h = PILImage.open(path).size
    img = Image(path, width=width - 4, height=(width - 4) * h / w)
    t = Table([[img]], colWidths=[width])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#334155')),
                           ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
    return [KeepTogether([t, Paragraph(caption, cap)])]


def callout(text, bg='#fff7ed', border='#c2410c'):
    t = Table([[Paragraph(text, note)]], colWidths=[487])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg)), ('LINEBEFORE', (0, 0), (0, -1), 2.5, colors.HexColor(border)),
                           ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LEFTPADDING', (0, 0), (-1, -1), 9)]))
    return t


def build(out_pdf):
    doc = SimpleDocTemplate(out_pdf, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=52, bottomMargin=54,
                            title="Wearables x Hemograma x NHANES - Artigo Tecnico-Academico", author="Open Health LEPoli")
    s = []
    e1, e2, an, nv = V["etapa1_pop_HGB"], V["etapa2_calibrada"], V["ancorado_OLS"], V["naive_FC3_igual_FC1"]
    rs = V["etapa2_residuo"]; hb = V["OLS_Hb_FCR_adultos"]; hb13 = V["OLS_Hb_FCR_Hb_lt13"]

    # ------------------------------------------------------------ CAPA
    s.append(P("ARTIGO TÉCNICO-ACADÊMICO (PARTE III)", kicker))
    s.append(P("Integração de Dados de Wearables, Análise Estatística e Modelagem Preditiva Cruzada com o "
               "Hemograma em uma Plataforma Open Health", title))
    s.append(P("Clusters fisiológicos wearable–sangue, base populacional CDC NHANES e calibração individual em duas etapas "
               "da frequência cardíaca de repouso", subtitle))
    s.append(P("Grupo de Pesquisa em Informática Médica e Ciência de Dados Aplicada à Saúde", author))
    s.append(P("Escola Politécnica / Hackathon Gama House &amp; LEPoli — Desafio Rivio | São Paulo, 09–10 de novembro de 2026", affil))
    resumo = (
        "<b>RESUMO:</b> Este artigo documenta o módulo que relaciona séries temporais de dispositivos vestíveis (<i>wearables</i>) aos "
        "exames laboratoriais armazenados na tabela <i>observations</i> (HL7 FHIR BR Core / LOINC) da plataforma Open Health. "
        "<b>Métodos:</b> integraram-se, pela chave <i>SEQN</i>, módulos do CDC NHANES 2017–mar/2020 (N = 15.560) e 2011–2012 "
        "(subcoorte hormonal), e um conjunto de dados de wearable com 300 usuários e 55.200 registros diários. Foram formulados três "
        "clusters de validação cruzada wearable–sangue (transporte de O<sub>2</sub>, inflamatório e hipóxia) e treinados, com "
        "<i>gradient boosting</i> e modelos lineares, um modelo principal de frequência cardíaca de repouso (FCR) calibrado em duas "
        "etapas e três modelos complementares (metabólico, apneia e inflamatório). O desempenho foi reavaliado por validação cruzada "
        "estratificada de 5 partições. <b>Resultados:</b> o hemograma, a idade, o sexo e o IMC explicam isoladamente pouca variância da "
        f"FCR (R² = {f(e1['R2_cv'])}; EMA = {f(e1['MAE_cv'],1)} bpm), confirmando a inexistência de uma equação determinística. "
        f"A calibração pelo \"marco zero\" individual eleva o desempenho para R² = {f(e2['R2'])} (EMA = {f(e2['MAE'],2)} bpm), com resíduo "
        f"de desvio-padrão {f(rs['dp'],2)} bpm, que passa a ser o sinal de detecção de anomalias. Fora da amostra, os classificadores "
        f"atingiram ROC-AUC de {f(V['metab_hba1c_expandido']['AUC_cv'],2)} (HbA1c ≥ 5,7%), {f(V['m1_ferritina_baixa']['AUC_cv'],2)} "
        f"(ferritina &lt; 30 ng/mL) e {f(V['apneia_HGB']['AUC_cv'],2)} (sintomas de apneia), valores inferiores aos exibidos no painel "
        "(calculados na própria amostra de treino). <b>Conclusão:</b> a arquitetura é viável como camada de triagem e de "
        "contextualização pré-consulta, desde que a saída seja restrita a alertas determinísticos, sem emissão de diagnóstico.<br/><br/>"
        "<b>Palavras-chave:</b> Wearables; Hemograma; NHANES; Frequência Cardíaca de Repouso; Calibração Individual; Open Health; LGPD.<br/><br/>"
        "<b>ABSTRACT:</b> <i>We describe an Open Health module linking consumer wearable time series to FHIR/LOINC blood test records. "
        "Using NHANES (2017–2020 and 2011–2012) linked by SEQN, we define three wearable–blood physiological clusters and train a "
        "two-stage calibrated resting heart rate model plus metabolic, sleep-apnea and inflammatory models. Cross-validated "
        f"performance is reported (calibrated RHR R² = {e2['R2']}; HbA1c AUC = {V['metab_hba1c_expandido']['AUC_cv']}). Outputs are "
        "restricted to deterministic contextual alerts, never automated diagnoses.</i>")
    ta = Table([[P(resumo, absx)]], colWidths=[487])
    ta.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')), ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#94a3b8')),
                            ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10)]))
    s += [ta, Spacer(1, 6)]

    # ------------------------------------------------------------ 1. INTRODUCAO
    s.append(P("1. Introdução", h1))
    s.append(P(
        "As Partes I e II desta série especificaram, respectivamente, o modelo relacional normalizado da plataforma Open Health "
        "(<i>patients</i>, <i>diagnostic_reports</i>, <i>observations</i> e <i>consents</i>) e o motor determinístico de classificação "
        "e exibição longitudinal de exames de sangue. Um exame laboratorial, contudo, é uma fotografia pontual: entre duas coletas "
        "podem transcorrer meses sem qualquer informação fisiológica. Os <i>wearables</i> de consumo preenchem esse intervalo com "
        "medidas diárias de frequência cardíaca de repouso (FCR), variabilidade da frequência cardíaca (HRV), saturação periférica de "
        "oxigênio (SpO<sub>2</sub>), sono e atividade física."))
    s.append(P(
        "A pergunta de pesquisa deste módulo é se é possível relacionar esses sinais contínuos ao hemograma de forma estatisticamente "
        "defensável, de modo que (i) um desvio sustentado no relógio sugira a antecipação de um exame, e (ii) um exame alterado ganhe "
        "contexto fisiológico no <i>briefing</i> pré-consulta do médico. Como não existem bases públicas que contenham simultaneamente "
        "séries de wearable e hemogramas das mesmas pessoas, adotou-se o <b>CDC NHANES</b> como base de treinamento populacional, "
        "estabelecendo uma ponte de equivalência entre suas variáveis clínicas e as métricas do dispositivo. A literatura sustenta a "
        "plausibilidade da abordagem: desvios da FCR e do sono captados por wearables anteciparam doença infecciosa em estudos "
        "populacionais [6, 7], e a FCR é marcador prognóstico independente [5]."))

    # ------------------------------------------------------------ 2. METODOLOGIA
    s.append(P("2. Metodologia", h1))
    s.append(P("2.1. Fontes de Dados e Integração pela Chave SEQN", h2))
    s.append(P(
        "Todos os arquivos do NHANES compartilham o identificador <i>SEQN</i>, que representa o mesmo participante em diferentes "
        "módulos. Os arquivos SAS Transport (.xpt) foram unidos por junção externa em uma tabela mestre de 15.560 participantes do "
        "ciclo 2017–mar/2020; a subcoorte de 2011–2012 (ciclo G) foi integrada separadamente porque seus <i>SEQN</i> não se sobrepõem "
        "aos do ciclo P. A Tabela 1 resume os módulos utilizados."))
    s.append(table([
        ["Módulo NHANES", "Ciclo", "Conteúdo utilizado", "Papel no módulo"],
        ["P_DEMO", "2017–2020", "Idade (RIDAGEYR), sexo (RIAGENDR)", "Covariáveis obrigatórias"],
        ["P_BPXO", "2017–2020", "Pulso BPXOPLS1–3; PA BPXOSY/BPXODI 1–3", "Alvo FCR e equivalente do wearable"],
        ["P_CBC", "2017–2020", "Hb, Hct, hemácias, leucócitos, neutrófilos, plaquetas, VCM, RDW", "Preditores hematológicos"],
        ["P_FERTIN", "2017–2020", "Ferritina sérica (LBXFER)", "Reserva de ferro (Cluster A)"],
        ["P_BMX", "2017–2020", "IMC (BMXBMI)", "Covariável antropométrica"],
        ["P_SLQ", "2017–2020", "Sono (SLD012); ronco, pausas, sonolência (SLQ030/040/120)", "Equivalente de sono; alvo de apneia"],
        ["P_PAQ", "2017–2020", "Minutos sedentários (PAD680) e atividade", "Equivalente de workout_minutes"],
        ["P_HSCRP", "2017–2020", "PCR ultrassensível (LBXHSCRP)", "Modelo inflamatório"],
        ["P_GLU / P_GHB", "2017–2020", "Glicose de jejum, HbA1c", "Alvos do modelo metabólico"],
        ["P_BPQ, P_ALQ", "2017–2020", "Hipertensão, anti-hipertensivos, álcool", "Critérios de coorte saudável e filtros"],
        ["THYROD_G, TST_G, CBC_G, BPX_G, DEMO_G, BMX_G", "2011–2012", "TSH, T4L, T3L, testosterona + hemograma e pulso", "Análise hormonal exploratória"],
    ], [92, 52, 190, 153]))
    s.append(P("<b>Tabela 1.</b> Módulos do CDC NHANES integrados pela chave SEQN.", cap))
    w = V.get("wearable_csv", {})
    s.append(P(
        f"O conjunto de dados de wearable (<i>wearables_health_6mo_daily.csv</i>) contém {w.get('users',300)} usuários e "
        f"{w.get('rows',55200):,} registros diários (≈ 6 meses por usuário)".replace(",", ".") +
        ", com as colunas <i>resting_hr_bpm</i>, <i>avg_hr_day_bpm</i>, <i>hrv_rmssd_ms</i>, <i>spo2_avg_pct</i>, <i>sbp_mmHg</i>, "
        "<i>dbp_mmHg</i>, <i>sleep_duration_hours</i>, <i>sleep_efficiency</i>, <i>wake_after_sleep_onset_min</i> (WASO), estágios do "
        "sono, <i>workout_minutes</i>, <i>steps</i>, <i>alcohol_units</i>, <i>caffeine_mg</i> e <i>stress_score</i>. Nesta etapa, ele "
        "foi utilizado <b>apenas como entrada</b> da camada de inferência, sem participar do treinamento."))

    s.append(P("2.2. Interdependência entre os Sensores do Wearable", h2))
    s.append(P(
        "As métricas do wearable não são independentes: um mesmo estímulo fisiológico altera vários sensores simultaneamente, e um "
        "sensor pode distorcer a estimativa de outro. Ignorar essa estrutura produz alertas redundantes ou falsos. A Tabela 2 "
        "sistematiza as interferências consideradas no desenho dos clusters."))
    s.append(table([
        ["Estímulo / sinal primário", "Efeito nos demais sensores", "Mecanismo fisiológico", "Implicação para o algoritmo"],
        [f"{UP} Temperatura cutânea (febre, inflamação)", f"{UP} FCR (≈ 8–10 bpm/°C); {DN} HRV", "Ativação simpática e aumento da taxa metabólica",
         "Desvio de FCR com temperatura elevada sugere Cluster B, não Cluster A"],
        [f"{UP} FCR por estresse ou sono ruim", "Subestimação do VO<sub>2</sub>máx", "Algoritmos estimam VO<sub>2</sub>máx pela razão FCmáx/FCR",
         f"{DN} VO<sub>2</sub>máx só é valorizado se a FCR basal estiver estável"],
        [f"Quedas noturnas de SpO<sub>2</sub>", f"{UP} WASO, {DN} sono profundo, {UP} FCR matinal", "Microdespertares por hipóxia intermitente",
         "Fragmentação do sono é avaliada em conjunto com SpO<sub>2</sub> (Cluster C)"],
        ["Treino intenso (workout_minutes)", f"{UP} FCR e temperatura por 24–48 h; {DN} HRV", "Recuperação autonômica pós-esforço",
         "Dias pós-treino são excluídos/ponderados do baseline"],
        ["Álcool (alcohol_units)", f"{UP} FCR noturna; {DN} HRV; {UP} WASO", "Vasodilatação e supressão vagal",
         "Noites com álcool são filtradas antes do cálculo do desvio"],
    ], [98, 112, 125, 152]))
    s.append(P("<b>Tabela 2.</b> Matriz de interdependência entre sensores e consequências algorítmicas.", cap))
    c = V.get("wearable_corr", {})
    if c:
        s.append(P(
            "No conjunto de dados atual, as correlações empíricas mais fortes foram <i>avg_hr_day_bpm</i> × <i>resting_hr_bpm</i> "
            f"(r = {f(c['resting_hr_bpm']['avg_hr_day_bpm'])}), <i>alcohol_units</i> × WASO (r = {f(c['alcohol_units']['wake_after_sleep_onset_min'])}), "
            f"<i>sleep_duration_hours</i> × HRV (r = {f(c['sleep_duration_hours']['hrv_rmssd_ms'])}) e <i>alcohol_units</i> × HRV "
            f"(r = {f(c['alcohol_units']['hrv_rmssd_ms'])}), coerentes com a Tabela 2. Por outro lado, FCR × HRV foi praticamente nula "
            f"(r = {f(c['resting_hr_bpm']['hrv_rmssd_ms'])}), o que é atípico para dados reais e indica que o conjunto possui caráter "
            "sintético ou simulado. As variáveis temperatura cutânea e VO<sub>2</sub>máx, previstas na especificação, <b>ainda não constam</b> "
            "no conjunto e foram mantidas no desenho para integração futura."))

    s.append(P("2.3. Clusters de Validação Cruzada Wearable–Sangue", h2))
    s.append(P(
        "Em vez de interpretar cada sensor isoladamente, o sistema procura <b>padrões conjuntos</b> que tenham correspondência "
        "fisiológica com grupos de analitos do hemograma. Um cluster só é sinalizado quando seus componentes se movem na direção "
        "esperada, e o exame correspondente é o instrumento de confirmação (Figura 1)."))
    s += figure(os.path.join(ROOT, "figura3_2_clusters_wearable_hemograma.png"),
                "<b>Figura 1:</b> Clusters de validação cruzada. Cada padrão de sensores (esquerda) corresponde a uma hipótese fisiológica "
                "(centro) verificável em analitos LOINC da tabela <i>observations</i> (direita). Variáveis comportamentais atuam como filtro "
                "de falsos positivos.")
    s.append(table([
        ["Cluster", "Padrão no wearable", "Analitos confirmatórios (LOINC)", "Fundamento"],
        ["A — Transporte de O<sub>2</sub> (anemia / fadiga)", f"{UP} FCR sustentada + {DN} VO<sub>2</sub>máx + temperatura estável",
         "Hemoglobina 718-7, Hematócrito 4544-3, Hemácias 789-8, Ferritina 2276-4", "Taquicardia compensatória para manter a oferta de O<sub>2</sub> (DO<sub>2</sub>)"],
        ["B — Inflamatório / imunológico", f"{UP} temperatura basal + {DN} HRV persistente + {UP} FCR",
         "Leucócitos 6690-2, PCR 1988-5 / 30522-7, VHS 4537-7", "Citocinas elevam a frequência intrínseca e suprimem o tônus vagal"],
        ["C — Hipóxia / apneia", f"{DN} spo2_avg_pct noturna recorrente + {UP} WASO",
         f"{UP} Hematócrito, {UP} Hemácias", "Hipóxia crônica estimula eritropoetina (policitemia secundária)"],
    ], [92, 125, 140, 130]))
    s.append(P("<b>Tabela 3.</b> Clusters de validação cruzada wearable–sangue.", cap))
    s.append(P(
        "<b>Filtros de falsos positivos.</b> O uso de <i>workout_minutes</i> e <i>alcohol_units</i> é obrigatório: um treino intenso "
        "eleva FCR e temperatura e reduz a HRV por até 48 h, e uma noite com álcool reproduz quase integralmente o padrão do Cluster B. "
        "Esses dias são removidos (ou recebem peso reduzido) tanto do <i>baseline</i> quanto da janela de avaliação, de modo que apenas "
        "desvios não explicados por comportamento agudo sejam atribuídos a alterações fisiológicas."))

    s.append(P("2.4. Por que não Existe uma Equação Determinística Única", h2))
    s.append(P(
        "A relação fisiológica entre sangue e FCR decorre do princípio de Fick aplicado à oferta de oxigênio (DO<sub>2</sub>):"))
    s.append(P("DO<sub>2</sub> = DC × CaO<sub>2</sub> ,   DC = FC × VS ,   CaO<sub>2</sub> = 1,34 × Hb × SaO<sub>2</sub> + 0,003 × PaO<sub>2</sub>", formula))
    s.append(P("FC = DO<sub>2</sub> / ( VS × CaO<sub>2</sub> )", formula))
    s.append(P(
        "Para uma demanda tecidual constante, uma queda de hemoglobina (Hb) reduz o CaO<sub>2</sub> e precisa ser compensada por "
        "aumento da frequência cardíaca (FC) <i>ou</i> do volume sistólico (VS). O VS, a demanda metabólica, a volemia/hidratação, o "
        "condicionamento físico e o uso de medicamentos (p. ex., betabloqueadores) não são mensuráveis pelo relógio nem pelo hemograma. "
        "Toda equação estatística assume, portanto, a forma FCR = f(Hb, idade, sexo, IMC, …) + ε, em que o erro residual ε é dominante."))
    s.append(P(
        "Os dados confirmam empiricamente essa limitação. Na regressão linear multivariada em adultos do NHANES (N = "
        f"{hb['N']:,}".replace(",", ".") + f"), ajustada por idade, sexo e IMC, o coeficiente da hemoglobina foi β = +{f(hb['beta_Hb'])} bpm por g/dL "
        f"(IC95% {f(hb['ci'][0])} a {f(hb['ci'][1])}; R² = {f(hb['R2'])}), e no subgrupo com Hb &lt; 13 g/dL foi β = {f(hb13['beta_Hb'])} "
        f"(p = {f(hb13['p'],2)}; não significativo). Ou seja, a associação inversa de 1 a 3 bpm por g/dL descrita na fisiologia da anemia "
        "<b>não se reproduz em dados transversais populacionais</b>, nos quais a compensação via VS e os fatores de confusão predominam. "
        "Por isso, o sistema não usa uma fórmula populacional fixa: ele compara cada indivíduo consigo mesmo (Seção 3.1)."))

    s.append(P("2.5. Mapeamento de Equivalência NHANES ↔ Wearable", h2))
    s.append(P(
        "Os modelos são treinados com variáveis clínicas e de questionário do NHANES, mas em produção recebem médias móveis do wearable. "
        "A Tabela 4 define a ponte estatística implementada na classe <i>WearableBridge</i>."))
    s.append(table([
        ["Variável NHANES (treino)", "Métrica do wearable (produção)", "Agregação", "Observação de equivalência"],
        ["BPXOPLS1–3 / pulse_avg", "resting_hr_bpm", "Média 7–14 dias", "Pulso sentado em consultório vs. FCR noturna: viés sistemático absorvido por Δ<sub>ind</sub>"],
        ["BPXOPLS1 (1ª leitura)", "Média dos 7 primeiros dias", "Baseline", "\"Marco zero\" individual (FC<sub>0</sub>)"],
        ["SLD012", "sleep_duration_hours", "Média noturna", "Autorrelato vs. medida do sensor"],
        ["PAD680 (minutos sedentários)", "workout_minutes", "Média diária", "Relação inversa aproximada: sedentário ≈ 600 − 3,5 × workout (mín. 180)"],
        ["BMXBMI", "bmi (perfil)", "Último valor", "Equivalência direta"],
        ["BPXOSY / BPXODI", "sbp_mmHg / dbp_mmHg", "Média 7–14 dias", "Disponível apenas em dispositivos com PA"],
        ["SLQ040 (pausas respiratórias)", "wake_after_sleep_onset_min + spo2_avg_pct", "Média noturna", "Modificadores do escore de apneia"],
    ], [102, 112, 68, 205]))
    s.append(P("<b>Tabela 4.</b> Mapeamento de equivalência entre variáveis de treino e de produção.", cap))

    s.append(P("2.6. Protocolo de Treinamento e Validação", h2))
    s.append(P(
        "Utilizaram-se <i>HistGradientBoosting</i> (scikit-learn) para os modelos não lineares e regressão linear/logística (statsmodels) "
        "para os coeficientes interpretáveis (β, <i>odds ratios</i>, IC95%). A coorte saudável do modelo de FCR excluiu diagnóstico de "
        "hipertensão (BPQ020), uso de anti-hipertensivos (BPQ040A), PA ≥ 135/85 mmHg e leituras de pulso fora de 45–130 bpm. As métricas "
        "do painel interativo (<i>localhost</i>) foram calculadas na própria amostra de treino; para este artigo, todas foram "
        "<b>recalculadas por validação cruzada de 5 partições</b> (estratificada nos classificadores), procedimento recomendado pela "
        "declaração TRIPOD [12] para estimar o desempenho em dados não vistos."))

    # ------------------------------------------------------------ 3. ARQUITETURA DOS MODELOS
    s.append(P("3. Arquitetura dos Modelos", h1))
    s.append(P("3.1. Modelo Principal: Previsão de FCR Calibrada em Duas Etapas", h2))
    s.append(P(
        "A primeira versão do modelo (\"ancoragem em saudáveis\") usava a 1ª leitura de pulso como preditor da 3ª. Ela atingiu "
        f"R² = {f(an['R2_cv'])} (EMA = {f(an['MAE_cv'],2)} bpm) fora da amostra, mas a simples regra \"3ª leitura = 1ª leitura\" já produz "
        f"R² = {f(nv['R2'])} (EMA = {f(nv['MAE'],2)} bpm): a medição inicial concentra quase todo o peso preditivo (β = 0,934; t = 150) e o "
        "sangue contribui marginalmente. Para impedir que a primeira medição domine o treino, o modelo foi reestruturado em duas etapas:"))
    s.append(P(
        "• <b>Etapa 1 — Regressão populacional (NHANES).</b> Um modelo treinado apenas com série vermelha (Hb, Hct, hemácias), série branca "
        "(leucócitos), plaquetas, idade, sexo e IMC estima a FCR basal populacional esperada:", bullet))
    s.append(P("FC<sub>pop</sub> = f<sub>NHANES</sub>( série vermelha, série branca, plaquetas, idade, sexo, IMC )", formula))
    s.append(P(
        "• <b>Etapa 2 — Calibração individual (\"marco zero\").</b> A primeira marcação real do usuário (FC<sub>0</sub>, média dos 7 "
        "primeiros dias no wearable) define o desvio individual, que absorve condicionamento, VS e diferenças de sensor:", bullet))
    s.append(P("Δ<sub>ind</sub> = FC<sub>0</sub> − FC<sub>pop</sub>(t<sub>0</sub>)   <font name='DVS'>⇒</font>   FC<sub>prevista</sub>(t<sub>1</sub>) = FC<sub>pop</sub>(t<sub>1</sub>) + Δ<sub>ind</sub>", formula))
    s.append(P("Resíduo(t<sub>1</sub>) = FC<sub>wearable</sub>(t<sub>1</sub>) − FC<sub>prevista</sub>(t<sub>1</sub>)", formula))
    s.append(P(
        "Quando um novo hemograma é registrado em <i>observations</i>, FC<sub>pop</sub>(t<sub>1</sub>) é recalculado; o resíduo mede, "
        "portanto, a parte da mudança da FCR que <b>não</b> é explicada nem pelo sangue nem pelo perfil basal do indivíduo. "
        f"Na coorte saudável (N = {e2['N']:,}".replace(",", ".") + f"), a Etapa 1 isolada obteve R² = {f(e1['R2_cv'])} (EMA = {f(e1['MAE_cv'],1)} bpm) e "
        f"a combinação das duas etapas obteve R² = {f(e2['R2'])} (EMA = {f(e2['MAE'],2)} bpm). O resíduo apresentou média {f(rs['media'],2)} bpm, "
        f"desvio-padrão σ = {f(rs['dp'],2)} bpm e percentil 95 do valor absoluto de {f(rs['p95_abs'],2)} bpm (Figura 2C), valores que "
        "fundamentam os limiares de alerta."))

    s.append(P("3.2. Modelos Complementares Treinados no NHANES", h2))
    s.append(table([
        ["Modelo", "Entradas (X)", "Alvo (y)", "Conexão com o wearable"],
        ["Metabólico", "Sono (SLD012), sedentarismo (PAD680), pulso, IMC; versão expandida + idade e sexo",
         "HbA1c ≥ 5,7% (P_GHB); glicose ≥ 100 mg/dL (P_GLU)", "sleep_duration_hours, workout_minutes, resting_hr_bpm"],
        ["Apneia / hipóxia", "Hct, hemácias, Hb, IMC, PAS/PAD, idade, sexo",
         "Pausas respiratórias (SLQ040 ≥ 1) ou ronco frequente + sonolência (SLQ030 ≥ 2 e SLQ120 ≥ 3)", "spo2_avg_pct noturna e WASO como modificadores"],
        ["Inflamatório / autonômico", "PCR-us (P_HSCRP ≤ 20 mg/L), leucócitos, neutrófilos, IMC, idade, sexo",
         "Pulso de repouso e PAS (P_BPXO)", "Base para desvios de resting_hr_bpm, sbp_mmHg e hrv_rmssd_ms"],
        ["Cardio → sangue (triagem)", "Pulso, PAS/PAD, IMC, sono, sedentarismo, idade, sexo",
         "Anemia (OMS: Hb &lt; 13/12 g/dL); ferritina &lt; 30 ng/mL", "Sugere antecipação de hemograma"],
    ], [80, 145, 140, 122]))
    s.append(P("<b>Tabela 5.</b> Especificação dos modelos complementares.", cap))
    io = V["inflam_OLS_adultos_betas"]
    s.append(P(
        "No modelo inflamatório (adultos), a PCR-us associou-se a +" + f(io['LBXHSCRP'][0]) + " bpm por mg/L e os neutrófilos a +" +
        f(io['LBDNENO'][0]) + " bpm por 10<sup>3</sup>/µL (ambos p &lt; 10<sup>-13</sup>), confirmando a hipótese do Cluster B. No modelo "
        "metabólico, cada hora adicional de sono associou-se a menor chance de HbA1c ≥ 5,7% (OR = 0,955; p = 0,003) e cada kg/m² de IMC a "
        "maior chance (OR = 1,080; p &lt; 0,001). Dois modelos explorados durante o desenvolvimento foram <b>descartados</b>: a regressão "
        "contínua de TSH/T4 livre (R² entre 0,08 e 0,14; mais de 90% da coorte é eutireoidiana) e a estimativa contínua de ferritina a "
        "partir de sinais vitais (R² &lt; 0,10). A análise hormonal de 2011–2012 permanece apenas como achado exploratório "
        "(T3 livre: +2,37 bpm por pg/mL; testosterona total: −0,010 bpm por ng/dL)."))

    s.append(P("3.3. Desempenho Fora da Amostra", h2))
    rows = [["Modelo", "Métrica", "Painel (in-sample)", "Validação cruzada 5-fold", "Classificação de uso"]]
    rows += [
        ["FCR calibrada (Etapas 1 + 2)", "R² / EMA", "0,875 / 2,95 bpm", f"{f(e2['R2'])} / {f(e2['MAE'],2)} bpm", "Linha de base para detecção de anomalia"],
        ["FCR só sangue (Etapa 1)", "R² / EMA", "≈ 0,10", f"{f(e1['R2_cv'])} / {f(e1['MAE_cv'],1)} bpm", "Não utilizável isoladamente"],
        ["Metabólico expandido", "ROC-AUC", "0,842", f(V['metab_hba1c_expandido']['AUC_cv']), "Triagem (comparável a FINDRISC [9])"],
        ["Metabólico estrito (4 variáveis)", "ROC-AUC", "0,716", f(V['metab_hba1c_estrito']['AUC_cv']), "Fraco; usar só a versão expandida"],
        ["Glicose ≥ 100 (expandido)", "ROC-AUC", "—", f(V['metab_glicose_expandido']['AUC_cv']), "Triagem complementar"],
        ["HbA1c contínua", "R²", "0,400", f(V['metab_hba1c_continuo']['R2_cv']), "Não exibir valor estimado ao paciente"],
        ["Cardio → anemia", "ROC-AUC", "0,852", f(V['m1_anemia']['AUC_cv']), "Triagem moderada"],
        ["Cardio → ferritina &lt; 30", "ROC-AUC", "0,863", f(V['m1_ferritina_baixa']['AUC_cv']), "Triagem (dominado por sexo e idade)"],
        ["Apneia / hipóxia (sem SpO<sub>2</sub>)", "ROC-AUC", "0,773", f(V['apneia_HGB']['AUC_cv']), "Fraco sem sensor noturno"],
        ["Inflamatório → pulso", "R²", "0,371", f(V['inflam_pulso_HGB']['R2_cv']), "Contextual (coeficientes interpretáveis)"],
        ["Inflamatório → PAS", "R²", "0,542", f(V['inflam_PAS_HGB']['R2_cv']), "Contextual"],
    ]
    s.append(table(rows, [118, 52, 72, 92, 153]))
    s.append(P("<b>Tabela 6.</b> Comparação entre as métricas exibidas no painel (calculadas na amostra de treino) e as métricas "
               "fora da amostra recalculadas para este artigo.", cap))
    s += figure(os.path.join(ROOT, "figura3_3_desempenho_modelos_cv.png"),
                "<b>Figura 2:</b> (A) ROC-AUC dos classificadores no painel (cinza) e em validação cruzada (azul); a linha tracejada marca 0,70. "
                "(B) R² dos regressores no painel e fora da amostra. (C) Distribuição do resíduo da FCR na coorte saudável: a calibração "
                "individual estreita a distribuição e define a faixa de normalidade de ±1,5σ.")
    s.append(callout(
        "<b>Nota metodológica.</b> As métricas do painel interativo foram obtidas avaliando cada modelo nos mesmos dados usados para "
        "treiná-lo, o que superestima o desempenho dos modelos de <i>gradient boosting</i> (p. ex., apneia: 0,773 → "
        f"{f(V['apneia_HGB']['AUC_cv'])}; pulso inflamatório: 0,371 → {f(V['inflam_pulso_HGB']['R2_cv'])}). Os valores fora da amostra da "
        "Tabela 6 são os que devem orientar decisões de implantação, e o painel deve ser atualizado para exibi-los."))

    s.append(P("3.4. Métricas de Detecção em Produção", h2))
    s.append(P(
        "Sobre as séries diárias filtradas (Seção 2.3), três métricas complementares são calculadas para cada sinal x "
        "(FCR, HRV, SpO<sub>2</sub>, temperatura):"))
    s.append(P("Z<sub>t</sub> = ( x̄<sub>7d</sub>(t) − μ<sub>baseline</sub> ) / σ<sub>baseline</sub> ,   alerta se |Z<sub>t</sub>| ≥ 1,5", formula))
    s.append(P("Δ<sub>t</sub> = x̄<sub>7–14d</sub>(t) − x̄<sub>baseline (30–90d)</sub>        slope = β<sub>1</sub> em x = β<sub>0</sub> + β<sub>1</sub> · dia + ε", formula))
    s.append(P(
        "O <i>Z-score</i> individual compara o indivíduo com sua própria variabilidade (σ pessoal, não populacional); a diferença de médias "
        "móveis quantifica a magnitude clínica do desvio; e a inclinação da regressão linear sobre a janela distingue uma oscilação "
        "isolada de uma tendência sustentada. Um cluster é sinalizado apenas quando todos os seus componentes atingem o limiar na "
        "direção esperada. <b>Estado de implementação:</b> a versão atual da <i>WearableBridge</i> já calcula o baseline dos 7 primeiros "
        "dias, a média da janela de 7 ou 14 dias, Δ<sub>ind</sub> e o resíduo; o <i>Z-score</i>, o <i>slope</i> e os filtros "
        "comportamentais constituem a próxima etapa."))

    s.append(P("3.5. Camada de Inferência, Display e Trava Regulatória", h2))
    s += figure(os.path.join(ROOT, "figura3_1_arquitetura_inferencia_wearable.png"),
                "<b>Figura 3:</b> Arquitetura da camada de inferência. Dados do wearable e exames LOINC autorizados por consentimento ativo "
                "são mapeados para as variáveis NHANES, processados pelos modelos e convertidos em alertas contextuais determinísticos para o "
                "paciente e para o médico.")
    s.append(P(
        "A camada foi implementada no módulo <i>nhanes_explorer</i> (Flask, porta 5055) com os endpoints <i>POST /wearables/sync</i> "
        "(recebe a janela do wearable e devolve calibração, resíduos e escores), <i>GET /api/wearables/users</i>, "
        "<i>GET /api/wearables/user/&lt;id&gt;?days=14</i> e <i>GET /api/wearables/patient_labs</i> (lê os exames mais recentes de "
        "<i>open_health.db</i>). O resíduo autonômico é classificado em zonas:"))
    s.append(table([
        ["Zona", "Critério atual (resíduo)", "Texto ao paciente (determinístico)", "Briefing ao médico"],
        ["Verde", "|resíduo| ≤ 2,5 bpm", "Seu ritmo de repouso está dentro do esperado para você.", "Sem desvio"],
        ["Amarela", "+2,5 a +5,0 bpm", "Seu ritmo de repouso está um pouco acima do seu habitual. Sono e recuperação podem influenciar.", "Desvio leve; verificar filtros comportamentais"],
        ["Vermelha", "&gt; +5,0 bpm", "Notamos uma elevação persistente. Vale conversar com seu médico na próxima consulta.", "Desvio relevante; cruzar com Clusters A/B e exames"],
        ["Azul", "&lt; −5,0 bpm", "Seu ritmo de repouso está abaixo do seu habitual.", "Possível efeito de treino ou medicação"],
    ], [50, 92, 205, 140]))
    s.append(P("<b>Tabela 7.</b> Zonas do resíduo autonômico e saídas determinísticas.", cap))
    s.append(P(
        f"Como o desvio-padrão do resíduo em leitura única foi de {f(rs['dp'],2)} bpm, os limiares fixos de 2,5 e 5,0 bpm devem ser "
        "substituídos por limiares em unidades de σ individual (|Z| ≥ 1,5), estimado sobre médias de 7–14 dias, que possuem ruído menor "
        "que o de uma leitura isolada de consultório. No exemplo de demonstração (usuária U0001), FC<sub>pop</sub> = 72,5 bpm e "
        "FC<sub>0</sub> = 68,3 bpm resultaram em Δ<sub>ind</sub> = −4,2 bpm; a HbA1c estimada pelo modelo (5,43%) diferiu em −0,17 ponto "
        "percentual do laudo real (5,60%)."))
    s.append(P(
        "<b>Trava regulatória.</b> Assim como no módulo de exames (Parte II), nenhuma saída é gerada por texto livre: cada combinação "
        "(cluster, zona) aponta para um texto pré-redigido e revisado, de caráter educativo, que nunca nomeia doenças nem recomenda "
        "condutas. Ao médico, o <i>briefing</i> pré-consulta apresenta os desvios, os resíduos e os exames LOINC relacionados como "
        "<i>informação de contexto</i>, cabendo exclusivamente a ele a interpretação diagnóstica. Esse desenho mantém o módulo fora do "
        "escopo de diagnóstico automatizado (CFM e ANVISA RDC nº 657/2022) e restringe o tratamento de dados sensíveis às finalidades "
        "consentidas na tabela <i>consents</i> (LGPD, art. 11) [13]."))

    s.append(P("3.6. Extensão Proposta do Modelo de Dados", h2))
    s.append(P(
        "O banco <i>open_health.db</i> contém hoje as quatro tabelas da Parte I; os dados de wearable ainda são lidos de arquivo. Para "
        "persistência em produção, propõe-se a tabela <i>wearable_metrics</i> (recurso FHIR <i>Observation</i> de sinais vitais, "
        "categoria <i>vital-signs</i>) e a tabela <i>inference_results</i> para auditoria das saídas:"))
    s.append(table([
        ["Tabela proposta", "Atributos principais", "Restrições / Interoperabilidade"],
        ["wearable_metrics", "id (UUID PK), patient_id (FK), data (DATE), device_model, resting_hr_bpm, hrv_rmssd_ms, spo2_avg_pct, "
         "sleep_duration_hours, wake_after_sleep_onset_min, workout_minutes, alcohol_units, skin_temp_delta_c, created_at",
         "UNIQUE (patient_id, data, device_model); LOINC 40443-4 (FCR), 80404-7 (HRV), 59408-5 (SpO<sub>2</sub>); acesso condicionado a consents.escopo"],
        ["inference_results", "id (UUID PK), patient_id (FK), janela_inicio, janela_fim, modelo, versao_modelo, fc_pop, delta_ind, residuo, "
         "zona, cluster, texto_id, created_at", "Imutável (somente inserção); rastreabilidade da versão do modelo e do texto exibido"],
    ], [82, 235, 170]))
    s.append(P("<b>Tabela 8.</b> Extensão proposta do esquema relacional para o módulo de wearables.", cap))

    # ------------------------------------------------------------ 4. CONCLUSAO
    s.append(P("4. Conclusão", h1))
    s.append(P(
        "O trabalho estabeleceu uma ponte metodológica entre séries de wearable e o hemograma em uma arquitetura Open Health. Três "
        "conclusões principais emergem. Primeiro, não há equação determinística que derive a FCR do hemograma: o sangue, a idade, o "
        f"sexo e o IMC explicam cerca de {round(e1['R2_cv']*100)}% de sua variância, e a associação inversa entre hemoglobina e FCR não "
        "aparece em dados populacionais transversais. Segundo, a calibração individual em duas etapas transforma esse limite em "
        "método: ao comparar cada pessoa com o próprio \"marco zero\", o resíduo torna-se um sinal estreito "
        f"(σ ≈ {f(rs['dp'],1)} bpm) e adequado à detecção de mudanças. Terceiro, os modelos de triagem apresentam desempenho fora da "
        "amostra moderado (ROC-AUC entre 0,63 e 0,80), adequado para sugerir a antecipação de exames e contextualizar consultas, mas "
        "não para inferências diagnósticas."))
    s.append(P(
        "<b>Limitações.</b> (i) Os dados de wearable e de sangue provêm de populações distintas, e a ponte NHANES–wearable não foi "
        "validada em indivíduos com ambas as medidas; (ii) o conjunto de wearable aparenta ser sintético e não contém temperatura nem "
        "VO<sub>2</sub>máx; (iii) o NHANES é transversal, de modo que a Etapa 2 foi validada com leituras repetidas da mesma visita, e não "
        "com hemogramas seriados; (iv) os pesos amostrais complexos do NHANES não foram aplicados; (v) na versão atual, a "
        "<i>WearableBridge</i> usa coeficientes fixos para FC<sub>pop</sub> e HbA1c estimada, em vez de invocar os modelos serializados."))
    s.append(P(
        "<b>Próximos passos.</b> Substituir os coeficientes fixos pelos modelos treinados e versionados; implementar o <i>Z-score</i>, o "
        "<i>slope</i> e os filtros de treino e álcool; atualizar o painel para exibir métricas de validação cruzada; persistir as tabelas "
        "<i>wearable_metrics</i> e <i>inference_results</i>; e conduzir um estudo prospectivo com participantes que tenham wearable e "
        "hemogramas seriados, para validar a calibração individual em condições reais."))

    # ------------------------------------------------------------ REFERENCIAS
    s.append(P("Referências", h1))
    refs = [
        "[1] CENTERS FOR DISEASE CONTROL AND PREVENTION (CDC); NCHS. <i>National Health and Nutrition Examination Survey 2017–March 2020 Pre-pandemic Data Files</i>. Hyattsville, MD, 2021.",
        "[2] CDC; NCHS. <i>NHANES 2011–2012 Data Documentation, Codebook and Frequencies</i> (THYROD_G, TST_G, CBC_G, BPX_G). Hyattsville, MD, 2013.",
        "[3] HALL, J. E.; HALL, M. E. <i>Guyton and Hall Textbook of Medical Physiology</i>. 14. ed. Philadelphia: Elsevier, 2021.",
        "[4] SHAFFER, F.; GINSBERG, J. P. An Overview of Heart Rate Variability Metrics and Norms. <i>Frontiers in Public Health</i>, v. 5, p. 258, 2017.",
        "[5] JENSEN, M. T. et al. Elevated resting heart rate, physical fitness and all-cause mortality: a 16-year follow-up in the Copenhagen Male Study. <i>Heart</i>, v. 99, n. 12, p. 882–887, 2013.",
        "[6] RADIN, J. M. et al. Harnessing wearable device data to improve state-level real-time surveillance of influenza-like illness in the USA. <i>The Lancet Digital Health</i>, v. 2, n. 2, p. e85–e93, 2020.",
        "[7] MISHRA, T. et al. Pre-symptomatic detection of COVID-19 from smartwatch data. <i>Nature Biomedical Engineering</i>, v. 4, p. 1208–1220, 2020.",
        "[8] CHUNG, F. et al. STOP Questionnaire: a tool to screen patients for obstructive sleep apnea. <i>Anesthesiology</i>, v. 108, n. 5, p. 812–821, 2008.",
        "[9] LINDSTRÖM, J.; TUOMILEHTO, J. The Diabetes Risk Score: a practical tool to predict type 2 diabetes risk. <i>Diabetes Care</i>, v. 26, n. 3, p. 725–731, 2003.",
        "[10] AMERICAN DIABETES ASSOCIATION. Standards of Care in Diabetes — 2. Diagnosis and Classification of Diabetes. <i>Diabetes Care</i>, v. 47, supl. 1, 2024.",
        "[11] WORLD HEALTH ORGANIZATION. <i>Haemoglobin concentrations for the diagnosis of anaemia and assessment of severity</i>. Geneva: WHO, 2011.",
        "[12] COLLINS, G. S. et al. Transparent Reporting of a multivariable prediction model for Individual Prognosis or Diagnosis (TRIPOD). <i>Annals of Internal Medicine</i>, v. 162, n. 1, p. 55–63, 2015.",
        "[13] BRASIL. Lei nº 13.709/2018 (LGPD); ANVISA. RDC nº 657, de 24 de março de 2022 (Software como Dispositivo Médico); CFM. Resolução nº 2.314/2022 (Telemedicina).",
        "[14] PEDREGOSA, F. et al. Scikit-learn: Machine Learning in Python. <i>Journal of Machine Learning Research</i>, v. 12, p. 2825–2830, 2011.",
    ]
    for r in refs:
        s.append(P(r, ref))
    doc.build(s, canvasmaker=ScholarlyCanvas)
    return out_pdf


if __name__ == "__main__":
    print(build(os.path.join(ROOT, "Artigo_Tecnico_Wearables_Hemograma_NHANES.pdf")))
