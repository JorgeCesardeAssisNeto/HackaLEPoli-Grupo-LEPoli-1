import os
import csv
import re
import unicodedata
from typing import Dict, Any, List, Optional

COLUNAS_PLANILHA = [
    "id_laudo", "cpf_paciente", "cns_paciente", "nome_paciente", "data_nascimento", "sexo_biologico",
    "laboratorio_origem", "data_coleta", "data_emissao", "hemacias_10e6_uL", "hemoglobina_g_dL",
    "hematocrito_pct", "vcm_fL", "hcm_pg", "chcm_g_dL", "rdw_pct", "leucocitos_totais_10e3_uL",
    "neutrofilos_abs_10e3_uL", "neutrofilos_pct", "bastonetes_pct", "segmentados_pct",
    "linfocitos_abs_10e3_uL", "linfocitos_pct", "monocitos_abs_10e3_uL", "monocitos_pct",
    "eosinofilos_abs_10e3_uL", "eosinofilos_pct", "basofilos_abs_10e3_uL", "basofilos_pct",
    "plaquetas_10e3_uL", "vpm_fL", "glicose_jejum_mg_dL", "hemoglobina_glicada_hba1c_pct",
    "insulina_basal_uIU_mL", "indice_homa_ir", "colesterol_total_mg_dL", "colesterol_hdl_mg_dL",
    "colesterol_ldl_mg_dL", "colesterol_vldl_mg_dL", "colesterol_nao_hdl_mg_dL", "triglicerideos_mg_dL",
    "apolipoproteina_a1_mg_dL", "apolipoproteina_b_mg_dL", "lipoproteina_a_mg_dL", "creatinina_mg_dL",
    "tfg_estimada_mL_min", "ureia_mg_dL", "acido_urico_mg_dL", "sodio_mEq_L", "potassio_mEq_L",
    "calcio_total_mg_dL", "calcio_ionico_mmol_L", "magnesio_mg_dL", "fosforo_mg_dL", "cloro_mEq_L",
    "tgo_ast_U_L", "tgp_alt_U_L", "gama_gt_ggt_U_L", "fosfatase_alcalina_U_L", "bilirrubina_total_mg_dL",
    "bilirrubina_direta_mg_dL", "bilirrubina_indireta_mg_dL", "proteinas_totais_g_dL", "albumina_g_dL",
    "globulinas_g_dL", "ldh_desidrogenase_lactica_U_L", "tsh_uIU_mL", "t4_livre_ng_dL", "t4_total_ug_dL",
    "t3_livre_pg_mL", "t3_total_ng_dL", "anti_tpo_IU_mL", "anti_tireoglobulina_IU_mL", "cortisol_basal_ug_dL",
    "testosterona_total_ng_dL", "testosterona_livre_pg_mL", "estradiol_pg_mL", "progesterona_ng_mL",
    "fsh_mIU_mL", "lh_mIU_mL", "prolactina_ng_mL", "shbg_nmol_L", "dhea_s_ug_dL", "pth_paratormonio_pg_mL",
    "igf1_ng_mL", "ferritina_ng_mL", "ferro_serico_ug_dL", "transferrina_mg_dL", "tibc_ug_dL",
    "saturacao_transferrina_pct", "vitamina_d_25oh_ng_mL", "vitamina_b12_pg_mL", "acido_folico_folato_ng_mL",
    "homocisteina_umol_L", "zinco_ug_dL", "pcr_ultrassensivel_mg_L", "vhs_mm_h", "fibrinogenio_mg_dL",
    "d_dimero_ng_mL", "tap_tempo_protrombina_seg", "inr", "ttpa_seg", "fator_reumatoide_IU_mL",
    "fan_fator_antinuclear", "alfa_fetoproteina_afp_ng_mL", "cea_ng_mL", "psa_total_ng_mL", "psa_livre_ng_mL",
    "ca_125_U_mL", "ca_19_9_U_mL", "ca_15_3_U_mL", "beta_hcg_quantitativo_mIU_mL",
    "ck_total_creatinofosfoquinase_U_L", "ck_mb_ng_mL", "troponina_i_alta_sensibilidade_ng_L", "bnp_pg_mL",
    "nt_probnp_pg_mL", "hiv_1_2", "hbsag_hepatite_b", "anti_hbs_hepatite_b", "anti_hcv_hepatite_c", "vdrl_sifilis"
]

def normalizar_texto(texto: str) -> str:
    """Remove acentos, pontuação e converte para minúsculas."""
    if not texto:
        return ""
    texto_sem_acento = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-zA-Z0-9]', ' ', texto_sem_acento).lower().strip()

