# -*- coding: utf-8 -*-
"""Gera os CSVs de conhecimento a partir da base existente (somente leitura) + conteúdo redigido + NHANES local.

Uso (a partir da raiz do repositório):
    python conhecimento_exames_csv/_gerador/gerar_csvs.py

Não altera nenhum arquivo existente do projeto.
"""
import csv, json, os, re, sys
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.dirname(AQUI)
RAIZ = os.path.dirname(SAIDA)
SEM = os.path.join(RAIZ, "02_backend", "03_semantica_ontologias")
NH = os.path.join(RAIZ, "dados_nhanes")
sys.path.insert(0, AQUI)
from conteudo_exames import C  # noqa: E402

DATA = "2026-11-14"
AUSENTE = ""

kb = json.load(open(os.path.join(SEM, "base_conhecimento_exames_565.json"), encoding="utf-8"))
cat = {x["coluna"]: x for x in json.load(open(os.path.join(SEM, "catalogo_colunas_completo.json"), encoding="utf-8"))}
mapa = json.load(open(os.path.join(SEM, "mapa_colunas_loinc.json"), encoding="utf-8"))


def escrever(nome, cab, linhas):
    with open(os.path.join(SAIDA, nome), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(cab)
        for l in linhas:
            w.writerow(["" if l.get(c) is None else l.get(c) for c in cab])


def fmt(x, nd=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    return f"{x:.{nd}f}"


# ---------------------------------------------------------------- unidades
SUF = [("_10e6_uL", "10^6/µL"), ("_10e3_uL", "10^3/µL"), ("_g_dL", "g/dL"), ("_mg_dL", "mg/dL"), ("_ng_dL", "ng/dL"),
       ("_ug_dL", "µg/dL"), ("_pct", "%"), ("_fL", "fL"), ("_pg_mL", "pg/mL"), ("_pg", "pg"), ("_uIU_mL", "µUI/mL"),
       ("_mIU_mL", "mUI/mL"), ("_IU_mL", "UI/mL"), ("_mL_min", "mL/min"), ("_mEq_L", "mEq/L"), ("_mmol_L", "mmol/L"),
       ("_nmol_L", "nmol/L"), ("_umol_L", "µmol/L"), ("_U_L", "U/L"), ("_U_mL", "U/mL"), ("_ng_mL", "ng/mL"),
       ("_ng_L", "ng/L"), ("_mg_L", "mg/L"), ("_mm_h", "mm/h"), ("_seg", "s")]


def unidade(col):
    for s, u in SUF:
        if col.endswith(s):
            return u
    return ""


# --------------------------------------------------------------- referências
REFS = [
 dict(ref_id="REF_PROJ_KB565", instituicao_autoria="Projeto HackaLEPoli/Open Health", titulo="base_conhecimento_exames_565.json", versao="arquivo do ZIP fornecido", ano="", url_doi="02_backend/03_semantica_ontologias/base_conhecimento_exames_565.json", secao_pagina="", data_consulta=DATA, tipo_fonte="dado_do_projeto", status_acesso="lido_localmente", observacao="Textos e percentuais sem fonte declarada; usados apenas para identificação (coluna, LOINC, nome, categoria)."),
 dict(ref_id="REF_PROJ_CATALOGO", instituicao_autoria="Projeto HackaLEPoli/Open Health", titulo="catalogo_colunas_completo.json e mapa_colunas_loinc.json", versao="arquivo do ZIP fornecido", ano="", url_doi="02_backend/03_semantica_ontologias/", secao_pagina="", data_consulta=DATA, tipo_fonte="dado_do_projeto", status_acesso="lido_localmente", observacao=""),
 dict(ref_id="REF_PROJ_FAIXAS_DB", instituicao_autoria="Projeto HackaLEPoli/Open Health", titulo="FAIXAS_PADRAO_LOINC em database.py", versao="arquivo do ZIP fornecido", ano="", url_doi="02_backend/04_persistencia_dados/database.py", secao_pagina="dicionário FAIXAS_PADRAO_LOINC", data_consulta=DATA, tipo_fonte="dado_do_projeto", status_acesso="lido_localmente", observacao="Comentário cita CLSI EP28-A3c/SBPC-ML, mas não informa população, método nem laboratório. Hemoglobina, hematócrito e hemácias usam limites femininos para todos."),
 dict(ref_id="REF_PROJ_CLASSIFICADOR", instituicao_autoria="Projeto HackaLEPoli/Open Health", titulo="classificador.py — classificar_resultado_gradiente", versao="arquivo do ZIP fornecido", ano="", url_doi="02_backend/03_semantica_ontologias/classificador.py", secao_pagina="NIVEIS_5_CLASSIFICACOES, NIVEIS_4_VISUAIS_PACIENTE, classificar_resultado_gradiente", data_consulta=DATA, tipo_fonte="regra_do_projeto", status_acesso="lido_localmente", observacao="Regras de posição (10%/90%) e desvio (15%/50%) são do projeto; não são critério médico validado."),
 dict(ref_id="REF_RASCUNHO_AUTORAL", instituicao_autoria="Redação desta entrega", titulo="Textos de resumo, causas, impactos e mitigação", versao="1.0", ano="2026", url_doi="conhecimento_exames_csv/_gerador/conteudo_exames.py", secao_pagina="", data_consulta=DATA, tipo_fonte="rascunho_sem_fonte_primaria", status_acesso="nao_aplicavel", observacao="Redigido a partir de conhecimento médico geral. Nenhuma fonte primária conferida por item. Exige revisão clínica antes de uso."),
 dict(ref_id="REF_CLSI_EP28", instituicao_autoria="Clinical and Laboratory Standards Institute (CLSI)", titulo="EP28-A3c: Defining, Establishing, and Verifying Reference Intervals in the Clinical Laboratory", versao="A3c", ano="2010 (3ª ed.; corrigida 2010)", url_doi="https://clsi.org/shop/standards/ep28/", secao_pagina="", data_consulta="", tipo_fonte="norma", status_acesso="nao_acessado_nesta_sessao", observacao="Escopo: estabelecimento e verificação de intervalos de referência. Não define cinco níveis de gravidade, zona ideal nem percentuais de desvio. Texto completo é pago."),
 dict(ref_id="REF_CTCAE_V5", instituicao_autoria="National Cancer Institute (NCI) / U.S. DHHS", titulo="Common Terminology Criteria for Adverse Events (CTCAE)", versao="5.0", ano="2017", url_doi="https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events", secao_pagina="Termos laboratoriais (SOC Investigations; Blood and lymphatic system disorders; Metabolism and nutrition disorders); página não registrada", data_consulta="", tipo_fonte="criterio_evento_adverso", status_acesso="nao_acessado_nesta_sessao", observacao="Versão 5.0 escolhida porque é a citada no código do projeto. A versão 6.0 existe e não foi usada; não misturar. Graus de evento adverso em pesquisa oncológica; grau 5 = morte. Limites transcritos de memória: conferir no documento oficial antes do uso."),
 dict(ref_id="REF_CAP_CRITICOS", instituicao_autoria="College of American Pathologists (CAP)", titulo="Report Elements Part 2 (material institucional sobre resultados críticos)", versao="2019", ano="2019", url_doi="https://documents-cloud.cap.org/appsuite/learning/AP3/LMD/GoodLabDecisions/04_FrmtRsltRprts/story_content/external_files/Report%20Elements%20Part%202_2019_Proof.pdf", secao_pagina="", data_consulta="", tipo_fonte="escopo_valor_critico", status_acesso="nao_acessado_nesta_sessao", observacao="Usado apenas como escopo: valores críticos são definidos pela política de cada laboratório. Nenhum limite crítico foi extraído desta fonte."),
 dict(ref_id="REF_ADA_SOC_2025", instituicao_autoria="American Diabetes Association Professional Practice Committee", titulo="2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2025", versao="2025", ano="2025", url_doi="Diabetes Care 2025;48(Suppl. 1)", secao_pagina="Seção 2, critérios diagnósticos de diabetes e pré-diabetes; página não registrada", data_consulta="", tipo_fonte="diretriz_sociedade", status_acesso="nao_acessado_nesta_sessao", observacao="Limites amplamente publicados; transcritos sem conferência nesta sessão. Diagnóstico exige confirmação por repetição ou segundo teste."),
 dict(ref_id="REF_NHANES_1720", instituicao_autoria="CDC / National Center for Health Statistics", titulo="NHANES 2017–March 2020 Pre-pandemic (arquivos P_DEMO, P_CBC, P_GLU, P_GHB, P_TCHOL, P_HSCRP, P_FERTIN)", versao="2017–mar/2020", ano="2021", url_doi="https://wwwn.cdc.gov/nchs/nhanes/", secao_pagina="", data_consulta=DATA, tipo_fonte="dado_populacional", status_acesso="arquivos_xpt_lidos_localmente", observacao="População civil não institucionalizada dos EUA. Não representa a população brasileira."),
 dict(ref_id="REF_NHANES_1112", instituicao_autoria="CDC / National Center for Health Statistics", titulo="NHANES 2011–2012 (arquivos DEMO_G, HDL_G, TRIGLY_G, THYROD_G, TST_G)", versao="2011–2012", ano="2013", url_doi="https://wwwn.cdc.gov/nchs/nhanes/", secao_pagina="", data_consulta=DATA, tipo_fonte="dado_populacional", status_acesso="arquivos_xpt_lidos_localmente", observacao="População civil não institucionalizada dos EUA. Não representa a população brasileira."),
 dict(ref_id="REF_NHANES_GUIA", instituicao_autoria="CDC / National Center for Health Statistics", titulo="NHANES Analytic and Reporting Guidelines / Quality Analyses Guidelines", versao="", ano="", url_doi="https://wwwn.cdc.gov/nchs/nhanes/QualityAnalysesGuidelines.aspx", secao_pagina="", data_consulta="", tipo_fonte="guia_metodologico", status_acesso="nao_acessado_nesta_sessao", observacao="Pesos aplicados; variância pelo desenho (PSU/estrato) não calculada nesta entrega."),
]

# ------------------------------------------------------------ catálogo
SEXO_DEP = {"hemacias_10e6_uL", "hemoglobina_g_dL", "hematocrito_pct", "creatinina_mg_dL", "acido_urico_mg_dL",
            "ferritina_ng_mL", "gama_gt_ggt_U_L", "colesterol_hdl_mg_dL", "testosterona_total_ng_dL",
            "testosterona_livre_pg_mL", "estradiol_pg_mL", "progesterona_ng_mL", "fsh_mIU_mL", "lh_mIU_mL",
            "prolactina_ng_mL", "shbg_nmol_L", "dhea_s_ug_dL", "psa_total_ng_mL", "psa_livre_ng_mL",
            "ca_125_U_mL", "beta_hcg_quantitativo_mIU_mL", "ck_total_creatinofosfoquinase_U_L",
            "troponina_i_alta_sensibilidade_ng_L", "tfg_estimada_mL_min"}

catalogo, pend = [], []
pid = [0]


def pendencia(exame, registro, problema, impacto, necessario):
    pid[0] += 1
    pend.append(dict(pendencia_id=f"PEND_{pid[0]:04d}", exame_id=exame, registro_afetado=registro, problema=problema,
                     impacto_integracao=impacto, informacao_necessaria=necessario))


for col, v in kb.items():
    d, *_ = C[col]
    tipo = "qualitativo" if d == "qualitativo" else "quantitativo"
    if col in ("fan_fator_antinuclear", "vdrl_sifilis"):
        tipo = "qualitativo_com_titulo"
    if col == "anti_hbs_hepatite_b":
        tipo = "pendente_validacao"
    u = unidade(col)
    obs = []
    loinc_mapa = mapa.get(col, "")
    status = "conferido_com_catalogo"
    if loinc_mapa != v["codigo_loinc"]:
        status = "inconsistencia_registrada"
        obs.append(f"LOINC da base ({v['codigo_loinc']}) difere do mapa ({loinc_mapa})")
        pendencia(col, "catalogo_exames.csv", f"Campo codigo_loinc na base 565 e no catálogo contém '{v['codigo_loinc']}'; mapa_colunas_loinc.json contém '{loinc_mapa}'.",
                  "Busca por LOINC no interpretador não encontra este exame pelo código correto.", "Confirmar o código LOINC correto e corrigir na fonte do projeto.")
    if re.search(r" (G Dl|Ng Dl|Miu Ml|Umol L|Nmol L|U Ml|Seg)$", v["nome_exame"]):
        obs.append("nome_exame parece gerado a partir do identificador (contém unidade)")
    cat_num = v["categoria"].split(".")[0]
    if col in ("pcr_ultrassensivel_mg_L", "vhs_mm_h", "fibrinogenio_mg_dL", "d_dimero_ng_mL", "tap_tempo_protrombina_seg", "inr", "ttpa_seg", "fator_reumatoide_IU_mL", "fan_fator_antinuclear") and cat_num == "9":
        obs.append("categoria '9. MARCADORES TUMORAIS' não corresponde ao exame (inflamação/coagulação/autoimunidade)")
    if col in ("alfa_fetoproteina_afp_ng_mL", "cea_ng_mL", "psa_total_ng_mL", "psa_livre_ng_mL", "ca_125_U_mL", "ca_19_9_U_mL", "ca_15_3_U_mL", "beta_hcg_quantitativo_mIU_mL", "hiv_1_2", "hbsag_hepatite_b", "anti_hbs_hepatite_b", "anti_hcv_hepatite_c", "vdrl_sifilis") and cat_num == "10":
        obs.append("categoria '10. MARCADORES CARDÍACOS E MUSCULARES' não corresponde ao exame")
    if col in ("ferritina_ng_mL", "ferro_serico_ug_dL", "transferrina_mg_dL", "tibc_ug_dL", "saturacao_transferrina_pct", "vitamina_d_25oh_ng_mL", "vitamina_b12_pg_mL", "acido_folico_folato_ng_mL", "homocisteina_umol_L", "zinco_ug_dL") and cat_num == "8":
        obs.append("categoria '8. INFLAMAÇÃO, AUTOIMUNIDADE E COAGULAÇÃO' não corresponde ao exame (ferro/vitaminas)")
    if not u:
        obs.append("unidade ausente no identificador e na base; não atribuída por suposição")
    catalogo.append(dict(exame_id=col, coluna=col, codigo_loinc=v["codigo_loinc"], codigo_loinc_mapa=loinc_mapa,
                         nome_exame=v["nome_exame"], categoria=v["categoria"], tipo_resultado=tipo, unidade=u,
                         unidade_origem="sufixo_do_identificador_coluna" if u else "ausente",
                         sexo_dependente="sim" if col in SEXO_DEP else "nao_avaliado",
                         direcoes_relevantes=d, resumo_exame=C[col][1], ref_id_resumo="REF_RASCUNHO_AUTORAL",
                         status_catalogo=status, observacoes="; ".join(obs)))

# categoria 7 ausente
cats = sorted({v["categoria"] for v in kb.values()})
if not any(c.startswith("7.") for c in cats):
    pendencia("", "catalogo_exames.csv", "Não existe categoria '7.' na base; numeração salta de 6 para 8.", "Nenhum impacto funcional; afeta exibição/ordenação.", "Confirmar se havia uma categoria 7 prevista.")
pendencia("vdrl_sifilis", "base_conhecimento_exames_565.json", "codigo_loinc corrompido também no catálogo (texto concatenado com CIP).", "Join por LOINC falha.", "Corrigir a origem do código.")

# ------------------------------------------------------------ critérios
crit = []
cid = [0]


def criterio(**k):
    cid[0] += 1
    base = dict(criterio_id=f"CRIT_{cid[0]:04d}", nivel_id_produto="", codigo_destino_atual="", direcao="",
                operador_inferior="", limite_inferior="", operador_superior="", limite_superior="",
                limite_relativo="", unidade="", populacao="", sexo="", metodo="", ref_id="",
                condicoes_clinicas="", e_valor_critico="nao", urgencia="nao_definida", status_validacao="")
    base.update(k)
    crit.append(base)


# Mapa LOINC -> faixa do projeto (database.py), lido do fonte para não copiar à mão
src = open(os.path.join(RAIZ, "02_backend", "04_persistencia_dados", "database.py"), encoding="utf-8").read()
faixas = {m.group(1): (float(m.group(2)), float(m.group(3)), m.group(4))
          for m in re.finditer(r'"([\d-]+)":\s*\(([\d.]+),\s*([\d.]+),\s*"([^"]*)"', src)}
loinc2col = {v["codigo_loinc"]: k for k, v in kb.items()}
IR, IR_UNID = {}, {}
# Unidade da faixa do projeto vs unidade da coluna (sufixo); grafias equivalentes
EQUIV_U = {"µUI/mL": "µUI/mL", "10^6/µL": "10^6/µL", "10^3/µL": "10^3/µL"}
METODO_DEP = {"t4_livre_ng_dL", "tsh_uIU_mL"}
for lo, (a, b, u) in faixas.items():
    col = loinc2col.get(lo)
    if not col:
        pendencia("", "criterios_classificacao.csv", f"LOINC {lo} em FAIXAS_PADRAO_LOINC não existe na base 565.", "Faixa sem exame correspondente.", "Conferir código.")
        continue
    IR[col] = (a, b)
    IR_UNID[col] = u
    if col == "pcr_ultrassensivel_mg_L":
        pendencia(col, "criterios_classificacao.csv", f"Faixa do projeto em '{u}' (0,01–0,30) e coluna em mg/L.", "Comparar valor em mg/L com limite em mg/dL classifica errado por fator 10.", "Converter (1 mg/dL = 10 mg/L) ou corrigir a faixa.")
    criterio(exame_id=col, tipo_criterio="intervalo_referencia", nivel_id_produto="1", direcao="dentro_referencia",
             operador_inferior=">=", limite_inferior=fmt(a, 2), operador_superior="<=", limite_superior=fmt(b, 2),
             unidade=u, populacao="não informada na fonte", sexo="não informado", metodo="não informado",
             ref_id="REF_PROJ_FAIXAS_DB", condicoes_clinicas="Usar preferencialmente o intervalo impresso no laudo do laboratório.",
             status_validacao="fonte_do_projeto_sem_validacao")
    if col in ("hemoglobina_g_dL", "hematocrito_pct", "hemacias_10e6_uL"):
        pendencia(col, "criterios_classificacao.csv", "Faixa do projeto corresponde a limites femininos e é aplicada a todos.", "Homens podem ser classificados como acima da referência indevidamente.", "Faixas por sexo, de fonte identificada.")
    # Regras algorítmicas do projeto, convertidas em limites numéricos
    w = b - a
    # Operadores reproduzem classificar_resultado_gradiente: abaixo se valor < min; acima se valor > max;
    # limítrofe se posição < 0,10 ou > 0,90; leve se desvio <= 0,15; moderado se <= 0,50; acentuada se > 0,50.
    for cod, di, oi, lo_, os_, hi_ in [
        ("NORMAL", "dentro_referencia", ">=", a + 0.10 * w, "<=", b - 0.10 * w),
        ("LIMITROFE", "abaixo_dentro", ">=", a, "<", a + 0.10 * w), ("LIMITROFE", "acima_dentro", ">", b - 0.10 * w, "<=", b),
        ("ALTERADO_LEVE", "abaixo", ">=", a - 0.15 * w, "<", a), ("ALTERADO_LEVE", "acima", ">", b, "<=", b + 0.15 * w),
        ("ALTERADO_MODERADO", "abaixo", ">=", a - 0.50 * w, "<", a - 0.15 * w), ("ALTERADO_MODERADO", "acima", ">", b + 0.15 * w, "<=", b + 0.50 * w),
        ("ALTERACAO_ACENTUADA", "abaixo", "", None, "<", a - 0.50 * w), ("ALTERACAO_ACENTUADA", "acima", ">", b + 0.50 * w, "", None)]:
        criterio(exame_id=col, tipo_criterio="regra_algoritmica_projeto", codigo_destino_atual=cod, direcao=di,
                 operador_inferior=oi, limite_inferior=fmt(lo_, 3) if lo_ is not None else "",
                 operador_superior=os_, limite_superior=fmt(hi_, 3) if hi_ is not None else "",
                 unidade=u, populacao="não aplicável (regra matemática)", ref_id="REF_PROJ_CLASSIFICADOR",
                 condicoes_clinicas="Regra do classificador atual; operadores reproduzidos de classificar_resultado_gradiente; valores negativos indicam limite sem sentido físico.",
                 status_validacao="regra_do_projeto_nao_validada_clinicamente")
        if lo_ is not None and lo_ < 0:
            pendencia(col, "criterios_classificacao.csv", f"Regra {cod} ({di}) gera limite inferior negativo ({lo_:.3f}).", "Faixa sem sentido físico.", "Definir critério clínico para valores baixos.")

# Exames sem faixa no projeto
for col in kb:
    if col not in IR and C[col][0] != "qualitativo":
        pendencia(col, "criterios_classificacao.csv", "Sem intervalo de referência no projeto; o classificador depende da faixa extraída do laudo.", "Sem faixa no laudo, o classificador retorna INDETERMINADO.", "Intervalo de referência com população, método e fonte.")

# CTCAE v5.0 — termos laboratoriais (conferir no documento oficial)
CT = [
 ("hemoglobina_g_dL", "Anemia", "abaixo", [("1", "<LLN a 10,0 g/dL"), ("2", "<10,0 a 8,0 g/dL"), ("3", "<8,0 g/dL"), ("4", "consequências com risco de vida")]),
 ("leucocitos_totais_10e3_uL", "White blood cell decreased", "abaixo", [("1", "<LLN a 3,0 x10^3/µL"), ("2", "<3,0 a 2,0"), ("3", "<2,0 a 1,0"), ("4", "<1,0")]),
 ("neutrofilos_abs_10e3_uL", "Neutrophil count decreased", "abaixo", [("1", "<LLN a 1,5 x10^3/µL"), ("2", "<1,5 a 1,0"), ("3", "<1,0 a 0,5"), ("4", "<0,5")]),
 ("linfocitos_abs_10e3_uL", "Lymphocyte count decreased", "abaixo", [("1", "<LLN a 0,8 x10^3/µL"), ("2", "<0,8 a 0,5"), ("3", "<0,5 a 0,2"), ("4", "<0,2")]),
 ("plaquetas_10e3_uL", "Platelet count decreased", "abaixo", [("1", "<LLN a 75 x10^3/µL"), ("2", "<75 a 50"), ("3", "<50 a 25"), ("4", "<25")]),
 ("creatinina_mg_dL", "Creatinine increased", "acima", [("1", ">ULN a 1,5x ULN"), ("2", ">1,5 a 3,0x ULN"), ("3", ">3,0 a 6,0x ULN"), ("4", ">6,0x ULN")]),
 ("tgp_alt_U_L", "Alanine aminotransferase increased", "acima", [("1", ">ULN a 3,0x ULN (basal normal)"), ("2", ">3,0 a 5,0x ULN"), ("3", ">5,0 a 20,0x ULN"), ("4", ">20,0x ULN")]),
 ("tgo_ast_U_L", "Aspartate aminotransferase increased", "acima", [("1", ">ULN a 3,0x ULN (basal normal)"), ("2", ">3,0 a 5,0x ULN"), ("3", ">5,0 a 20,0x ULN"), ("4", ">20,0x ULN")]),
 ("fosfatase_alcalina_U_L", "Alkaline phosphatase increased", "acima", [("1", ">ULN a 2,5x ULN (basal normal)"), ("2", ">2,5 a 5,0x ULN"), ("3", ">5,0 a 20,0x ULN"), ("4", ">20,0x ULN")]),
 ("gama_gt_ggt_U_L", "GGT increased", "acima", [("1", ">ULN a 2,5x ULN (basal normal)"), ("2", ">2,5 a 5,0x ULN"), ("3", ">5,0 a 20,0x ULN"), ("4", ">20,0x ULN")]),
 ("bilirrubina_total_mg_dL", "Blood bilirubin increased", "acima", [("1", ">ULN a 1,5x ULN (basal normal)"), ("2", ">1,5 a 3,0x ULN"), ("3", ">3,0 a 10,0x ULN"), ("4", ">10,0x ULN")]),
 ("potassio_mEq_L", "Hyperkalemia", "acima", [("1", ">ULN a 5,5 mmol/L"), ("2", ">5,5 a 6,0"), ("3", ">6,0 a 7,0"), ("4", ">7,0")]),
 ("potassio_mEq_L", "Hypokalemia", "abaixo", [("1", "<LLN a 3,0 mmol/L (sem sintomas)"), ("2", "<LLN a 3,0 com sintomas"), ("3", "<3,0 a 2,5"), ("4", "<2,5")]),
]
for col, termo, di, graus in CT:
    for g, txt in graus:
        criterio(exame_id=col, tipo_criterio="grau_evento_adverso_ctcae", direcao=di, limite_relativo=f"CTCAE v5.0 '{termo}' grau {g}: {txt}",
                 unidade=unidade(col), populacao="pacientes em pesquisa clínica oncológica", ref_id="REF_CTCAE_V5",
                 condicoes_clinicas="Grau de evento adverso, não nível do produto. LLN/ULN = limites do laboratório. Alguns graus dependem de sintomas ou intervenção.",
                 status_validacao="transcrito_sem_conferencia_documento")

# ADA 2025 — limites de decisão clínica
for col, faixas_ada in [
    ("glicose_jejum_mg_dL", [("100", "125", "pré-diabetes (glicemia de jejum alterada)"), ("126", "", "compatível com diabetes, se confirmado")]),
    ("hemoglobina_glicada_hba1c_pct", [("5.7", "6.4", "pré-diabetes"), ("6.5", "", "compatível com diabetes, se confirmado")])]:
    for lo_, hi_, txt in faixas_ada:
        criterio(exame_id=col, tipo_criterio="limite_decisao_clinica", direcao="acima", operador_inferior=">=", limite_inferior=lo_,
                 operador_superior="<=" if hi_ else "", limite_superior=hi_, unidade=unidade(col), populacao="adultos não gestantes",
                 metodo="HbA1c por método certificado NGSP" if "hba1c" in col else "", ref_id="REF_ADA_SOC_2025",
                 condicoes_clinicas=f"{txt}. Exige repetição ou segundo teste; não define nível do produto sozinho.",
                 status_validacao="transcrito_sem_conferencia_documento")

pendencia("", "criterios_classificacao.csv", "Nenhum valor crítico laboratorial foi definido: o CAP não publica tabela universal e o projeto não tem política de laboratório.", "Campo e_valor_critico fica 'nao_definido' em interpretações; urgência não é deduzida do nível.", "Política de valores críticos do laboratório parceiro (limites, população, comunicação).")

# ------------------------------------------------------------ NHANES
def wq(x, w, qs):
    o = np.argsort(x); x, w = x[o], w[o]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return np.interp(qs, cw, x)


def le(rel):
    return pd.read_sas(os.path.join(NH, rel), format="xport")


NHV = {
 "hemacias_10e6_uL": ("P_CBC", "LBXRBCSI", "10^6/µL"), "hemoglobina_g_dL": ("P_CBC", "LBXHGB", "g/dL"),
 "hematocrito_pct": ("P_CBC", "LBXHCT", "%"), "vcm_fL": ("P_CBC", "LBXMCVSI", "fL"), "hcm_pg": ("P_CBC", "LBXMCHSI", "pg"),
 "chcm_g_dL": ("P_CBC", "LBXMC", "g/dL"), "rdw_pct": ("P_CBC", "LBXRDW", "%"),
 "leucocitos_totais_10e3_uL": ("P_CBC", "LBXWBCSI", "10^3/µL"), "neutrofilos_abs_10e3_uL": ("P_CBC", "LBDNENO", "10^3/µL"),
 "neutrofilos_pct": ("P_CBC", "LBXNEPCT", "%"), "linfocitos_abs_10e3_uL": ("P_CBC", "LBDLYMNO", "10^3/µL"),
 "linfocitos_pct": ("P_CBC", "LBXLYPCT", "%"), "monocitos_abs_10e3_uL": ("P_CBC", "LBDMONO", "10^3/µL"),
 "monocitos_pct": ("P_CBC", "LBXMOPCT", "%"), "eosinofilos_abs_10e3_uL": ("P_CBC", "LBDEONO", "10^3/µL"),
 "eosinofilos_pct": ("P_CBC", "LBXEOPCT", "%"), "basofilos_abs_10e3_uL": ("P_CBC", "LBDBANO", "10^3/µL"),
 "basofilos_pct": ("P_CBC", "LBXBAPCT", "%"), "plaquetas_10e3_uL": ("P_CBC", "LBXPLTSI", "10^3/µL"),
 "vpm_fL": ("P_CBC", "LBXMPSI", "fL"), "glicose_jejum_mg_dL": ("P_GLU", "LBXGLU", "mg/dL"),
 "hemoglobina_glicada_hba1c_pct": ("P_GHB", "LBXGH", "%"), "colesterol_total_mg_dL": ("P_TCHOL", "LBXTC", "mg/dL"),
 "pcr_ultrassensivel_mg_L": ("P_HSCRP", "LBXHSCRP", "mg/L"), "ferritina_ng_mL": ("P_FERTIN", "LBXFER", "ng/mL"),
 "colesterol_hdl_mg_dL": ("2012/HDL_G", "LBDHDD", "mg/dL"), "triglicerideos_mg_dL": ("2012/TRIGLY_G", "LBXTR", "mg/dL"),
 "colesterol_ldl_mg_dL": ("2012/TRIGLY_G", "LBDLDL", "mg/dL"), "tsh_uIU_mL": ("2012/THYROD_G", "LBXTSH1", "µUI/mL"),
 "t4_livre_ng_dL": ("2012/THYROD_G", "LBXT4F", "ng/dL"), "t3_livre_pg_mL": ("2012/THYROD_G", "LBXT3F", "pg/mL"),
 "t3_total_ng_dL": ("2012/THYROD_G", "LBXTT3", "ng/dL"), "t4_total_ug_dL": ("2012/THYROD_G", "LBXTT4", "µg/dL"),
 "anti_tpo_IU_mL": ("2012/THYROD_G", "LBXTPO", "UI/mL"), "anti_tireoglobulina_IU_mL": ("2012/THYROD_G", "LBXATG", "UI/mL"),
 "testosterona_total_ng_dL": ("2012/TST_G", "LBXTST", "ng/dL"),
}
demo = {"P": le("P_DEMO.xpt"), "G": le("2012/DEMO_G.xpt")}
cache, pares, nh_resumo, percentis = {}, [], {}, []
N_MIN = 100
for col, (arq, var, u) in NHV.items():
    ciclo = "G" if arq.startswith("2012") else "P"
    if arq not in cache:
        cache[arq] = le(arq + ".xpt")
    d = cache[arq].merge(demo[ciclo], on="SEQN")
    wcol = next((c for c in ("WTSAFPRP", "WTSAF2YR", "WTSA2YR") if c in cache[arq].columns), "WTMECPRP" if ciclo == "P" else "WTMEC2YR")
    base = d[(d.RIDAGEYR >= 18) & (d.RIDAGEYR <= 25)]
    base = base[base.RIDEXPRG != 1]
    nome_ciclo = "2017–mar/2020" if ciclo == "P" else "2011–2012"
    ref = "REF_NHANES_1720" if ciclo == "P" else "REF_NHANES_1112"
    for sx, sl in ((1, "masculino"), (2, "feminino")):
        g = base[base.RIAGENDR == sx]
        tot = len(g)
        g = g[g[var].notna() & (g[wcol] > 0)]
        n = len(g)
        rid = f"PAR_{col}_{sl[:3]}"
        lim = []
        if n < N_MIN:
            lim.append(f"amostra < {N_MIN}: estimativa não confiável")
        lim.append("pesos aplicados; erro-padrão pelo desenho amostral (SDMVPSU/SDMVSTRA) não calculado")
        lim.append("população dos EUA; não representa a população brasileira; percentis não são intervalo clínico")
        if col in METODO_DEP:
            lim.append("resultado depende do método de ensaio; % fora da faixa do projeto não calculado")
        if col in IR and IR_UNID.get(col) != u:
            lim.append(f"faixa do projeto em {IR_UNID.get(col)} e dado em {u}; % fora da faixa não calculado")
        row = dict(par_id=rid, exame_id=col, populacao=f"NHANES {nome_ciclo}, EUA, civis não institucionalizados", faixa_etaria="18–25 anos",
                   sexo=sl, criterios_inclusao="idade 18–25 no exame; valor laboratorial presente; peso > 0; exclui gestantes (RIDEXPRG=1)",
                   ciclo=nome_ciclo, arquivo=arq + ".xpt", variavel=var, peso=wcol, unidade=u, n_amostra=n, n_sem_valor=tot - n,
                   p2_5="", p50="", p97_5="", pct_abaixo_ref_projeto="", pct_acima_ref_projeto="",
                   metodo_calculo="percentis ponderados por interpolação da distribuição acumulada dos pesos; % ponderada fora da faixa do projeto",
                   ref_id=ref, limitacoes="; ".join(lim), status_informacao="evidencia_insuficiente" if n < N_MIN else "estimativa_disponivel")
        if n >= N_MIN:
            x, w = g[var].to_numpy(float), g[wcol].to_numpy(float)
            for k, val in enumerate(wq(x, w, np.linspace(0, 1, 101))):
                percentis.append(dict(par_id=rid, exame_id=col, sexo=sl, percentil=k, valor=fmt(val, 4), unidade=u))
            q = wq(x, w, [0.025, 0.5, 0.975])
            row.update(p2_5=fmt(q[0]), p50=fmt(q[1]), p97_5=fmt(q[2]))
            if col in IR and IR_UNID.get(col) == u and col not in METODO_DEP:
                a, b = IR[col]
                row["pct_abaixo_ref_projeto"] = fmt(100 * w[x < a].sum() / w.sum(), 1)
                row["pct_acima_ref_projeto"] = fmt(100 * w[x > b].sum() / w.sum(), 1)
            nh_resumo.setdefault(col, []).append(row)
        pares.append(row)

# ------------------------------------------------------------ níveis
NIVEIS = [(1, "Normal"), (2, "Levemente alterado"), (3, "Nível de atenção"), (4, "Alterado de maneira moderada"), (5, "Alterado grave")]
SEM_PAR = "Não há estimativa validada disponível nesta base para este exame e recorte etário."

mapn = [
 dict(mapeamento_id="MAP_01", escala_origem="produto_5_niveis", nivel_id="1", nivel_nome="Normal", codigo_atual="NORMAL", nivel_atual="1",
      status_correspondencia="equivalencia_parcial", condicao="Valor dentro do intervalo de referência.",
      conflito="NORMAL atual cobre só a zona central (10%–90% da largura); valores dentro do intervalo, nas bordas, viram LIMITROFE.",
      adaptacao="Tratar NORMAL e LIMITROFE como nível 1 do produto, com LIMITROFE como sinalizador informativo."),
 dict(mapeamento_id="MAP_02", escala_origem="produto_5_niveis", nivel_id="2", nivel_nome="Levemente alterado", codigo_atual="", nivel_atual="",
      status_correspondencia="pendente", condicao="Exige critério por exame para alteração discreta fora do intervalo.",
      conflito="LIMITROFE (nível 2 atual) está dentro do intervalo; não é alteração. ALTERADO_LEVE (nível 3 atual) é candidato, mas usa desvio de 15% sem validação clínica.",
      adaptacao="Definir critério por exame; até lá não mapear automaticamente."),
 dict(mapeamento_id="MAP_03", escala_origem="produto_5_niveis", nivel_id="3", nivel_nome="Nível de atenção", codigo_atual="", nivel_atual="",
      status_correspondencia="pendente", condicao="Sem definição operacional no produto nem no código.",
      conflito="Nenhum código atual equivale. 'Atenção' não tem limite numérico definido.",
      adaptacao="Produto precisa definir o critério (ex.: limite de decisão clínica de diretriz) por exame."),
 dict(mapeamento_id="MAP_04", escala_origem="produto_5_niveis", nivel_id="4", nivel_nome="Alterado de maneira moderada", codigo_atual="ALTERADO_MODERADO", nivel_atual="4",
      status_correspondencia="candidato_condicional", condicao="Somente se o critério por exame for validado clinicamente.",
      conflito="ALTERADO_MODERADO usa desvio 15%–50% da largura do intervalo, regra do projeto. Não equivale a CTCAE grau 2.",
      adaptacao="Substituir a regra genérica por critério por exame; manter código só como destino técnico."),
 dict(mapeamento_id="MAP_05", escala_origem="produto_5_niveis", nivel_id="5", nivel_nome="Alterado grave", codigo_atual="ALTERACAO_ACENTUADA", nivel_atual="5",
      status_correspondencia="candidato_condicional", condicao="Somente com critério por exame validado.",
      conflito="ALTERACAO_ACENTUADA usa desvio > 50%. Não equivale a CTCAE graus 3–4 nem a valor crítico; CTCAE grau 5 significa morte.",
      adaptacao="Separar 'grave' de 'valor crítico'; urgência vem do campo de valor crítico, não do nível."),
 dict(mapeamento_id="MAP_06", escala_origem="codigo_atual", nivel_id="", nivel_nome="", codigo_atual="LIMITROFE", nivel_atual="2",
      status_correspondencia="sem_equivalente", condicao="Dentro do intervalo, nos 10% das bordas.",
      conflito="Não existe nível 'limítrofe' entre os cinco solicitados.", adaptacao="Exibir como nível 1 com sinalizador."),
 dict(mapeamento_id="MAP_07", escala_origem="codigo_atual", nivel_id="", nivel_nome="", codigo_atual="ALTERADO_LEVE", nivel_atual="3",
      status_correspondencia="pendente", condicao="Fora do intervalo com desvio ≤ 15%.",
      conflito="Posição numérica 3 coincide com 'Nível de atenção', mas o conceito é de alteração leve.", adaptacao="Não mapear pela posição numérica."),
 dict(mapeamento_id="MAP_08", escala_origem="codigo_atual", nivel_id="", nivel_nome="", codigo_atual="INDETERMINADO", nivel_atual="0",
      status_correspondencia="estado_tecnico", condicao="Sem faixa numérica ou resultado qualitativo.",
      conflito="", adaptacao="Nunca converter em NORMAL; manter como informação insuficiente."),
 dict(mapeamento_id="MAP_09", escala_origem="visual_4_niveis", nivel_id="", nivel_nome="", codigo_atual="NORMAL (visual 1)", nivel_atual="1",
      status_correspondencia="informativo", condicao="Escala visual ao paciente.", conflito="", adaptacao="Documentado no README; não usado na nova base."),
 dict(mapeamento_id="MAP_10", escala_origem="visual_4_niveis", nivel_id="", nivel_nome="", codigo_atual="LIMITROFE (visual 2)", nivel_atual="2",
      status_correspondencia="informativo", condicao="Inclui LIMITROFE e ALTERADO_LEVE do classificador.", conflito="Junta 'dentro do intervalo' e 'fora do intervalo' na mesma cor.", adaptacao="Documentado no README."),
 dict(mapeamento_id="MAP_11", escala_origem="visual_4_niveis", nivel_id="", nivel_nome="", codigo_atual="ALTERADO_MODERADO (visual 3)", nivel_atual="3",
      status_correspondencia="informativo", condicao="", conflito="", adaptacao="Documentado no README."),
 dict(mapeamento_id="MAP_12", escala_origem="visual_4_niveis", nivel_id="", nivel_nome="", codigo_atual="ALTERACAO_ACENTUADA (visual 4)", nivel_atual="4",
      status_correspondencia="informativo", condicao="", conflito="", adaptacao="Documentado no README."),
]

# ------------------------------------------------------------ interpretações
GRAU = {2: "levemente", 3: "em grau que pede atenção,", 4: "moderadamente", 5: "acentuadamente"}
MIT = {
 1: "Não há ação específica indicada por este resultado isolado. Seguir o acompanhamento de rotina definido com o profissional de saúde.",
 2: "Repetir ou acompanhar conforme orientação médica, considerando os demais exames. Verificar se houve fatores pré-analíticos na coleta.",
 3: "Levar o resultado à próxima consulta para avaliação conforme os critérios descritos e os demais exames.",
 4: "Este achado requer avaliação clínica. Agendar consulta com o resultado e os exames anteriores.",
 5: "Este achado requer avaliação médica com prioridade. Se houver sintomas novos ou intensos, procurar atendimento de urgência.",
}
LIM_MIT = " Não iniciar nem suspender medicamentos ou suplementos sem orientação profissional."
interp = []


def par_texto(col, di):
    rs = nh_resumo.get(col)
    if not rs:
        return SEM_PAR, ""
    # A comparação é exibida em gráfico; o texto só aponta para os dados.
    return (f"Comparação exibida em gráfico de distribuição por nível (NHANES {rs[0]['ciclo']}, EUA, 18–25 anos). "
            "Dados em pares_etarios.csv e pares_etarios_percentis.csv. Não representa a população brasileira.",
            ";".join(r["par_id"] for r in rs))


iid = [0]


def add(col, niv, di, status, desc, imp, cau, mit, refs, status_crit):
    iid[0] += 1
    nome = dict(NIVEIS).get(niv, "") if niv else ""
    ptxt, pids = par_texto(col, di) if status != "nao_aplicavel" else ("", "")
    interp.append(dict(interp_id=f"INT_{iid[0]:05d}", exame_id=col, nivel_id=str(niv) if niv else "", nivel_nome=nome, direcao=di,
                       populacao_aplicavel="18–25 anos (recorte inicial); sexo conforme critério do exame",
                       status_informacao=status, descricao_resultado=desc, informacoes_pares_etarios=ptxt, par_ids=pids,
                       impactos_individuo=imp, possiveis_causas=cau, mitigacao=mit, ref_id_texto=refs,
                       status_criterio=status_crit, resultado_critico="nao_definido", urgencia="nao_deduzida_do_nivel",
                       revisao_clinica="nao_realizada"))


for col, v in kb.items():
    d, resumo, bc, bi, ac, ai, pre = C[col]
    nome = v["nome_exame"]
    crit_l1 = "fonte_do_projeto_sem_validacao" if col in IR else "pendente_validacao"
    pre_txt = f" Interferências possíveis: {pre}" if pre else ""
    if d == "qualitativo":
        add(col, 1, "nao_reagente", "conteudo_disponivel" if col != "anti_hbs_hepatite_b" else "pendente_validacao",
            f"O resultado de {nome} foi não reagente/negativo." + (" Um resultado negativo não afasta exposição muito recente (janela)." if col in ("hiv_1_2", "hbsag_hepatite_b", "anti_hcv_hepatite_c", "vdrl_sifilis") else ""),
            "", "", MIT[1], "REF_RASCUNHO_AUTORAL", "pendente_validacao")
        for n in range(2, 6):
            add(col, n, "nao_aplicavel", "nao_aplicavel", "Exame qualitativo; não há graduação reconhecida em cinco níveis.", "", "", "", "", "nao_aplicavel")
        if ac or bc:
            add(col, None, "reagente" if ac else "abaixo_limiar", "pendente_validacao",
                f"O resultado de {nome} foi {'reagente/positivo' if ac else 'abaixo do limiar informado pelo laboratório'}. Este achado requer confirmação e avaliação conforme os critérios descritos.",
                ai or bi, (ac or bc) + pre_txt, "Procurar o serviço de saúde para exames de confirmação e orientação. Não há conduta automática a partir deste resultado isolado." + LIM_MIT,
                "REF_RASCUNHO_AUTORAL", "pendente_validacao")
        continue
    add(col, 1, "dentro_referencia", "conteudo_disponivel",
        f"O resultado de {nome} está dentro do intervalo de referência informado.", "Isoladamente, não indica alteração relacionada a este exame.",
        "Não se aplica: valores dentro do intervalo não são atribuídos a causas específicas." , MIT[1], "REF_RASCUNHO_AUTORAL", crit_l1)
    for di, causas, imp in (("abaixo", bc, bi), ("acima", ac, ai)):
        rel = (d == "ambas") or (d == "alto" and di == "acima") or (d == "baixo" and di == "abaixo") or d == "contexto"
        for n in range(2, 6):
            if not rel:
                add(col, n, di, "nao_aplicavel", f"Valores {'reduzidos' if di == 'abaixo' else 'elevados'} de {nome} não têm significado clínico estabelecido para graduação.",
                    "", "", "", "", "nao_aplicavel")
                continue
            if not causas:
                add(col, n, di, "evidencia_insuficiente", "", "", "", "", "", "pendente_validacao")
                continue
            if d == "contexto":
                desc = f"O resultado de {nome} está {'abaixo' if di == 'abaixo' else 'acima'} do intervalo informado. A interpretação depende de sexo, idade, fase do ciclo, gestação ou uso de hormônios; não há graduação em cinco níveis sem esse contexto."
                add(col, n, di, "pendente_validacao", desc, imp, causas + pre_txt, MIT[3] + LIM_MIT, "REF_RASCUNHO_AUTORAL", "pendente_validacao")
                continue
            desc = (f"O resultado de {nome} está {GRAU[n]} {'abaixo' if di == 'abaixo' else 'acima'} do intervalo de referência. "
                    "A interpretação depende dos demais exames e do contexto clínico; um marcador isolado não define diagnóstico.")
            add(col, n, di, "pendente_validacao", desc, imp, causas + pre_txt, MIT[n] + (LIM_MIT if n >= 2 else ""), "REF_RASCUNHO_AUTORAL", "pendente_validacao")

# ------------------------------------------------------------ escrita
escrever("catalogo_exames.csv", ["exame_id", "coluna", "codigo_loinc", "codigo_loinc_mapa", "nome_exame", "categoria", "tipo_resultado", "unidade", "unidade_origem", "sexo_dependente", "direcoes_relevantes", "resumo_exame", "ref_id_resumo", "status_catalogo", "observacoes"], catalogo)
escrever("interpretacoes_exames.csv", ["interp_id", "exame_id", "nivel_id", "nivel_nome", "direcao", "populacao_aplicavel", "status_informacao", "descricao_resultado", "informacoes_pares_etarios", "par_ids", "impactos_individuo", "possiveis_causas", "mitigacao", "ref_id_texto", "status_criterio", "resultado_critico", "urgencia", "revisao_clinica"], interp)
escrever("criterios_classificacao.csv", ["criterio_id", "exame_id", "tipo_criterio", "nivel_id_produto", "codigo_destino_atual", "direcao", "operador_inferior", "limite_inferior", "operador_superior", "limite_superior", "limite_relativo", "unidade", "populacao", "sexo", "metodo", "ref_id", "condicoes_clinicas", "e_valor_critico", "urgencia", "status_validacao"], crit)
escrever("pares_etarios.csv", ["par_id", "exame_id", "populacao", "faixa_etaria", "sexo", "criterios_inclusao", "ciclo", "arquivo", "variavel", "peso", "unidade", "n_amostra", "n_sem_valor", "p2_5", "p50", "p97_5", "pct_abaixo_ref_projeto", "pct_acima_ref_projeto", "metodo_calculo", "ref_id", "limitacoes", "status_informacao"], pares)
escrever("pares_etarios_percentis.csv", ["par_id", "exame_id", "sexo", "percentil", "valor", "unidade"], percentis)
escrever("mapeamento_niveis.csv", ["mapeamento_id", "escala_origem", "nivel_id", "nivel_nome", "codigo_atual", "nivel_atual", "status_correspondencia", "condicao", "conflito", "adaptacao"], mapn)
escrever("referencias.csv", ["ref_id", "instituicao_autoria", "titulo", "versao", "ano", "url_doi", "secao_pagina", "data_consulta", "tipo_fonte", "status_acesso", "observacao"], REFS)
escrever("pendencias.csv", ["pendencia_id", "exame_id", "registro_afetado", "problema", "impacto_integracao", "informacao_necessaria"], pend)
print("ok", len(catalogo), len(interp), len(crit), len(pares), len(pend))
