"""Gera 3 figuras didaticas, limpas e sem qualquer sobreposicao de texto para o Artigo Final de Sintese."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['DejaVu Serif', 'Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r"c:\Users\janna\Desktop\Hackathon LEPoli"


def draw_clean_card(ax, x, y, w, h, badge, title, subtitle, lines, header_bg, border_col, body_bg="#f8fafc"):
    # Card box
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.016",
        fc=body_bg, ec=border_col, lw=1.5, zorder=2
    ))
    # Header box
    hh = 0.082
    ax.add_patch(FancyBboxPatch(
        (x, y + h - hh), w, hh, boxstyle="round,pad=0.003,rounding_size=0.014",
        fc=header_bg, ec=border_col, lw=1.0, zorder=3
    ))
    ax.text(x + 0.014, y + h - 0.028, f"{badge} — {title}",
            fontsize=9.2, weight="bold", color="white", va="center", ha="left", zorder=4)
    ax.text(x + 0.014, y + h - 0.060, subtitle,
            fontsize=7.6, style="italic", color="#e2e8f0", va="center", ha="left", zorder=4)

    curr_y = y + h - hh - 0.024
    for line in lines:
        ax.text(x + 0.014, curr_y, line, fontsize=7.8, color="#0f172a", va="top", ha="left", zorder=4)
        curr_y -= 0.043


def draw_arrow(ax, x1, y1, x2, y2, label="", color="#1e3a8a", label_offset=(0.0, 0.0)):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=14, lw=1.6, color=color, zorder=5
    ))
    if label:
        mx = (x1 + x2) / 2.0 + label_offset[0]
        my = (y1 + y2) / 2.0 + label_offset[1]
        ax.text(mx, my, label, fontsize=7.4, weight="bold", color=color, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.9), zorder=6)


def gerar_figura4_1():
    fig = plt.figure(figsize=(14.0, 8.2), dpi=240)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.968,
            "VISÃO GERAL DO PROJETO: COMO OS 4 MÓDULOS SE COMPLEMENTAM",
            fontsize=12.0, weight="bold", color="#0f172a", ha="center", va="center")
    ax.text(0.5, 0.936,
            "Integração entre Exames de Sangue (Porta :5000), Modelos Populacionais NHANES (Porta :5055) e Motor Causal de Wearables (Porta :5050)",
            fontsize=8.8, style="italic", color="#334155", ha="center", va="center")

    # Top-Left: Modulo I
    draw_clean_card(
        ax, 0.02, 0.54, 0.41, 0.36,
        "ETAPA 1", "Exames de Sangue & Banco FHIR (:5000)",
        "Verdade bioquímica episódica e governança LGPD",
        [
            "• Leitura de PDFs: Gemini 2.5 Flash (online) ou extrator local offline",
            "• Banco relacional em 4 tabelas: patients, diagnostic_reports,",
            "  observations (formato vertical por exame) e consents (LGPD)",
            "• Padronização universal: 113+ exames com código LOINC e UCUM",
            "• Papel no todo: fornece os exames reais que servem de base",
            "  confirmatória e ponto de partida para os demais módulos"
        ],
        header_bg="#1e3a8a", border_col="#1d4ed8", body_bg="#f8fafc"
    )

    # Top-Right: Modulo II
    draw_clean_card(
        ax, 0.57, 0.54, 0.41, 0.36,
        "ETAPA 2", "Gradiente Clínico & Display (:5000)",
        "Tradução visual segura e textos sem risco de alucinação",
        [
            "• Régua de Gradiente: converte qualquer exame para uma escala",
            "  de 0% a 100% (diretrizes CLSI EP28-A3c, CTCAE e CAP)",
            "• 4 cores seguras (Verde, Amarelo, Laranja, Vermelho) + seta",
            "  de tendência (↗ / ↘) quando o exame varia mais de 20%",
            "• 565 textos determinísticos pré-prontos (113 exames × 5 faixas)",
            "• Gráficos de linha do tempo unificando vários laboratórios"
        ],
        header_bg="#0369a1", border_col="#0284c7", body_bg="#f0f9ff"
    )

    # Bottom-Left: Modulo III
    draw_clean_card(
        ax, 0.02, 0.09, 0.41, 0.36,
        "ETAPA 3", "Base NHANES & Calibração (:5055)",
        "Ponte estatística populacional e Marco Zero individual",
        [
            "• Base pública CDC NHANES: 15.560 pessoas (2017–2020) e",
            "  1.846 com hormônios (2011–2012) unificadas pelo ID SEQN",
            "• Como o sangue sozinho explica só 12,9% do pulso em repouso,",
            "  usamos Calibração em 2 Etapas pelo 'Marco Zero' (Δ_ind)",
            "• A precisão salta para R² = 0,864 (erro médio de 3,02 bpm)",
            "• Inclui modelos de Risco Metabólico, Apneia e Inflamação"
        ],
        header_bg="#5b21b6", border_col="#6d28d9", body_bg="#f5f3ff"
    )

    # Bottom-Right: Modulo IV
    draw_clean_card(
        ax, 0.57, 0.09, 0.41, 0.36,
        "ETAPA 4", "Inferência Causal no Wearable (:5050)",
        "Filtro de hábitos cotidianos em 55.200 registros diários",
        [
            "• Separa o que é efeito de hábito agudo (poucos passos, álcool,",
            "  cafeína, tela à noite, sono curto) do que é sinal de doença",
            "• Filtra de 56,1% a 97,4% de falsos alarmes nos 4 alvos:",
            "  (1) Sono Profundo, (2) Glicose/HbA1c, (3) PCR e (4) Anemia",
            "• Consulta o histórico do banco FHIR (Etapa 1) e envia apenas",
            "  desvios persistentes reais para o médico (Etapa 2)"
        ],
        header_bg="#047857", border_col="#059669", body_bg="#ecfdf5"
    )

    # Arrows in the wide central corridors (x between 0.43 and 0.57, y between 0.45 and 0.54)
    draw_arrow(ax, 0.432, 0.72, 0.568, 0.72, "Exames LOINC\n+ Faixas Ref.", "#0369a1")
    draw_arrow(ax, 0.225, 0.538, 0.225, 0.452, "Histórico de Exames Reais\npara Calibrar o Modelo", "#5b21b6")
    draw_arrow(ax, 0.568, 0.27, 0.432, 0.27, "Médias Filtradas\n(7 a 14 dias)", "#047857")
    draw_arrow(ax, 0.775, 0.452, 0.775, 0.538, "Sugestão de Exame\n& Briefing Médico", "#b45309")

    # Bottom banner
    ax.add_patch(FancyBboxPatch(
        (0.02, 0.012), 0.96, 0.056, boxstyle="round,pad=0.005,rounding_size=0.012",
        fc="#fff7ed", ec="#c2410c", lw=1.3, zorder=3
    ))
    ax.text(0.5, 0.040,
            "TRAVA DE SEGURANÇA E CONFORMIDADE (LGPD • CFM • ANVISA): Nenhum módulo emite diagnóstico médico automatizado.\n"
            "O sistema filtra ruídos cotidianos, educa o paciente com textos pré-validados e entrega um resumo mastigado para o médico.",
            fontsize=7.8, weight="bold", color="#7c2d12", ha="center", va="center", zorder=4)

    out = os.path.join(ROOT, "figura4_1_arquitetura_complementar_4_modulos.png")
    fig.savefig(out, dpi=240, facecolor="white")
    plt.close(fig)
    return out


def gerar_figura4_2():
    """Figura dedicada exclusivamente ao Grafo Causal de 3 Camadas (zero sobreposicao)."""
    fig = plt.figure(figsize=(14.0, 6.2), dpi=240)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.96,
            "ARQUITETURA DE INFERÊNCIA CAUSAL EM 3 CAMADAS (GRAFOS ACÍCLICOS DIRECIONADOS — DAGs)",
            fontsize=11.5, weight="bold", color="#0f172a", ha="center", va="center")
    ax.text(0.5, 0.92,
            "Por que não podemos ligar uma alteração do relógio diretamente a uma doença sem antes descontar os hábitos do dia a dia",
            fontsize=8.8, style="italic", color="#334155", ha="center", va="center")

    col_headers = [
        (0.02, 0.26, "CAMADA 1: Hábitos & Ruídos Agudos\n(Fatores de Confusão / Confounders)", "#b45309"),
        (0.37, 0.26, "CAMADA 2: Sinais do Smartwatch\n(Mediadores Fisiológicos)", "#0369a1"),
        (0.72, 0.26, "CAMADA 3: Alvos Clínicos & Sangue\n(Acionados Só Se o Sinal Persistir)", "#15803d"),
    ]
    for x, w, title_txt, col in col_headers:
        ax.text(x + w / 2, 0.855, title_txt, ha="center", va="center", fontsize=9.0, weight="bold", color=col)

    rows = [
        # Row 1: Target 1 (Deep Sleep)
        (0.66,
         "Poucos Passos no Dia (< 6.500)\n+ Consumo de Álcool à Noite",
         "Queda do Sono Profundo N3 (< 16%)\n+ Aumento de Despertares (WASO)",
         "ALVO 1: Arquitetura do Sono\n• Se passos baixos: meta 8.000 passos/14d\n• Só investiga apneia se ativo e N3 baixo",
         "Passos × N3:\nr = +0,766\nÁlcool × WASO:\nr = +0,296",
         "Filtro de\nPassos e\nÁlcool"),

        # Row 2: Target 2 (Metabolic)
        (0.46,
         "Tela à Noite (> 130 min)\n+ Cafeína Alta (> 80 mg)",
         "Subida da FC de Repouso (>= 72 bpm)\n+ Atraso para Dormir (+22 min)",
         "ALVO 2: Risco Metabólico (Sangue)\n• Exames: Glicose e HbA1c (LOINC 4548-4)\n• Exige janela de 14–21 dias sem excessos",
         "Tela × Estresse:\nr = +0,311\nCafeína × Estresse:\nr = +0,305",
         "Janela de\n14 a 21\nDias"),

        # Row 3: Target 3 (Inflammation)
        (0.26,
         "Noite Curta (< 6,0 h de sono)\n+ Efeito Agudo do Álcool",
         "Queda Brusca da HRV (< 38 ms)\n+ Subida da FC Basal",
         "ALVO 3: Inflamação Sistêmica\n• Exames: PCR-us (30522-7) e Leucócitos\n• Regra de 4 dias seguidos de HRV baixa",
         "Sono × HRV:\nr = +0,287\nÁlcool × HRV:\nr = −0,163",
         "Persistência\n>= 4 Dias\nSeguidos"),

        # Row 4: Target 4 (Anemia)
        (0.06,
         "Sedentarismo / Falta de Treino\n+ Uso de Termogênico / Cafeína",
         "FC Diurna Alta (> 92 bpm)\nMesmo com Poucos Passos (< 6.000)",
         "ALVO 4: Triagem de Anemia / Ferro\n• Exames: Hemoglobina e Ferritina (2276-4)\n• Cruza ICD com histórico no banco FHIR",
         "Esforço Cardíaco\nICD = FC_dia /\nln(passos + 1)",
         "Ancoragem\nno Banco\nFHIR"),
    ]

    for y, c1_txt, c2_txt, c3_txt, edge1_lbl, edge2_lbl in rows:
        h = 0.145
        # Box 1
        ax.add_patch(FancyBboxPatch((0.02, y), 0.26, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                    fc="#fef3c7", ec="#b45309", lw=1.3))
        ax.text(0.15, y + h / 2, c1_txt, ha="center", va="center", fontsize=8.0, color="#0f172a", weight="bold")

        # Box 2
        ax.add_patch(FancyBboxPatch((0.37, y), 0.26, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                    fc="#e0f2fe", ec="#0369a1", lw=1.3))
        ax.text(0.50, y + h / 2, c2_txt, ha="center", va="center", fontsize=8.0, color="#0f172a", weight="bold")

        # Box 3
        ax.add_patch(FancyBboxPatch((0.72, y), 0.26, h, boxstyle="round,pad=0.006,rounding_size=0.015",
                                    fc="#dcfce7", ec="#15803d", lw=1.3))
        ax.text(0.85, y + h / 2, c3_txt, ha="center", va="center", fontsize=7.7, color="#0f172a")

        # Arrow 1 -> 2
        draw_arrow(ax, 0.282, y + h / 2, 0.368, y + h / 2, edge1_lbl, "#475569")
        # Arrow 2 -> 3
        draw_arrow(ax, 0.632, y + h / 2, 0.718, y + h / 2, edge2_lbl, "#15803d")

    out = os.path.join(ROOT, "figura4_2_dag_causal_e_mitigacao_55200.png")
    fig.savefig(out, dpi=240, facecolor="white")
    plt.close(fig)
    return out


def gerar_figura4_3():
    """Figura dedicada ao grafico de barras horizontais das 55.200 medicoes diarias (zero sobreposicao)."""
    fig = plt.figure(figsize=(13.0, 4.9), dpi=240)
    ax = fig.add_axes([0.34, 0.27, 0.61, 0.61])

    targets = [
        "Alvo 1: Queda do Sono Profundo N3 (< 16%)\nTotal: 14.553 dias anômalos na coorte",
        "Alvo 2: FC de Repouso Elevada (>= 72 bpm)\nTotal: 9.893 dias anômalos na coorte",
        "Alvo 3: Queda Crítica da HRV (< 38 ms)\nTotal: 21.028 dias anômalos na coorte",
        "Alvo 4: FC Diurna Alta p/ Poucos Passos\nTotal: 3.834 dias anômalos na coorte"
    ]
    explained_pct = [77.0, 97.4, 56.1, 70.4]
    explained_counts = [11211, 9633, 11803, 2701]
    residual_pct = [23.0, 2.6, 43.9, 29.6]
    residual_counts = [3342, 260, 9225, 1133]

    y_pos = np.arange(len(targets))[::-1]

    ax.barh(y_pos, explained_pct, height=0.54, color="#059669", edgecolor="#065f46",
            label="Falsos Positivos Evitados (Explicados por Hábitos: Passos, Álcool, Tela, Cafeína ou Sono Curto)")
    ax.barh(y_pos, residual_pct, left=explained_pct, height=0.54, color="#dc2626", edgecolor="#991b1b",
            label="Sinal Clínico Residual (Encaminhado para Regra de Persistência / Exame de Sangue LOINC)")

    for yp, ep, ec, rp, rc in zip(y_pos, explained_pct, explained_counts, residual_pct, residual_counts):
        ax.text(ep / 2.0, yp, f"{ep:.1f}% ({ec:,} dias)".replace(",", ".").replace(".", ",", 1),
                ha="center", va="center", color="white", fontsize=8.6, weight="bold")
        if rp >= 15:
            ax.text(ep + rp / 2.0, yp, f"{rp:.1f}% ({rc:,} d)".replace(",", ".").replace(".", ",", 1),
                    ha="center", va="center", color="white", fontsize=8.2, weight="bold")
        else:
            ax.text(101.2, yp, f"{rp:.1f}% ({rc} d)".replace(".", ","),
                    ha="left", va="center", color="#991b1b", fontsize=8.4, weight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(targets, fontsize=8.6, color="#0f172a", weight="bold")
    ax.set_xlim(0, 112)
    ax.set_xlabel("Proporção dos Dias com Alteração no Smartwatch (Base: 55.200 Registros Diários de 300 Pacientes)", fontsize=8.8)
    ax.set_title("IMPACTO PRÁTICO DA INFERÊNCIA CAUSAL: PROPORÇÃO DE ALARMES EXPLICADOS POR HÁBITOS COTIDIANOS",
                 fontsize=10.0, weight="bold", color="#0f172a", pad=12)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.18), ncol=1, fontsize=8.2, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)

    out = os.path.join(ROOT, "figura4_3_impacto_mitigacao_55200.png")
    fig.savefig(out, dpi=240, facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(gerar_figura4_1())
    print(gerar_figura4_2())
    print(gerar_figura4_3())
