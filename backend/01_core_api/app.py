import os
import tempfile
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Carrega variáveis de ambiente do .env local e pai
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))
load_dotenv()

from flask import Flask, request, jsonify, render_template_string, send_file
from extrator import extrair_informacoes_laudo
from extrator_local import extrair_local_offline
from mapeador_planilha import criar_linha_planilha, salvar_em_planilha_csv, COLUNAS_PLANILHA
from database import (
    inicializar_banco, 
    salvar_laudo_relacional, 
    obter_dados_tabelas, 
    limpar_todas_tabelas,
    obter_pacientes_completo,
    obter_detalhes_paciente,
    obter_observacoes_laudo_colunas,
    alternar_status_consentimento,
    criar_consentimento_paciente,
    popular_historico_longitudinal_3_anos,
    listar_biomarcadores_paciente,
    obter_evolucao_biomarcador_paciente,
    get_db_connection
)
from interpretador_rag import executar_pipeline_rag_interpretacao

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB

CSV_OFICIAL_NOME = "Planilha Padrão - Exame de Sangue (BR Core _ LOINC) - Registro_Exames_BRCore.csv"
caminho_oficial = os.path.join(BASE_DIR, CSV_OFICIAL_NOME)
CSV_BANCO_PATH = caminho_oficial if os.path.exists(caminho_oficial) else os.path.join(BASE_DIR, "banco_exames.csv")

