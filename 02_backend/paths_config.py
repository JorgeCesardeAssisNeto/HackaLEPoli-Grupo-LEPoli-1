# -*- coding: utf-8 -*-
"""
Configuracao centralizada de caminhos e sys.path para o ecossistema Open Health.
Permite que qualquer modulo dentro de 02_backend/ importe os demais modulos
e localize bancos de dados, datasets NHANES/Wearables, ontologias e laudos
independentemente do diretorio de trabalho atual (cwd).
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BACKEND_DIR)

# Injeta todas as 10 pastas de sessoes do backend no sys.path
for _sub in sorted(os.listdir(BACKEND_DIR)):
    _sub_path = os.path.join(BACKEND_DIR, _sub)
    if os.path.isdir(_sub_path) and not _sub.startswith("__"):
        if _sub_path not in sys.path:
            sys.path.insert(0, _sub_path)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Diretorios das sessoes do backend
CORE_API_DIR = os.path.join(BACKEND_DIR, "01_core_api")
INGESTAO_DIR = os.path.join(BACKEND_DIR, "02_ingestao_ocr")
SEMANTICA_DIR = os.path.join(BACKEND_DIR, "03_semantica_ontologias")
PERSISTENCIA_DIR = os.path.join(BACKEND_DIR, "04_persistencia_dados")
RAG_DIR = os.path.join(BACKEND_DIR, "05_inteligencia_rag")
POPULACIONAL_DIR = os.path.join(BACKEND_DIR, "06_populacional_nhanes")
WEARABLES_MOD_DIR = os.path.join(BACKEND_DIR, "07_sensores_wearables")
ML_CAUSAL_DIR = os.path.join(BACKEND_DIR, "08_machine_learning_causal")
GERADORES_DIR = os.path.join(BACKEND_DIR, "09_geradores_sinteticos")
RELATORIOS_DIR = os.path.join(BACKEND_DIR, "10_relatorios_cientificos")

# Diretorios globais do repositorio
FRONTEND_DIR = os.path.join(REPO_ROOT, "01_frontend")
DATABASES_DIR = os.path.join(REPO_ROOT, "03_bases_de_dados")
NHANES_DATA_DIR = os.path.join(DATABASES_DIR, "dados_nhanes")
NHANES_2012_DIR = os.path.join(NHANES_DATA_DIR, "2012")
WEARABLES_DATA_DIR = os.path.join(DATABASES_DIR, "dataset_wearables")
WEARABLES_CSV_PATH = os.path.join(WEARABLES_DATA_DIR, "wearables_health_6mo_daily.csv")

LAUDOS_DIR = os.path.join(REPO_ROOT, "04_laudos_clinicos")
LAUDOS_HIPOTETICOS_DIR = os.path.join(LAUDOS_DIR, "laudos_hipoteticos")
LAUDOS_REAIS_DIR = os.path.join(LAUDOS_DIR, "laudos_reais")
RETROSPECTIVA_JSON_PATH = os.path.join(LAUDOS_HIPOTETICOS_DIR, "retrospectiva_3_anos_janaina.json")

DOCS_DIR = os.path.join(REPO_ROOT, "05_documentacao_e_artigos")
ARTIGOS_DIR = os.path.join(DOCS_DIR, "artigos_e_relatorios")
REGULAMENTACAO_DIR = os.path.join(DOCS_DIR, "regulamentacao_e_desafio")
FIGURAS_DIR = os.path.join(DOCS_DIR, "figuras_e_diagramas")

# Arquivos chave do backend
DB_SQLITE_PATH = os.path.join(PERSISTENCIA_DIR, "open_health.db")
BANCO_EXAMES_CSV_PATH = os.path.join(PERSISTENCIA_DIR, "banco_exames.csv")
CSV_OFICIAL_BRCORE_PATH = os.path.join(SEMANTICA_DIR, "planilha_padrao_exames_brcore_loinc.csv")
MAPA_LOINC_PATH = os.path.join(SEMANTICA_DIR, "mapa_colunas_loinc.json")
KB_LOINC_PATH = os.path.join(SEMANTICA_DIR, "base_conhecimento_loinc.json")
KB_565_PATH = os.path.join(SEMANTICA_DIR, "base_conhecimento_exames_565.json")
CATALOGO_COLUNAS_PATH = os.path.join(SEMANTICA_DIR, "catalogo_colunas_completo.json")
