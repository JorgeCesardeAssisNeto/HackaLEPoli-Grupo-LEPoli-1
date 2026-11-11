"""Figuras academicas do Artigo Parte III - Wearables x Hemograma x NHANES."""
import os, sys, json, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['DejaVu Serif', 'Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r"c:\Users\janna\Desktop\Hackathon LEPoli"
OUT = ROOT
VAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validacao_cv.json")
if not os.path.exists(VAL):
    VAL = r"C:\Users\janna\.gemini\antigravity\brain\bbb68fb2-9595-4ef1-b666-fcaa93e47f43\scratch\validacao_cv.json"
val = json.load(open(VAL, encoding="utf-8"))


def box(ax, x, y, w, h, title, lines, fc, ec, tsize=9.2, lsize=7.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top", fontsize=tsize, weight="bold", color="#0f172a")
    for i, l in enumerate(lines):
        ax.text(x + 0.012, y + h - 0.09 - i * 0.047, l, ha="left", va="top", fontsize=lsize, color="#1e293b")


def arrow(ax, x1, y1, x2, y2, color="#334155"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, lw=1.4, color=color))


# =====================================================================
# FIGURA 1 - Arquitetura de inferencia
# =====================================================================
def figura1():
    fig, ax = plt.subplots(figsize=(13, 6.2), dpi=220)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    box(ax, 0.01, 0.55, 0.19, 0.40, "1. Wearable (diário)",
        ["resting_hr_bpm · avg_hr_day_bpm", "hrv_rmssd_ms · spo2_avg_pct", "sleep_duration_hours · WASO",
         "sbp_mmHg / dbp_mmHg", "workout_minutes · alcohol_units", "POST /wearables/sync"], "#e0f2fe", "#0369a1")
    box(ax, 0.01, 0.06, 0.19, 0.40, "2. Exames (Open Health)",
        ["observations (LOINC/UCUM)", "Hb 718-7 · Hct 4544-3", "Leucócitos 6690-2", "PCR-us 30522-7",
         "Glicose 2345-7 · HbA1c 4548-4", "consents (LGPD) ativo"], "#fee2e2", "#b91c1c")
    box(ax, 0.26, 0.30, 0.20, 0.44, "3. WearableBridge",
        ["Janela móvel 7–14 dias", "Baseline: 7 primeiros dias", "Mapeamento → variáveis NHANES",
         "resting_hr_bpm → BPXOPLS", "sleep_h → SLD012", "workout → PAD680 (inverso)", "Filtros: treino / álcool"], "#f1f5f9", "#334155")
    box(ax, 0.52, 0.30, 0.21, 0.44, "4. Modelos (treino NHANES)",
        ["Etapa 1: FC_pop = f(sangue, idade,", "   sexo, IMC)", "Etapa 2: Δ_ind = FC_0 − FC_pop(t_0)",
         "Resíduo = FC_wear − (FC_pop + Δ_ind)", "Metabólico · Apneia · Inflamatório", "Z-score · Δ média · slope"], "#ede9fe", "#6d28d9")
    box(ax, 0.79, 0.55, 0.20, 0.40, "5a. Display do Paciente",
        ["Zonas: Verde / Amarelo /", "   Vermelho / Azul", "Textos determinísticos", "Educação em saúde", "Sem diagnóstico"], "#dcfce7", "#15803d")
    box(ax, 0.79, 0.06, 0.20, 0.40, "5b. Briefing Pré-consulta",
        ["Resumo de desvios", "Resíduos + exames LOINC", "Clusters sinalizados", "Sugestão de reavaliação", "Decisão: médico"], "#fef3c7", "#b45309")
    arrow(ax, 0.20, 0.75, 0.26, 0.60); arrow(ax, 0.20, 0.26, 0.26, 0.44)
    arrow(ax, 0.46, 0.52, 0.52, 0.52)
    arrow(ax, 0.73, 0.60, 0.79, 0.75); arrow(ax, 0.73, 0.44, 0.79, 0.26)
    ax.text(0.625, 0.20, "Trava regulatória: saída = alerta contextual pré-redigido\n(par cluster × zona), nunca diagnóstico automatizado",
            ha="center", va="center", fontsize=8.2, style="italic", color="#7f1d1d",
            bbox=dict(boxstyle="round,pad=0.4", fc="#fff1f2", ec="#be123c", lw=0.9))
    plt.tight_layout()
    p = os.path.join(OUT, "figura3_1_arquitetura_inferencia_wearable.png")
    fig.savefig(p, bbox_inches="tight", facecolor="white"); plt.close(fig); return p


# =====================================================================
# FIGURA 2 - Clusters Wearable <-> Sangue
# =====================================================================
def figura2():
    fig, ax = plt.subplots(figsize=(13, 5.6), dpi=220)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    rows = [
        ("Cluster A — Transporte de O₂ (anemia / fadiga)", "#b91c1c", "#fee2e2",
         "↑ FCR sustentada · ↓ VO₂máx*\ntemperatura cutânea* estável", "Hemoglobina · Hematócrito\nHemácias · Ferritina"),
        ("Cluster B — Inflamatório / imunológico", "#c2410c", "#ffedd5",
         "↑ temperatura cutânea* basal\n↓ HRV (hrv_rmssd_ms) · ↑ FCR", "Leucócitos · PCR\nVHS"),
        ("Cluster C — Hipóxia / apneia", "#1d4ed8", "#dbeafe",
         "↓ spo2_avg_pct noturna recorrente\n↑ WASO (fragmentação)", "↑ Hematócrito · ↑ Hemácias\n(compensação crônica)"),
    ]
    ys = [0.70, 0.40, 0.10]
    ax.text(0.17, 0.97, "Sinal do wearable (janela 7–14 d)", ha="center", fontsize=10, weight="bold")
    ax.text(0.50, 0.97, "Hipótese fisiológica", ha="center", fontsize=10, weight="bold")
    ax.text(0.83, 0.97, "Validação no hemograma", ha="center", fontsize=10, weight="bold")
    for (t, ec, fc, w, b), y in zip(rows, ys):
        ax.add_patch(FancyBboxPatch((0.02, y), 0.30, 0.20, boxstyle="round,pad=0.01", fc="#f8fafc", ec="#475569"))
        ax.text(0.17, y + 0.10, w, ha="center", va="center", fontsize=8.6)
        ax.add_patch(FancyBboxPatch((0.37, y), 0.26, 0.20, boxstyle="round,pad=0.01", fc=fc, ec=ec, lw=1.4))
        ax.text(0.50, y + 0.10, t.replace(" — ", "\n"), ha="center", va="center", fontsize=8.8, weight="bold", color=ec)
        ax.add_patch(FancyBboxPatch((0.68, y), 0.30, 0.20, boxstyle="round,pad=0.01", fc="#fff", ec=ec, lw=1.2))
        ax.text(0.83, y + 0.10, b, ha="center", va="center", fontsize=8.6)
        arrow(ax, 0.32, y + 0.10, 0.37, y + 0.10, ec); arrow(ax, 0.63, y + 0.10, 0.68, y + 0.10, ec)
    ax.text(0.5, 0.025, "Filtro de falsos positivos: dias com workout_minutes elevado ou alcohol_units > 0 nas 24–48 h anteriores são excluídos/ponderados "
            "antes do cálculo do desvio.   * Variável prevista na especificação, ainda ausente no dataset atual.",
            ha="center", fontsize=7.6, style="italic", color="#334155")
    plt.tight_layout()
    p = os.path.join(OUT, "figura3_2_clusters_wearable_hemograma.png")
    fig.savefig(p, bbox_inches="tight", facecolor="white"); plt.close(fig); return p


# =====================================================================
# FIGURA 3 - Desempenho (in-sample vs CV) + residuo da Etapa 2
# =====================================================================
def residuos_etapa2():
    sys.path.insert(0, os.path.join(ROOT, "nhanes_explorer")); os.chdir(ROOT)
    import data_engine as de
    from sklearn.ensemble import HistGradientBoostingRegressor as HGR
    from sklearn.model_selection import KFold, cross_val_predict
    eng = object.__new__(de.NhanesDataEngine)
    eng.data_dir = "Dados NHANHES"; eng.tables = {}; eng.meta = {}; eng.codebook = []; eng.seqn_by_table = {}
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        eng.load_data()
    df = eng.master_df
    h = df[(df['BPQ020'] == 2.0) & (df['BPQ040A'] != 1.0) & (df['bp_sys_avg'] < 135) & (df['bp_dia_avg'] < 85)
           & df['BPXOPLS1'].between(45, 130) & df['BPXOPLS3'].between(45, 130) & df['LBXHGB'].notna()]
    pop = ['LBXHGB', 'LBXHCT', 'LBXRBCSI', 'LBXWBCSI', 'LBXPLTSI', 'RIDAGEYR', 'RIAGENDR', 'BMXBMI']
    d = h[pop + ['BPXOPLS1', 'BPXOPLS3']].dropna()
    kf = KFold(5, shuffle=True, random_state=42)
    m = HGR(max_depth=4, learning_rate=0.04, random_state=42)
    p3 = cross_val_predict(m, d[pop], d['BPXOPLS3'], cv=kf)
    p1 = cross_val_predict(m, d[pop], d['BPXOPLS1'], cv=kf)
    pred = p3 + (d['BPXOPLS1'] - p1)
    return (d['BPXOPLS3'] - pred).values, (d['BPXOPLS3'] - p3).values


def figura3():
    fig = plt.figure(figsize=(13, 4.6), dpi=220)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1.0, 1.05], wspace=0.32)
    # A - AUC
    ax = fig.add_subplot(gs[0])
    names = ["Anemia\n(M1)", "Ferritina\n<30 (M1)", "HbA1c≥5,7\nestrito", "HbA1c≥5,7\nexpandido", "Glicose≥100\nestrito", "Apneia\n(SLQ)"]
    ins = [0.852, 0.863, 0.716, 0.842, 0.712, 0.773]
    cv = [val["m1_anemia"]["AUC_cv"], val["m1_ferritina_baixa"]["AUC_cv"], val["metab_hba1c_estrito"]["AUC_cv"],
          val["metab_hba1c_expandido"]["AUC_cv"], val["metab_glicose_estrito"]["AUC_cv"], val["apneia_HGB"]["AUC_cv"]]
    x = np.arange(len(names))
    ax.bar(x - 0.19, ins, 0.38, color="#cbd5e1", ec="#475569", label="Painel (in-sample)")
    ax.bar(x + 0.19, cv, 0.38, color="#1e3a8a", label="Validação cruzada 5-fold")
    for i, v in enumerate(cv):
        ax.text(i + 0.19, v + 0.01, f"{v:.2f}".replace(".", ","), ha="center", fontsize=7, color="#1e3a8a")
    ax.axhline(0.70, ls="--", color="#b91c1c", lw=0.9); ax.text(5.6, 0.705, "0,70", color="#b91c1c", fontsize=7, ha="right")
    ax.set_ylim(0.5, 0.95); ax.set_xticks(x); ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("ROC-AUC", fontsize=9); ax.set_title("A. Classificadores de triagem", fontsize=10, weight="bold", loc="left")
    ax.legend(fontsize=7, loc="upper right", frameon=False); ax.spines[['top', 'right']].set_visible(False)
    # B - R2
    ax = fig.add_subplot(gs[1])
    n2 = ["FC só\nsangue\n(Etapa 1)", "FC\ncalibrada\n(Etapa 2)", "FC por\ninflamação", "PAS por\ninflamação", "HbA1c\ncontínua"]
    i2 = [0.129, 0.874, 0.371, 0.542, 0.400]
    c2 = [val["etapa1_pop_HGB"]["R2_cv"], val["etapa2_calibrada"]["R2"], val["inflam_pulso_HGB"]["R2_cv"],
          val["inflam_PAS_HGB"]["R2_cv"], val["metab_hba1c_continuo"]["R2_cv"]]
    x = np.arange(len(n2))
    ax.bar(x - 0.19, i2, 0.38, color="#cbd5e1", ec="#475569")
    ax.bar(x + 0.19, c2, 0.38, color="#6d28d9")
    for i, v in enumerate(c2):
        ax.text(i + 0.19, v + 0.015, f"{v:.2f}".replace(".", ","), ha="center", fontsize=7, color="#6d28d9")
    ax.set_ylim(0, 1); ax.set_xticks(x); ax.set_xticklabels(n2, fontsize=7)
    ax.set_ylabel("R²", fontsize=9); ax.set_title("B. Regressores (cinza: painel)", fontsize=10, weight="bold", loc="left")
    ax.spines[['top', 'right']].set_visible(False)
    # C - residuos
    ax = fig.add_subplot(gs[2])
    r2, r1 = residuos_etapa2()
    sd = r2.std()
    bins = np.arange(-35, 36, 1.5)
    ax.hist(r1, bins=bins, color="#fca5a5", alpha=0.6, label=f"Só Etapa 1 (DP {r1.std():.1f})".replace(".", ","))
    ax.hist(r2, bins=bins, color="#1e3a8a", alpha=0.75, label=f"Etapa 1 + 2 (DP {sd:.1f})".replace(".", ","))
    for k in (-1.5, 1.5):
        ax.axvline(k * sd, color="#b45309", ls="--", lw=1)
    ax.text(1.5 * sd + 0.6, ax.get_ylim()[1] * 0.85, "±1,5σ", color="#b45309", fontsize=7.5)
    ax.set_xlim(-30, 30); ax.set_xlabel("Resíduo: FC medida − prevista (bpm)", fontsize=8.5)
    ax.set_ylabel("Indivíduos (coorte saudável)", fontsize=8.5)
    ax.set_title("C. Resíduo da FCR calibrada", fontsize=10, weight="bold", loc="left")
    ax.legend(fontsize=7, frameon=False, loc="upper left"); ax.spines[['top', 'right']].set_visible(False)
    p = os.path.join(OUT, "figura3_3_desempenho_modelos_cv.png")
    fig.savefig(p, bbox_inches="tight", facecolor="white"); plt.close(fig)
    return p, float(sd)


if __name__ == "__main__":
    print(figura1()); print(figura2()); print(figura3())