# Garante inicialização e população do banco com os 10 laudos unificados
inicializar_banco()
popular_historico_longitudinal_3_anos(forcar=False)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open Health Brasil — Navegação Relacional HL7 FHIR & LOINC</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --surface: #111827;
            --surface-card: #182235;
            --surface-hover: #223048;
            --border: #24324c;
            --border-light: #374b70;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --accent: #818cf8;
            --loinc: #38bdf8;
            --success: #34d399;
            --success-bg: rgba(52, 211, 153, 0.12);
            --danger: #fb7185;
            --danger-bg: rgba(251, 113, 133, 0.12);
            --warning: #fbbf24;
            --warning-bg: rgba(251, 191, 36, 0.12);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --radius: 12px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text-main); min-height: 100vh; padding: 24px 16px; }
        .container { max-width: 1360px; margin: 0 auto; }

        /* Top Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
            flex-wrap: wrap;
            gap: 16px;
        }
        .header-title h1 { font-size: 1.8rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
        .header-title h1 span { color: var(--primary); }
        .header-title p { color: var(--text-muted); font-size: 0.88rem; margin-top: 2px; }
        .badge-system {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--primary);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 999px;
            padding: 3px 12px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .header-actions { display: flex; gap: 10px; align-items: center; }

        /* Breadcrumb Navigation */
        .breadcrumb-bar {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 12px 20px;
            margin-bottom: 24px;
            font-size: 0.9rem;
            flex-wrap: wrap;
        }
        .bc-item {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
        }
        .bc-item:hover { color: var(--primary); }
        .bc-item.active { color: #fff; font-weight: 700; cursor: default; }
        .bc-sep { color: #475569; font-size: 0.8rem; }

        /* Buttons */
        .btn-action {
            background: var(--primary);
            color: #090d16;
            font-weight: 700;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.88rem;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-action:hover { background: var(--primary-hover); transform: translateY(-1px); }
        .btn-action:disabled { opacity: 0.5; cursor: not-allowed; }

        .btn-secondary {
            background: var(--surface-card);
            color: #fff;
            border: 1px solid var(--border);
            padding: 9px 16px;
            border-radius: 8px;
            font-size: 0.84rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .btn-secondary:hover { background: var(--surface-hover); border-color: var(--border-light); }

        .btn-danger {
            background: rgba(251, 113, 133, 0.1);
            color: var(--danger);
            border: 1px solid rgba(251, 113, 133, 0.3);
            padding: 9px 14px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-danger:hover { background: rgba(251, 113, 133, 0.2); }

        .btn-sm { padding: 6px 12px; font-size: 0.78rem; border-radius: 6px; }

        /* Collapsible Upload Panel */
        .upload-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            margin-bottom: 24px;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .upload-panel-header {
            padding: 14px 20px;
            background: rgba(15, 23, 42, 0.7);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            border-bottom: 1px solid transparent;
        }
        .upload-panel-header.open { border-bottom-color: var(--border); }
        .upload-body { padding: 20px; display: none; }
        .upload-body.open { display: block; }

        .engine-selector {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 16px;
        }
        .engine-option {
            background: var(--surface-card);
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 10px 16px;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .engine-option input { display: none; }
        .engine-option.active { border-color: var(--primary); background: rgba(56, 189, 248, 0.08); }
        .engine-title { font-weight: 600; font-size: 0.86rem; color: #fff; }
        .engine-desc { font-size: 0.72rem; color: var(--text-muted); }

        .upload-drop-area {
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            padding: 24px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(0, 0, 0, 0.15);
        }
        .upload-drop-area:hover, .upload-drop-area.dragover {
            border-color: var(--primary);
            background: rgba(56, 189, 248, 0.04);
        }

        /* Loading */
        .loading-box {
            display: none;
            text-align: center;
            padding: 30px 20px;
            background: var(--surface);
            border-radius: var(--radius);
            margin-bottom: 24px;
            border: 1px solid var(--border);
        }
        .spinner {
            width: 38px;
            height: 38px;
            border: 4px solid var(--border);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 12px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* Main View Container */
        .view-section { display: none; }
        .view-section.active { display: block; }

        /* Cards & Grids */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            margin-bottom: 24px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
            flex-wrap: wrap;
            gap: 10px;
        }
        .card-title { font-size: 1.15rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; }

        .patient-info-banner {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px 22px;
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
        }
        .info-col label { display: block; font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
        .info-col div { font-size: 0.95rem; font-weight: 600; color: #fff; }

        /* Tables */
        .table-responsive {
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--surface);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.85rem;
        }
        th {
            background: rgba(10, 15, 29, 0.9);
            color: var(--text-muted);
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 14px;
            font-weight: 600;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            color: #e2e8f0;
            vertical-align: middle;
        }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255, 255, 255, 0.02); }

        .uuid-code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            color: #94a3b8;
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 4px;
            max-width: 120px;
            display: inline-block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .hash-code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: #c084fc;
            background: rgba(168, 85, 247, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            max-width: 130px;
            display: inline-block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .loinc-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 700;
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 2px 8px;
            border-radius: 6px;
            display: inline-block;
        }

        .badge {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-active { background: var(--success-bg); color: var(--success); border: 1px solid rgba(52, 211, 153, 0.3); }
        .badge-revoked { background: var(--danger-bg); color: var(--danger); border: 1px solid rgba(251, 113, 133, 0.3); }
        .badge-normal { background: var(--success-bg); color: var(--success); }
        .badge-alterado { background: var(--danger-bg); color: var(--danger); }
        .badge-vazio { background: rgba(148, 163, 184, 0.1); color: #64748b; }

        /* OBSERVATIONS BY COLUMNS (The Special View requested by user) */
        .filters-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }
        .filter-group { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .pill-filter {
            background: var(--surface-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .pill-filter:hover { color: #fff; border-color: var(--primary); }
        .pill-filter.active { background: rgba(56, 189, 248, 0.15); border-color: var(--primary); color: #fff; }

        .search-box {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 14px;
            color: #fff;
            font-size: 0.85rem;
            width: 260px;
        }
        .search-box:focus { outline: none; border-color: var(--primary); }

        /* Wide Matrix Table for All Columns */
        .matrix-container {
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow-x: auto;
            max-height: 650px;
            background: #0b1120;
            margin-bottom: 24px;
        }
        .matrix-table {
            border-collapse: separate;
            border-spacing: 0;
            min-width: 100%;
            font-size: 0.82rem;
        }
        .matrix-table th {
            position: sticky;
            top: 0;
            z-index: 10;
            background: #0f172a;
            border-bottom: 2px solid var(--border);
            padding: 14px 16px;
            text-align: center;
            vertical-align: top;
            min-width: 160px;
        }
        .matrix-table th .col-name { font-size: 0.8rem; color: #fff; font-weight: 600; margin-bottom: 4px; }
        .matrix-table th .col-loinc { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--primary); }
        .matrix-table th .col-cat { font-size: 0.68rem; color: #64748b; margin-top: 3px; font-weight: normal; }

        .matrix-table td {
            padding: 16px;
            text-align: center;
            border-bottom: 1px solid var(--border);
            border-right: 1px solid rgba(255, 255, 255, 0.04);
            background: #0b1120;
            vertical-align: middle;
        }
        .matrix-cell-filled {
            background: rgba(56, 189, 248, 0.04) !important;
        }
        .cell-value { font-size: 1.05rem; font-weight: 700; color: #fff; margin-bottom: 2px; }
        .cell-unit { font-size: 0.74rem; color: var(--text-muted); }
        .cell-ref { font-size: 0.7rem; color: #64748b; margin-top: 3px; }
        .cell-empty { color: #475569; font-size: 0.85rem; font-style: italic; }

        /* Categorized Grid View */
        .category-block {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px;
            margin-bottom: 20px;
        }
        .category-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .columns-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
            gap: 12px;
        }
        .col-card {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 100px;
            transition: all 0.2s;
        }
        .col-card.filled {
            border-color: rgba(56, 189, 248, 0.4);
            background: rgba(56, 189, 248, 0.04);
        }
        .col-card.empty { opacity: 0.65; }
        .col-card:hover { transform: translateY(-2px); border-color: var(--primary); opacity: 1; }
        .col-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
        .col-card-name { font-size: 0.82rem; font-weight: 600; color: #e2e8f0; line-height: 1.2; }
        .col-card-loinc { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--primary); }
        .col-card-value { font-size: 1.15rem; font-weight: 700; color: #fff; margin-top: 4px; }
        .col-card-unit { font-size: 0.75rem; color: var(--text-muted); margin-left: 4px; font-weight: normal; }
        .col-card-ref { font-size: 0.7rem; color: #64748b; margin-top: 4px; }

        /* Empty state */
        .empty-state { text-align: center; padding: 40px 20px; color: var(--text-muted); }
        .empty-state-icon { font-size: 40px; margin-bottom: 8px; }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(4px);
            z-index: 999;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .modal.open { display: flex; }
        .modal-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            max-width: 650px;
            width: 100%;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .modal-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body { padding: 20px; overflow-y: auto; }
        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px; }
        .form-control {
            width: 100%;
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            color: #fff;
            font-size: 0.88rem;
        }
        .form-control:focus { outline: none; border-color: var(--primary); }

        /* ==========================================================================
           MÓDULO DE CLASSIFICAÇÃO, HISTÓRICO LONGITUDINAL & INTERPRETAÇÃO RAG
           ========================================================================== */
        .biomarker-tabs-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
        }
        .bm-tab {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 9px 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #e2e8f0;
            font-size: 0.82rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .bm-tab:hover {
            border-color: var(--primary);
            transform: translateY(-1px);
            background: var(--surface-hover);
        }
        .bm-tab.active {
            background: rgba(56, 189, 248, 0.14);
            border-color: var(--primary);
            color: #fff;
            box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.35);
        }
        .bm-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }
        .bm-loinc-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            color: #94a3b8;
            background: rgba(0, 0, 0, 0.25);
            padding: 2px 6px;
            border-radius: 4px;
        }
        .bm-trend-pill {
            font-size: 0.72rem;
            font-weight: 800;
            padding: 1px 6px;
            border-radius: 999px;
            background: rgba(245, 158, 11, 0.18);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }

        /* Norma de 5 Classificações Clínicas (CLSI EP28-A3c / CTCAE Graus 1–4 / CAP) */
        .grad-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 11px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .grad-NORMAL {
            background: rgba(16, 185, 129, 0.14);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.40);
        }
        .grad-LIMITROFE {
            background: rgba(234, 179, 8, 0.15);
            color: #eab308;
            border: 1px solid rgba(234, 179, 8, 0.45);
        }
        .grad-ALTERADO_LEVE {
            background: rgba(245, 158, 11, 0.16);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.48);
        }
        .grad-ALTERADO_MODERADO {
            background: rgba(249, 115, 22, 0.16);
            color: #f97316;
            border: 1px solid rgba(249, 115, 22, 0.48);
        }
        .grad-ALTERACAO_ACENTUADA {
            background: rgba(239, 68, 68, 0.17);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.55);
        }
        .grad-INDETERMINADO {
            background: rgba(148, 163, 184, 0.12);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.30);
        }

        /* Seletor de Modo de Classificação (5 Estados vs 4 Níveis) */
        .toggle-norma-group {
            display: inline-flex;
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 3px;
            gap: 4px;
        }
        .toggle-norma-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .toggle-norma-btn:hover {
            color: #fff;
        }
        .toggle-norma-btn.active {
            background: rgba(56, 189, 248, 0.18);
            color: #38bdf8;
            font-weight: 700;
        }

        .status-summary-banner {
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }

        /* Interactive Chart Container & Tooltip */
        .chart-wrapper {
            position: relative;
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 16px 12px 16px;
            margin-bottom: 20px;
        }
        .chart-legend-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 10px;
            font-size: 0.78rem;
            color: var(--text-muted);
        }
        .legend-items {
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
            align-items: center;
        }
        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .chart-tooltip {
            position: absolute;
            pointer-events: none;
            background: rgba(15, 23, 42, 0.96);
            border: 1px solid var(--primary);
            border-radius: 10px;
            padding: 12px 14px;
            color: #f8fafc;
            font-size: 0.8rem;
            z-index: 50;
            min-width: 245px;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55);
            display: none;
            backdrop-filter: blur(6px);
        }

        /* RAG Interpretation Card */
        .btn-rag-interpret {
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
            color: #090d16;
            font-weight: 800;
            padding: 11px 22px;
            border: none;
            border-radius: 10px;
            font-size: 0.9rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 16px rgba(56, 189, 248, 0.25);
            transition: all 0.2s ease;
        }
        .btn-rag-interpret:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 22px rgba(129, 140, 248, 0.4);
        }
        .rag-card {
            display: none;
            background: linear-gradient(180deg, rgba(24, 34, 53, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
            border: 1px solid rgba(129, 140, 248, 0.45);
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 22px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        }
        .rag-card.open { display: block; }
        .rag-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-top: 14px;
        }
        .rag-block {
            background: rgba(9, 13, 22, 0.65);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
        }
        .rag-block h4 {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .rag-block p {
            font-size: 0.88rem;
            line-height: 1.55;
            color: #e2e8f0;
        }
        .doctor-questions-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 10px;
        }
        .doctor-question-item {
            background: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.28);
            border-radius: 8px;
            padding: 11px 14px;
            font-size: 0.86rem;
            color: #fff;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            line-height: 1.45;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Header -->
        <header>
            <div class="header-title">
                <div class="badge-system">🇧🇷 Open Health Brasil • HL7 FHIR (BR Core) & LOINC</div>
                <h1>Navegador Clínico & Banco Relacional <span>Open Health</span></h1>
                <p>Navegue de forma relacional: selecione um <strong>Paciente</strong>, visualize seus <strong>Laudos & Consentimentos LGPD</strong>, e entre nas <strong>Observações por Colunas</strong>.</p>
            </div>
            <div class="header-actions">
                <button class="btn-action" onclick="alternarPainelUpload()">📤 Anexar Novo Laudo em PDF</button>
                <button class="btn-secondary" onclick="recarregarVisaoAtual()">🔄 Atualizar</button>
                <button class="btn-danger" onclick="limparBancoGeral()">🗑️ Limpar Banco</button>
            </div>
        </header>

        <!-- Breadcrumb Bar -->
        <div class="breadcrumb-bar" id="breadcrumb-bar">
            <div class="bc-item" onclick="navegarParaPacientes()">👥 <strong>1. Pacientes</strong> (BR Core)</div>
            <div class="bc-sep" id="bc-sep-1" style="display:none;">›</div>
            <div class="bc-item" id="bc-paciente" style="display:none;" onclick="voltarParaPacienteAtual()">📑 Laudos & Consentimentos</div>
            <div class="bc-sep" id="bc-sep-2" style="display:none;">›</div>
            <div class="bc-item active" id="bc-laudo" style="display:none;">🔬 Observações por Colunas (LOINC)</div>
        </div>

        <!-- Collapsible Upload Panel -->
        <div class="upload-panel" id="upload-panel">
            <div class="upload-panel-header" onclick="alternarPainelUpload()">
                <div style="font-weight: 700; font-size: 0.95rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <span>📤 Upload de Laudo em PDF</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal;">(Clique para recolher/expandir)</span>
                </div>
                <div id="upload-toggle-icon" style="color: var(--primary); font-size: 1.1rem;">▲</div>
            </div>
            <div class="upload-body open" id="upload-body">
                <div class="engine-selector">
                    <label class="engine-option active" id="opt-nuvem" onclick="selecionarMotor('nuvem')">
                        <input type="radio" name="motor" value="nuvem" checked>
                        <div>
                            <div class="engine-title">☁️ Gemini 2.5 Flash (Nuvem)</div>
                            <div class="engine-desc">Padrão Structured Outputs de alta acurácia</div>
                        </div>
                    </label>
                    <label class="engine-option" id="opt-local" onclick="selecionarMotor('local')">
                        <input type="radio" name="motor" value="local">
                        <div>
                            <div class="engine-title">⚡ Modo Local Offline</div>
                            <div class="engine-desc">100% privado no dispositivo (Zero envio externo)</div>
                        </div>
                    </label>
                </div>

                <div class="upload-drop-area" id="drop-zone" onclick="document.getElementById('file-input').click()">
                    <input type="file" id="file-input" accept=".pdf" style="display:none;">
                    <div style="font-size: 32px; margin-bottom: 6px;">📄</div>
                    <h3 id="upload-title" style="font-size: 1.05rem; margin-bottom: 4px; font-weight: 600; color: #fff;">Clique ou arraste o Laudo em PDF aqui</h3>
                    <p id="upload-subtitle" style="color: var(--text-muted); font-size: 0.82rem;">Aceita PDFs de qualquer laboratório (Fleury, Dasa, Hermes Pardini, Einstein, etc.)</p>
                    <div style="margin-top: 14px;">
                        <button type="button" class="btn-action" id="btn-processar" onclick="event.stopPropagation(); enviarArquivo()" disabled>
                            ⚡ Processar & Inserir no Banco Relacional
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Loading Box -->
        <div class="loading-box" id="loading-box">
            <div class="spinner"></div>
            <h3 style="color: #fff; margin-bottom: 6px;">Processando Laudo & Alimentando Schema Open Health...</h3>
            <p style="color: var(--text-muted); font-size: 0.88rem;">Extraindo analitos, associando ao paciente e normalizando métricas com LOINC...</p>
        </div>

        <!-- ============================================================== -->
        <!-- NÍVEL 1: LISTA DE PACIENTES (patients - HL7 FHIR BR CORE)       -->
        <!-- ============================================================== -->
        <section class="view-section active" id="view-pacientes">
            <!-- Banner de Acesso Rápido aos 10 Laudos Unificados -->
            <div class="patient-info-banner" id="banner-quick-paciente" style="margin-bottom: 20px; border-color: rgba(56, 189, 248, 0.45); background: linear-gradient(135deg, rgba(24, 34, 53, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);">
                <div style="display:flex; justify-content:space-between; align-items:center; width:100%; flex-wrap:wrap; gap:14px;">
                    <div>
                        <div class="badge-system" style="margin-bottom:4px;">✨ Histórico Longitudinal Unificado Disponível</div>
                        <div style="font-size:1.15rem; font-weight:800; color:#fff;">
                            Janaina de Assis — 10 Laudos de 5 Laboratórios Integrados (2023 a 2026)
                        </div>
                        <div style="font-size:0.84rem; color:var(--text-muted); margin-top:2px;">
                            🏥 Frischmann Aisengart (DASA) • Fleury Medicina e Saúde • Hermes Pardini • Einstein • Sabin
                        </div>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn-action" onclick="abrirPacientePrincipal()">
                            📈 Abrir Prontuário Longitudinal & Gráfico →
                        </button>
                    </div>
                </div>
            </div>

            <!-- Tabela de Pacientes Cadastrados -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span>👤 Tabela de Pacientes</span>
                        <span class="badge badge-active" id="badge-total-pacientes">0 Pacientes</span>
                    </div>
                    <div>
                        <input type="text" class="search-box" id="search-paciente" placeholder="Buscar por Nome ou CPF..." onkeyup="filtrarPacientes()">
                    </div>
                </div>
                <div class="table-responsive">
                    <table id="table-pacientes">
                        <thead>
                            <tr>
                                <th>Paciente (Nome)</th>
                                <th>CPF (BR Core)</th>
                                <th>CNS (Cartão Saúde)</th>
                                <th>Data Nasc.</th>
                                <th>Sexo</th>
                                <th>Laudos Emitidos</th>
                                <th>Consentimento LGPD</th>
                                <th style="text-align: right;">Ação</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-pacientes">
                            <tr><td colspan="8" class="empty-state"><div class="empty-state-icon">👤</div>Carregando pacientes...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TABELA COM TODOS OS 10 LAUDOS UNIFICADOS DIRETO NA TELA PRINCIPAL -->
            <div class="card" style="margin-top: 24px; border-color: rgba(129, 140, 248, 0.35);">
                <div class="card-header">
                    <div>
                        <div class="card-title">
                            <span>📑 10 Laudos Laboratoriais Unificados na Rede Open Health</span>
                            <span class="badge badge-active" id="badge-total-laudos-geral">10 Laudos</span>
                        </div>
                        <p style="font-size:0.82rem; color:var(--text-muted); margin-top:3px;">
                            Rede interoperável com laudos do <strong>Frischmann Aisengart (DASA)</strong>, <strong>Fleury</strong>, <strong>Hermes Pardini</strong>, <strong>Albert Einstein</strong> e <strong>Sabin</strong>.
                        </p>
                    </div>
                </div>
                <div class="table-responsive">
                    <table id="table-todos-laudos-geral">
                        <thead>
                            <tr>
                                <th>Paciente</th>
                                <th>Laboratório de Origem</th>
                                <th>Data da Coleta</th>
                                <th>Data de Emissão</th>
                                <th>Versão</th>
                                <th>Assinatura ICP-Brasil (Hash)</th>
                                <th>Métricas LOINC</th>
                                <th style="text-align: right;">Ações Rápidas</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-todos-laudos-geral">
                            <tr><td colspan="8" class="empty-state">Carregando laudos unificados...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ============================================================== -->
        <!-- NÍVEL 2: DETALHES DO PACIENTE (consents + diagnostic_reports)    -->
        <!-- ============================================================== -->
        <section class="view-section" id="view-paciente-detalhe">
            <!-- Banner Dados do Paciente -->
            <div class="patient-info-banner" id="banner-paciente-info">
                <!-- Preenchido via JS -->
            </div>

            <!-- ========================================================================= -->
            <!-- MÓDULO PARTE 1: CLASSIFICAÇÃO, HISTÓRICO LONGITUDINAL E DISPLAY PACIENTE  -->
            <!-- ========================================================================= -->
            <div class="card" id="card-evolucao-paciente" style="border-color: rgba(56, 189, 248, 0.35);">
                <div class="card-header">
                    <div>
                        <div class="badge-system" style="margin-bottom: 6px;">📈 Módulo do Paciente • Norma de 5 Classificações Clínicas (CLSI EP28-A3c / CTCAE / CAP)</div>
                        <div class="card-title">
                            <span>Evolução Longitudinal de Biomarcadores & Interpretação Clínica (RAG)</span>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--text-muted); margin-top: 3px;">
                            Unificação cronológica de laudos de diferentes laboratórios por código <strong>LOINC</strong> com faixa de referência translúcida e a <strong>Norma de 5 Classificações Clínicas</strong>.
                        </p>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                        <div class="toggle-norma-group" title="Alterne entre a Norma de 5 Estados Clínicos ou a visão simplificada de 4 Níveis de Segurança">
                            <button type="button" class="toggle-norma-btn active" id="btn-norma-5" onclick="alternarModoNorma('5')">
                                🔬 Norma 5 Classificações
                            </button>
                            <button type="button" class="toggle-norma-btn" id="btn-norma-4" onclick="alternarModoNorma('4')">
                                🛡️ 4 Níveis UX Paciente
                            </button>
                        </div>
                        <button class="btn-rag-interpret" id="btn-entender-evolucao" onclick="acionarInterpretacaoRAG()">
                            ✨ Entender minha evolução
                        </button>
                    </div>
                </div>

                <!-- 1. Seletor Rápido de Biomarcadores (Abas por LOINC) -->
                <div style="font-size: 0.76rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; font-weight: 700;">
                    Selecione o Biomarcador (Filtro por Código LOINC):
                </div>
                <div class="biomarker-tabs-bar" id="biomarker-tabs-bar">
                    <!-- Preenchido dinamicamente via JS (Ferritina 2276-4, Hemoglobina 718-7, TSH 3016-3, Glicose 2345-7, etc.) -->
                </div>

                <!-- 2. Banner de Status Atual (Norma de 5 Classificações + Tendência ↗/↘) -->
                <div id="banner-status-gradiente" class="status-summary-banner" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35);">
                    <!-- Preenchido via JS -->
                </div>

                <!-- 3. Card de Interpretação RAG (POST /exams/interpret) -->
                <div class="rag-card" id="card-rag-resultado">
                    <!-- Preenchido via JS ao clicar em "Entender minha evolução" -->
                </div>

                <!-- 4. Gráfico de Evolução Temporal (SVG Interativo com Faixa Sombreada Translúcida e Tooltips) -->
                <div class="chart-wrapper" id="chart-wrapper-evolucao">
                    <div class="chart-legend-bar">
                        <div id="chart-title-analito" style="font-weight: 700; color: #fff; font-size: 0.92rem;">
                            Carregando gráfico longitudinal...
                        </div>
                        <div class="legend-items" id="legend-items-container">
                            <!-- Preenchido via renderizarLegendaGrafico() -->
                        </div>
                    </div>
                    <div id="svg-chart-container" style="width: 100%; overflow-x: auto;">
                        <!-- SVG renderizado via JS -->
                    </div>
                    <div class="chart-tooltip" id="chart-tooltip"></div>
                </div>

                <!-- 5. Lista / Histórico Cronológico de Laudos deste Biomarcador -->
                <div style="margin-top: 18px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px; flex-wrap:wrap; gap:8px;">
                        <h4 style="font-size: 0.92rem; color: #fff; font-weight: 700;">
                            📋 Histórico Cronológico Unificado do Biomarcador
                        </h4>
                        <span id="badge-labs-unificados" style="font-size: 0.76rem; color: var(--primary);"></span>
                    </div>
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>Data da Coleta</th>
                                    <th>Laboratório de Origem (Unificado)</th>
                                    <th>Resultado</th>
                                    <th>Faixa de Referência</th>
                                    <th>Posição / Desvio</th>
                                    <th id="th-col-classificacao">Classificação (Norma 5 Estados)</th>
                                    <th>Tendência Temporal</th>
                                </tr>
                            </thead>
                            <tbody id="tbody-historico-biomarcador">
                                <tr><td colspan="7" class="empty-state">Selecione um biomarcador acima.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
                            <tbody id="tbody-historico-biomarcador">
                                <tr><td colspan="7" class="empty-state">Selecione um biomarcador acima.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TABELA 4: CONSENTIMENTOS ANEXADOS AO PACIENTE (LGPD) -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span>🛡️ Consentimentos LGPD do Paciente</span>
                        <span class="badge badge-active" id="badge-total-consents">0</span>
                    </div>
                    <div>
                        <button class="btn-secondary btn-sm" onclick="abrirModalNovoConsentimento()">+ Conceder Novo Consentimento</button>
                    </div>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Hospital / Laboratório Origem</th>
                                <th>Destino Autorizado</th>
                                <th>Escopo</th>
                                <th>Status</th>
                                <th>Expira em</th>
                                <th>ID Consent (PK)</th>
                                <th style="text-align: right;">Ação</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-consents-paciente">
                            <tr><td colspan="7" class="empty-state">Nenhum consentimento registrado para este paciente.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TABELA 2: DIAGNOSTIC REPORTS DESTE PACIENTE -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span>📑 Laudos Laboratoriais (DiagnosticReports)</span>
                        <span class="badge badge-active" id="badge-total-reports">0</span>
                    </div>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Laboratório de Origem</th>
                                <th>Data da Coleta</th>
                                <th>Data de Emissão</th>
                                <th>Versão</th>
                                <th>Assinatura ICP-Brasil (Hash)</th>
                                <th>Total de Métricas</th>
                                <th style="text-align: right;">Ação</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-reports-paciente">
                            <tr><td colspan="7" class="empty-state">Nenhum laudo encontrado para este paciente.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ============================================================== -->
        <!-- NÍVEL 3: OBSERVATIONS DO LAUDO EXIBIDAS POR COLUNAS (LOINC)    -->
        <!-- ============================================================== -->
        <section class="view-section" id="view-laudo-observacoes">
            <!-- Banner Metadados do Laudo -->
            <div class="patient-info-banner" id="banner-laudo-info">
                <!-- Preenchido via JS -->
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span>🔬 Observações por Colunas (Padrão BR Core / LOINC)</span>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center;">
                        <span class="badge badge-active" id="stat-col-preenchidas">0 Preenchidas</span>
                        <span class="badge badge-vazio" id="stat-col-vazias">0 Vazias</span>
                        <span class="badge" style="background:#1e1b4b; color:#a5b4fc;" id="stat-col-total">Total: 113 Colunas</span>
                    </div>
                </div>

                <!-- Barra de Filtros das Colunas -->
                <div class="filters-toolbar">
                    <div class="filter-group">
                        <button class="pill-filter active" id="filter-all" onclick="aplicarFiltroColunas('todas')">Todas as 113 Colunas</button>
                        <button class="pill-filter" id="filter-filled" onclick="aplicarFiltroColunas('preenchidas')">Apenas Preenchidas (com resultado)</button>
                        <button class="pill-filter" id="filter-empty" onclick="aplicarFiltroColunas('vazias')">Apenas Colunas Vazias</button>
                    </div>
                    <div class="filter-group">
                        <select class="form-control" id="select-categoria" style="width: auto; padding: 7px 12px; font-size: 0.8rem;" onchange="filtrarPorCategoria()">
                            <option value="">Todas as Categorias Clínicas</option>
                            <option value="HEMOGRAMA">Hemograma Completo</option>
                            <option value="METABOLISMO">Metabolismo e Perfil Lipídico</option>
                            <option value="RENAL">Função Renal e Eletrólitos</option>
                            <option value="HEPÁTICA">Função Hepática e Biliar</option>
                            <option value="TIREOIDE">Tireoide e Hormônios</option>
                            <option value="INFLAMAÇÃO">Inflamação, Autoimunidade e Coagulação</option>
                            <option value="MARCADORES">Marcadores Tumorais e Cardíacos</option>
                        </select>
                        <input type="text" class="search-box" id="search-coluna" placeholder="Buscar analito ou LOINC (ex: 718-7)..." onkeyup="filtrarPorTextoColuna()">
                    </div>
                </div>

                <!-- Abas de Alternância de Exibição das Colunas -->
                <div style="display:flex; gap:8px; margin-bottom: 16px;">
                    <button class="btn-secondary btn-sm" id="btn-view-matrix" onclick="alternarModoExibicao('matrix')">📊 Exibição em Tabela de Colunas (Matriz Larga)</button>
                    <button class="btn-secondary btn-sm" id="btn-view-cards" onclick="alternarModoExibicao('cards')">📑 Exibição em Cartões Clínicos</button>
                </div>

                <!-- MODO 1: TABELA DE COLUNAS (MATRIZ HORIZONTAL LARGA) -->
                <div id="wrapper-matrix-view">
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px;">
                        👉 <em>Role horizontalmente para navegar por todas as colunas do laudo:</em>
                    </div>
                    <div class="matrix-container">
                        <table class="matrix-table" id="table-colunas-matriz">
                            <thead id="thead-matriz">
                                <!-- Colunas geradas via JS -->
                            </thead>
                            <tbody id="tbody-matriz">
                                <!-- Linha com os valores gerada via JS -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- MODO 2: CARTÕES AGRUPADOS POR CATEGORIA -->
                <div id="wrapper-cards-view" style="display:none;">
                    <div id="container-categorias-cards">
                        <!-- Categorias e cards de colunas gerados via JS -->
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- Modal Novo Consentimento -->
    <div class="modal" id="modal-novo-consent" onclick="fecharModalConsent(event)">
        <div class="modal-box" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h3 style="color: #fff; font-size: 1rem;">Conceder Novo Consentimento (LGPD)</h3>
                <button class="btn-secondary btn-sm" onclick="fecharModalConsent()">Fechar</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Hospital / Laboratório de Origem</label>
                    <input type="text" class="form-control" id="input-origem" value="Laboratório Frischmann Aisengart">
                </div>
                <div class="form-group">
                    <label>Hospital / Rede de Destino Autorizada</label>
                    <input type="text" class="form-control" id="input-destino" value="Hospital das Clínicas / ConecteSUS">
                </div>
                <div class="form-group">
                    <label>Escopo do Compartilhamento</label>
                    <input type="text" class="form-control" id="input-escopo" value="exames_sangue">
                </div>
                <div class="form-group">
                    <label>Validade da Concessão</label>
                    <select class="form-control" id="input-validade">
                        <option value="365">1 Ano (365 dias)</option>
                        <option value="180">6 Meses (180 dias)</option>
                        <option value="30">30 Dias</option>
                    </select>
                </div>
                <div style="text-align: right; margin-top: 18px;">
                    <button class="btn-action" onclick="salvarNovoConsentimento()">Salvar Consentimento</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let motorSelecionado = 'nuvem';
        let arquivoSelecionado = null;
        let pacienteAtualId = null;
        let laudoAtualId = null;
        let listaPacientesCache = [];
        let dadosLaudoColunasCache = null;
        let filtroColunaAtual = 'todas';
        let modoExibicaoAtual = 'matrix';

        // Inicialização com Abertura Direta do Prontuário
        document.addEventListener('DOMContentLoaded', async () => {
            await carregarListaPacientes();
            // Se existir paciente (Janaina de Assis), abre automaticamente seu prontuário com os 10 laudos e o gráfico longitudinal!
            if (listaPacientesCache && listaPacientesCache.length > 0) {
                const pacDefault = listaPacientesCache.find(p => p.nome.includes('Janaina')) || listaPacientesCache[0];
                await abrirPaciente(pacDefault.id);
            }
        });

        // Alternância do painel de upload
        function alternarPainelUpload() {
            const body = document.getElementById('upload-body');
            const icon = document.getElementById('upload-toggle-icon');
            if (body.classList.contains('open')) {
                body.classList.remove('open');
                icon.innerText = '▼';
            } else {
                body.classList.add('open');
                icon.innerText = '▲';
            }
        }

        function selecionarMotor(tipo) {
            motorSelecionado = tipo;
            document.querySelectorAll('.engine-option').forEach(el => el.classList.remove('active'));
            document.getElementById('opt-' + tipo).classList.add('active');
        }

        // Drag & Drop com Auto-Envio Imediato
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const btnProcessar = document.getElementById('btn-processar');

        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                arquivoSelecionado = e.dataTransfer.files[0];
                atualizarInterfaceArquivo();
                enviarArquivo();
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                arquivoSelecionado = fileInput.files[0];
                atualizarInterfaceArquivo();
                enviarArquivo();
            }
        });

        function atualizarInterfaceArquivo() {
            document.getElementById('upload-title').innerHTML = `Arquivo Selecionado: <strong>${arquivoSelecionado.name}</strong>`;
            document.getElementById('upload-subtitle').innerText = `Tamanho: ${(arquivoSelecionado.size / 1024).toFixed(1)} KB — Processando...`;
            btnProcessar.disabled = false;
        }

        async function enviarArquivo() {
            if (!arquivoSelecionado) return;
            document.getElementById('loading-box').style.display = 'block';
            btnProcessar.disabled = true;

            const formData = new FormData();
            formData.append('arquivo', arquivoSelecionado);
            formData.append('motor', motorSelecionado);

            try {
                const response = await fetch('/api/extrair', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.erro || 'Falha ao processar o exame');

                const msgMotor = data.motor || 'Padrão';
                const totalMetricas = (data.db_status && data.db_status.observacoes_inseridas) ? data.db_status.observacoes_inseridas : (data.exames ? data.exames.length : 0);
                alert(`✅ Sucesso! Exame processado e inserido no banco relacional.\nMotor: ${msgMotor}\nTotal de métricas LOINC: ${totalMetricas}\nAtualizando prontuário...`);
                // Redireciona e atualiza a visão do paciente
                await carregarListaPacientes();
                const targetPatient = (data.db_status && data.db_status.patient_id) || pacienteAtualId;
                if (targetPatient) {
                    await abrirPaciente(targetPatient);
                }
            } catch (err) {
                alert('Erro ao processar: ' + err.message);
            } finally {
                document.getElementById('loading-box').style.display = 'none';
                btnProcessar.disabled = false;
                if (fileInput) fileInput.value = '';
                arquivoSelecionado = null;
            }
        }

        // ==========================================
        // NAVEGAÇÃO ENTRE OS 3 NÍVEIS
        // ==========================================
        function navegarParaPacientes() {
            document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
            document.getElementById('view-pacientes').classList.add('active');
            
            document.getElementById('bc-sep-1').style.display = 'none';
            document.getElementById('bc-paciente').style.display = 'none';
            document.getElementById('bc-sep-2').style.display = 'none';
            document.getElementById('bc-laudo').style.display = 'none';
            
            pacienteAtualId = null;
            laudoAtualId = null;
            carregarListaPacientes();
        }

        function voltarParaPacienteAtual() {
            if (pacienteAtualId) {
                abrirPaciente(pacienteAtualId);
            }
        }

        // ==========================================
        // NÍVEL 1: CARREGAR LISTA DE PACIENTES
        // ==========================================
        let todosLaudosGeralCache = [];

        function abrirPacientePrincipal() {
            if (listaPacientesCache.length > 0) {
                const pac = listaPacientesCache.find(p => p.nome.includes('Janaina')) || listaPacientesCache[0];
                abrirPaciente(pac.id);
            } else {
                alert("Nenhum paciente encontrado.");
            }
        }

        async function carregarListaPacientes() {
            try {
                const res = await fetch('/api/pacientes');
                const pacientes = await res.json();
                listaPacientesCache = pacientes;
                document.getElementById('badge-total-pacientes').innerText = `${pacientes.length} Pacientes Cadastrados`;

                renderizarTabelaPacientes(pacientes);

                // Carrega também a lista unificada de todos os laudos na tela principal
                await carregarTodosLaudosGeral();
            } catch (e) {
                console.error("Erro ao listar pacientes:", e);
            }
        }

        async function carregarTodosLaudosGeral() {
            try {
                const res = await fetch('/api/todos_laudos');
                const laudos = await res.json();
                todosLaudosGeralCache = Array.isArray(laudos) ? laudos : [];

                const badgeTotal = document.getElementById('badge-total-laudos-geral');
                if (badgeTotal) badgeTotal.innerText = `${todosLaudosGeralCache.length} Laudos Unificados`;

                const tbody = document.getElementById('tbody-todos-laudos-geral');
                if (!tbody) return;

                if (todosLaudosGeralCache.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Nenhum laudo encontrado no banco relacional.</td></tr>`;
                    return;
                }

                tbody.innerHTML = todosLaudosGeralCache.map(r => `
                    <tr>
                        <td><strong>${r.nome_paciente}</strong></td>
                        <td><span style="color:var(--primary); font-weight:700;">🏥 ${r.laboratorio_origem}</span></td>
                        <td><strong>${r.data_coleta || '—'}</strong></td>
                        <td>${r.data_emissao || '—'}</td>
                        <td><span style="font-weight:700; color:var(--primary);">v${r.versao}</span></td>
                        <td><span class="hash-code" title="${r.assinatura_hash}">${r.assinatura_hash}</span></td>
                        <td><span class="badge badge-active">${r.total_observacoes} Métricas LOINC</span></td>
                        <td style="text-align: right; white-space: nowrap;">
                            <button class="btn-action btn-sm" onclick="abrirPaciente('${r.patient_id}')" style="margin-right:4px;">
                                📈 Ver no Gráfico
                            </button>
                            <button class="btn-secondary btn-sm" onclick="abrirLaudoObservacoes('${r.id}')">
                                🔬 Colunas LOINC
                            </button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error("Erro ao carregar todos os laudos:", err);
            }
        }

        function renderizarTabelaPacientes(pacientes) {
            const tbody = document.getElementById('tbody-pacientes');
            if (!pacientes || pacientes.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="empty-state"><div class="empty-state-icon">👤</div>Nenhum paciente cadastrado ainda. Envie um laudo em PDF para criar o primeiro!</td></tr>`;
                return;
            }

            tbody.innerHTML = pacientes.map(p => {
                const badgeConsent = p.total_consents_ativos > 0 
                    ? `<span class="badge badge-active">Ativo (${p.total_consents_ativos})</span>`
                    : `<span class="badge badge-revoked">Nenhum Ativo</span>`;

                return `
                    <tr>
                        <td><strong>${p.nome}</strong></td>
                        <td><code>${p.cpf}</code></td>
                        <td>${p.cns || '—'}</td>
                        <td>${p.data_nascimento || '—'}</td>
                        <td>${p.sexo_biologico || '—'}</td>
                        <td><span style="font-weight:700; color:var(--primary);">${p.total_reports} Laudo(s)</span></td>
                        <td>${badgeConsent}</td>
                        <td style="text-align: right;">
                            <button class="btn-action btn-sm" onclick="abrirPaciente('${p.id}')">
                                📂 Entrar no Paciente →
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function filtrarPacientes() {
            const q = document.getElementById('search-paciente').value.toLowerCase();
            const filtrados = listaPacientesCache.filter(p => 
                (p.nome && p.nome.toLowerCase().includes(q)) || 
                (p.cpf && p.cpf.toLowerCase().includes(q))
            );
            renderizarTabelaPacientes(filtrados);
        }

        // ==========================================
        // NÍVEL 2: ABRIR DETALHES DO PACIENTE
        // ==========================================
        async function abrirPaciente(patientId) {
            pacienteAtualId = patientId;
            try {
                const res = await fetch(`/api/paciente/${patientId}`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.erro || 'Falha ao buscar detalhes do paciente');

                const pac = data.paciente;
                const reports = data.reports || [];
                const consents = data.consents || [];

                // Atualiza Breadcrumbs
                document.getElementById('bc-sep-1').style.display = 'inline-block';
                const bcPac = document.getElementById('bc-paciente');
                bcPac.style.display = 'inline-flex';
                bcPac.innerHTML = `👤 <strong>${pac.nome}</strong>`;
                document.getElementById('bc-sep-2').style.display = 'none';
                document.getElementById('bc-laudo').style.display = 'none';

                // Banner de Informações do Paciente
                document.getElementById('banner-paciente-info').innerHTML = `
                    <div class="info-col"><label>Nome do Paciente</label><div>${pac.nome}</div></div>
                    <div class="info-col"><label>CPF (BR Core)</label><div>${pac.cpf}</div></div>
                    <div class="info-col"><label>CNS (SUS)</label><div>${pac.cns || '—'}</div></div>
                    <div class="info-col"><label>Data Nascimento</label><div>${pac.data_nascimento || '—'}</div></div>
                    <div class="info-col"><label>Sexo Biológico</label><div>${pac.sexo_biologico || '—'}</div></div>
                    <div class="info-col"><label>UUID Paciente (PK)</label><div><span class="uuid-code" title="${pac.id}">${pac.id}</span></div></div>
                `;

                // Tabela de Consentimentos Anexados ao Paciente
                document.getElementById('badge-total-consents').innerText = `${consents.length} Consentimentos`;
                const tbodyConsents = document.getElementById('tbody-consents-paciente');
                if (consents.length === 0) {
                    tbodyConsents.innerHTML = `<tr><td colspan="7" class="empty-state">Nenhum consentimento cadastrado para este paciente.</td></tr>`;
                } else {
                    tbodyConsents.innerHTML = consents.map(c => `
                        <tr>
                            <td><strong>${c.hospital_origem}</strong></td>
                            <td>${c.hospital_destino}</td>
                            <td><code>${c.escopo}</code></td>
                            <td><span class="badge ${c.status === 'ativo' ? 'badge-active' : 'badge-revoked'}">${c.status.toUpperCase()}</span></td>
                            <td>${c.expira_em || 'Indeterminado'}</td>
                            <td><span class="uuid-code" title="${c.id}">${c.id}</span></td>
                            <td style="text-align: right;">
                                <button class="btn-secondary btn-sm" onclick="alternarConsentimento('${c.id}')">
                                    ${c.status === 'ativo' ? 'Revogar Autorização' : 'Reativar'}
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }

                // Tabela de DiagnosticReports do Paciente
                document.getElementById('badge-total-reports').innerText = `${reports.length} Laudos`;
                const tbodyReports = document.getElementById('tbody-reports-paciente');
                if (reports.length === 0) {
                    tbodyReports.innerHTML = `<tr><td colspan="7" class="empty-state">Nenhum laudo emitido para este paciente.</td></tr>`;
                } else {
                    tbodyReports.innerHTML = reports.map(r => `
                        <tr>
                            <td><strong>${r.laboratorio_origem}</strong></td>
                            <td>${r.data_coleta || '—'}</td>
                            <td>${r.data_emissao || '—'}</td>
                            <td><span style="font-weight:700; color:var(--primary);">v${r.versao}</span></td>
                            <td><span class="hash-code" title="${r.assinatura_hash}">${r.assinatura_hash}</span></td>
                            <td><span class="badge badge-active">${r.total_observacoes} Métricas LOINC</span></td>
                            <td style="text-align: right;">
                                <button class="btn-action btn-sm" onclick="abrirLaudoObservacoes('${r.id}')">
                                    🔬 Entrar nas Observações (Ver por Colunas) →
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }

                // Alterna visualização
                document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
                document.getElementById('view-paciente-detalhe').classList.add('active');

                // Carrega o Módulo Parte 1: Evolução Longitudinal & Classificação por Gradiente
                await carregarBiomarcadoresPaciente(patientId);

            } catch (e) {
                alert("Erro ao carregar detalhes do paciente: " + e.message);
            }
        }

        // =========================================================================
        // MÓDULO PARTE 1: EVOLUÇÃO LONGITUDINAL, NORMA DE 5 CLASSIFICAÇÕES E RAG
        // =========================================================================
        let biomarcadoresCache = [];
        let loincSelecionadoAtual = '2276-4';
        let evolucaoAtualCache = null;
        let modoNormaAtual = '5'; // '5': Norma de 5 Classificações Clínicas | '4': 4 Níveis Simplificados UX

        function alternarModoNorma(modo) {
            modoNormaAtual = modo;
            const btn5 = document.getElementById('btn-norma-5');
            const btn4 = document.getElementById('btn-norma-4');
            if (btn5) btn5.classList.toggle('active', modo === '5');
            if (btn4) btn4.classList.toggle('active', modo === '4');

            const thClass = document.getElementById('th-col-classificacao');
            if (thClass) {
                thClass.innerText = modo === '5' ? 'Classificação (Norma 5 Estados)' : 'Classificação (4 Níveis UX)';
            }

            renderizarLegendaGrafico();
            if (evolucaoAtualCache) {
                renderizarBannerGradienteAtual(evolucaoAtualCache);
                renderizarGraficoEvolucaoSVG(evolucaoAtualCache);
                renderizarTabelaHistoricoBiomarcador(evolucaoAtualCache);
            }
            renderizarAbasBiomarcadores();
        }

        function obterClassificacaoAtiva(clf) {
            if (!clf) {
                return {
                    nivel: 0,
                    codigo: 'INDETERMINADO',
                    rotulo: 'Sem Faixa',
                    cor_nome: 'Cinza',
                    cor_hex: '#94a3b8',
                    cor_bg: 'rgba(148, 163, 184, 0.12)',
                    cor_borda: 'rgba(148, 163, 184, 0.30)',
                    mensagem_paciente: 'Consulte a referência textual do laudo com seu médico.',
                    equivalencia_clinica: 'Sem Faixa Numérica'
                };
            }
            if (modoNormaAtual === '4' && clf.norma_4_niveis) {
                const n4 = clf.norma_4_niveis;
                const bgMap = {
                    '#10b981': 'rgba(16, 185, 129, 0.14)',
                    '#f59e0b': 'rgba(245, 158, 11, 0.15)',
                    '#f97316': 'rgba(249, 115, 22, 0.15)',
                    '#ef4444': 'rgba(239, 68, 68, 0.16)'
                };
                return {
                    nivel: n4.nivel_4,
                    codigo: n4.codigo_4,
                    rotulo: n4.rotulo_4,
                    cor_nome: n4.cor_nome_4,
                    cor_hex: n4.cor_hex_4,
                    cor_bg: bgMap[n4.cor_hex_4] || 'rgba(148, 163, 184, 0.12)',
                    cor_borda: n4.cor_hex_4,
                    mensagem_paciente: n4.mensagem_4,
                    equivalencia_clinica: 'Mapeamento UX Paciente (4 Níveis Seguros)'
                };
            }
            return clf; // Norma de 5 Classificações por padrão
        }

        function renderizarLegendaGrafico() {
            const container = document.getElementById('legend-items-container');
            if (!container) return;
            const refMin = evolucaoAtualCache ? evolucaoAtualCache.faixa_referencia_min : null;
            const refMax = evolucaoAtualCache ? evolucaoAtualCache.faixa_referencia_max : null;
            const unid = evolucaoAtualCache ? evolucaoAtualCache.unidade : '';
            const refTxt = (refMin !== null && refMax !== null) ? `${refMin} – ${refMax} ${unid}` : '—';

            if (modoNormaAtual === '5') {
                container.innerHTML = `
                    <span class="legend-item">
                        <span style="width:14px; height:10px; background:rgba(16, 185, 129, 0.18); border:1px dashed #10b981; display:inline-block; border-radius:2px;"></span>
                        Faixa de Referência (<span id="legend-ref-range">${refTxt}</span>)
                    </span>
                    <span class="legend-item"><span class="bm-dot" style="background:#10b981;"></span> 1. Normal (10%–90%)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#eab308;"></span> 2. Limítrofe (&lt;10% / &gt;90% int.)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f59e0b;"></span> 3. Alterado Leve (&le;15% ext. / Grau 1)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f97316;"></span> 4. Alterado Moderado (15%–50% / Grau 2)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#ef4444;"></span> 5. Alteração Acentuada (&gt;50% / Grau 3–4)</span>
                `;
            } else {
                container.innerHTML = `
                    <span class="legend-item">
                        <span style="width:14px; height:10px; background:rgba(16, 185, 129, 0.18); border:1px dashed #10b981; display:inline-block; border-radius:2px;"></span>
                        Faixa de Referência (<span id="legend-ref-range">${refTxt}</span>)
                    </span>
                    <span class="legend-item"><span class="bm-dot" style="background:#10b981;"></span> Normal (10%–90%)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f59e0b;"></span> Limítrofe / Atenção (&lt;10% / &gt;90% ou &le;15% ext.)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f97316;"></span> Alterado Moderado (15%–50%)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#ef4444;"></span> Alteração Acentuada (&gt;50%)</span>
                `;
            }
        }

        async function carregarBiomarcadoresPaciente(patientId) {
            try {
                const res = await fetch(`/api/paciente/${patientId}/biomarcadores`);
                const lista = await res.json();
                biomarcadoresCache = Array.isArray(lista) ? lista : [];

                const tabsContainer = document.getElementById('biomarker-tabs-bar');
                if (biomarcadoresCache.length === 0) {
                    tabsContainer.innerHTML = `<div style="color:var(--text-muted); font-size:0.84rem;">Nenhum biomarcador numérico registrado para este paciente.</div>`;
                    return;
                }

                // Seleciona Ferritina (2276-4) por padrão se existir, ou o primeiro da lista
                const temAtual = biomarcadoresCache.some(b => b.codigo_loinc === loincSelecionadoAtual);
                if (!temAtual) {
                    const ferritina = biomarcadoresCache.find(b => b.codigo_loinc === '2276-4');
                    loincSelecionadoAtual = ferritina ? '2276-4' : biomarcadoresCache[0].codigo_loinc;
                }

                renderizarAbasBiomarcadores();
                await selecionarBiomarcador(loincSelecionadoAtual);
            } catch (err) {
                console.error("Erro ao carregar biomarcadores:", err);
            }
        }

        function renderizarAbasBiomarcadores() {
            const tabsContainer = document.getElementById('biomarker-tabs-bar');
            tabsContainer.innerHTML = biomarcadoresCache.map(bm => {
                const isActive = bm.codigo_loinc === loincSelecionadoAtual ? 'active' : '';
                const clfAtivo = obterClassificacaoAtiva(bm.classificacao_atual);
                const corDot = clfAtivo.cor_hex || '#10b981';
                const tend = bm.tendencia_atual || {};
                const badgeTend = tend.exibir_badge_tendencia
                    ? `<span class="bm-trend-pill" title="${tend.texto_tendencia}">${tend.seta} ${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}%</span>`
                    : (tend.seta && tend.seta !== '→' ? `<span style="color:#94a3b8; font-size:0.75rem;">${tend.seta}</span>` : '');

                return `
                    <button type="button" class="bm-tab ${isActive}" onclick="selecionarBiomarcador('${bm.codigo_loinc}')">
                        <span class="bm-dot" style="background:${corDot};"></span>
                        <span>${bm.nome_exame}</span>
                        <span class="bm-loinc-tag">${bm.codigo_loinc}</span>
                        ${badgeTend}
                    </button>
                `;
            }).join('');
        }

        async function selecionarBiomarcador(codigoLoinc) {
            loincSelecionadoAtual = codigoLoinc;
            renderizarAbasBiomarcadores();
            const ragCard = document.getElementById('card-rag-resultado');
            if (ragCard) {
                ragCard.classList.remove('open');
                ragCard.innerHTML = '';
            }

            try {
                const res = await fetch(`/api/paciente/${pacienteAtualId}/evolucao/${encodeURIComponent(codigoLoinc)}`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.erro || 'Erro ao buscar evolução do biomarcador');

                evolucaoAtualCache = data;
                renderizarLegendaGrafico();
                renderizarBannerGradienteAtual(data);
                renderizarGraficoEvolucaoSVG(data);
                renderizarTabelaHistoricoBiomarcador(data);
            } catch (err) {
                console.error("Erro na evolução do biomarcador:", err);
            }
        }

        function renderizarBannerGradienteAtual(data) {
            const banner = document.getElementById('banner-status-gradiente');
            const ultimo = data.ultimo_resultado;
            const clfOriginal = ultimo.classificacao;
            const clfAtivo = obterClassificacaoAtiva(clfOriginal);
            const tend = ultimo.tendencia;

            banner.style.background = clfAtivo.cor_bg;
            banner.style.border = `1px solid ${clfAtivo.cor_borda}`;

            const metricPosDesvio = clfOriginal.dentro_faixa
                ? `Posição na faixa: <strong>${clfOriginal.posicao_percentual}%</strong> (Largura: ${clfOriginal.largura_faixa} ${data.unidade})`
                : `Desvio além da borda: <strong>${clfOriginal.desvio_percentual}%</strong> (${clfOriginal.direcao_desvio === 'ABAIXO_DO_MINIMO' ? 'abaixo do mínimo' : 'acima do máximo'})`;

            const badgeTendenciaHtml = tend.exibir_badge_tendencia
                ? `<span class="bm-trend-pill" style="font-size:0.8rem; padding:4px 10px;">⚠️ ${tend.texto_tendencia}</span>`
                : (tend.possui_historico ? `<span style="font-size:0.8rem; color:#cbd5e1;">${tend.seta || '→'} ${tend.texto_tendencia}</span>` : '');

            const rotuloModo = modoNormaAtual === '5'
                ? `● Nível ${clfAtivo.nivel} (Norma 5): ${clfAtivo.rotulo} (${clfAtivo.cor_nome})`
                : `● Nível ${clfAtivo.nivel} (UX 4): ${clfAtivo.rotulo} (${clfAtivo.cor_nome})`;

            banner.innerHTML = `
                <div>
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:6px;">
                        <span style="font-size:1.25rem; font-weight:800; color:#fff;">
                            ${data.nome_exame}: ${ultimo.valor_numerico} ${data.unidade}
                        </span>
                        <span class="grad-badge grad-${clfAtivo.codigo}">
                            ${rotuloModo}
                        </span>
                        ${badgeTendenciaHtml}
                    </div>
                    <div style="font-size:0.88rem; color:#f8fafc; font-weight:500; margin-bottom:4px;">
                        💬 ${clfAtivo.mensagem_paciente}
                    </div>
                    <div style="font-size:0.76rem; color:#94a3b8;">
                        📐 ${metricPosDesvio} • Referência: <strong>${data.faixa_referencia_min} a ${data.faixa_referencia_max} ${data.unidade}</strong> • Base: ${clfAtivo.equivalencia_clinica}
                    </div>
                </div>
                <div style="text-align:right; font-size:0.78rem; color:#cbd5e1;">
                    <div>Última coleta: <strong>${ultimo.data_coleta}</strong></div>
                    <div>Origem: <strong style="color:var(--primary);">${ultimo.laboratorio_origem}</strong></div>
                </div>
            `;
        }

        function renderizarGraficoEvolucaoSVG(data) {
            const container = document.getElementById('svg-chart-container');
            const serie = data.serie_temporal || [];
            const refMin = data.faixa_referencia_min;
            const refMax = data.faixa_referencia_max;

            document.getElementById('chart-title-analito').innerHTML = `
                 Evolução Longitudinal — <span style="color:var(--primary);">${data.nome_exame} (LOINC ${data.codigo_loinc})</span> em ${serie.length} coletas
            `;

            if (serie.length === 0) {
                container.innerHTML = `<div class="empty-state">Sem pontos numéricos para plotar.</div>`;
                return;
            }

            const width = 960;
            const height = 320;
            const padLeft = 64;
            const padRight = 36;
            const padTop = 28;
            const padBottom = 52;
            const plotW = width - padLeft - padRight;
            const plotH = height - padTop - padBottom;

            const valores = serie.map(s => Number(s.valor_numerico));
            let minVal = Math.min(...valores);
            let maxVal = Math.max(...valores);
            if (refMin !== null && refMin !== undefined) minVal = Math.min(minVal, Number(refMin));
            if (refMax !== null && refMax !== undefined) maxVal = Math.max(maxVal, Number(refMax));

            const span = (maxVal - minVal) || (Math.abs(maxVal) * 0.2) || 10;
            const yMin = Math.max(0, minVal - span * 0.18);
            const yMax = maxVal + span * 0.18;

            const toX = (i) => serie.length === 1
                ? padLeft + plotW / 2
                : padLeft + (i / (serie.length - 1)) * plotW;
            const toY = (v) => padTop + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

            // 1. Linhas de grade horizontais (Eixo Y)
            let gridHtml = '';
            const stepsY = 5;
            for (let i = 0; i <= stepsY; i++) {
                const valY = yMin + (i / stepsY) * (yMax - yMin);
                const py = toY(valY);
                gridHtml += `
                    <line x1="${padLeft}" y1="${py}" x2="${width - padRight}" y2="${py}" stroke="rgba(148, 163, 184, 0.12)" stroke-width="1" />
                    <text x="${padLeft - 10}" y="${py + 4}" text-anchor="end" fill="#94a3b8" font-size="11" font-family="JetBrains Mono, monospace">
                        ${valY.toFixed(valY < 10 ? 2 : 1)}
                    </text>
                `;
            }

            // 2. FAIXA SOMBREADA TRANSLÚCIDA OBRIGATÓRIA (faixa_referencia_min a faixa_referencia_max)
            let refBandHtml = '';
            if (refMin !== null && refMax !== null && refMax > refMin) {
                const yTopRef = toY(Number(refMax));
                const yBotRef = toY(Number(refMin));
                const bandH = Math.max(2, yBotRef - yTopRef);

                // Zonas internas de 10% e 90% (fronteira Limítrofe CLSI)
                const largRef = Number(refMax) - Number(refMin);
                const y90 = toY(Number(refMin) + 0.90 * largRef);
                const y10 = toY(Number(refMin) + 0.10 * largRef);

                // Zonas externas de até 15% (CTCAE Grau 1 - Alterado Leve)
                const yExtSup15 = toY(Number(refMax) + 0.15 * largRef);
                const yExtInf15 = toY(Math.max(0, Number(refMin) - 0.15 * largRef));

                refBandHtml = `
                    <!-- Faixa de Referência Normal Sombreada Translúcida (CLSI EP28-A3c) -->
                    <rect x="${padLeft}" y="${yTopRef}" width="${plotW}" height="${bandH}"
                          fill="rgba(16, 185, 129, 0.13)" />
                    <!-- Linha tracejada externa de 15% (Borda Alterado Leve Grau 1) -->
                    <line x1="${padLeft}" y1="${yExtSup15}" x2="${width - padRight}" y2="${yExtSup15}"
                          stroke="rgba(245, 158, 11, 0.35)" stroke-width="1" stroke-dasharray="2,4" />
                    <line x1="${padLeft}" y1="${yExtInf15}" x2="${width - padRight}" y2="${yExtInf15}"
                          stroke="rgba(245, 158, 11, 0.35)" stroke-width="1" stroke-dasharray="2,4" />
                    <!-- Guias sutis de 10% e 90% internos (Zona Limítrofe Interna) -->
                    <line x1="${padLeft}" y1="${y90}" x2="${width - padRight}" y2="${y90}"
                          stroke="rgba(234, 179, 8, 0.40)" stroke-width="1" stroke-dasharray="3,4" />
                    <line x1="${padLeft}" y1="${y10}" x2="${width - padRight}" y2="${y10}"
                          stroke="rgba(234, 179, 8, 0.40)" stroke-width="1" stroke-dasharray="3,4" />
                    <!-- Bordas Superior (Max) e Inferior (Min) -->
                    <line x1="${padLeft}" y1="${yTopRef}" x2="${width - padRight}" y2="${yTopRef}"
                          stroke="rgba(16, 185, 129, 0.70)" stroke-width="1.5" stroke-dasharray="6,4" />
                    <line x1="${padLeft}" y1="${yBotRef}" x2="${width - padRight}" y2="${yBotRef}"
                          stroke="rgba(16, 185, 129, 0.70)" stroke-width="1.5" stroke-dasharray="6,4" />
                    <text x="${width - padRight - 6}" y="${yTopRef - 5}" text-anchor="end" fill="#34d399" font-size="10" font-weight="600">
                        Máx: ${refMax} ${data.unidade}
                    </text>
                    <text x="${width - padRight - 6}" y="${yBotRef + 13}" text-anchor="end" fill="#34d399" font-size="10" font-weight="600">
                        Mín: ${refMin} ${data.unidade}
                    </text>
                `;
            }

            // 3. Linha de conexão temporal dos resultados
            const coords = serie.map((s, idx) => ({ x: toX(idx), y: toY(Number(s.valor_numerico)), item: s, idx }));
            const pathD = coords.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(' ');

            // 4. Pontos interativos coloridos pelo gradiente ativo + rótulos eixo X
            let pointsHtml = '';
            coords.forEach(pt => {
                const clfAtivo = obterClassificacaoAtiva(pt.item.classificacao);
                const cor = clfAtivo.cor_hex || '#38bdf8';
                const setaTend = pt.item.tendencia && pt.item.tendencia.exibir_badge_tendencia
                    ? pt.item.tendencia.seta
                    : '';

                pointsHtml += `
                    <!-- Rótulo Data Coleta Eixo X -->
                    <text x="${pt.x}" y="${height - 18}" text-anchor="middle" fill="#cbd5e1" font-size="11" font-weight="500">
                        ${pt.item.data_coleta}
                    </text>
                    <!-- Valor acima do ponto -->
                    <text x="${pt.x}" y="${pt.y - 12}" text-anchor="middle" fill="${cor}" font-size="11" font-weight="700" font-family="JetBrains Mono, monospace">
                        ${pt.item.valor_numerico}${setaTend ? ' ' + setaTend : ''}
                    </text>
                    <!-- Halo e Círculo Interativo -->
                    <circle cx="${pt.x}" cy="${pt.y}" r="11" fill="${cor}" fill-opacity="0.18"
                            style="cursor:pointer;"
                            onmouseenter="mostrarTooltipPonto(event, ${pt.idx})"
                            onmousemove="moverTooltipPonto(event)"
                            onmouseleave="ocultarTooltipPonto()" />
                    <circle cx="${pt.x}" cy="${pt.y}" r="6" fill="${cor}" stroke="#090d16" stroke-width="2"
                            style="cursor:pointer;"
                            onmouseenter="mostrarTooltipPonto(event, ${pt.idx})"
                            onmousemove="moverTooltipPonto(event)"
                            onmouseleave="ocultarTooltipPonto()" />
                `;
            });

            container.innerHTML = `
                <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:auto; min-width:680px; display:block;">
                    ${gridHtml}
                    ${refBandHtml}
                    <path d="${pathD}" fill="none" stroke="#38bdf8" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
                    ${pointsHtml}
                </svg>
            `;
        }

        function mostrarTooltipPonto(event, idx) {
            if (!evolucaoAtualCache || !evolucaoAtualCache.serie_temporal[idx]) return;
            const pt = evolucaoAtualCache.serie_temporal[idx];
            const clfOrig = pt.classificacao;
            const clfAtivo = obterClassificacaoAtiva(clfOrig);
            const tend = pt.tendencia;
            const tooltip = document.getElementById('chart-tooltip');

            const posOuDesvio = clfOrig.dentro_faixa
                ? `Posição na faixa: ${clfOrig.posicao_percentual}%`
                : `Desvio da borda: ${clfOrig.desvio_percentual}%`;

            tooltip.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; border-bottom:1px solid #24324c; padding-bottom:6px;">
                    <strong style="color:#fff; font-size:0.86rem;">📅 ${pt.data_coleta}</strong>
                    <span class="grad-badge grad-${clfAtivo.codigo}" style="font-size:0.68rem; padding:2px 8px;">
                        ${clfAtivo.rotulo} (${clfAtivo.cor_nome})
                    </span>
                </div>
                <div style="font-size:1.05rem; font-weight:800; color:${clfAtivo.cor_hex}; margin-bottom:4px;">
                    Resultado: ${pt.valor_numerico} ${pt.unidade || evolucaoAtualCache.unidade}
                    ${tend && tend.seta ? `<span style="color:#fbbf24; font-size:0.82rem; margin-left:4px;">${tend.seta} (${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}%)</span>` : ''}
                </div>
                <div style="font-size:0.76rem; color:#cbd5e1; margin-bottom:4px;">
                    🏥 <strong>Laboratório:</strong> <span style="color:#38bdf8; font-weight:700;">${pt.laboratorio_origem}</span>
                </div>
                <div style="font-size:0.73rem; color:#94a3b8; margin-bottom:3px;">
                    🎯 Ref: ${pt.faixa_referencia_min} a ${pt.faixa_referencia_max} ${pt.unidade || evolucaoAtualCache.unidade} • ${posOuDesvio}
                </div>
                <div style="font-size:0.70rem; color:#a5b4fc;">
                    📐 ${clfOrig.equivalencia_clinica}
                </div>
            `;
            tooltip.style.display = 'block';
            moverTooltipPonto(event);
        }

        function moverTooltipPonto(event) {
            const wrapper = document.getElementById('chart-wrapper-evolucao');
            const tooltip = document.getElementById('chart-tooltip');
            const rect = wrapper.getBoundingClientRect();
            let left = event.clientX - rect.left + 14;
            let top = event.clientY - rect.top - 20;
            if (left + 260 > rect.width) left = event.clientX - rect.left - 265;
            if (top < 10) top = 10;
            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        }

        function ocultarTooltipPonto() {
            const tooltip = document.getElementById('chart-tooltip');
            if (tooltip) tooltip.style.display = 'none';
        }

        function renderizarTabelaHistoricoBiomarcador(data) {
            const tbody = document.getElementById('tbody-historico-biomarcador');
            const labsBadge = document.getElementById('badge-labs-unificados');
            const labs = data.laboratorios_unificados || [];
            labsBadge.innerHTML = `🔗 <strong>${labs.length} Laboratórios Unificados:</strong> ${labs.join(' • ')}`;

            // Exibe em ordem cronológica reversa (mais recente no topo) na tabela
            const invertida = [...(data.serie_temporal || [])].reverse();
            tbody.innerHTML = invertida.map(item => {
                const clfOrig = item.classificacao;
                const clfAtivo = obterClassificacaoAtiva(clfOrig);
                const tend = item.tendencia;
                const posTxt = clfOrig.dentro_faixa
                    ? `Posição: <strong>${clfOrig.posicao_percentual}%</strong> (interna)`
                    : `Desvio: <strong>${clfOrig.desvio_percentual}%</strong> (externo)`;

                const tendHtml = !tend.possui_historico
                    ? `<span style="color:#64748b; font-size:0.76rem;">1º Registro</span>`
                    : (tend.exibir_badge_tendencia
                        ? `<span class="bm-trend-pill">${tend.seta} ${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}% (Alerta Borda)</span>`
                        : `<span style="color:#cbd5e1; font-size:0.8rem;">${tend.seta} ${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}%</span>`);

                return `
                    <tr>
                        <td><strong>${item.data_coleta}</strong></td>
                        <td><span style="color:var(--primary); font-weight:600;">🏥 ${item.laboratorio_origem}</span></td>
                        <td style="font-family:'JetBrains Mono', monospace; font-weight:700; font-size:0.92rem; color:#fff;">
                            ${item.valor_numerico} ${item.unidade || data.unidade}
                        </td>
                        <td>${item.faixa_referencia_min} a ${item.faixa_referencia_max} ${item.unidade || data.unidade}</td>
                        <td style="font-size:0.78rem; color:#cbd5e1;">${posTxt}</td>
                        <td>
                            <span class="grad-badge grad-${clfAtivo.codigo}">
                                ● ${clfAtivo.rotulo} (${clfAtivo.cor_nome})
                            </span>
                        </td>
                        <td>${tendHtml}</td>
                    </tr>
                `;
            }).join('');
        }

        async function acionarInterpretacaoRAG() {
            if (!pacienteAtualId || !loincSelecionadoAtual) return;
            const btn = document.getElementById('btn-entender-evolucao');
            const card = document.getElementById('card-rag-resultado');
            const textoOriginal = btn.innerHTML;

            btn.disabled = true;
            btn.innerHTML = `⏳ Carregando Interpretação Determinística...`;

            try {
                const res = await fetch('/exams/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pacienteAtualId,
                        codigo_loinc: loincSelecionadoAtual,
                        usar_llm: false
                    })
                });
                const payload = await res.json();
                if (!res.ok) throw new Error(payload.erro || 'Falha ao interpretar evolução');

                const interp = payload.interpretacao_paciente;
                const meta = payload.rag_metadata || {};
                const clfAtivo = obterClassificacaoAtiva(payload.classificacao_atual);
                const pilares = interp.cinco_pilares_18_25 || {};

                const perguntasHtml = (interp.perguntas_para_o_medico || []).map((q, idx) => `
                    <li class="doctor-question-item">
                        <span style="background:var(--primary); color:#090d16; font-weight:800; border-radius:50%; width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; font-size:0.75rem;">
                            ${idx + 1}
                        </span>
                        <span>"${q}"</span>
                    </li>
                `).join('');

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap; border-bottom:1px solid var(--border); padding-bottom:12px;">
                        <div>
                            <div style="font-size:0.74rem; color:var(--primary); font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">
                                📋 Interpretação Clínica Determinística • Faixa Etária 18 a 25 Anos
                            </div>
                            <h3 style="color:#fff; font-size:1.15rem; margin-top:3px;">
                                ${payload.nome_exame} <span style="font-size:0.85rem; color:var(--text-muted);">(LOINC ${payload.codigo_loinc})</span>
                            </h3>
                        </div>
                        <span class="grad-badge grad-${clfAtivo.codigo}" style="font-size:0.84rem; padding:6px 14px;">
                            Classificação: ${clfAtivo.rotulo} (${clfAtivo.cor_nome})
                        </span>
                    </div>

                    <!-- RESUMO DO EXAME (113 TEXTOS) -->
                    <div class="rag-block" style="margin-top:14px; border-left:4px solid var(--primary); background:rgba(56, 189, 248, 0.05);">
                        <h4 style="color:var(--primary);">🔬 Resumo do Exame e Papel no Organismo</h4>
                        <p style="font-size:0.92rem; color:#f8fafc; line-height:1.6;">${interp.resumo_exame || interp.resumo_acessivel}</p>
                    </div>

                    <!-- TENDÊNCIA NOS ÚLTIMOS EXAMES -->
                    <div class="rag-block" style="margin-top:10px; border-left:4px solid var(--accent); background:rgba(129, 140, 248, 0.05);">
                        <h4 style="color:var(--accent);">📈 Evolução nos Seus Laudos Unificados</h4>
                        <p style="font-size:0.88rem; color:#e2e8f0; line-height:1.55;">${interp.analise_tendencia_numerica}</p>
                    </div>

                    <!-- OS 5 PILARES DETERMINÍSTICOS DO RESULTADO (565 TEXTOS) -->
                    <div style="margin-top:18px;">
                        <h4 style="font-size:0.88rem; text-transform:uppercase; letter-spacing:0.05em; color:#fff; margin-bottom:12px;">
                            🎯 Resumo Estruturado do Resultado (Padrão Open Health):
                        </h4>
                        <div class="rag-grid">
                            <div class="rag-block" style="border-top:3px solid ${clfAtivo.cor_hex};">
                                <h4 style="color:${clfAtivo.cor_hex};">1. Descrição do Resultado</h4>
                                <p>${pilares['1_descricao_resultado'] || interp.o_que_significa_nivel_atual}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #38bdf8;">
                                <h4 style="color:#38bdf8;">2. Pares Etários (18 a 25 Anos)</h4>
                                <p>${pilares['2_estatistica_etaria_18_25'] || 'Prevalência populacional alinhada com as referências do Ministério da Saúde.'}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #fbbf24;">
                                <h4 style="color:#fbbf24;">3. Impactos para o Indivíduo</h4>
                                <p>${pilares['3_impactos_individuo'] || 'Manutenção da rotina saudável e bem-estar físico e mental.'}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #f97316;">
                                <h4 style="color:#f97316;">4. Possíveis Causas do Desvio</h4>
                                <p>${pilares['4_possiveis_causas'] || 'Hábitos alimentares, rotina de sono e variações fisiológicas transitórias.'}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #34d399;">
                                <h4 style="color:#34d399;">5. Correção / Conduta Recomendada</h4>
                                <p>${pilares['5_correcao_desvio'] || 'Manter hábitos preventivos e acompanhamento regular com médico.'}</p>
                            </div>
                        </div>
                    </div>

                    <!-- PERGUNTAS SUGERIDAS PARA A CONSULTA MÉDICA -->
                    <div class="rag-block" style="margin-top:16px; border-color:rgba(56, 189, 248, 0.35); background:rgba(9, 13, 22, 0.75);">
                        <h4>🩺 Perguntas Sugeridas para Levar ao seu Médico na Próxima Consulta</h4>
                        <ul class="doctor-questions-list">
                            ${perguntasHtml}
                        </ul>
                    </div>

                    <div style="margin-top:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-size:0.74rem; color:#94a3b8; border-top:1px solid var(--border); padding-top:10px;">
                        <span>📚 <strong>Diretrizes Clínicas:</strong> SBPC-ML • CLSI EP28-A3c • CTCAE v5.0 • Valores Críticos CAP</span>
                        <span>🛡️ ${interp.aviso_seguranca_etica}</span>
                    </div>
                `;
                card.classList.add('open');
            } catch (err) {
                alert("Erro ao obter interpretação determinística: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = textoOriginal;
            }
        }

        async function alternarConsentimento(consentId) {
            try {
                const res = await fetch(`/api/consent/${consentId}/toggle`, { method: 'POST' });
                if (!res.ok) throw new Error('Falha ao alternar consentimento');
                abrirPaciente(pacienteAtualId);
            } catch (e) {
                alert("Erro: " + e.message);
            }
        }

        function abrirModalNovoConsentimento() {
            document.getElementById('modal-novo-consent').classList.add('open');
        }
        function fecharModalConsent() {
            document.getElementById('modal-novo-consent').classList.remove('open');
        }

        async function salvarNovoConsentimento() {
            if (!pacienteAtualId) return;
            const origem = document.getElementById('input-origem').value;
            const destino = document.getElementById('input-destino').value;
            const escopo = document.getElementById('input-escopo').value;
            const validade = parseInt(document.getElementById('input-validade').value);

            try {
                const res = await fetch('/api/consent/novo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pacienteAtualId,
                        hospital_origem: origem,
                        hospital_destino: destino,
                        escopo: escopo,
                        dias_validade: validade
                    })
                });
                if (!res.ok) throw new Error('Falha ao criar consentimento');
                fecharModalConsent();
                abrirPaciente(pacienteAtualId);
            } catch (e) {
                alert("Erro ao criar consentimento: " + e.message);
            }
        }

        // ==============================================================
        // NÍVEL 3: OBSERVATIONS DO LAUDO EXIBIDAS POR COLUNAS (LOINC)
        // (AQUI É A PARTE CRUCIAL ONDE MOSTRAMOS TODAS AS COLUNAS, INCLUINDO AS VAZIAS!)
        // ==============================================================
        async function abrirLaudoObservacoes(reportId) {
            laudoAtualId = reportId;
            try {
                const res = await fetch(`/api/laudo/${reportId}/colunas`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.erro || 'Falha ao buscar colunas do laudo');

                dadosLaudoColunasCache = data;
                const laudo = data.laudo;

                // Atualiza Breadcrumbs
                document.getElementById('bc-sep-2').style.display = 'inline-block';
                const bcLaudo = document.getElementById('bc-laudo');
                bcLaudo.style.display = 'inline-flex';
                bcLaudo.innerHTML = `🔬 Laudo: <strong>${laudo.laboratorio_origem} (${laudo.data_coleta || 'S/D'})</strong>`;

                // Banner de Informações do Laudo
                document.getElementById('banner-laudo-info').innerHTML = `
                    <div class="info-col"><label>Paciente</label><div>${laudo.nome_paciente}</div></div>
                    <div class="info-col"><label>Laboratório</label><div>${laudo.laboratorio_origem}</div></div>
                    <div class="info-col"><label>Data da Coleta</label><div>${laudo.data_coleta || '—'}</div></div>
                    <div class="info-col"><label>Data da Emissão</label><div>${laudo.data_emissao || '—'}</div></div>
                    <div class="info-col"><label>Versão do Laudo</label><div><span style="color:var(--primary); font-weight:700;">v${laudo.versao}</span></div></div>
                    <div class="info-col"><label>Hash ICP-Brasil</label><div><span class="hash-code" title="${laudo.assinatura_hash}">${laudo.assinatura_hash}</span></div></div>
                `;

                // Badges de Resumo das Colunas
                document.getElementById('stat-col-preenchidas').innerText = `${data.total_preenchidas} Preenchidas`;
                document.getElementById('stat-col-vazias').innerText = `${data.total_vazias} Colunas Vazias`;
                document.getElementById('stat-col-total').innerText = `Total: ${data.total_colunas} Colunas Padronizadas`;

                // Renderiza as visualizações de colunas
                renderizarMatrizColunas(data.colunas);
                renderizarCardsCategorias(data.colunas);

                // Alterna para visualização de Observações
                document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
                document.getElementById('view-laudo-observacoes').classList.add('active');

            } catch (e) {
                alert("Erro ao carregar observações por colunas: " + e.message);
            }
        }

        function alternarModoExibicao(modo) {
            modoExibicaoAtual = modo;
            if (modo === 'matrix') {
                document.getElementById('wrapper-matrix-view').style.display = 'block';
                document.getElementById('wrapper-cards-view').style.display = 'none';
                document.getElementById('btn-view-matrix').style.borderColor = 'var(--primary)';
                document.getElementById('btn-view-cards').style.borderColor = 'var(--border)';
            } else {
                document.getElementById('wrapper-matrix-view').style.display = 'none';
                document.getElementById('wrapper-cards-view').style.display = 'block';
                document.getElementById('btn-view-cards').style.borderColor = 'var(--primary)';
                document.getElementById('btn-view-matrix').style.borderColor = 'var(--border)';
            }
        }

        // 1. RENDERIZAÇÃO DA MATRIZ DE COLUNAS (FORMATO LARGO HORIZONTAL COM SCROLL)
        function renderizarMatrizColunas(colunas) {
            const thead = document.getElementById('thead-matriz');
            const tbody = document.getElementById('tbody-matriz');

            const colunasFiltradas = obterColunasFiltradas(colunas);

            if (colunasFiltradas.length === 0) {
                thead.innerHTML = `<tr><th>Nenhuma coluna encontrada com o filtro atual</th></tr>`;
                tbody.innerHTML = `<tr><td class="empty-state">Tente alterar os filtros de busca acima.</td></tr>`;
                return;
            }

            // Cabeçalho: Cada métrica vira uma coluna com Nome e Código LOINC
            thead.innerHTML = `<tr>` + colunasFiltradas.map(col => `
                <th>
                    <div class="col-name">${col.nome_exibicao}</div>
                    <div class="col-loinc">LOINC: ${col.loinc}</div>
                    <div class="col-cat">${col.categoria.replace(/^\d+\.\s*/, '')}</div>
                </th>
            `).join('') + `</tr>`;

            // Linha com os valores: Exibe os valores preenchidos ou "—" para as colunas vazias
            tbody.innerHTML = `<tr>` + colunasFiltradas.map(col => {
                if (col.preenchida) {
                    const statusClass = col.status_clinico === 'alto' || col.status_clinico === 'baixo' ? 'badge-alterado' : 'badge-normal';
                    return `
                        <td class="matrix-cell-filled">
                            <div class="cell-value">${col.valor}</div>
                            <div class="cell-unit">${col.unidade || '—'}</div>
                            <div class="cell-ref">Ref: ${col.faixa_referencia_formatada}</div>
                            <div style="margin-top:6px;">
                                <span class="badge ${statusClass}">${col.status_clinico.toUpperCase()}</span>
                            </div>
                        </td>
                    `;
                } else {
                    return `
                        <td>
                            <div class="cell-empty">—</div>
                            <div style="font-size:0.68rem; color:#475569; margin-top:4px;">(coluna vazia)</div>
                        </td>
                    `;
                }
            }).join('') + `</tr>`;
        }

        // 2. RENDERIZAÇÃO DOS CARDS DE COLUNAS AGRUPADOS POR CATEGORIA
        function renderizarCardsCategorias(colunas) {
            const container = document.getElementById('container-categorias-cards');
            const colunasFiltradas = obterColunasFiltradas(colunas);

            // Agrupa por categoria
            const grupos = {};
            colunasFiltradas.forEach(col => {
                const cat = col.categoria || 'Geral';
                if (!grupos[cat]) grupos[cat] = [];
                grupos[cat].push(col);
            });

            if (Object.keys(grupos).length === 0) {
                container.innerHTML = `<div class="empty-state">Nenhuma coluna encontrada com o filtro atual.</div>`;
                return;
            }

            container.innerHTML = Object.entries(grupos).map(([cat, lista]) => {
                const preenchidasCat = lista.filter(c => c.preenchida).length;
                const totalCat = lista.length;

                const cardsHtml = lista.map(c => {
                    if (c.preenchida) {
                        return `
                            <div class="col-card filled">
                                <div class="col-card-header">
                                    <div class="col-card-name">${c.nome_exibicao}</div>
                                    <span class="col-card-loinc">${c.loinc}</span>
                                </div>
                                <div class="col-card-value">${c.valor} <span class="col-card-unit">${c.unidade}</span></div>
                                <div class="col-card-ref">Ref: ${c.faixa_referencia_formatada}</div>
                            </div>
                        `;
                    } else {
                        return `
                            <div class="col-card empty">
                                <div class="col-card-header">
                                    <div class="col-card-name" style="color:#64748b;">${c.nome_exibicao}</div>
                                    <span class="col-card-loinc" style="color:#475569;">${c.loinc}</span>
                                </div>
                                <div style="color:#475569; font-size:0.95rem; font-style:italic; margin-top:8px;">— (Coluna Vazia)</div>
                                <div class="col-card-ref" style="color:#334155;">Não coletado neste laudo</div>
                            </div>
                        `;
                    }
                }).join('');

                return `
                    <div class="category-block">
                        <div class="category-title">
                            <span>${cat}</span>
                            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">
                                ${preenchidasCat} preenchidas de ${totalCat} colunas
                            </span>
                        </div>
                        <div class="columns-grid">
                            ${cardsHtml}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Filtros e buscas de colunas
        function obterColunasFiltradas(colunas) {
            if (!colunas) return [];
            let result = [...colunas];

            // Filtro Preenchidas / Vazias / Todas
            if (filtroColunaAtual === 'preenchidas') {
                result = result.filter(c => c.preenchida);
            } else if (filtroColunaAtual === 'vazias') {
                result = result.filter(c => !c.preenchida);
            }

            // Filtro por Categoria do Dropdown
            const catFiltro = document.getElementById('select-categoria').value.toLowerCase();
            if (catFiltro) {
                result = result.filter(c => c.categoria.toLowerCase().includes(catFiltro));
            }

            // Filtro por texto digitado
            const busca = document.getElementById('search-coluna').value.toLowerCase().trim();
            if (busca) {
                result = result.filter(c => 
                    c.nome_exibicao.toLowerCase().includes(busca) || 
                    c.coluna.toLowerCase().includes(busca) ||
                    c.loinc.includes(busca)
                );
            }

            return result;
        }

        function aplicarFiltroColunas(tipo) {
            filtroColunaAtual = tipo;
            document.querySelectorAll('.filters-toolbar .pill-filter').forEach(b => b.classList.remove('active'));
            if (tipo === 'todas') document.getElementById('filter-all').classList.add('active');
            if (tipo === 'preenchidas') document.getElementById('filter-filled').classList.add('active');
            if (tipo === 'vazias') document.getElementById('filter-empty').classList.add('active');

            if (dadosLaudoColunasCache) {
                renderizarMatrizColunas(dadosLaudoColunasCache.colunas);
                renderizarCardsCategorias(dadosLaudoColunasCache.colunas);
            }
        }

        function filtrarPorCategoria() {
            if (dadosLaudoColunasCache) {
                renderizarMatrizColunas(dadosLaudoColunasCache.colunas);
                renderizarCardsCategorias(dadosLaudoColunasCache.colunas);
            }
        }

        function filtrarPorTextoColuna() {
            if (dadosLaudoColunasCache) {
                renderizarMatrizColunas(dadosLaudoColunasCache.colunas);
                renderizarCardsCategorias(dadosLaudoColunasCache.colunas);
            }
        }

        function recarregarVisaoAtual() {
            if (laudoAtualId) {
                abrirLaudoObservacoes(laudoAtualId);
            } else if (pacienteAtualId) {
                abrirPaciente(pacienteAtualId);
            } else {
                carregarListaPacientes();
            }
        }

        async function limparBancoGeral() {
            if (!confirm("Atenção: Deseja realmente zerar todos os pacientes, laudos, observações e consentimentos para reiniciar do zero?")) return;
            try {
                await fetch('/api/limpar_banco', { method: 'POST' });
                navegarParaPacientes();
                alert("Banco de dados zerado com sucesso!");
            } catch (e) {
                alert("Erro ao limpar banco: " + e.message);
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# ROTAS DA API
# ==========================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/pacientes')
def api_pacientes():
    """Retorna a lista de pacientes com totais de laudos e consentimentos."""
    return jsonify(obter_pacientes_completo())

@app.route('/api/paciente/<patient_id>')
def api_paciente_detalhe(patient_id):
    """Retorna dados do paciente, seus laudos e seus consentimentos anexados."""
    detalhes = obter_detalhes_paciente(patient_id)
    if not detalhes:
        return jsonify({'erro': 'Paciente não encontrado'}), 404
    return jsonify(detalhes)

@app.route('/api/laudo/<report_id>/colunas')
def api_laudo_colunas(report_id):
    """Retorna as observações de um laudo formatadas por colunas (incluindo as vazias)."""
    dados = obter_observacoes_laudo_colunas(report_id)
    if not dados:
        return jsonify({'erro': 'Laudo não encontrado'}), 404
    return jsonify(dados)

@app.route('/api/consent/<consent_id>/toggle', methods=['POST'])
def api_consent_toggle(consent_id):
    """Alterna o status do consentimento entre 'ativo' e 'revogado'."""
    res = alternar_status_consentimento(consent_id)
    if not res:
        return jsonify({'erro': 'Consentimento não encontrado'}), 404
    return jsonify(res)

@app.route('/api/consent/novo', methods=['POST'])
def api_consent_novo():
    """Adiciona um novo consentimento LGPD para um paciente."""
    dados = request.get_json() or {}
    patient_id = dados.get('patient_id')
    origem = dados.get('hospital_origem', 'Hospital Geral')
    destino = dados.get('hospital_destino', 'Rede Open Health')
    escopo = dados.get('escopo', 'exames_sangue')
    validade = int(dados.get('dias_validade', 365))

    if not patient_id:
        return jsonify({'erro': 'patient_id é obrigatório'}), 400

    res = criar_consentimento_paciente(patient_id, origem, destino, escopo, validade)
    return jsonify(res)

@app.route('/api/extrair', methods=['POST'])
def api_extrair():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400

    motor = request.form.get('motor', 'nuvem')

    suffix = os.path.splitext(file.filename)[1] or '.pdf'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        caminho_temporario = tmp.name

    try:
        dados_brutos = None
        motor_label = ""
        mapa_direto = None

        if motor == 'local':
            dados_brutos = extrair_local_offline(caminho_temporario)
            mapa_direto = None
            motor_label = "Local Offline (Algoritmo Leve / Zero RAM)"
        else:
            try:
                resultado_pydantic = extrair_informacoes_laudo(caminho_temporario)
                dados_brutos = resultado_pydantic.model_dump()
                mapa_direto = dados_brutos.get("campos_planilha")
                motor_label = "Gemini 2.5 Flash (Nuvem)"
            except Exception as e_nuvem:
                print(f"[!] Falha no motor Nuvem ({e_nuvem}). Executando extração Local Offline de contingência...")
                dados_brutos = extrair_local_offline(caminho_temporario)
                mapa_direto = None
                motor_label = f"Local Offline (Fallback automático: {str(e_nuvem)[:40]})"

        # Mapeia diretamente para a linha oficial da planilha BR CORE / LOINC
        linha_oficial = criar_linha_planilha(dados_brutos, mapa_direto)

        # Salva na planilha CSV acumulada
        salvar_em_planilha_csv(CSV_BANCO_PATH, linha_oficial)

        # SALVA NO BANCO RELACIONAL OPEN HEALTH (4 TABELAS)
        db_res = salvar_laudo_relacional(dados_brutos, linha_oficial)

        dados_brutos["linha_planilha"] = linha_oficial
        dados_brutos["motor"] = motor_label
        dados_brutos["db_status"] = db_res
        return jsonify(dados_brutos)

    except Exception as e:
        return jsonify({'erro': f"Falha na extração e inserção: {str(e)}"}), 500
    finally:
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)

@app.route('/api/todos_laudos')
def api_todos_laudos():
    """Retorna todos os laudos (diagnostic_reports) unificados de todos os laboratórios."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dr.*, p.nome as nome_paciente, p.cpf as cpf_paciente,
               (SELECT COUNT(*) FROM observations obs WHERE obs.report_id = dr.id) as total_observacoes
        FROM diagnostic_reports dr
        JOIN patients p ON p.id = dr.patient_id
        ORDER BY dr.data_coleta DESC, dr.created_at DESC;
    """)
    laudos = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(laudos)

@app.route('/api/tabelas')
def api_tabelas():
    """Retorna os dados gerais das 4 tabelas relacionais."""
    return jsonify(obter_dados_tabelas())

@app.route('/api/limpar_banco', methods=['POST'])
def api_limpar_banco():
    """Limpa as tabelas de teste."""
    return jsonify(limpar_todas_tabelas())

# ==============================================================================
# ENDPOINTS DO MÓDULO PARTE 1: EVOLUÇÃO LONGITUDINAL & INTERPRETAÇÃO RAG
# ==============================================================================

@app.route('/api/paciente/<patient_id>/biomarcadores')
def api_paciente_biomarcadores(patient_id):
    """Lista os biomarcadores do paciente com classificação de gradiente e seta de tendência."""
    return jsonify(listar_biomarcadores_paciente(patient_id))

@app.route('/api/paciente/<patient_id>/evolucao/<codigo_loinc>')
def api_paciente_evolucao_loinc(patient_id, codigo_loinc):
    """Retorna a série temporal longitudinal de um biomarcador específico (LOINC)."""
    dados = obter_evolucao_biomarcador_paciente(patient_id, codigo_loinc)
    if not dados:
        return jsonify({'erro': f'Nenhum histórico encontrado para o LOINC {codigo_loinc}'}), 404
    return jsonify(dados)

@app.route('/api/conhecimento/<identificador>')
def api_conhecimento_analito(identificador):
    """
    Retorna deterministamente da base pré-processada de 113 analitos x 5 faixas:
      - Resumo do exame (o que ele representa no corpo em linguagem acessível);
      - Resumo das 5 faixas de resultados formatadas para 18 a 25 anos:
        1. Descrição do resultado;
        2. Estatísticas sobre os pares etários (18 a 25 anos);
        3. O que pode impactar para o indivíduo;
        4. Possíveis causas para o desvio;
        5. Correção / Conduta recomendada.
    """
    kb565_path = os.path.join(BASE_DIR, "base_conhecimento_exames_565.json")
    if not os.path.exists(kb565_path):
        return jsonify({'erro': 'Base de conhecimento 565 não encontrada.'}), 404
    try:
        with open(kb565_path, "r", encoding="utf-8") as f:
            base = json.load(f)
        
        # Busca por chave direta (coluna)
        id_clean = identificador.strip().lower()
        if id_clean in base:
            return jsonify(base[id_clean])
        
        # Busca por código LOINC
        for col, dados in base.items():
            if str(dados.get('codigo_loinc', '')).strip() == identificador.strip():
                return jsonify(dados)
            if col.replace('_', '').lower() == id_clean.replace('_', ''):
                return jsonify(dados)

        return jsonify({'erro': f'Analito {identificador} não encontrado na base determinística.'}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/exams/interpret', methods=['POST'])
@app.route('/api/exams/interpret', methods=['POST'])
def api_exams_interpret():
    """
    Endpoint de Interpretação DETERMINÍSTICA (sem RAG dinâmico nem chamadas externas de LLM):
      - Passo 1 (SQL): Busca a série unificada de `patient_id` e `codigo_loinc` no banco relacional.
      - Passo 2: Recupera da base determinística estruturada o Resumo do Exame (1 de 113) e
        o Resumo do Resultado para a faixa atual (1 de 565) com foco estrito em pares de 18 a 25 anos.
      - Retorno imediato (0ms de latência) com os 5 pilares clínicos e sem alarmismo.
    """
    body = request.get_json() or {}
    patient_id = body.get('patient_id')
    codigo_loinc = body.get('codigo_loinc')

    if not patient_id or not codigo_loinc:
        return jsonify({'erro': 'Os campos patient_id e codigo_loinc são obrigatórios.'}), 400

    dados_evolucao = obter_evolucao_biomarcador_paciente(patient_id, codigo_loinc)
    if not dados_evolucao or not dados_evolucao.get('serie_temporal'):
        return jsonify({'erro': f'Não há registros para patient_id={patient_id} e codigo_loinc={codigo_loinc}'}), 404

    try:
        # Força usar_llm=False para garantia absoluta de interpretação determinística rápida e offline
        resultado_deterministico = executar_pipeline_rag_interpretacao(
            patient_id=patient_id,
            codigo_loinc=codigo_loinc,
            registros_sql=dados_evolucao['serie_temporal'],
            paciente_info=dados_evolucao['paciente'],
            usar_llm=False
        )
        return jsonify(resultado_deterministico)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    popular_historico_longitudinal_3_anos(forcar=False)
    porta = int(os.environ.get("PORT", 5000))
    print(f"[*] Servidor iniciado em http://localhost:{porta}")
    app.run(host='0.0.0.0', port=porta, debug=False)
