"""Gera o Artigo Tecnico-Academico Final de Sintese do Projeto Open Health (Parte IV) com linguagem acessivel, didatica e foco central em Inferencia Causal."""
import os
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

ROOT = r"c:\Users\janna\Desktop\Hackathon LEPoli"
UP = "<font name='DVS'>↑</font>"
DN = "<font name='DVS'>↓</font>"
LR = "<font name='DVS'>↔</font>"
AR = "<font name='DVS'>→</font>"
RA = "<font name='DVS'>⇒</font>"
UR = "<font name='DVS'>↗</font>"
DR = "<font name='DVS'>↘</font>"


class CleanAcademicCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._states = []

    def showPage(self):
        self._states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._states)
        for s in self._states:
            self.__dict__.update(s)
            self.chrome(n)
            super().showPage()
        super().save()

    def chrome(self, n):
        self.saveState()
        w, h = A4
        l, r = 54, w - 54
        if self._pageNumber == 1:
            self.setStrokeColor(colors.HexColor("#0f172a"))
            self.setLineWidth(1.4)
            self.line(l, h - 36, r, h - 36)
            self.setLineWidth(0.4)
            self.line(l, h - 39, r, h - 39)
            self.setFont("TNR-Italic", 8.2)
            self.setFillColor(colors.HexColor("#334155"))
            self.drawString(l, h - 31, "PROJETO OPEN HEALTH BRASIL — SÍNTESE TÉCNICA E ARQUITETURAL")
            self.drawRightString(r, h - 31, "Artigo Final Consolidador — Novembro de 2026")
        else:
            self.setFont("TNR-Italic", 8.4)
            self.setFillColor(colors.HexColor("#1e293b"))
            self.drawString(l, h - 38, "Síntese do Projeto Open Health: Exames FHIR/LOINC, Modelos NHANES e Inferência Causal")
            self.setFont("TNR", 8.4)
            self.drawRightString(r, h - 38, "Desafio Rivio / LEPoli")
            self.setStrokeColor(colors.HexColor("#1e293b"))
            self.setLineWidth(0.5)
            self.line(l, h - 43, r, h - 43)

        self.setStrokeColor(colors.HexColor("#94a3b8"))
        self.setLineWidth(0.5)
        self.line(l, 44, r, 44)
        self.setFont("TNR-Italic", 8.0)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(l, 32, "Artigo Técnico Final | Exames de Sangue, Calibração Individual e Engenharia Causal em Wearables")
        self.setFont("TNR-Bold", 8.5)
        self.setFillColor(colors.HexColor("#0f172a"))
        self.drawRightString(r, 32, f"Página {self._pageNumber} de {n}")
        self.restoreState()


def booktabs(header_bg="#0f172a"):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (-1, 0), 1.2, colors.HexColor('#0f172a')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.0, colors.HexColor('#0f172a')),
        ('LINEBELOW', (0, 1), (-1, -2), 0.35, colors.HexColor('#cbd5e1')),
        ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor('#0f172a')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])


ss = getSampleStyleSheet()
def S(name, **kw):
    parent = kw.pop('parent', ss['Normal'])
    return ParagraphStyle(name, parent=parent, **kw)

kicker = S('k', fontName='TNR-Bold', fontSize=9.2, leading=12.5, textColor=colors.HexColor('#1e3a8a'), alignment=1, spaceAfter=4)
title = S('t', fontName='TNR-Bold', fontSize=15.5, leading=20.0, textColor=colors.HexColor('#0f172a'), alignment=1, spaceAfter=6)
subtitle = S('st', fontName='TNR-Italic', fontSize=10.5, leading=14.2, textColor=colors.HexColor('#334155'), alignment=1, spaceAfter=8)
author = S('au', fontName='TNR-Bold', fontSize=9.5, leading=13.0, alignment=1, spaceAfter=2)
affil = S('af', fontName='TNR-Italic', fontSize=8.5, leading=11.5, textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=10)
absx = S('ab', fontName='TNR', fontSize=8.8, leading=12.8, textColor=colors.HexColor('#1e293b'), alignment=4)
h1 = S('h1', fontName='TNR-Bold', fontSize=12.0, leading=15.5, textColor=colors.HexColor('#0f172a'), spaceBefore=11, spaceAfter=4.5, keepWithNext=True)
h2 = S('h2', fontName='TNR-BoldItalic', fontSize=10.3, leading=13.6, textColor=colors.HexColor('#1e3a8a'), spaceBefore=8, spaceAfter=3.8, keepWithNext=True)
body = S('b', fontName='TNR', fontSize=9.6, leading=13.8, textColor=colors.HexColor('#1e293b'), alignment=4, firstLineIndent=15, spaceAfter=4.5)
bullet = S('bl', fontName='TNR', fontSize=9.3, leading=13.3, textColor=colors.HexColor('#1e293b'), alignment=4, leftIndent=15, firstLineIndent=-10, spaceAfter=3.8)
formula = S('fo', fontName='TNR-Italic', fontSize=9.8, leading=14.5, textColor=colors.HexColor('#0f172a'), alignment=1, spaceBefore=3.5, spaceAfter=5.5)
th = S('th', fontName='TNR-Bold', fontSize=8.1, leading=10.5, textColor=colors.white)
td = S('td', fontName='TNR', fontSize=8.0, leading=10.8, textColor=colors.HexColor('#0f172a'))
tdb = S('tdb', parent=td, fontName='TNR-Bold')
cap = S('cap', fontName='TNR', fontSize=8.4, leading=11.6, textColor=colors.HexColor('#334155'), alignment=4, spaceBefore=4.0, spaceAfter=7.0)
ref = S('ref', fontName='TNR', fontSize=8.2, leading=11.2, alignment=4, leftIndent=16, firstLineIndent=-16, spaceAfter=3.0)
note = S('note', fontName='TNR', fontSize=9.0, leading=13.0, textColor=colors.HexColor('#7c2d12'), alignment=4)

