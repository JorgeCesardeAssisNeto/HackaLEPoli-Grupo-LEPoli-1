import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Configura fonte serifada acadêmica no Matplotlib com suporte completo a setas diagonais Unicode (↗ / ↘)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['DejaVu Serif', 'Times New Roman']
plt.rcParams['axes.edgecolor'] = '#334155'
plt.rcParams['axes.linewidth'] = 0.8


def gerar_figura1_fluxo_arquitetura(output_path):
    """
    Gera a Figura 1: Fluxograma Arquitetural Completo do Sistema Open Health em Operação
    (Ingestão -> 4 Tabelas FHIR/LOINC -> Motor de Gradiente -> Base Determinística 565 -> Display Longitudinal).
    """
    fig, ax = plt.subplots(figsize=(12, 4.6), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 42)

    # Título interno sutil
    ax.text(50, 39.5, "ARQUITETURA EM OPERAÇÃO — FLUXO DE CLASSIFICAÇÃO, INTERPRETAÇÃO DETERMINÍSTICA E DISPLAY LONGITUDINAL",
            ha='center', va='center', fontsize=9.5, weight='bold', color='#0f172a')

    def draw_stage(x, y, w, h, num, title, subtitle, items, header_color, border_color, bg_color='#f8fafc'):
        # Sombra leve
        sh = patches.FancyBboxPatch((x + 0.3, y - 0.4), w, h, boxstyle="round,pad=0.2,rounding_size=0.8",
                                    fc='#cbd5e1', ec='none', alpha=0.5, zorder=1)
        ax.add_patch(sh)
        # Caixa principal
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.8",
                                     fc=bg_color, ec=border_color, lw=1.2, zorder=2)
        ax.add_patch(box)
        # Faixa de cabeçalho
        hh = 5.8
        hdr = patches.FancyBboxPatch((x, y + h - hh), w, hh, boxstyle="round,pad=0.2,rounding_size=0.8",
                                     fc=header_color, ec=border_color, lw=1.0, zorder=3)
        ax.add_patch(hdr)
        ax.add_patch(patches.Rectangle((x, y + h - hh), w, 1.5, fc=header_color, ec='none', zorder=3))

        ax.text(x + w/2, y + h - 2.1, f"{num}. {title}", ha='center', va='center',
                color='#ffffff', fontsize=8.0, weight='bold', zorder=4)
        ax.text(x + w/2, y + h - 4.3, subtitle, ha='center', va='center',
                color='#e2e8f0', fontsize=6.6, style='italic', zorder=4)

        curr_y = y + h - hh - 2.6
        for it in items:
            ax.text(x + 1.1, curr_y, f"• {it}", ha='left', va='center',
                    color='#1e293b', fontsize=6.7, zorder=4)
            curr_y -= 3.1

    # 5 Estágios Horizontais
    w_box = 17.2
    h_box = 31.0
    y_box = 4.5
    xs = [1.8, 21.3, 40.8, 60.3, 79.8]

    draw_stage(xs[0], y_box, w_box, h_box, "1", "Ingestão & Extração", "Híbrida (Nuvem / Local)", [
        "Upload de PDF do Laudo",
        "Gemini 2.5 Flash (Pydantic)",
        "Contingência Offline (20MB)",
        "Mapeamento 113 Analitos",
        "Codificação LOINC & UCUM",
        "Hash SHA-256 (ICP-Brasil)",
        "Unificação de 10 Laudos"
    ], "#1e293b", "#334155")

    draw_stage(xs[1], y_box, w_box, h_box, "2", "Banco Relacional", "4 Tabelas FHIR / LGPD", [
        "patients (CPF, CNS, Sexo)",
        "diagnostic_reports (Origem)",
        "observations (Vertical EAV)",
        "consents (Gatekeeper LGPD)",
        "Query SQL por codigo_loinc",
        "Ordenação: data_coleta ASC",
        "Índices B-Tree O(log n)"
    ], "#1e3a8a", "#1d4ed8")

    draw_stage(xs[2], y_box, w_box, h_box, "3", "Motor de Gradiente", "CLSI / CTCAE / CAP", [
        "Largura L = R_max - R_min",
        "Posição P = (V - R_min) / L",
        "Desvio D = |V - Borda| / L",
        "5 Estados Clínicos Internos",
        "Mapeamento 4 Níveis UX",
        "Tendência Temporal (↗ / ↘)",
        "Alerta se Variação > 20%"
    ], "#0f766e", "#0d9488")

    draw_stage(xs[3], y_box, w_box, h_box, "4", "Base Determinística", "Zero LLM em Runtime", [
        "Chave (LOINC, Nível_1_a_5)",
        "113 Exames × 5 Faixas = 565",
        "Lookup em Memória O(1) <1ms",
        "Zero Risco de Alucinação",
        "5 Pilares Educativos (18-25a)",
        "2 a 3 Perguntas p/ o Médico",
        "Proibição Estrita Diagnóstico"
    ], "#6d28d9", "#7c3aed")

    draw_stage(xs[4], y_box, w_box, h_box, "5", "Display do Paciente", "UX Longitudinal Segura", [
        "Curva Temporal por LOINC",
        "Banda Sombreada Referência",
        "Cores: Verde/Amarelo/Lar/Verm",
        "Tooltips Multi-Laboratório",
        "Badges de Tendência (↗ / ↘)",
        "Cards dos 5 Pilares Clínicos",
        "Visão Tabular Pivotada"
    ], "#b45309", "#d97706")

    # Setas conectoras entre os estágios
    for i in range(4):
        x_start = xs[i] + w_box + 0.2
        x_end = xs[i+1] - 0.2
        y_mid = y_box + h_box / 2
        ax.annotate('', xy=(x_end, y_mid), xytext=(x_start, y_mid),
                    arrowprops=dict(arrowstyle="->,head_width=0.35,head_length=0.45", color="#0f172a", lw=1.6),
                    zorder=5)

    # Rodapé explicativo dentro da figura
    ax.text(50, 1.3,
            "Conformidade Técnica: HL7 FHIR R4 (BR Core)  |  LOINC v2.76 & UCUM  |  CLSI EP28-A3c & GP47  |  NCI CTCAE v5.0  |  LGPD (Art. 11 e 18)",
            ha='center', va='center', fontsize=7.2, style='italic', color='#475569')

    plt.tight_layout(pad=0.3)
    plt.savefig(output_path, dpi=300, facecolor='#ffffff')
    plt.close()
    print(f"Figura 1 salva em: {output_path}")


