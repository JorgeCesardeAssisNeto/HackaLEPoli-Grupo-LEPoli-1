# -*- coding: utf-8 -*-
# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
"""
Script de organização do Backend Open Health e geração do Manual Técnico em PDF.
"""
import os
import shutil
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Mapeamento dos módulos e arquivos
ESTRUTURA_BACKEND = {
    "01_core_api": {
        "titulo": "Sessão 01: Core Web & APIs de Serviços (Flask / Microserviços)",
        "descricao": "Servidores HTTP, orquestradores de endpoints REST e interfaces interativas da plataforma.",
        "arquivos": [
            ("Etapa Exames de Sangue/app.py", "app.py", "Servidor Web principal (Flask) do módulo clínico. Gerencia upload de laudos PDF, orquestração de OCR, consultas longitudinais (3 anos), painel de consentimento LGPD e integração com RAG."),
            ("nhanes_explorer/app.py", "app_nhanes.py", "Servidor Web analítico do explorador populacional NHANES. Provê endpoints para consultas analíticas multivariadas, gráficos epidemiológicos e calibração estatística."),
            ("Dataset Wearables/app_wearables.py", "app_wearables.py", "Microserviço dedicado ao processamento analítico e exploração de séries temporais de wearables (frequência cardíaca, HRV, sono, passos e estresse).")
        ]
    },
    "02_ingestao_ocr": {
        "titulo": "Sessão 02: Pipeline de Ingestão & OCR de Laudos",
        "descricao": "Módulos de ingestão documental para conversão de laudos em PDF para dados estruturados.",
        "arquivos": [
            ("Etapa Exames de Sangue/extrator.py", "extrator.py", "Extrator inteligente via LLM multimodal (Gemini). Processa páginas de laudos em PDF e extrai JSON estrito com valores, unidades e referências."),
            ("Etapa Exames de Sangue/extrator_local.py", "extrator_local.py", "Extrator offline determinístico baseado em expressões regulares e heurísticas laboratoriais para execução sem dependência de nuvem.")
        ]
    },
    "03_semantica_ontologias": {
        "titulo": "Sessão 03: Padronização Semântica & Ontologias (LOINC / FHIR)",
        "descricao": "Padronização semântica, dicionários biomédicos e motores de regras determinísticas de referência.",
        "arquivos": [
            ("Etapa Exames de Sangue/mapeador_planilha.py", "mapeador_planilha.py", "Algoritmo de mapeamento semântico que correlaciona nomes laboratoriais livres a códigos oficiais LOINC e padrões BR Core / HL7 FHIR."),
            ("Etapa Exames de Sangue/classificador.py", "classificador.py", "Motor de classificação clínica determinística. Compara valores com intervalos biológicos de referência e gera alertas e criticidades clínicas."),
            ("Etapa Exames de Sangue/base_conhecimento_exames_565.json", "base_conhecimento_exames_565.json", "Base estruturada contendo o catálogo de 565 biomarcadores clínicos, suas unidades e significados fisiológicos."),
            ("Etapa Exames de Sangue/base_conhecimento_loinc.json", "base_conhecimento_loinc.json", "Ontologia internacional LOINC com descrições, termos canônicos, sistemas corporais e métodos analíticos."),
            ("Etapa Exames de Sangue/mapa_colunas_loinc.json", "mapa_colunas_loinc.json", "Mapeamento De-Para entre nomes comerciais de exames laboratoriais e suas colunas padronizadas LOINC."),
            ("Etapa Exames de Sangue/catalogo_colunas_completo.json", "catalogo_colunas_completo.json", "Catálogo unificado de metadados, tipos de dados e especificações de colunas laboratoriais.")
        ]
    },
    "04_persistencia_dados": {
        "titulo": "Sessão 04: Persistência & Longitude Relacional (SQL / SQLite)",
        "descricao": "Camada de acesso a dados (DAO), scripts DDL e integridade referencial relacional.",
        "arquivos": [
            ("Etapa Exames de Sangue/database.py", "database.py", "Camada DAO (Data Access Object) SQLite. Controla migrações de esquema, inserções de pacientes, laudos, observações, consentimentos e consultas históricas longitudinais."),
            ("Etapa Exames de Sangue/schema_open_health.sql", "schema_open_health.sql", "Script SQL DDL de criação do banco de dados relacional (pacientes, consentimentos, laudos, observations, wearable_metrics e views analíticas)."),
            ("check_views.py", "check_views.py", "Script de validação e integridade de views SQL analíticas e consistência de índices temporais.")
        ]
    },
    "05_inteligencia_rag": {
        "titulo": "Sessão 05: Inteligência Médica & RAG (Retrieval-Augmented Generation)",
        "descricao": "Sistemas de suporte à decisão clínica com LLM baseados em contexto temporal e diretrizes.",
        "arquivos": [
            ("Etapa Exames de Sangue/interpretador_rag.py", "interpretador_rag.py", "Pipeline de RAG clínico. Combina a evolução longitudinal do paciente com a base de conhecimento médico para gerar relatórios diagnósticos fundamentados."),
            ("Etapa Exames de Sangue/gerador_conhecimento.py", "gerador_conhecimento.py", "Indexador e compilador das bases de diretrizes e evidências médicas para enriquecimento do contexto do modelo de linguagem.")
        ]
    },
    "06_populacional_nhanes": {
        "titulo": "Sessão 06: Big Data Populacional & Bridge Wearables (CDC NHANES)",
        "descricao": "Motor analítico de dados populacionais do CDC e ponte de inferência contínua.",
        "arquivos": [
            ("nhanes_explorer/data_engine.py", "data_engine.py", "Motor de Big Data epidemiológico CDC NHANES. Processa demografia, exames CBC, colesterol e pressão com regressões e aprendizado de máquina."),
            ("nhanes_explorer/wearable_bridge.py", "wearable_bridge.py", "Ponte de inferência e calibração de wearables. Translada métricas contínuas de sensores de pulso em predições de biomarcadores laboratoriais."),
            ("inspect_nhanes.py", "inspect_nhanes.py", "Script utilitário de inspeção descritiva e análise exploratória de variáveis das tabelas NHANES."),
            ("nhanes_summary.json", "nhanes_summary.json", "Sumário estatístico consolidado com distribuições, medianas e desvios das coortes populacionais do NHANES."),
            ("check_thyroid.py", "check_thyroid.py", "Módulo de verificação estatística e clínica dos biomarcadores tireoidianos (TSH e T4 Livre).")
        ]
    },
    "07_sensores_wearables": {
        "titulo": "Sessão 07: Sensores Wearables & Séries Biométricas",
        "descricao": "Processamento de séries temporais de alta frequência provenientes de dispositivos vestíveis.",
        "arquivos": [
            ("Dataset Wearables/app_wearables.py", "engine_wearables.py", "Motor de cálculo de métricas fisiológicas contínuas: HRV RMSSD, eficiência do sono, estágios REM/Profundo, estresse e cadência de atividade.")
        ]
    },
    "08_machine_learning_causal": {
        "titulo": "Sessão 08: Modelos Preditivos & Inferência Causal",
        "descricao": "Treinamento, validação e deploy de algoritmos preditivos e grafos acíclicos direcionados (DAGs).",
        "arquivos": [
            ("train_models_1_and_2.py", "train_models_1_and_2.py", "Pipeline de treinamento e validação cruzada dos modelos preditivos primários (Wearables -> Hemograma Completo)."),
            ("test_3_new_models.py", "test_3_new_models.py", "Suite de testes e validação empírica dos 3 modelos complementares (marcadores inflamatórios, metabólicos e lipídicos)."),
            ("update_engine_3_models.py", "update_engine_3_models.py", "Script de deploy e sincronização dos modelos treinados para incorporação ao motor em tempo real `data_engine.py`.")
        ]
    },
    "09_geradores_sinteticos": {
        "titulo": "Sessão 09: Geradores de Dados Sintéticos & Ferramentas Auxiliares",
        "descricao": "Simuladores de coortes clínicas, validação de sintaxe e criação de laudos hipotéticos realistas.",
        "arquivos": [
            ("Etapa Exames de Sangue/gerador_laudos.py", "gerador_laudos.py", "Gerador de laudos laboratoriais sintéticos em formato PDF com layout hospitalar idêntico a exames reais."),
            ("Etapa Exames de Sangue/gerar_10_laudos.py", "gerar_10_laudos.py", "Script orquestrador que simula o acompanhamento longitudinal de 3 anos de um paciente com 10 episódios laboratoriais consecutivos."),
            ("Etapa Exames de Sangue/check_js_syntax.py", "check_js_syntax.py", "Validador e linter sintático para scripts JavaScript embutidos em templates HTML."),
            ("validate_js.py", "validate_js.py", "Script complementar de teste e validação de lógica frontend.")
        ]
    },
    "10_relatorios_cientificos": {
        "titulo": "Sessão 10: Motores de Relatórios Científicos & Gráficos Automatizados",
        "descricao": "Compiladores de artigos acadêmicos em PDF, relatórios regulatórios e gráficos de publicação.",
        "arquivos": [
            ("Etapa Exames de Sangue/gerar_artigo_final_sintese_pdf.py", "gerar_artigo_final_sintese_pdf.py", "Compilador ReportLab que gera o Artigo Final de Síntese da Arquitetura Open Health Completa."),
            ("Etapa Exames de Sangue/gerar_artigo_wearables_nhanes_pdf.py", "gerar_artigo_wearables_nhanes_pdf.py", "Compilador do artigo científico sobre correlação de biossensores e exames laboratoriais no NHANES."),
            ("Etapa Exames de Sangue/gerar_relatorio_modulo_clinico_pdf.py", "gerar_relatorio_modulo_clinico_pdf.py", "Gerador de relatório técnico do módulo clínico longitudinal."),
            ("Etapa Exames de Sangue/gerar_relatorio_pdf.py", "gerar_relatorio_pdf.py", "Gerador de relatório executivo de conformidade LGPD e interoperabilidade BR Core."),
            ("Etapa Exames de Sangue/gerar_figuras_artigo_final_sintese.py", "gerar_figuras_artigo_final_sintese.py", "Script de geração de figuras de alta resolução (PNG/DPI 300) da arquitetura global."),
            ("Etapa Exames de Sangue/gerar_figuras_wearables_nhanes.py", "gerar_figuras_wearables_nhanes.py", "Geração de gráficos de correlação, dispersão e curvas ROC de wearables e hemograma."),
            ("Etapa Exames de Sangue/gerar_figuras_modulo_clinico.py", "gerar_figuras_modulo_clinico.py", "Geração de gráficos de séries temporais e gradientes clínicos longitudinais."),
            ("gerar_fluxograma_completo.py", "gerar_fluxograma_completo.py", "Script de geração automatizada do fluxograma gráfico completo da plataforma."),
            ("Etapa Exames de Sangue/gerar_diagrama.py", "gerar_diagrama.py", "Gerador do diagrama relacional entre tabelas do banco de dados."),
            ("Etapa Exames de Sangue/gerar_documento_academico.py", "gerar_documento_academico.py", "Gerador de especificações acadêmicas complementares.")
        ]
    }
}