P = lambda t, s=body: Paragraph(t, s)


def table(rows, widths, bold_first=True, header_bg="#0f172a"):
    data = [[Paragraph(c, th) for c in rows[0]]]
    for r in rows[1:]:
        data.append([Paragraph(c, tdb if (i == 0 and bold_first) else td) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(booktabs(header_bg))
    return t


def figure(path, caption, width=487, max_h=245):
    if not os.path.exists(path):
        return []
    w, h = PILImage.open(path).size
    iw = width - 6
    ih = iw * h / w
    if ih > max_h:
        ih = max_h
        iw = ih * w / h
    img = Image(path, width=iw, height=ih)
    t = Table([[img]], colWidths=[width])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return [KeepTogether([t, Paragraph(caption, cap)])]


def callout(text, bg='#fff7ed', border='#c2410c'):
    t = Table([[Paragraph(text, note)]], colWidths=[487])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg)),
        ('LINEBEFORE', (0, 0), (0, -1), 3.0, colors.HexColor(border)),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return t


def build(out_pdf):
    doc = SimpleDocTemplate(
        out_pdf, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=50, bottomMargin=52,
        title="Artigo Final - Sintese Completa e Inferencia Causal Open Health", author="Equipe Open Health LEPoli"
    )
    s = []

    # =========================================================================
    # CAPA E RESUMO ACESSÍVEL
    # =========================================================================
    s.append(P("ARTIGO TÉCNICO FINAL — SÍNTESE COMPLETA DO PROJETO OPEN HEALTH", kicker))
    s.append(P(
        "Como Exames de Sangue (HL7 FHIR / LOINC), Modelos Populacionais (CDC NHANES) e "
        "Inferência Causal em Smartwatches se Complementam em um Único Sistema de Saúde", title
    ))
    s.append(P(
        "Detalhamento técnico e didático do funcionamento ponta a ponta da plataforma, com ênfase no isolamento "
        "de fatores de confusão comportamentais (DAGs) para eliminar falsos alarmes clínicos", subtitle
    ))
    s.append(P("Equipe de Engenharia de Dados e Informática Médica — Projeto Open Health LEPoli", author))
    s.append(P("Escola Politécnica / Hackathon Gama House &amp; LEPoli — Desafio Rivio | São Paulo, 10 de novembro de 2026", affil))

    resumo_html = (
        "<b>RESUMO EXECUTIVO:</b> Este documento apresenta a visão integrada e acessível de tudo o que foi construído no projeto "
        "<b>Open Health Brasil</b>. O problema central que resolvemos é simples de entender, mas complexo de implementar: "
        "<b>exames de sangue</b> são extremamente precisos, porém funcionam como fotografias tiradas apenas uma ou duas vezes por ano; "
        "já os <b>relógios inteligentes (<i>wearables</i>)</b> filmam o corpo todos os dias, mas qualquer hábito comum (dormir tarde, "
        "caminhar pouco, tomar café, usar celular à noite ou beber álcool) altera os sensores do relógio exatamente da mesma forma que "
        "uma doença real (como diabetes, infecção ou anemia). Para resolver esse impasse, construímos uma arquitetura em <b>quatro "
        "etapas que se completam</b>: (1) um <b>Banco de Dados de Exames de Sangue</b> padronizado (HL7 FHIR, LOINC e LGPD) que extrai "
        "automaticamente laudos em PDF; (2) um <b>Motor de Classificação por Cores e Textos Determinísticos</b> (565 explicações "
        "pré-validadas, sem risco de alucinação de IA) que mostra a evolução dos exames no tempo; (3) uma <b>Ponte Estatística treinada "
        "no CDC NHANES</b> (15.560 pessoas) com <b>Calibração pelo \"Marco Zero\" individual</b>, que reduz o erro de previsão do "
        "batimento cardíaco de 8,32 bpm para <b>3,02 bpm (R² = 0,864)</b>; e (4) uma camada central de <b>Inferência Causal em 3 Camadas "
        "(DAGs)</b> testada em <b>55.200 registros diários de 300 pacientes</b>, capaz de filtrar entre <b>56,1% e 97,4% de falsos "
        "positivos</b> causados por hábitos do dia a dia nos quatro alvos clínicos do estudo (Sono Profundo, Glicose/HbA1c, Inflamação "
        "PCR-us e Anemia/Ferritina).<br/><br/>"
        "<b>Palavras-chave:</b> Open Health; Inferência Causal; Fatores de Confusão; Exames de Sangue LOINC; CDC NHANES; Wearables; LGPD."
    )
    ta = Table([[P(resumo_html, absx)]], colWidths=[487])
    ta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    s += [ta, Spacer(1, 6)]

    # =========================================================================
    # 1. COMO TUDO SE CONECTA: A LÓGICA DE COMPLEMENTARIDADE DO PROJETO
    # =========================================================================
    s.append(P("1. Visão Geral: Por que as 4 Partes do Projeto Precisam umas das Outras?", h1))
    s.append(P(
        "Para entender o funcionamento do nosso projeto, vale pensar em como um médico acompanha um paciente na vida real. "
        "Quando o paciente faz um exame de sangue no laboratório, o resultado é certeiro: sabemos exatamente quanto ele tem de "
        "hemoglobina, ferritina, glicose ou proteína inflamatória (PCR). Porém, depois que ele sai do laboratório, abre-se uma "
        "\"janela cega\" de 6 a 12 meses até o próximo check-up. Nesse intervalo, o único instrumento que acompanha o paciente "
        "todos os dias é o seu smartwatch."
    ))
    s.append(P(
        "O grande desafio técnico é que <b>não basta juntar o PDF do exame de sangue com o gráfico do relógio</b>. Se fizermos isso "
        "de forma direta e ingênua, três problemas graves acontecem: (1) cada laboratório escreve o exame com um nome e unidade "
        "diferentes; (2) cada ser humano tem um coração diferente (um atleta tem batimento de 48 bpm e um sedentário tem 78 bpm, "
        "mesmo com exames de sangue idênticos); e (3) os sensores do relógio reagem a qualquer mudança de rotina (um dia sem caminhar, "
        "duas xícaras extras de café ou uma taça de vinho parecem, para um algoritmo comum, um princípio de doença). "
        "Por isso, cada uma das quatro etapas construídas no projeto resolve exatamente a limitação da etapa anterior (<b>Figura 1</b>):"
    ))

    s += figure(
        os.path.join(ROOT, "figura4_1_arquitetura_complementar_4_modulos.png"),
        "<b>Figura 1:</b> Arquitetura completa do projeto mostrando como as 4 etapas funcionam em ciclo fechado. As Etapas 1 e 2 "
        "padronizam e explicam os exames de sangue (porta :5000); a Etapa 3 calibra a linha de base de cada pessoa usando o CDC NHANES "
        "(porta :5055); e a Etapa 4 aplica Inferência Causal nos dados diários do smartwatch (porta :5050) para filtrar hábitos antes de alertar o médico.",
        max_h=260
    )

    s.append(table([
        ["Etapa do Projeto", "Qual problema ela resolve?", "Como ela funciona na prática?", "Como ela ajuda as outras etapas?"],
        ["Etapa 1 — Banco de Dados de Exames (FHIR / LOINC / LGPD)",
         "Exames vêm espalhados em PDFs de laboratórios diferentes e sem padrão único.",
         "Lê o PDF (via IA ou modo offline), converte cada exame para o código internacional LOINC e salva em 4 tabelas SQL seguras.",
         "Entrega os valores reais de sangue para a Etapa 2 mostrar ao paciente e para as Etapas 3 e 4 calibrarem os modelos."],
        ["Etapa 2 — Gradiente de Cores & 565 Textos Determinísticos",
         "Pacientes não entendem números técnicos e IAs generativas podem inventar diagnósticos (alucinar).",
         f"Transforma qualquer exame em uma régua de 0 a 100% com 4 cores seguras, setas de tendência ({UR}/{DR}) e 565 textos pré-revisados.",
         "Recebe da Etapa 4 os alertas de quando um exame precisa ser repetido e exibe a linha do tempo para o paciente e o médico."],
        ["Etapa 3 — Modelos NHANES & Calibração 'Marco Zero'",
         "Não existe fórmula única que preveja o batimento cardíaco só pelo sangue (erro alto de ±8,3 bpm).",
         "Usa dados de 15.560 pessoas (NHANES) somados à 1ª semana do relógio do usuário (Δ<sub>ind</sub>), baixando o erro para 3,02 bpm.",
         "Transforma os dados do relógio em uma expectativa individualizada de pulso, glicose/HbA1c, apneia e inflamação."],
        ["Etapa 4 — Inferência Causal em 3 Camadas no Wearable",
         "O relógio confunde efeitos de hábitos (café, álcool, tela, poucos passos) com doenças reais.",
         "Analisa 55.200 dias de 300 pacientes e desconta o efeito dos hábitos do dia a dia antes de culpar o metabolismo ou o sangue.",
         "Filtra de 56,1% a 97,4% de falsos alarmes, garantindo que só desvios reais cheguem à Etapa 3 e ao médico na Etapa 2."],
    ], [105, 115, 137, 130]))
    s.append(P("<b>Tabela 1.</b> Síntese didática de como as quatro partes do projeto trabalham juntas.", cap))

    # =========================================================================
    # 2. ÊNFASE CENTRAL: ENGENHARIA CAUSAL E ISOLAMENTO DE FATORES DE CONFUSÃO
    # =========================================================================
    s.append(P("2. O Coração Inteligente do Protótipo: Inferência Causal e Filtro de Hábitos nos 4 Alvos Clínicos", h1))
    s.append(P("2.1. Por que Modelos Comuns Erram tanto com Dados de Smartwatch? (O Viés de Confusão)", h2))
    s.append(P(
        "A inovação mais importante que implementamos hoje no protótipo (ativa em <i>Dataset Wearables/app_wearables.py</i>, na porta "
        "<i>:5050</i>) é a <b>Engenharia Causal</b>. Na medicina e na ciência de dados, quando tentamos ligar um sinal do relógio "
        "diretamente a um exame de sangue — por exemplo, ver que o <i>sono profundo caiu</i> ou que o <i>batimento em repouso subiu</i> "
        "e concluir imediatamente que a pessoa está desenvolvendo diabetes ou uma infecção —, cometemos um erro clássico chamado "
        "<b>viés de confusão (<i>confounding bias</i>)</b>."
    ))
    s.append(P(
        "Isso acontece porque o corpo humano não reage apenas a doenças; ele reage fortemente ao nosso comportamento das últimas "
        "24 horas. Ao analisarmos matematicamente todos os <b>325 pares possíveis de correlação e covariância</b> dentro da nossa base "
        "de <b>55.200 registros diários</b> (300 pacientes acompanhados durante 184 dias completos, com 33 variáveis medidas por dia), "
        "comprovamos que os dados funcionam em uma <b>cadeia causal de três camadas (Grafo Acíclico Direcionado — DAG)</b>:"
    ))
    s.append(P(
        f"Camada 1 (Hábitos do Dia a Dia)   {AR}   Camada 2 (Alteração nos Sensores do Relógio)   {AR}   Camada 3 (Suspeita Clínica / Exame de Sangue)",
        formula
    ))
    s.append(P(
        "Em termos simples: os hábitos da <b>Camada 1</b> (caminhar pouco, beber álcool, tomar muito café, ficar no celular à noite ou "
        "dormir poucas horas) empurram os sensores da <b>Camada 2</b> (sono profundo, batimento cardíaco e variabilidade cardíaca HRV). "
        "Se o sistema não enxergar a Camada 1 e não \"descontar\" matematicamente o efeito desses hábitos, ele vai disparar falsos "
        "alarmes médicos na <b>Camada 3</b> o tempo inteiro (<b>Figura 2</b>)."
    ))

    s += figure(
        os.path.join(ROOT, "figura4_2_dag_causal_e_mitigacao_55200.png"),
        "<b>Figura 2:</b> Diagrama Causal em 3 Camadas implementado no protótipo. Antes de relacionar qualquer queda de sono profundo, "
        "subida de frequência cardíaca ou queda de HRV (Camada 2) aos quatro alvos clínicos e exames LOINC (Camada 3), o algoritmo mede e "
        "desconta o impacto direto dos hábitos cotidianos (Camada 1).",
        max_h=220
    )

    s.append(P("2.2. Como o Filtro Causal Funciona nos 4 Alvos Clínicos Previstos pelo Estudo", h2))
    s.append(P(
        "Abaixo explicamos, de forma clara e com os números exatos medidos nos 55.200 dias do dataset, como desenhamos e implementamos "
        "a proteção contra falsos alarmes para cada uma das <b>quatro variáveis clínicas</b> que o nosso sistema monitora:"
    ))

    s.append(P(
        "• <b>Alvo Clínico 1 — Queda do Sono Profundo (N3 &lt; 16%) explicada pelo Volume de Passos e pelo Álcool:</b><br/>"
        "<i>O que um sistema comum faria de errado:</i> Ao ver que o paciente teve menos de 16% de sono profundo reparador (estágio N3), "
        "um aplicativo comum sugeriria insônia primária, alteração hormonal ou descontrole da glicose noturna.<br/>"
        "<i>O que descobrimos nos dados:</i> O sono profundo tem uma correlação positiva fortíssima com a quantidade de passos dados no "
        "dia (<b>r = +0,766; covariância = +209,2</b>). Fisiologicamente, o cérebro precisa acumular <i>adenosina</i> (gerada pelo "
        "esforço muscular de caminhar e se mover durante o dia) para criar a chamada \"pressão homeostática de sono\" à noite. Quando a "
        "pessoa passa o dia sentada (&lt; 6.500 passos), o sono profundo cai mecanicamente. Além disso, o consumo de álcool aumenta os "
        "despertares noturnos WASO (<b>r = +0,296</b>) e destrói a arquitetura do sono.<br/>"
        "<i>Como o nosso algoritmo mitiga:</i> Nos <b>14.553 dias</b> em que houve queda de sono profundo na base, o nosso motor "
        "identificou que <b>11.211 dias (77,0%)</b> aconteceram justamente em dias de poucos passos (8.996 dias) ou consumo de álcool "
        "(5.632 dias). Por isso, o sistema calcula o <i>Sono Profundo Esperado pelo Movimento</i>: se a pessoa dormiu mal porque "
        "caminhou pouco, o sistema não fala em doença nem pede exame de sangue; ele orienta primeiro atingir <b>8.000 passos/dia por "
        "14 dias</b>.", bullet
    ))

    s.append(P(
        "• <b>Alvo Clínico 2 — Risco Metabólico (Glicose e HbA1c) confundido por Tempo de Tela Noturno e Cafeína:</b><br/>"
        "<i>O que um sistema comum faria de errado:</i> Como pessoas com resistência à insulina e pré-diabetes (HbA1c ≥ 5,7%, código "
        "LOINC <i>4548-4</i>) costumam ter frequência cardíaca de repouso mais alta (≥ 72 bpm), um modelo direto recomendaria exames "
        "de glicemia sempre que o batimento basal subisse.<br/>"
        "<i>O que descobrimos nos dados:</i> Ficar mais de 130 minutos em frente a telas à noite aumenta o nível de estresse "
        "(<b>r = +0,311</b>) e atrasa o início do sono em +22 minutos (<b>r = +0,278</b>), enquanto tomar mais de 80 mg de cafeína "
        "aciona adrenalina e eleva o estresse e o batimento basal (<b>r = +0,305</b>). Na nossa base, de <b>9.893 dias</b> com FC de "
        "repouso elevada (≥ 72 bpm), impressionantes <b>9.633 dias (97,4%)</b> ocorreram em dias de excesso de tela ou cafeína!<br/>"
        "<i>Como o nosso algoritmo mitiga:</i> Criamos um <b>Filtro de Janela Móvel de 14 a 21 dias</b>. O sistema bloqueia qualquer "
        "alerta metabólico se a subida do batimento vier acompanhada de picos de cafeína ou tela. Ele só sugere checar Glicose e HbA1c "
        "nos <b>2,6% de casos residuais</b> em que o coração continua acelerado mesmo com rotina limpa e sono regular.", bullet
    ))

    s.append(P(
        "• <b>Alvo Clínico 3 — Inflamação Sistêmica (PCR-us) confundida por Noite Mal Dormida (&lt; 6h) e Ressaca Autonômica:</b><br/>"
        "<i>O que um sistema comum faria de errado:</i> Quando o corpo enfrenta uma infecção ou inflamação (aumento de PCR-us, LOINC "
        "<i>30522-7</i>, e leucócitos, LOINC <i>6690-2</i>), a variabilidade da frequência cardíaca (HRV RMSSD) despenca para menos de "
        "38 ms. Um modelo sem filtro acusaria inflamação a cada queda da HRV.<br/>"
        "<i>O que descobrimos nos dados:</i> A duração do sono tem relação direta com a HRV do dia seguinte (<b>r = +0,287</b> — dormir "
        "menos de 6 horas derruba a HRV em até 35% na manhã seguinte), e o álcool reduz imediatamente a HRV (<b>r = −0,163</b>). Dos "
        "<b>21.028 dias</b> com HRV baixa (&lt; 38 ms) no dataset, <b>11.803 dias (56,1%)</b> foram causados simplesmente por uma noite "
        "curta de sono ou bebida alcoólica na véspera.<br/>"
        "<i>Como o nosso algoritmo mitiga:</i> Implementamos a <b>Regra de Persistência de 4 Dias Consecutivos</b>. Quedas de HRV que "
        "duram 1 a 3 dias após uma noite curta ou festa são classificadas como fadiga passageira (que se resolve com uma noite de 7,5 h "
        "de sono). O sistema só sugere dosar PCR-us no sangue se a HRV ficar reprimida (Z-score ≤ −1,5σ) por mais de 4 dias seguidos em "
        "noites bem dormidas e sem álcool.", bullet
    ))

    s.append(P(
        "• <b>Alvo Clínico 4 — Triagem de Anemia e Falta de Ferro (Hemoglobina e Ferritina) confundida por Sedentarismo e Estimulantes:</b><br/>"
        "<i>O que um sistema comum faria de errado:</i> Na anemia (Hemoglobina baixa, LOINC <i>718-7</i>) ou na falta de estoque de "
        "ferro (Ferritina &lt; 30 ng/mL, LOINC <i>2276-4</i>), o coração precisa bater mais rápido durante o dia (&gt; 92 bpm) mesmo "
        "quando a pessoa anda pouco (&lt; 6.000 passos), para compensar a falta de oxigênio no sangue.<br/>"
        "<i>O que descobrimos nos dados:</i> Uma pessoa sedentária (fora de forma) ou que tomou termogênico/cafeína alta (&gt; 90 mg) "
        "apresenta exatamente esse mesmo batimento diurno alto sem ter anemia! Dos <b>3.834 dias</b> com esse padrão na base, "
        "<b>2.701 dias (70,4%)</b> tinham consumo elevado de cafeína.<br/>"
        "<i>Como o nosso algoritmo mitiga:</i> Criamos o <b>Índice de Carga Diurna Normalizado</b>, dado por "
        "<i>ICD = FC_diurna / ln(passos + 1)</i>, e conectamos esse índice diretamente ao <b>Banco de Dados de Sangue da Etapa 1 "
        "(Ancoragem Retrospectiva FHIR)</b>. O sistema olha o último exame de sangue salvo no banco: se a paciente já tinha ferritina "
        "normal e tomou muita cafeína, o alarme é cancelado; se a ferritina anterior já estava na borda baixa (Amarela) e o ICD subiu "
        "sem cafeína, o sistema recomenda adiantar o hemograma.", bullet
    ))

    s += figure(
        os.path.join(ROOT, "figura4_3_impacto_mitigacao_55200.png"),
        "<b>Figura 3:</b> Resultado prático do motor causal sobre os 55.200 registros diários. As barras verdes mostram a enorme fatia "
        "de alertas (56,1% a 97,4%) que seriam falsos positivos se o sistema não filtrasse os hábitos cotidianos; as barras vermelhas "
        "mostram os casos residuais genuínos que realmente justificam atenção clínica ou exame de sangue.",
        max_h=190
    )

    s.append(table([
        ["Alvo Clínico Previsto", "O que parece no Relógio (Camada 2)", "O que na verdade causou (Hábito / Camada 1)", "Falsos Alarmes Evitados (55.200 d)", "Regra Inteligente Aplicada pelo Protótipo"],
        ["1. Sono Profundo (N3 &lt; 16%)",
         "Pouco sono reparador à noite",
         "Dia sedentário (&lt;6.500 passos, r=+0,766) ou álcool (WASO r=+0,296)",
         "<b>77,0%</b><br/>(11.211 de 14.553 dias)",
         "Desconta os passos do dia; prescreve caminhar 8.000 passos/dia por 14 dias antes de suspeitar de distúrbio."],
        ["2. Risco Metabólico (Glicose / HbA1c)",
         "Batimento de repouso alto (≥ 72 bpm)",
         "Excesso de tela à noite (&gt;130 min, r=+0,311) ou cafeína (&gt;80 mg, r=+0,305)",
         "<b>97,4%</b><br/>(9.633 de 9.893 dias)",
         "Exige janela móvel de 14 a 21 dias sem abuso de tela/cafeína antes de sugerir exame de HbA1c."],
        ["3. Inflamação (PCR-us / Leucócitos)",
         "Queda brusca da HRV (&lt; 38 ms)",
         "Dormir pouco (&lt;6,0 h, r=+0,287) ou bebida alcoólica (r=−0,163)",
         "<b>56,1%</b><br/>(11.803 de 21.028 dias)",
         "Regra dos 4 dias seguidos: ignora quedas de 1–3 dias pós-insônia/álcool; só alerta se persistir ≥ 4 dias."],
        ["4. Triagem de Anemia (Hb / Ferritina)",
         "FC diurna &gt; 92 bpm com &lt; 6.000 passos",
         "Falta de condicionamento físico ou cafeína alta (&gt;90 mg)",
         "<b>70,4%</b><br/>(2.701 de 3.834 dias)",
         "Calcula o índice ICD = FC_dia / ln(passos+1) e consulta a ferritina anterior no banco de sangue FHIR."],
    ], [85, 88, 110, 82, 122]))
    s.append(P("<b>Tabela 2.</b> Resumo claro das 4 variáveis previstas, seus confundidores indiretos e como o protótipo mitiga cada caso.", cap))

    # =========================================================================
    # 3. ETAPA 3 DO PROJETO: OS MODELOS TREINADOS NO NHANES E O "MARCO ZERO"
    # =========================================================================
    s.append(P("3. Como o Relógio Conversa com o Sangue: Base CDC NHANES e Calibração pelo 'Marco Zero'", h1))
    s.append(P(
        "Depois que o filtro causal (Seção 2) limpa os ruídos dos hábitos diários, os sinais limpos do smartwatch entram na nossa "
        "camada de inteligência estatística (<i>nhanes_explorer</i>, rodando na porta <i>:5055</i>). Aqui respondemos a duas perguntas "
        "fundamentais do estudo:"
    ))
    s.append(P("3.1. Por que não Existe uma Fórmula Única Universal entre Hemograma e Batimento Cardíaco?", h2))
    s.append(P(
        "Pela física da circulação sanguínea (<b>Princípio de Fick</b>), a quantidade de oxigênio entregue aos órgãos (DO<sub>2</sub>) "
        "depende do batimento cardíaco (FC), do volume de sangue bombeado a cada batida (Volume Sistólico — VS) e da quantidade de "
        "hemoglobina no sangue ([Hb]):"
    ))
    s.append(P("Oferta de O<sub>2</sub> (DO<sub>2</sub>) = FC × Volume Sistólico (VS) × ( 1,34 × [Hemoglobina] × SaO<sub>2</sub> )", formula))
    s.append(P(
        "Quando a hemoglobina cai (anemia), o coração precisa bater mais rápido para compensar — em média, cada 1 g/dL a menos de "
        "hemoglobina acelera o pulso entre 1 e 3 bpm. Porém, <b>de uma pessoa para outra, o tamanho do coração (Volume Sistólico) e o "
        "condicionamento físico mudam completamente o batimento basal</b>. Testamos isso na prática unificando, pelo código de "
        "identificação <i>SEQN</i>, <b>15.560 participantes reais do CDC NHANES (ciclo 2017–2020)</b> e <b>1.846 participantes com "
        "exames hormonais de tireoide e testosterona (ciclo 2011–2012)</b>: um modelo de Machine Learning que tenta adivinhar o "
        "batimento cardíaco olhando <i>apenas</i> para o sangue, idade, sexo e IMC consegue explicar apenas <b>12,9% da variação "
        "(R²<sub>CV</sub> = 0,129)</b>, errando em média <b>±8,32 bpm</b>."
    ))

    s.append(P("3.2. A Solução: Calibração Individual em 2 Etapas (O 'Marco Zero' do Paciente)", h2))
    s.append(P(
        "Se colocarmos a 1ª medição de pulso da pessoa diretamente junto com o hemograma durante o treino do modelo, o algoritmo fica "
        "\"preguiçoso\" e dá 99% do peso para o pulso inicial, ignorando o sangue. Para resolver isso de forma limpa, dividimos o "
        "modelo principal em <b>duas etapas separadas</b>:"
    ))
    s.append(P(
        "• <b>1ª Etapa — Previsão Populacional pelo Sangue (FC<sub>pop</sub>):</b> O modelo (<i>Gradient Boosting / Random Forest</i>) "
        "aprende no NHANES qual seria o batimento médio esperado para alguém com aquela hemoglobina, hematócrito, leucócitos, "
        "plaquetas, idade, sexo e IMC.", bullet
    ))
    s.append(P(
        "• <b>2ª Etapa — Calibração pelo \"Marco Zero\" Individual (Δ<sub>ind</sub>):</b> Nos primeiros 7 dias em que o usuário usa o "
        "smartwatch em estado saudável (FC<sub>0</sub>), medimos a diferença fixa do coração dele em relação à média da população: "
        "<b>Δ<sub>ind</sub> = FC<sub>0</sub> − FC<sub>pop</sub>(t<sub>0</sub>)</b>. A partir daí, sabemos exatamente qual é o batimento "
        "esperado para <i>aquela pessoa específica</i>: <b>FC<sub>esperada</sub>(t<sub>1</sub>) = FC<sub>pop</sub>(t<sub>1</sub>) + "
        "Δ<sub>ind</sub></b>. Com essa calibração, a precisão salta de 12,9% para <b>86,4% (R² = 0,864)</b> e o erro médio cai para "
        "apenas <b>3,02 bpm</b>!", bullet
    ))
    s.append(P(
        "Além do modelo principal de frequência cardíaca, treinamos no NHANES três modelos complementares que conversam com o relógio: "
        "(1) o <b>Modelo Metabólico</b> (usa sono, atividade, pulso e IMC para estimar risco de Glicose ≥ 100 mg/dL e HbA1c ≥ 5,7%, "
        "atingindo <b>ROC-AUC = 0,801</b> em validação cruzada e provando que cada 1 hora a mais de sono reduz o risco de alteração "
        "glicêmica em −4,5%, OR = 0,955); (2) o <b>Modelo de Apneia e Hipóxia Noturna</b> (cruza hematócrito e hemácias elevados com "
        "IMC, pressão arterial e quedas de SpO<sub>2</sub> noturna do relógio); e (3) o <b>Modelo Inflamatório</b> (mostra que cada "
        "+1 mg/L de PCR-us no sangue eleva o pulso em +0,37 bpm e cada +1.000 neutrófilos elevam o pulso em +1,29 bpm)."
    ))

    # =========================================================================
    # 4. ETAPAS 1 E 2 DO PROJETO: EXAMES DE SANGUE, GRADIENTE E TEXTOS SEGUROS
    # =========================================================================
    s.append(P("4. A Base de Tudo: Banco de Dados de Exames (FHIR/LOINC), Régua de Cores e Textos Seguros", h1))
    s.append(P(
        "Para que a calibração individual (Seção 3) e a ancoragem causal (Seção 2) funcionem, os exames de sangue do paciente precisam "
        "estar organizados em um banco de dados confiável e fácil de visualizar (implementado em <i>Etapa Exames de Sangue/app.py</i>, "
        "na porta <i>:5000</i>). Essa base funciona em três pilares:"
    ))
    s.append(P(
        "1. <b>Leitura Automática de PDFs e 4 Tabelas Normalizadas (HL7 FHIR BR Core, LOINC e LGPD):</b> Quando o paciente faz upload "
        "de um PDF de exame de sangue (seja do Fleury, Delboni ou Hospital das Clínicas), nosso extrator híbrido (que funciona tanto "
        "online com <i>Gemini 2.5 Flash</i> quanto 100% offline com <i>pdfplumber</i> e <i>Qwen 2.5</i>) identifica mais de 113 tipos "
        "de exames, atribui o código internacional <b>LOINC</b> e a unidade <b>UCUM</b>, e salva tudo em 4 tabelas SQL: "
        "<b><i>patients</i></b> (dados do paciente), <b><i>diagnostic_reports</i></b> (cabeçalho do laudo com hash SHA-256 estilo "
        "ICP-Brasil), <b><i>observations</i></b> (tabela vertical onde cada exame ocupa uma linha, evitando espaços vazios e aceitando "
        "qualquer exame novo sem mudar o banco) e <b><i>consents</i></b> (controle de consentimento ativo ou revogado exigido pela LGPD).", bullet
    ))
    s.append(P(
        "2. <b>Régua Matemática de 4 Cores e Setas de Tendência:</b> Como cada exame tem números muito diferentes (a creatinina vai de "
        "0,6 a 1,2, enquanto as plaquetas vão de 150.000 a 450.000), criamos uma fórmula que calcula a largura da faixa normal "
        "(<i>L = máximo − mínimo</i>) e mede em que porcentagem da faixa o paciente está. Com base em três diretrizes médicas oficiais "
        "(<b>CLSI EP28-A3c</b>, <b>NCI CTCAE v5.0</b> e <b>Valores Críticos CAP</b>), classificamos qualquer exame em 4 níveis visuais "
        "fáceis de entender e sem palavras assustadoras: <b>Verde (Normal, 10% a 90% da faixa)</b>, <b>Amarelo (Atenção/Leve, nas "
        "bordas internas &lt;10% ou &gt;90% ou até 15% fora)</b>, <b>Laranja (Moderado, 15% a 50% fora)</b> e <b>Vermelho (Alteração "
        f"Acentuada, &gt;50% fora)</b>. Além disso, se um exame variar mais de 20% em relação à coleta anterior rumo à borda, aparece "
        f"uma seta de tendência ({UR} ou {DR}) avisando precocemente.", bullet
    ))
    s.append(P(
        "3. <b>565 Textos Determinísticos Pré-Prontos e Gráficos no Tempo:</b> Em vez de pedir para uma IA inventar uma explicação na "
        "hora (o que demora e corre o risco de gerar um diagnóstico errado), deixamos prontos <b>565 textos educativos revisados</b> "
        "(113 exames × 5 situações clínicas), que carregam em menos de 1 milissegundo, explicam para que serve o exame e sugerem "
        "perguntas para fazer ao médico, junto com gráficos que unem exames de diferentes laboratórios na mesma linha do tempo.", bullet
    ))

    # =========================================================================
    # 5. ARQUITETURA OPERACIONAL COMPLETA E EXEMPLO REAL DE PONTA A PONTA
    # =========================================================================
    s.append(P("5. Funcionamento Técnico Integrado: Os 3 Servidores e o Caso Real no Sistema", h1))
    s += figure(
        os.path.join(ROOT, "fluxograma_open_health_completo.png"),
        "<b>Figura 4:</b> Fluxograma geral da solução mostrando a Trilha 1 (Exames de Sangue em PDF até o Dashboard :5000) e a Trilha 2 "
        "(Dataset de 55.200 registros de Wearables até o Dashboard Causal :5050), unidas pela camada de calibração e convergência Open Health (:5055).",
        max_h=220
    )

    s.append(table([
        ["Servidor Ativo", "Arquivos Principais do Projeto", "O que ele faz no passo a passo da demonstração"],
        ["1. Sistema de Exames de Sangue (localhost:5000)",
         "<i>Etapa Exames de Sangue/extrator_pdfs/app.py</i>, <i>classificador.py</i>, <i>interpretador_rag.py</i>, <i>open_health.db</i>",
         f"Recebe os PDFs de exames, grava nas 4 tabelas SQL (FHIR/LOINC/LGPD), calcula as 4 cores e setas ({UR}/{DR}), mostra os 565 "
         "textos educativos instantâneos e plota o gráfico histórico de cada marcador."],
        ["2. Sistema de Wearables & Inferência Causal (localhost:5050)",
         "<i>Dataset Wearables/app_wearables.py</i>, <i>wearables_health_6mo_daily.csv</i>",
         "Carrega em menos de 1 segundo os 55.200 dias de 300 pacientes, exibe o painel de Diagnóstico Diferencial Causal dos 4 Alvos "
         "(mostrando quantos % das alterações vêm de passos, álcool, tela ou cafeína) e audita as 33 variáveis do relógio."],
        ["3. Sistema NHANES & Ponte WearableBridge (localhost:5055)",
         "<i>nhanes_explorer/app.py</i>, <i>data_engine.py</i>, <i>wearable_bridge.py</i>",
         "Explora os 15.560 pacientes do CDC NHANES, roda os simuladores de Machine Learning e conecta via <i>POST /wearables/sync</i> "
         "os exames reais do banco <i>open_health.db</i> com a janela de 7–14 dias do smartwatch."],
    ], [105, 130, 252]))
    s.append(P("<b>Tabela 3.</b> Mapa técnico dos três sistemas integrados que compõem o protótipo funcional.", cap))

    s.append(P("5.1. Exemplo Prático Completo: Seguindo uma Paciente Real pelo Sistema (U0001 — Janaina de Assis)", h2))
    s.append(P(
        "Para ver como tudo faz sentido junto, basta acompanhar o caminho dos dados da paciente <b>U0001 (Janaina de Assis)</b> dentro "
        "do nosso ecossistema:"
    ))
    s.append(P(
        "1. <b>Passo 1 (Exames no Banco FHIR — Porta :5000):</b> Os laudos de sangue da Janaina estão salvos em <i>open_health.db</i> "
        "com consentimento LGPD ativo. Lá constam, por exemplo, sua Hemoglobina Glicada real (<b>HbA1c = 5,60%</b>, LOINC <i>4548-4</i>), "
        "sua Glicose, sua PCR-us e seu Hemograma completo.", bullet
    ))
    s.append(P(
        "2. <b>Passo 2 (Calibração do 'Marco Zero' no NHANES — Porta :5055):</b> Com base na idade, sexo, IMC e leucócitos da Janaina, "
        "o modelo populacional do NHANES estimaria um batimento em repouso de <b>72,5 bpm</b>. Porém, nos primeiros 7 dias de uso do "
        "smartwatch, o repouso real dela foi <b>68,3 bpm</b>. O sistema grava então a calibração pessoal dela: "
        "<b>Δ<sub>ind</sub> = −4,2 bpm</b>. A partir desse momento, o alvo saudável individual da Janaina passa a ser 68,3 bpm (e não "
        "72,5 bpm), e a HbA1c estimada pelo relógio (<b>5,43%</b>) fica a apenas <b>−0,17%</b> de distância do exame de sangue real (5,60%).", bullet
    ))
    s.append(P(
        "3. <b>Passo 3 (Filtro Causal Diário no Smartwatch — Porta :5050):</b> Durante os 6 meses de uso do relógio, sempre que o "
        "sono profundo da Janaina cai ou seu batimento sobe em um dia isolado, o motor causal (<i>compute_causal_differential</i>) "
        "checa seus hábitos: se naquele dia ela caminhou menos de 6.500 passos ou tomou mais cafeína/tela, o sistema avisa que a "
        "variação é explicada pela rotina e evita assustá-la.", bullet
    ))
    s.append(P(
        "4. <b>Passo 4 (Alerta Contextual e Briefing para o Médico):</b> Se, por outro lado, o batimento subir mais de +5 bpm acima "
        "do alvo calibrado dela (68,3 bpm) ou a HRV cair por mais de 4 dias seguidos mesmo em dias de rotina saudável, o sistema gera "
        "um aviso educativo seguro para a paciente e prepara um <b>briefing pré-consulta para o médico</b>, já informando quais hábitos "
        "foram descartados e qual exame LOINC vale a pena repetir.", bullet
    ))

    s.append(callout(
        "<b>Conformidade Regulatória Total (LGPD, CFM e ANVISA RDC nº 657/2022):</b> Todo o projeto foi desenhado sob uma regra de ouro: "
        "<b>inteligência artificial e estatística servem para limpar ruídos e organizar o contexto, nunca para dar diagnóstico no "
        "lugar do médico</b>. O paciente recebe apenas textos educativos pré-aprovados e metas saudáveis de rotina, enquanto o médico "
        "recebe dados limpos, calibrados e interoperáveis para tomar a decisão clínica."
    ))

    # =========================================================================
    # 6. CONCLUSÃO
    # =========================================================================
    s.append(P("6. Conclusão", h1))
    s.append(P(
        "Este artigo final demonstra que o valor do projeto <b>Open Health Brasil</b> está na união inteligente de suas quatro partes. "
        "O banco relacional HL7 FHIR / LOINC e o motor de gradiente com 565 textos determinísticos organizam e explicam os exames de "
        "sangue com segurança total. A modelagem no CDC NHANES calibrada pelo \"Marco Zero\" individual (R² = 0,864; erro de 3,02 bpm) "
        "permite que o smartwatch acompanhe o paciente nos meses entre duas coletas de sangue. E, fechando o ciclo, a <b>Engenharia "
        "Causal em 3 Camadas</b> resolve o maior gargalo dos dispositivos vestíveis atuais: ao separar matematicamente o efeito de "
        "hábitos cotidianos (passos, álcool, cafeína, tela e noites curtas) dos sinais fisiológicos reais, ela elimina de 56,1% a "
        "97,4% de falsos alarmes nos quatro alvos clínicos estudados, entregando tranquilidade ao paciente e precisão ao médico."
    ))

    # =========================================================================
    # REFERÊNCIAS
    # =========================================================================
    s.append(P("Referências Bibliográficas Principais", h1))
    refs = [
        "[1] HL7 INTERNATIONAL. <i>HL7 FHIR Release 4 (R4) — Perfil BR Core (Patient, DiagnosticReport, Observation, Consent)</i> &amp; <i>LOINC / UCUM Standards</i>. 2023.",
        "[2] CLINICAL AND LABORATORY STANDARDS INSTITUTE (CLSI). <i>EP28-A3c: Defining, Establishing, and Verifying Reference Intervals in the Clinical Laboratory</i>; <i>NCI CTCAE v5.0</i>; <i>CAP Critical Values</i>.",
        "[3] CENTERS FOR DISEASE CONTROL AND PREVENTION (CDC). <i>National Health and Nutrition Examination Survey (NHANES) 2017–March 2020 &amp; 2011–2012 Microdata</i>. Hyattsville, MD.",
        "[4] PEARL, J.; GLYMOUR, M.; JEWELL, N. P. <i>Causal Inference in Statistics: A Primer</i>. Wiley, 2016. (Grafos Acíclicos Direcionados — DAGs e controle de fatores de confusão).",
        "[5] BORBÉLY, A. A. et al. The two-process model of sleep regulation: a reappraisal. <i>Journal of Sleep Research</i>, v. 25, p. 131–143, 2016. (Relação entre atividade física diurna, adenosina e sono profundo N3).",
        "[6] HALL, J. E.; HALL, M. E. <i>Guyton and Hall Textbook of Medical Physiology</i>. 14. ed. Elsevier, 2021. (Princípio de Fick e transporte de oxigênio DO<sub>2</sub>).",
        "[7] BRASIL. Lei nº 13.709/2018 (LGPD); ANVISA RDC nº 657/2022 (Software como Dispositivo Médico — SaMD); CFM Resolução nº 2.314/2022.",
    ]
    for r in refs:
        s.append(P(r, ref))

    doc.build(s, canvasmaker=CleanAcademicCanvas)
    return out_pdf


if __name__ == "__main__":
    out_path = os.path.join(ROOT, "Artigo_Final_Sintese_Arquitetura_Open_Health_Completa.pdf")
    print(build(out_path))