def gerar_figura2_gradiente_e_serie(output_path):
    """
    Gera a Figura 2: Painel duplo acadêmico:
      (A) Régua Matemática de Normalização do Gradiente (5 Estados Clínicos CLSI/CTCAE -> 4 Níveis Visuais UX)
      (B) Série Temporal Longitudinal Real da Coorte (Ferritina Sérica LOINC 2276-4 e Glicose LOINC 2345-7) com Banda Sombreada
    """
    fig = plt.figure(figsize=(12, 5.2), dpi=300)
    fig.patch.set_facecolor('#ffffff')

    # Painel A (Superior): Régua Matemática do Gradiente
    ax1 = fig.add_axes([0.04, 0.56, 0.92, 0.38])
    ax1.set_facecolor('#ffffff')
    ax1.axis('off')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 32)

    ax1.text(50, 29.5, "(A) MODELO MATEMÁTICO DE GRADIENTE: NORMALIZAÇÃO DE ESCALA E MAPEAMENTO EM 4 NÍVEIS VISUAIS SEGUROS",
             ha='center', va='center', fontsize=9.0, weight='bold', color='#0f172a')

    # Blocos da régua horizontal (de x=4 a x=96)
    zones = [
        (4,  11, "#ef4444", "Alteração Acentuada\n(Vermelho — Nível 4 UX)", "Desvio > 50%\n(CTCAE Graus 3–4 / CAP)"),
        (15, 11, "#f97316", "Alterado Moderado\n(Laranja — Nível 3 UX)", "Desvio 15% a 50%\n(CTCAE Grau 2)"),
        (26, 9,  "#f59e0b", "Atenção / Leve\n(Amarelo — Nível 2)", "Desvio ≤ 15%\n(CTCAE Grau 1)"),
        (35, 7,  "#eab308", "Limítrofe Inf.\n(Amarelo — Nível 2)", "Posição < 10%\n(CLSI Fronteira)"),
        (42, 16, "#10b981", "NORMAL (ZONA CENTRAL)\n(Verde — Nível 1 UX)", "Posição 10% a 90% da Largura L\n(CLSI EP28-A3c — 95% Pop. Saudável)"),
        (58, 7,  "#eab308", "Limítrofe Sup.\n(Amarelo — Nível 2)", "Posição > 90%\n(CLSI Fronteira)"),
        (65, 9,  "#f59e0b", "Atenção / Leve\n(Amarelo — Nível 2)", "Desvio ≤ 15%\n(CTCAE Grau 1)"),
        (74, 11, "#f97316", "Alterado Moderado\n(Laranja — Nível 3 UX)", "Desvio 15% a 50%\n(CTCAE Grau 2)"),
        (85, 11, "#ef4444", "Alteração Acentuada\n(Vermelho — Nível 4 UX)", "Desvio > 50%\n(CTCAE Graus 3–4 / CAP)"),
    ]

    for x, w, col, top_lbl, bot_lbl in zones:
        rect = patches.FancyBboxPatch((x + 0.15, 11.5), w - 0.3, 8.5,
                                      boxstyle="round,pad=0.1,rounding_size=0.4",
                                      fc=col, ec='#1e293b', lw=0.7, alpha=0.90)
        ax1.add_patch(rect)
        ax1.text(x + w/2, 15.7, top_lbl, ha='center', va='center',
                 color='#ffffff' if col != '#eab308' else '#0f172a',
                 fontsize=6.1, weight='bold')
        ax1.text(x + w/2, 6.2, bot_lbl, ha='center', va='center',
                 color='#1e293b', fontsize=5.9)

    # Marcadores das Bordas R_min e R_max
    ax1.plot([35, 35], [9.5, 22.5], color='#0f172a', lw=1.8, ls='--')
    ax1.text(35, 24.2, "faixa_referencia_min\n(Posição = 0%)", ha='center', va='center',
             fontsize=6.8, weight='bold', color='#0f172a')

    ax1.plot([65, 65], [9.5, 22.5], color='#0f172a', lw=1.8, ls='--')
    ax1.text(65, 24.2, "faixa_referencia_max\n(Posição = 100%)", ha='center', va='center',
             fontsize=6.8, weight='bold', color='#0f172a')

    # Chave agrupando Limítrofe Interno + Grau 1 em "Atenção / Leve (Amarelo)"
    ax1.text(50, 1.2,
             "Fórmulas Universais:   Largura (L) = R_max − R_min   |   Posição Interna (P) = (Valor − R_min) / L   |   Desvio Externo (D) = |Valor − Borda| / L   |   Tendência (↗/↘): |Δ| > 20%",
             ha='center', va='center', fontsize=7.0, weight='bold', color='#1e3a8a')

    # Painel B (Inferior): Dois Gráficos de Evolução Longitudinal com Faixa Sombreada
    # Subplot B1: Glicose em Jejum (LOINC 2345-7 / 1558-6)
    ax2 = fig.add_axes([0.07, 0.09, 0.41, 0.39])
    datas = ["Mar/23", "Jun/23", "Out/23", "Jan/24", "Abr/24", "Set/24", "Fev/25", "Jul/25", "Out/25", "Jan/26"]
    glicose = [104, 96, 94, 93, 91, 90, 92, 93, 96, 99]
    x_idx = np.arange(len(datas))

    # Faixa de referência sombreada (70 a 99 mg/dL)
    ax2.axhspan(70, 99, color='#10b981', alpha=0.14, label='Faixa de Referência (70–99 mg/dL)')
    ax2.axhline(99, color='#059669', lw=0.9, ls='--', alpha=0.8)
    ax2.axhline(70, color='#059669', lw=0.9, ls='--', alpha=0.8)

    ax2.plot(x_idx, glicose, color='#1e3a8a', lw=1.8, zorder=3)
    cores_glic = ['#f97316' if v > 99 else ('#eab308' if v >= 96 else '#10b981') for v in glicose]
    for xi, yi, ci in zip(x_idx, glicose, cores_glic):
        ax2.scatter(xi, yi, color=ci, edgecolor='#0f172a', s=42, zorder=4, lw=0.8)
        ax2.text(xi, yi + 1.8, f"{yi}", ha='center', va='bottom', fontsize=6.5, weight='bold', color='#0f172a')

    ax2.set_title("(B1) Série Longitudinal: Glicose (LOINC 2345-7) — Unidade UCUM: mg/dL", fontsize=8.0, weight='bold', color='#0f172a', pad=6)
    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(datas, fontsize=6.5, rotation=25)
    ax2.set_ylabel("mg/dL", fontsize=7.5)
    ax2.set_ylim(64, 114)
    ax2.grid(True, ls=':', alpha=0.4, color='#94a3b8')
    ax2.legend(loc='lower left', fontsize=6.5, frameon=True)

    # Subplot B2: Ferritina Sérica (LOINC 2276-4) com Alerta de Tendência (↗ / ↘)
    ax3 = fig.add_axes([0.55, 0.09, 0.41, 0.39])
    ferritina = [42.0, 48.0, 35.0, 52.0, 38.1, 61.2, 75.0, 98.4, 96.0, 97.5]

    ax3.axhspan(10, 291, color='#10b981', alpha=0.14, label='Faixa de Referência (10–291 ng/mL)')
    ax3.axhline(10, color='#059669', lw=0.9, ls='--', alpha=0.8)
    ax3.plot(x_idx, ferritina, color='#0f766e', lw=1.8, zorder=3)

    for i, (xi, yi) in enumerate(zip(x_idx, ferritina)):
        ax3.scatter(xi, yi, color='#10b981', edgecolor='#0f172a', s=42, zorder=4, lw=0.8)
        lbl = f"{yi:.0f}"
        if i == 2:
            lbl += " (↘-27%)"
        elif i == 5:
            lbl += " (↗+61%)"
        ax3.text(xi, yi + 4.5, lbl, ha='center', va='bottom', fontsize=6.3, weight='bold',
                 color='#b45309' if i in (2, 5) else '#0f172a')

    ax3.set_title("(B2) Série Longitudinal: Ferritina (LOINC 2276-4) com Badges de Tendência (↗ / ↘)", fontsize=8.0, weight='bold', color='#0f172a', pad=6)
    ax3.set_xticks(x_idx)
    ax3.set_xticklabels(datas, fontsize=6.5, rotation=25)
    ax3.set_ylabel("ng/mL", fontsize=7.5)
    ax3.set_ylim(0, 125)
    ax3.grid(True, ls=':', alpha=0.4, color='#94a3b8')
    ax3.legend(loc='lower right', fontsize=6.5, frameon=True)

    plt.savefig(output_path, dpi=300, facecolor='#ffffff')
    plt.close()
    print(f"Figura 2 salva em: {output_path}")


if __name__ == '__main__':
    base_dir = r"c:\Users\janna\Desktop\Hackathon LEPoli"
    gerar_figura1_fluxo_arquitetura(os.path.join(base_dir, "figura1_fluxo_arquitetura_deterministica.png"))
    gerar_figura2_gradiente_e_serie(os.path.join(base_dir, "figura2_gradiente_e_serie_longitudinal.png"))
