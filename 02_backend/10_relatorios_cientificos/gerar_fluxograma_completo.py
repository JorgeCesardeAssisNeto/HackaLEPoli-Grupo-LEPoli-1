# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def gerar_fluxograma_ecossistema(output_path="fluxograma_open_health_completo.png"):
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    fig.patch.set_facecolor('#070b14')
    ax.set_facecolor('#070b14')
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Header
    ax.text(50, 96.2, "FLUXOGRAMA GERAL DO PROJETO — ECOSSISTEMA OPEN HEALTH BRASIL",
            ha='center', va='center', color='#f8fafc', fontsize=17, weight='bold', fontfamily='sans-serif')
    ax.text(50, 93.2, "Integração de Exames Laboratoriais (HL7 FHIR / LOINC) + Telemetria Contínua de Wearables (6 Meses)",
            ha='center', va='center', color='#38bdf8', fontsize=10.5, weight='bold', fontfamily='sans-serif')

    def draw_box(x, y, w, h, title, subtitle, items, header_color, border_color='#334155'):
        # Shadow
        shadow = patches.FancyBboxPatch((x+0.4, y-0.4), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                        fc='#000000', ec='none', alpha=0.45, zorder=2)
        ax.add_patch(shadow)
        # Body
        body = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                      fc='#111827', ec=border_color, lw=1.4, zorder=3)
        ax.add_patch(body)
        # Header
        hh = 3.8
        header = patches.FancyBboxPatch((x, y + h - hh), w, hh, boxstyle="round,pad=0.2,rounding_size=1.0",
                                        fc=header_color, ec='none', zorder=4)
        ax.add_patch(header)
        ax.add_patch(patches.Rectangle((x, y + h - hh), w, 1.0, fc=header_color, ec='none', zorder=4))

        ax.text(x + 1.2, y + h - 1.5, title, color='#ffffff', fontsize=9.8, weight='bold', zorder=5)
        ax.text(x + 1.2, y + h - 2.9, subtitle, color='#e2e8f0', fontsize=7.2, style='italic', zorder=5)

        curr_y = y + h - hh - 1.9
        for tag, txt in items:
            badge_c = header_color
            bb = patches.FancyBboxPatch((x + 1.0, curr_y - 0.65), 3.4, 1.35,
                                        boxstyle="round,pad=0.08,rounding_size=0.35",
                                        fc=badge_c, ec='none', alpha=0.85, zorder=5)
            ax.add_patch(bb)
            ax.text(x + 2.7, curr_y, tag, color='#ffffff', fontsize=6.2, weight='bold', ha='center', va='center', zorder=6)
            ax.text(x + 5.0, curr_y, txt, color='#e2e8f0', fontsize=7.5, va='center', zorder=5)
            curr_y -= 2.15

    def draw_arrow(x1, y1, x2, y2, label="", color='#38bdf8'):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.6,head_length=0.8", color=color, lw=1.8, ls='-'),
                    zorder=6)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my + 1.2, label, color=color, fontsize=7.2, weight='bold', ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.25", fc='#070b14', ec=color, lw=0.8), zorder=7)

    # LANE LABELS
    ax.text(3.2, 87.5, "TRILHA 1: EXAMES DE SANGUE (DADOS EPISÓDICOS / LABORATORIAIS)", color='#818cf8', fontsize=9.5, weight='bold')
    ax.text(3.2, 46.5, "TRILHA 2: DATASET DE WEARABLES (TELEMETRIA CONTÍNUA DIÁRIA - 6 MESES)", color='#34d399', fontsize=9.5, weight='bold')

    # --- LANE 1: BLOOD EXAMS ---
    draw_box(3, 55, 27, 30,
             "1A. Fontes de Laudos PDF",
             "Formatos Heterogêneos (Reais / Hipotéticos)",
             [
                 ("PDF", "Laudos Reais e Hipotéticos"),
                 ("HIST", "Retrospectiva 3 Anos (10 PDFs)"),
                 ("GEMINI", "Motor Online: Gemini 2.5 Flash"),
                 ("LOCAL", "Motor Offline: pdfplumber + RegEx"),
                 ("SLM", "Qwen 2.5 0.5B Instruct (GGUF)"),
                 ("JSON", "Validação Estruturada Pydantic")
             ],
             "#4f46e5", "#6366f1")

    draw_box(36.5, 55, 27, 30,
             "1B. Padronização & Banco FHIR",
             "Interoperabilidade BR Core & LOINC",
             [
                 ("LOINC", "Mapeamento p/ 120+ Analitos"),
                 ("CSV", "Planilha Padrão BR Core Oficial"),
                 ("SQL", "Banco Relacional (open_health.db)"),
                 ("TBL 1", "patients (Identificação BR Core)"),
                 ("TBL 2", "consents (Governança LGPD)"),
                 ("TBL 3", "diagnostic_reports & observations")
             ],
             "#0284c7", "#38bdf8")

    draw_box(70, 55, 27, 30,
             "1C. Aplicação Exames (:5000)",
             "Etapa Exames de Sangue / app.py",
             [
                 ("WEB", "Upload Drag & Drop de PDFs"),
                 ("MOTOR", "Seletor Gemini vs Offline Local"),
                 ("ALERT", "Detecção de Exames Alterados"),
                 ("VIEW", "Visualizador das 4 Tabelas SQL"),
                 ("DDL", "Inspeção do Schema Open Health"),
                 ("EXPORT", "Download CSV Padronizado")
             ],
             "#0369a1", "#38bdf8")

    draw_arrow(30.2, 70, 36.3, 70, "JSON Extraído", "#818cf8")
    draw_arrow(63.7, 70, 69.8, 70, "SQLite + CSV", "#38bdf8")

    # --- LANE 2: WEARABLES ---
    draw_box(3, 12, 27, 32,
             "2A. Dataset Wearables (CSV)",
             "wearables_health_6mo_daily.csv (18 MB)",
             [
                 ("COORTE", "300 Usuários (U0001 a U0300)"),
                 ("TEMPO", "184 Dias (Mai/2025 a Nov/2025)"),
                 ("LINHAS", "55.200 Registros Diários"),
                 ("COLS", "33 Variáveis Clínicas e Hábitos"),
                 ("DEVICES", "5 Modelos (FitPulse, SleepSense...)"),
                 ("SYNC", "1.057 Registros s/ Sync Mapeados")
             ],
             "#059669", "#34d399")

    draw_box(36.5, 12, 27, 32,
             "2B. Motor Analítico Python",
             "Dataset Wearables / app_wearables.py",
             [
                 ("INDEX", "Indexação em Memória (< 1 seg)"),
                 ("FILTROS", "Dispositivo, Sexo, Região, Treino"),
                 ("SERIES", "Agregação Temporal Diária"),
                 ("PEARSON", "Matriz de Correlação Bivariada (r)"),
                 ("ALERTS", "Regras: PA >=135/85, SpO2 <95%"),
                 ("AUDIT", "Cálculo de Completude e Desvio")
             ],
             "#0d9488", "#2dd4bf")

    draw_box(70, 12, 27, 32,
             "2C. Dashboard Wearables (:5050)",
             "Interface Interativa em Localhost",
             [
                 ("ABA 1", "Visão Geral, KPIs e Coorte"),
                 ("ABA 2", "Prontuário Individual (300 Pac.)"),
                 ("ABA 3", "Scatter Plot & Matriz de Pearson"),
                 ("ABA 4", "Explorador Paginado e Busca"),
                 ("ABA 5", "Auditoria das 33 Colunas & Nulls"),
                 ("CHARTS", "Gráficos Dinâmicos Chart.js")
             ],
             "#ca8a04", "#fbbf24")

    draw_arrow(30.2, 28, 36.3, 28, "Leitura & Parse", "#34d399")
    draw_arrow(63.7, 28, 69.8, 28, "REST API JSON", "#fbbf24")

    # Convergence Footer Banner
    footer = patches.FancyBboxPatch((3, 2.2), 94, 6.2, boxstyle="round,pad=0.2,rounding_size=1.0",
                                    fc='#1e293b', ec='#38bdf8', lw=1.5, zorder=3)
    ax.add_patch(footer)
    ax.text(50, 6.1, "VISÃO INTEGRADA DO PACIENTE NO OPEN HEALTH (CONVERGÊNCIA CLÍNICA)",
            ha='center', va='center', color='#38bdf8', fontsize=9.8, weight='bold', zorder=5)
    ax.text(50, 3.8, "Cruzamento de Biomarcadores Laboratoriais (Glicemia, HbA1c, Colesterol, PCR, Ferritina) com Sinais Vitais Contínuos (FC, HRV, PA, Sono, Passos e Estresse)",
            ha='center', va='center', color='#f8fafc', fontsize=8.3, zorder=5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[+] Fluxograma salvo com sucesso em: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    gerar_fluxograma_ecossistema()