# Mapa de sinônimos com prioridades (termos mais específicos primeiro)
REGRAS_MAPEAMENTO = [
    # Hemograma
    (r"hemoglobina glicada|hba1c|glicohemoglobina", "hemoglobina_glicada_hba1c_pct"),
    (r"hemoglobina", "hemoglobina_g_dL"),
    (r"hemacia|eritrocito|globulos vermelhos", "hemacias_10e6_uL"),
    (r"hematocrito", "hematocrito_pct"),
    (r"vcm", "vcm_fL"),
    (r"hcm", "hcm_pg"),
    (r"chcm", "chcm_g_dL"),
    (r"rdw", "rdw_pct"),
    (r"leucocito|globulos brancos|leucograma", "leucocitos_totais_10e3_uL"),
    (r"neutrofilos segmentados|segmentados", "segmentados_pct"),
    (r"bastonetes|bastoes", "bastonetes_pct"),
    (r"neutrofilos", "neutrofilos_abs_10e3_uL"),
    (r"linfocitos", "linfocitos_abs_10e3_uL"),
    (r"monocitos", "monocitos_abs_10e3_uL"),
    (r"eosinofilos", "eosinofilos_abs_10e3_uL"),
    (r"basofilos", "basofilos_abs_10e3_uL"),
    (r"plaqueta|trombocito", "plaquetas_10e3_uL"),
    (r"vpm", "vpm_fL"),

    # Glicose e Lipídios
    (r"glicose em jejum|glicose de jejum|glicemia de jejum|glicose|glicemia", "glicose_jejum_mg_dL"),
    (r"insulina basal|insulina", "insulina_basal_uIU_mL"),
    (r"homa ir|indice homa", "indice_homa_ir"),
    (r"colesterol total", "colesterol_total_mg_dL"),
    (r"colesterol hdl|hdl", "colesterol_hdl_mg_dL"),
    (r"colesterol ldl|ldl", "colesterol_ldl_mg_dL"),
    (r"colesterol vldl|vldl", "colesterol_vldl_mg_dL"),
    (r"nao hdl|nao-hdl", "colesterol_nao_hdl_mg_dL"),
    (r"triglicerideo|triglicerides|triglicerideos", "triglicerideos_mg_dL"),
    (r"apolipoproteina a", "apolipoproteina_a1_mg_dL"),
    (r"apolipoproteina b", "apolipoproteina_b_mg_dL"),
    (r"lipoproteina a", "lipoproteina_a_mg_dL"),

    # Função Renal e Eletrólitos
    (r"creatinina", "creatinina_mg_dL"),
    (r"taxa de filtracao glomerular|tfg|ritmo de filtracao", "tfg_estimada_mL_min"),
    (r"ureia", "ureia_mg_dL"),
    (r"acido urico", "acido_urico_mg_dL"),
    (r"sodio", "sodio_mEq_L"),
    (r"potassio", "potassio_mEq_L"),
    (r"calcio ionico|calcio ionizavel", "calcio_ionico_mmol_L"),
    (r"calcio total|calcio", "calcio_total_mg_dL"),
    (r"magnesio", "magnesio_mg_dL"),
    (r"fosforo", "fosforo_mg_dL"),
    (r"cloro|cloretos", "cloro_mEq_L"),

    # Função Hepática
    (r"tgo|ast|transaminase oxalacetica", "tgo_ast_U_L"),
    (r"tgp|alt|transaminase piruvica", "tgp_alt_U_L"),
    (r"gama gt|gama glutamil|ggt", "gama_gt_ggt_U_L"),
    (r"fosfatase alcalina", "fosfatase_alcalina_U_L"),
    (r"bilirrubina direta", "bilirrubina_direta_mg_dL"),
    (r"bilirrubina indireta", "bilirrubina_indireta_mg_dL"),
    (r"bilirrubina total|bilirrubinas", "bilirrubina_total_mg_dL"),
    (r"albumina", "albumina_g_dL"),
    (r"globulina", "globulinas_g_dL"),
    (r"proteinas totais", "proteinas_totais_g_dL"),
    (r"desidrogenase lactica|ldh|dhl", "ldh_desidrogenase_lactica_U_L"),

    # Tireoide e Hormônios
    (r"tsh ultrassensivel|tsh", "tsh_uIU_mL"),
    (r"t4 livre|tiroxina livre", "t4_livre_ng_dL"),
    (r"t4 total|tiroxina total", "t4_total_ug_dL"),
    (r"t3 livre|triiodotironina livre", "t3_livre_pg_mL"),
    (r"t3 total|triiodotironina total", "t3_total_ng_dL"),
    (r"anti tpo|anticorpo anti peroxidase", "anti_tpo_IU_mL"),
    (r"anti tireoglobulina|anti tg", "anti_tireoglobulina_IU_mL"),
    (r"cortisol basal|cortisol", "cortisol_basal_ug_dL"),
    (r"testosterona livre", "testosterona_livre_pg_mL"),
    (r"testosterona total|testosterona", "testosterona_total_ng_dL"),
    (r"estradiol|e2", "estradiol_pg_mL"),
    (r"progesterona", "progesterona_ng_mL"),
    (r"fsh|hormonio foliculo estimulante", "fsh_mIU_mL"),
    (r"lh|hormonio luteinizante", "lh_mIU_mL"),
    (r"prolactina", "prolactina_ng_mL"),
    (r"shbg", "shbg_nmol_L"),
    (r"dhea s|dhea sulfato|dhea", "dhea_s_ug_dL"),
    (r"pth|paratormonio", "pth_paratormonio_pg_mL"),
    (r"igf1|somatomedina c", "igf1_ng_mL"),

    # Ferro, Vitaminas e Minerais
    (r"ferritina serica|ferritina", "ferritina_ng_mL"),
    (r"ferro serico|ferro", "ferro_serico_ug_dL"),
    (r"transferrina", "transferrina_mg_dL"),
    (r"tibc|capacidade total de fixacao", "tibc_ug_dL"),
    (r"saturacao de transferrina|indice de saturacao", "saturacao_transferrina_pct"),
    (r"vitamina d|25 hidroxi|25 oh", "vitamina_d_25oh_ng_mL"),
    (r"vitamina b12|cobalamina", "vitamina_b12_pg_mL"),
    (r"acido folico|folato", "acido_folico_folato_ng_mL"),
    (r"homocisteina", "homocisteina_umol_L"),
    (r"zinco", "zinco_ug_dL"),

    # Inflamação e Coagulação
    (r"pcr ultrassensivel|pcr|proteina c reativa", "pcr_ultrassensivel_mg_L"),
    (r"vhs|velocidade de hemossedimentacao", "vhs_mm_h"),
    (r"fibrinogenio", "fibrinogenio_mg_dL"),
    (r"d dimero|dimero d", "d_dimero_ng_mL"),
    (r"tap|tempo de protrombina", "tap_tempo_protrombina_seg"),
    (r"inr", "inr"),
    (r"ttpa|tempo de tromboplastina", "ttpa_seg"),
    (r"fator reumatoide|prova do latex", "fator_reumatoide_IU_mL"),
    (r"fan|fator antinuclear", "fan_fator_antinuclear"),

    # Marcadores Tumorais e Cardíacos
    (r"psa livre", "psa_livre_ng_mL"),
    (r"psa total|psa", "psa_total_ng_mL"),
    (r"alfa fetoproteina|afp", "alfa_fetoproteina_afp_ng_mL"),
    (r"antigeno carcinoembrionario|cea", "cea_ng_mL"),
    (r"ca 125", "ca_125_U_mL"),
    (r"ca 19 9|ca 19", "ca_19_9_U_mL"),
    (r"ca 15 3|ca 15", "ca_15_3_U_mL"),
    (r"beta hcg quantitativo|beta hcg", "beta_hcg_quantitativo_mIU_mL"),
    (r"ck total|creatinofosfoquinase|cpk", "ck_total_creatinofosfoquinase_U_L"),
    (r"ck mb", "ck_mb_ng_mL"),
    (r"troponina i|troponina", "troponina_i_alta_sensibilidade_ng_L"),
    (r"bnp", "bnp_pg_mL"),
    (r"nt probnp|probnp", "nt_probnp_pg_mL"),

    # Sorologias
    (r"hiv", "hiv_1_2"),
    (r"hbsag|antigeno australia", "hbsag_hepatite_b"),
    (r"anti hbs", "anti_hbs_hepatite_b"),
    (r"anti hcv", "anti_hcv_hepatite_c"),
    (r"vdrl|sifilis", "vdrl_sifilis"),
]