def organizar_pastas():
    print("Iniciando organização das pastinhas do Backend...")
    os.makedirs(BACKEND_DIR, exist_ok=True)
    
    total_copiados = 0
    for pasta, info in ESTRUTURA_BACKEND.items():
        pasta_destino = os.path.join(BACKEND_DIR, pasta)
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Cria README específico da pasta
        readme_path = os.path.join(pasta_destino, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f_readme:
            f_readme.write(f"# {info['titulo']}\n\n")
            f_readme.write(f"{info['descricao']}\n\n")
            f_readme.write("## Arquivos nesta Sessão:\n\n")
            
            for origem_rel, nome_dest, desc in info["arquivos"]:
                origem_full = os.path.join(BASE_DIR, origem_rel)
                dest_full = os.path.join(pasta_destino, nome_dest)
                if os.path.exists(origem_full):
                    shutil.copy2(origem_full, dest_full)
                    total_copiados += 1
                f_readme.write(f"### `{nome_dest}`\n")
                f_readme.write(f"- **Origem no projeto:** `{origem_rel}`\n")
                f_readme.write(f"- **Descrição:** {desc}\n\n")
                
    print(f"Total de {total_copiados} arquivos organizados em {len(ESTRUTURA_BACKEND)} pastas com sucesso!")

    # Cria README principal dentro de backend/
    criar_readme_principal()

def criar_readme_principal():
    readme_main = os.path.join(BACKEND_DIR, "README.md")
    with open(readme_main, "w", encoding="utf-8") as f:
        f.write("# 🏛️ Arquitetura do Backend — Open Health Brasil (Hackathon LEPoli)\n\n")
        f.write("Esta pasta consolida e categoriza **todos os componentes de backend** da plataforma Open Health Brasil, organizados modularmente por responsabilidades.\n\n")
        f.write("## 📂 Estrutura de Pastas por Sessões\n\n")
        for pasta, info in ESTRUTURA_BACKEND.items():
            f.write(f"- [**`{pasta}/`**](./{pasta}): {info['titulo']}\n")
        f.write("\n---\n\n")
        f.write("## 🔄 Fluxograma Arquitetural Geral\n\n")
        f.write("```mermaid\n")
        f.write("""flowchart TD
    subgraph S_ENTRADAS ["📥 Fontes de Dados"]
        PDF_LAUDO["Laudos Médicos (PDF)"]
        WEARABLE_CSV["Séries Temporais Wearables"]
        CDC_NHANES["Repositório CDC NHANES"]
    end

    subgraph S02 ["02_ingestao_ocr"]
        EXT_CLOUD["extrator.py (Gemini LLM)"]
        EXT_LOCAL["extrator_local.py (Regex)"]
    end

    subgraph S03 ["03_semantica_ontologias"]
        MAPPER["mapeador_planilha.py"]
        CLASSIF["classificador.py"]
        ONTOLOGY[("Bases LOINC & FHIR")]
    end

    subgraph S04 ["04_persistencia_dados"]
        DB_MOD["database.py"]
        DB_SQL[("open_health.db (SQLite)")]
    end

    subgraph S05 ["05_inteligencia_rag"]
        RAG_MOD["interpretador_rag.py"]
        GEN_KNOW["gerador_conhecimento.py"]
    end

    subgraph S01 ["01_core_api"]
        APP_CLINICO["app.py (API Clínica)"]
        APP_NHANES["app_nhanes.py (Pop.)"]
        APP_WEAR["app_wearables.py (Sensores)"]
    end

    subgraph S06_08 ["06_populacional & 08_machine_learning"]
        ENGINE["data_engine.py"]
        BRIDGE["wearable_bridge.py"]
        MODELS["train_models & test_models"]
    end

    subgraph S10 ["10_relatorios_cientificos"]
        REPORTS["Compiladores PDF & Gráficos"]
    end

    PDF_LAUDO --> EXT_CLOUD & EXT_LOCAL
    EXT_CLOUD & EXT_LOCAL --> MAPPER
    ONTOLOGY --> MAPPER & CLASSIF
    MAPPER --> CLASSIF --> DB_MOD --> DB_SQL
    DB_SQL --> RAG_MOD & APP_CLINICO
    RAG_MOD --> APP_CLINICO
    WEARABLE_CSV --> APP_WEAR & BRIDGE
    CDC_NHANES --> ENGINE
    MODELS --> ENGINE --> BRIDGE
    DB_SQL <--> BRIDGE
    DB_SQL & ENGINE --> REPORTS
""")
        f.write("```\n")

# Canvas numerado para o PDF
class NumberedCanvas(canvas.Canvas):
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1e3a8a"))
            self.drawString(45, 808, "OPEN HEALTH BRASIL — DICIONÁRIO E ARQUITETURA DO BACKEND")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawRightString(550, 808, "Hackathon LEPoli | HL7 FHIR | LOINC | CDC NHANES")
            
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.75)
            self.line(45, 800, 550, 800)
            
            # Footer
            self.line(45, 45, 550, 45)
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(45, 33, "Documentação Técnica Oficial de Engenharia de Software e Ciência de Dados")
            self.drawRightString(550, 33, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()

def gerar_pdf_documentacao():
    pdf_filename = "Manual_Arquitetura_Backend_Open_Health.pdf"
    pdf_path_root = os.path.join(BASE_DIR, pdf_filename)
    pdf_path_backend = os.path.join(BACKEND_DIR, pdf_filename)
    
    doc = SimpleDocTemplate(
        pdf_path_root,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=18
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    desc_table_style = ParagraphStyle(
        'DescTable',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )
    
    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569')
    )

    story = []

    # CAPA / CABEÇALHO DO DOCUMENTO
    story.append(Paragraph("OPEN HEALTH BRASIL — HACKATHON LEPOLI", ParagraphStyle('SuperTitle', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#2563eb'), spaceAfter=4)))
    story.append(Paragraph("Dicionário e Manual Técnico da Arquitetura de Backend", title_style))
    story.append(Paragraph("Mapeamento Modular, Catálogo de Arquivos, Responsabilidades e Fluxo de Dados", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=14))

    # Box de Metadados
    meta_data = [
        [Paragraph("<b>Projeto:</b> Plataforma Open Health Brasil", desc_table_style), Paragraph("<b>Data:</b> Novembro / 2026", desc_table_style)],
        [Paragraph("<b>Padrões Semânticos:</b> HL7 FHIR BR Core | LOINC", desc_table_style), Paragraph("<b>Conformidade:</b> LGPD (Art. 7º & 11)", desc_table_style)],
        [Paragraph("<b>Módulos Analíticos:</b> CDC NHANES + Wearables Bridge", desc_table_style), Paragraph("<b>Status:</b> Pronto para GitHub", desc_table_style)]
    ]
    meta_table = Table(meta_data, colWidths=[270, 235])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Visão Geral
    story.append(Paragraph("1. Visão Geral da Arquitetura", h1_style))
    story.append(Paragraph(
        "O backend da plataforma <b>Open Health Brasil</b> foi concebido como uma arquitetura híbrida e modular, "
        "integrando microsserviços web em Python (Flask), pipelines inteligentes de ingestão documental com IA generativa multimodal (Gemini), "
        "motores determinísticos de classificação clínica, padronização internacional semântica (LOINC / HL7 FHIR), "
        "banco relacional estruturado com rastreamento longitudinal e auditoria LGPD, além de um motor de Big Data epidemiológico (CDC NHANES) "
        "e modelos de aprendizado de máquina para calibração contínua a partir de biossensores (wearables).",
        body_style
    ))
    story.append(Paragraph(
        "Para garantir máxima manutenibilidade, legibilidade e portabilidade no repositório GitHub, todo o ecossistema "
        "foi catalogado e organizado na pasta <code>backend/</code>, subdividida em <b>10 sessões temáticas especializadas</b>.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Tabela Resumo das Sessões
    story.append(Paragraph("2. Sumário das Pastas Organizacionais", h1_style))
    resumo_headers = [Paragraph("<b>Pasta / Sessão</b>", desc_table_style), Paragraph("<b>Domínio de Atuação</b>", desc_table_style), Paragraph("<b>Qtd. Arquivos</b>", desc_table_style)]
    resumo_rows = [resumo_headers]
    
    total_files = 0
    for pasta, info in ESTRUTURA_BACKEND.items():
        qtd = len(info["arquivos"])
        total_files += qtd
        resumo_rows.append([
            Paragraph(f"<b><code>{pasta}</code></b>", code_style),
            Paragraph(info["titulo"].split(":")[1].strip(), desc_table_style),
            Paragraph(f"<font color='#2563eb'><b>{qtd}</b></font>", desc_table_style)
        ])
    resumo_rows.append([
        Paragraph("<b>TOTAL GERAL</b>", desc_table_style),
        Paragraph("<b>Cobertura integral de todos os arquivos de backend</b>", desc_table_style),
        Paragraph(f"<b>{total_files} arquivos</b>", desc_table_style)
    ])

    t_resumo = Table(resumo_rows, colWidths=[130, 315, 60])
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_resumo)
    story.append(Spacer(1, 14))

    # Detalhamento de cada sessão
    story.append(Paragraph("3. Detalhamento Técnico Arquivo por Arquivo", h1_style))
    story.append(Paragraph("Abaixo está especificada a finalidade técnica exata de cada arquivo em sua respectiva pastinha:", body_style))
    story.append(Spacer(1, 8))

    for pasta, info in ESTRUTURA_BACKEND.items():
        bloco = []
        bloco.append(Paragraph(f"📂 Pasta: <code>{pasta}/</code> — {info['titulo']}", h2_style))
        bloco.append(Paragraph(f"<i>{info['descricao']}</i>", body_style))
        bloco.append(Spacer(1, 4))

        t_headers = [
            Paragraph("<b>Arquivo</b>", desc_table_style),
            Paragraph("<b>Caminho Original</b>", desc_table_style),
            Paragraph("<b>Função Técnica no Ecossistema</b>", desc_table_style)
        ]
        t_rows = [t_headers]
        for orig, dest, desc in info["arquivos"]:
            t_rows.append([
                Paragraph(f"<b><code>{dest}</code></b>", code_style),
                Paragraph(f"<font color='#64748b'>{orig}</font>", desc_table_style),
                Paragraph(desc, desc_table_style)
            ])

        t_detalhe = Table(t_rows, colWidths=[130, 140, 235])
        t_detalhe.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        bloco.append(t_detalhe)
        bloco.append(Spacer(1, 12))
        story.append(KeepTogether(bloco))

    # Conclusão e instruções de deploy
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Diretrizes de Versionamento e GitHub", h1_style))
    story.append(Paragraph(
        "• <b>Submódulos Independentes:</b> Cada pasta possui seu próprio arquivo <code>README.md</code> interno, permitindo que desenvolvedores naveguem e compreendam a responsabilidade do módulo diretamente na interface web do GitHub.<br/>"
        "• <b>Preservação dos Caminhos de Origem:</b> Os arquivos originais foram mantidos intactos em suas posições originais, garantindo que nenhum script dependente de caminho relativo seja corrompido durante a execução de pipelines já configurados.<br/>"
        "• <b>Interoperabilidade Semântica:</b> O esquema relacional do <code>database.py</code> opera em total conformidade com as diretrizes do Ministério da Saúde (RNDS - Rede Nacional de Dados em Saúde), adotando chaves primárias alinhadas ao HL7 FHIR BR Core.",
        body_style
    ))

    # Compila documento
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Copia o PDF gerado também para dentro de backend/
    shutil.copy2(pdf_path_root, pdf_path_backend)
    print(f"PDF gerado com sucesso em:\n- {pdf_path_root}\n- {pdf_path_backend}")

if __name__ == "__main__":
    organizar_pastas()
    gerar_pdf_documentacao()