def identificar_coluna_por_nome(nome_analito: str) -> Optional[str]:
    """Identifica o nome da coluna da planilha padrão com base no nome do analito."""
    norm = normalizar_texto(nome_analito)
    for padrao, coluna in REGRAS_MAPEAMENTO:
        if re.search(r'\b' + padrao + r'\b', norm):
            return coluna
    return None

def criar_linha_planilha(dados_laudo: Dict[str, Any], mapa_colunas_direto: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Gera um dicionário completo com todas as 120+ colunas da planilha,
    preenchendo exatamente as que foram identificadas.
    """
    linha = {col: "" for col in COLUNAS_PLANILHA}
    cab = dados_laudo.get("cabecalho", {})

    linha["id_laudo"] = cab.get("protocolo") or ""
    linha["cpf_paciente"] = cab.get("cpf") or ""
    linha["nome_paciente"] = cab.get("paciente") or ""
    linha["data_nascimento"] = cab.get("data_nascimento") or ""
    linha["laboratorio_origem"] = cab.get("laboratorio") or ""
    linha["data_coleta"] = cab.get("data_coleta") or ""
    linha["data_emissao"] = cab.get("data_liberacao") or ""

    # Varre cada exame identificado e encaixa na coluna correta
    exames = dados_laudo.get("exames", [])
    for ex in exames:
        nome = ex.get("analito", "")
        coluna = identificar_coluna_por_nome(nome)
        
        if coluna and coluna in linha:
            val = ex.get("valor_numerico")
            if val is None or val == "":
                val = ex.get("resultado_bruto")
            linha[coluna] = val

    return linha

def salvar_em_planilha_csv(caminho_csv: str, linha_dados: Dict[str, Any]):
    """Grava ou anexa a linha na planilha CSV oficial."""
    existe = os.path.exists(caminho_csv)
    
    with open(caminho_csv, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not existe or os.path.getsize(caminho_csv) == 0:
            writer.writerow(COLUNAS_PLANILHA)
            
        valores = [linha_dados.get(col, "") for col in COLUNAS_PLANILHA]
        writer.writerow(valores)
