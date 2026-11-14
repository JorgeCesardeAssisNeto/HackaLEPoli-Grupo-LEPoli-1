"""Endpoints unificados de Extração de Exames, Base de Conhecimento (RAG) e Interpretação Clínica Causal."""

import base64
import hashlib
import io
import json
import logging
import re
import unicodedata
import zlib
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.wearable_metrics import WearableDailyMetric
from schemas.interservice import FHIRLabEvolutionResponse, FHIRObservationPoint
from services.causal_engine import CausalInferenceEngine, causal_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Clinical Knowledge & Exam Interpretation (RAG)"])


def _normalize_slug(text: str) -> str:
    norm = unicodedata.normalize("NFKD", (text or "").strip().lower())
    ascii_text = "".join(c for c in norm if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")


def _parse_br_float(raw_str: str) -> Optional[float]:
    """
    Converte números em formato brasileiro ('1.234,56', '14,5', '4.500') ou internacional ('18.5') para float.
    Remove apenas pontos que atuam como separadores de milhar (?<=\\d)\\.(?=\\d{3}(?:\\D|$)),
    preservando pontos decimais ('18.5' -> 18.5) e convertendo vírgulas decimais ('18,5' -> 18.5).
    """
    if raw_str is None:
        return None
    s = re.sub(r"^[<>≤≥=\s]+", "", str(raw_str).strip())
    if not s:
        return None
    # Remove apenas pontos de milhar seguidos por exatamente 3 dígitos
    s = re.sub(r"(?<=\d)\.(?=\d{3}(?:\D|$))", "", s)
    # Converte vírgula decimal para ponto
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _make_entry(
    analito: str,
    name: str,
    loinc: str,
    unit: str,
    ref_min: float,
    ref_max: float,
    description: str,
    clinical_significance: str,
    causal_relationship: str,
    causal_target_id: str = "TARGET_2_METABOLIC_RISK",
    aliases: Optional[List[str]] = None,
    faixas_5_niveis: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    ref_range = f"{ref_min} a {ref_max} {unit}" if ref_min > 0 else f"< {ref_max} {unit}"
    return {
        "analito": analito,
        "name": name,
        "nome_exame": name,
        "codigo_loinc": loinc,
        "unit": unit,
        "unidade": unit,
        "reference_min": float(ref_min),
        "reference_max": float(ref_max),
        "reference_range": ref_range,
        "faixa_referencia": {"min": float(ref_min), "max": float(ref_max), "unidade": unit},
        "description": description,
        "resumo_exame": description,
        "clinical_significance": clinical_significance,
        "causal_relationship": causal_relationship,
        "causal_target_id": causal_target_id,
        "faixas_5_niveis": faixas_5_niveis
        or {
            "muito_baixo": f"< {round(ref_min * 0.7, 2)} {unit}: Redução acentuada; requer correlação clínica.",
            "baixo": f"{round(ref_min * 0.7, 2)} a {ref_min} {unit}: Abaixo da referência populacional.",
            "normal": f"{ref_min} a {ref_max} {unit}: Dentro do intervalo de referência esperado.",
            "alto": f"{ref_max} a {round(ref_max * 1.3, 2)} {unit}: Acima da referência populacional.",
            "muito_alto": f"> {round(ref_max * 1.3, 2)} {unit}: Elevação acentuada; requer avaliação médica.",
        },
        "aliases": aliases or [analito, loinc],
    }


# Catálogo clínico amplo (60+ exames laboratoriais brasileiros + relação causal com wearables)
CLINICAL_KNOWLEDGE_CATALOG: Dict[str, Dict[str, Any]] = {
    "ferritina": _make_entry(
        "ferritina",
        "Ferritina Sérica",
        "2276-4",
        "ng/mL",
        30.0,
        300.0,
        "Proteína intracelular de armazenamento de ferro; principal marcador precoce de depleção dos estoques corporais de ferro (ferropenia) e reagente de fase aguda.",
        "Ferritina < 30 ng/mL confirma ferropenia subclínica ou anemia ferropriva, causando fadiga, intolerância ao esforço e taquicardia compensatória diurna. Valores > 300 ng/mL sugerem sobrecarga férrica ou inflamação sistêmica.",
        "Ancora o ALVO 4 (Triagem Hematológica / ICD): quando o wearable detecta FC média diurna > 92 bpm desproporcional ao volume de passos (ICD elevado) sem excesso de cafeína, a Ferritina < 30 ng/mL confirma esforço cardíaco compensatório por déficit de O2.",
        "TARGET_4_ANEMIA_LOAD",
        ["ferritina", "ferritin", "ferritina_serica", "dosagem_de_ferritina", "2276-4"],
    ),
    "hemoglobina": _make_entry(
        "hemoglobina",
        "Hemoglobina",
        "718-7",
        "g/dL",
        12.0,
        16.5,
        "Metaloproteína rica em ferro presente nos eritrócitos, responsável pelo transporte de oxigênio dos pulmões para os tecidos periféricos e miocárdio.",
        "Hemoglobina < 12.0 g/dL reduz a oferta tecidual de O2 e exige aumento compensatório da frequência cardíaca em repouso e esforço.",
        "Relacionada diretamente ao ALVO 4 (ICD Diurno) e SpO2: queda de hemoglobina eleva a FC média diurna para manter a oxigenação tecidual mesmo com baixa contagem de passos.",
        "TARGET_4_ANEMIA_LOAD",
        ["hemoglobina", "hemoglobin", "hb", "718-7"],
    ),
    "hematocrito": _make_entry(
        "hematocrito",
        "Hematócrito",
        "4544-3",
        "%",
        36.0,
        50.0,
        "Proporção percentual do volume sanguíneo ocupada pelos glóbulos vermelhos (hemácias).",
        "Hematócrito < 36% acompanha quadros anêmicos; valores > 50% indicam hemoconcentração/desidratação ou policitemia.",
        "Correlaciona-se ao ALVO 4 (Carga Cardiovascular Diurna / ICD) e ao estado de hidratação pós-exercício.",
        "TARGET_4_ANEMIA_LOAD",
        ["hematocrito", "ht", "hct", "4544-3"],
    ),
    "hemacias": _make_entry(
        "hemacias",
        "Hemácias (Eritrócitos)",
        "789-8",
        "milhões/mm3",
        4.0,
        5.5,
        "Contagem total de glóbulos vermelhos circulantes responsáveis pelo transporte de oxigênio.",
        "Redução na contagem de eritrócitos compromete a capacidade aeróbica e eleva a frequência cardíaca submáxima.",
        "Integra a investigação hematológica do ALVO 4 (Taquicardia Diurna com baixo volume de passos).",
        "TARGET_4_ANEMIA_LOAD",
        ["hemacias", "eritrocitos", "globulos_vermelhos", "rbc", "789-8"],
    ),
    "vcm": _make_entry(
        "vcm",
        "Volume Corpuscular Médio (VCM)",
        "787-2",
        "fL",
        80.0,
        100.0,
        "Índice hematimétrico que mede o tamanho médio das hemácias.",
        "VCM < 80 fL caracteriza microcitose (típica da deficiência de ferro); VCM > 100 fL indica macrocitose (deficiência de B12/folato).",
        "Diferencia causas microcíticas (ferropenia) e macrocíticas nos alertas do ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["vcm", "volume_corpuscular_medio", "787-2"],
    ),
    "hcm": _make_entry(
        "hcm",
        "Hemoglobina Corpuscular Média (HCM)",
        "785-6",
        "pg",
        27.0,
        32.0,
        "Peso médio de hemoglobina conteúdo em cada glóbulo vermelho.",
        "HCM < 27 pg indica hipocromia (redução de hemoglobina celular por carência de ferro).",
        "Complementa a Ferritina e a Hemoglobina na avaliação do ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["hcm", "hemoglobina_corpuscular_media", "785-6"],
    ),
    "chcm": _make_entry(
        "chcm",
        "CHCM",
        "786-4",
        "g/dL",
        31.5,
        36.0,
        "Concentração de hemoglobina corpuscular média nas hemácias.",
        "Valores reduzidos refletem hipocromia eritrocitária.",
        "Auxilia na caracterização de anemias ferroprivas detectadas via ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["chcm", "786-4"],
    ),
    "rdw": _make_entry(
        "rdw",
        "RDW (Anisocitose)",
        "788-0",
        "%",
        11.5,
        14.5,
        "Índice de variação do tamanho das hemácias (amplitude de distribuição eritrocitária).",
        "RDW > 14.5% é um marcador precoce de deficiência nutricional (ferro, B12 ou folato) e estresse oxidativo.",
        "Eleva-se precocemente em conjunto com a queda da Ferritina no ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["rdw", "rdw_cv", "788-0"],
    ),
    "leucocitos": _make_entry(
        "leucocitos",
        "Leucócitos Totais",
        "6690-2",
        "/mm3",
        4000.0,
        10000.0,
        "Contagem total de células de defesa imunológica circulantes no sangue periférico.",
        "Leucocitose (> 10.000/mm3) sugere infecção aguda ou inflamação; leucopenia (< 4.000/mm3) sugere infecção viral ou imunossupressão.",
        "Correlaciona-se ao ALVO 3 (Queda persistente de HRV RMSSD < 38 ms por 4 dias consecutivos).",
        "TARGET_3_INFLAMMATION_HRV",
        ["leucocitos", "globulos_brancos", "leucograma", "wbc", "6690-2"],
    ),
    "neutrofilos": _make_entry(
        "neutrofilos",
        "Neutrófilos",
        "751-8",
        "%",
        40.0,
        70.0,
        "Subpopulação leucocitária predominante na resposta imune inata antibacteriana e inflamatória aguda.",
        "Neutrofilia associa-se a infecções bacterianas e estresse inflamatório agudo.",
        "Relaciona-se à supressão vagal (queda de HRV RMSSD) monitorada no ALVO 3.",
        "TARGET_3_INFLAMMATION_HRV",
        ["neutrofilos", "segmentados", "neutrofilos_segmentados", "751-8", "768-2"],
    ),
    "linfocitos": _make_entry(
        "linfocitos",
        "Linfócitos",
        "731-0",
        "%",
        20.0,
        45.0,
        "Células centrais da imunidade adaptativa humoral e celular (células T, B e NK).",
        "Linfocitose ocorre em quadros virais; linfopenia acompanha estresse sistêmico ou hipercortisolismo.",
        "Integra a avaliação imunológica do ALVO 3 (Inflamação Sistêmica / HRV).",
        "TARGET_3_INFLAMMATION_HRV",
        ["linfocitos", "731-0"],
    ),
    "monocitos": _make_entry(
        "monocitos",
        "Monócitos",
        "742-7",
        "%",
        2.0,
        10.0,
        "Células fagocíticas precursoras de macrófagos teciduais.",
        "Monocitose associa-se a processos inflamatórios subagudos ou fase de recuperação infecciosa.",
        "Correlaciona-se ao ALVO 3 (Inflamação / HRV).",
        "TARGET_3_INFLAMMATION_HRV",
        ["monocitos", "742-7"],
    ),
    "eosinofilos": _make_entry(
        "eosinofilos",
        "Eosinófilos",
        "711-2",
        "%",
        1.0,
        6.0,
        "Granulócitos envolvidos em respostas alérgicas, atópicas e antiparasitárias.",
        "Eosinofilia (> 6%) indica ativação alérgica/atópica ou parasitose.",
        "Processos alérgicos ativos podem fragmentar o sono profundo (ALVO 1) e reduzir a HRV (ALVO 3).",
        "TARGET_3_INFLAMMATION_HRV",
        ["eosinofilos", "711-2"],
    ),
    "basofilos": _make_entry(
        "basofilos",
        "Basófilos",
        "704-7",
        "%",
        0.0,
        2.0,
        "Granulócitos mediadores de reações de hipersensibilidade e liberação de histamina.",
        "Elevações acima de 2% requerem correlação com quadros alérgicos ou mieloproliferativos.",
        "Integra o diferencial inflamatório do ALVO 3.",
        "TARGET_3_INFLAMMATION_HRV",
        ["basofilos", "704-7"],
    ),
    "plaquetas": _make_entry(
        "plaquetas",
        "Plaquetas",
        "777-3",
        "mil/mm3",
        150.0,
        450.0,
        "Fragmentos citoplasmáticos megacariocíticos essenciais para a hemostasia primária e coagulação.",
        "Plaquetopenia (< 150 mil/mm3) eleva risco hemorrágico; trombocitose (> 450 mil/mm3) pode ser reativa a ferropenia ou inflamação.",
        "Correlaciona-se aos ALVOS 3 (Inflamação) e 4 (Ferropenia reativa).",
        "TARGET_4_ANEMIA_LOAD",
        ["plaquetas", "trombocitos", "contagem_de_plaquetas", "777-3"],
    ),
    "ferro": _make_entry(
        "ferro",
        "Ferro Sérico",
        "2498-4",
        "ug/dL",
        60.0,
        170.0,
        "Fração de ferro circulante ligada à transferrina plasmática.",
        "Ferro sérico < 60 ug/dL acompanha quadros de ferropenia e anemia de doença crônica.",
        "Complementa a Ferritina no ALVO 4 (Triagem de Anemia via Índice de Carga Diurna).",
        "TARGET_4_ANEMIA_LOAD",
        ["ferro", "ferro_serico", "iron", "2498-4"],
    ),
    "transferrina": _make_entry(
        "transferrina",
        "Transferrina",
        "3034-6",
        "mg/dL",
        200.0,
        360.0,
        "Glicoproteína plasmática transportadora de ferro para a medula óssea e tecidos.",
        "Eleva-se de forma compensatória na deficiência de ferro e reduz-se em estados inflamatórios.",
        "Auxilia na distinção entre ferropenia pura (ALVO 4) e bloqueio inflamatório de ferro (ALVO 3).",
        "TARGET_4_ANEMIA_LOAD",
        ["transferrina", "3034-6"],
    ),
    "saturacao_transferrina": _make_entry(
        "saturacao_transferrina",
        "Saturação de Transferrina",
        "2502-3",
        "%",
        20.0,
        50.0,
        "Percentual dos sítios de ligação da transferrina ocupados por ferro sérico.",
        "Valores < 20% confirmam suprimento insuficiente de ferro para a eritropoiese.",
        "Reforça o diagnóstico de deficiência funcional ou absoluta de ferro no ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["saturacao_transferrina", "indice_de_saturacao_da_transferrina", "ist", "2502-3"],
    ),
    "tibc": _make_entry(
        "tibc",
        "Capacidade Total de Ligação do Ferro (TIBC)",
        "2500-7",
        "ug/dL",
        250.0,
        450.0,
        "Medida indireta da disponibilidade total de sítios de ligação de ferro na transferrina circulante.",
        "TIBC > 450 ug/dL é clássico na ferropenia.",
        "Complementa o painel de ferro do ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["tibc", "ctlf", "capacidade_total_de_fixacao_do_ferro", "2500-7"],
    ),
    "vitamina_d": _make_entry(
        "vitamina_d",
        "Vitamina D (25-Hidroxivitamina D)",
        "1989-3",
        "ng/mL",
        30.0,
        100.0,
        "Pró-hormônio esteroide essencial para homeostase osteomineral, modulação imunológica, função muscular e regulação da arquitetura do sono.",
        "Hipovitaminose D (< 30 ng/mL) associa-se a fadiga neuromuscular, fragmentação do sono profundo (N3) e maior suscetibilidade inflamatória.",
        "Correlaciona-se com o ALVO 1 (Arquitetura do Sono Profundo N3 < 16%) e ALVO 3 (HRV/Inflamação).",
        "TARGET_1_DEEP_SLEEP",
        ["vitamina_d", "25_oh_vitamina_d", "hidroxivitamina_d", "colecalciferol", "1989-3"],
    ),
    "vitamina_b12": _make_entry(
        "vitamina_b12",
        "Vitamina B12 (Cianocobalamina)",
        "2132-9",
        "pg/mL",
        200.0,
        900.0,
        "Coenzima essencial para síntese de DNA eritrocitário, mielinização neuronal e função autonômica.",
        "Deficiência (< 200 pg/mL ou limítrofe < 300 pg/mL) causa fadiga, neuropatia autonômica e anemia megaloblástica.",
        "Relaciona-se ao ALVO 3 (Disautonomia / HRV reduzida) e ALVO 4 (Fadiga / Carga Diurna elevada).",
        "TARGET_4_ANEMIA_LOAD",
        ["vitamina_b12", "cobalamina", "cianocobalamina", "b12", "2132-9"],
    ),
    "acido_folico": _make_entry(
        "acido_folico",
        "Ácido Fólico (Folato)",
        "2284-8",
        "ng/mL",
        3.1,
        20.5,
        "Vitamina hidrossolúvel do complexo B (B9) indispensável para maturação eritrocitária e metilação da homocisteína.",
        "Valores < 3.1 ng/mL associam-se a anemia macrocítica e fadiga.",
        "Integra a avaliação hematológica do ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["acido_folico", "folato", "vitamina_b9", "2284-8"],
    ),
    "glicose": _make_entry(
        "glicose",
        "Glicose de Jejum",
        "2345-7",
        "mg/dL",
        70.0,
        99.0,
        "Concentração plasmática basal de glicose após jejum noturno; marcador primário de homeostase glicêmica.",
        "Hiperglicemia basal (>= 100 mg/dL) reflete resistência insulínica e hiperatividade simpática, cursando com elevação da FC de repouso (RHR).",
        "Integra o ALVO 2 (Risco Cardiometabólico — RHR >= 72 bpm sem confundidores de tela/cafeína).",
        "TARGET_2_METABOLIC_RISK",
        ["glicose", "glicemia", "glicose_de_jejum", "glicemia_de_jejum", "glucose", "2345-7"],
    ),
    "hba1c": _make_entry(
        "hba1c",
        "Hemoglobina Glicada (HbA1c)",
        "4548-4",
        "%",
        4.0,
        5.6,
        "Fração da hemoglobina ligada à glicose, refletindo a glicemia média dos últimos 60 a 90 dias.",
        "HbA1c entre 5.7% e 6.4% indica pré-diabetes e risco cardiometabólico aumentado; >= 6.5% é compatível com diabetes.",
        "Ancora o ALVO 2 (RHR >= 72 bpm) e ALVO 1 (Sono Profundo N3 < 16%).",
        "TARGET_2_METABOLIC_RISK",
        ["hba1c", "hemoglobina_glicada", "glicohemoglobina", "a1c", "4548-4"],
    ),
    "insulina": _make_entry(
        "insulina",
        "Insulina Basal",
        "20448-7",
        "uUI/mL",
        2.6,
        24.9,
        "Hormônio pancreático anabólico regulador da captação celular de glicose.",
        "Hiperinsulinemia de jejum sinaliza resistência insulínica precoce e estimula o tônus simpático cardíaco.",
        "Explica elevações persistentes de RHR no ALVO 2.",
        "TARGET_2_METABOLIC_RISK",
        ["insulina", "insulina_basal", "insulinemia", "20448-7"],
    ),
    "homa_ir": _make_entry(
        "homa_ir",
        "Índice HOMA-IR",
        "4024-6",
        "índice",
        0.5,
        2.5,
        "Modelo matemático de avaliação homeostática da resistência à insulina (Glicose x Insulina / 405).",
        "HOMA-IR > 2.5 confirma resistência insulínica e risco cardiometabólico.",
        "Correlaciona-se diretamente ao ALVO 2 (RHR >= 72 bpm) e ao déficit de sono profundo N3 (ALVO 1).",
        "TARGET_2_METABOLIC_RISK",
        ["homa_ir", "indice_homa", "homa", "4024-6"],
    ),
    "colesterol": _make_entry(
        "colesterol",
        "Colesterol Total",
        "2093-3",
        "mg/dL",
        0.0,
        190.0,
        "Soma das frações lipoproteicas circulantes (LDL, HDL e VLDL), fundamental na estratificação de risco cardiovascular.",
        "Hipercolesterolemia (> 190 mg/dL) eleva o risco aterogênico, especialmente quando combinada a sedentarismo e RHR elevado.",
        "Conecta-se ao ALVO 2 (Risco Cardiometabólico — RHR >= 72 bpm).",
        "TARGET_2_METABOLIC_RISK",
        ["colesterol", "colesterol_total", "cholesterol", "2093-3"],
    ),
    "hdl": _make_entry(
        "hdl",
        "Colesterol HDL",
        "2085-9",
        "mg/dL",
        40.0,
        100.0,
        "Lipoproteína de alta densidade responsável pelo transporte reverso do colesterol.",
        "HDL < 40 mg/dL associa-se a resistência insulínica e baixa atividade aeróbica.",
        "Eleva-se com o aumento consistente do volume diário de passos (> 7500 passos/dia) e minutos ativos.",
        "TARGET_2_METABOLIC_RISK",
        ["hdl", "colesterol_hdl", "hdl_colesterol", "2085-9"],
    ),
    "ldl": _make_entry(
        "ldl",
        "Colesterol LDL",
        "13457-7",
        "mg/dL",
        0.0,
        130.0,
        "Lipoproteína de baixa densidade, principal fração aterogênica circulante.",
        "Elevações de LDL (> 130 mg/dL) aceleram a aterogênese arterial.",
        "Sinérgico ao ALVO 2 (RHR >= 72 bpm) na estratificação cardiometabólica.",
        "TARGET_2_METABOLIC_RISK",
        ["ldl", "colesterol_ldl", "ldl_colesterol", "13457-7"],
    ),
    "vldl": _make_entry(
        "vldl",
        "Colesterol VLDL",
        "13458-5",
        "mg/dL",
        0.0,
        30.0,
        "Lipoproteína de muito baixa densidade rica em triglicerídeos endógenos.",
        "VLDL > 30 mg/dL reflete hipertrigliceridemia e resistência insulínica.",
        "Relaciona-se ao ALVO 2 (Risco Cardiometabólico).",
        "TARGET_2_METABOLIC_RISK",
        ["vldl", "colesterol_vldl", "13458-5"],
    ),
    "triglicerideos": _make_entry(
        "triglicerideos",
        "Triglicerídeos",
        "2571-8",
        "mg/dL",
        0.0,
        150.0,
        "Principal forma de armazenamento lipídico circulante, sensível à resistência insulínica e ingestão alcoólica.",
        "Triglicerídeos > 150 mg/dL compõem o diagnóstico de síndrome metabólica.",
        "Relacionado ao ALVO 2 (RHR >= 72 bpm) e aos confundidores de álcool e sedentarismo.",
        "TARGET_2_METABOLIC_RISK",
        ["triglicerideos", "triglicerides", "tg", "2571-8"],
    ),
    "tsh": _make_entry(
        "tsh",
        "Hormônio Tireoestimulante (TSH)",
        "3016-3",
        "mUI/L",
        0.4,
        4.5,
        "Hormônio hipofisário regulador da síntese de T3 e T4 pela tireoide, determinando a taxa metabólica basal e a sensibilidade adrenérgica cardíaca.",
        "TSH < 0.4 mUI/L (hipertireoidismo) causa taquicardia de repouso e diurna; TSH > 4.5 mUI/L (hipotireoidismo) provoca fadiga e lentificação metabólica.",
        "Atua no diagnóstico diferencial do ALVO 2 (RHR >= 72 bpm) e ALVO 4 (Taquicardia Diurna / ICD com ferritina normal).",
        "TARGET_2_METABOLIC_RISK",
        ["tsh", "tireotrofina", "tsh_ultrassensivel", "hormonio_tireoestimulante", "3016-3"],
    ),
    "t4_livre": _make_entry(
        "t4_livre",
        "T4 Livre (Tiroxina Livre)",
        "3024-7",
        "ng/dL",
        0.7,
        1.8,
        "Fração biologicamente ativa da tiroxina secretada pela glândula tireoide.",
        "T4 Livre > 1.8 ng/dL induz estado hiperdinâmico com elevação de RHR e queda de HRV; < 0.7 ng/dL indica hipotireoidismo.",
        "Complementa o TSH na investigação de taquicardia não-ferropriva (ALVOS 2 e 4).",
        "TARGET_2_METABOLIC_RISK",
        ["t4_livre", "tiroxina_livre", "ft4", "3024-7"],
    ),
    "t3_livre": _make_entry(
        "t3_livre",
        "T3 Livre (Triiodotironina Livre)",
        "3051-0",
        "pg/mL",
        2.0,
        4.4,
        "Hormônio tireoidiano metabolicamente mais potente nos receptores nucleares cardíacos e periféricos.",
        "Elevações aumentam diretamente o cronotropismo cardíaco.",
        "Correlaciona-se com RHR e FC diurna (ALVOS 2 e 4).",
        "TARGET_2_METABOLIC_RISK",
        ["t3_livre", "triiodotironina_livre", "ft3", "3051-0"],
    ),
    "pcr": _make_entry(
        "pcr",
        "Proteína C Reativa Ultrassensível (PCR)",
        "30522-7",
        "mg/L",
        0.0,
        3.0,
        "Proteína plasmática de fase aguda sintetizada pelo fígado em resposta à IL-6; biomarcador padrão-ouro de inflamação sistêmica.",
        "Elevações de PCR (> 3.0 mg/L) sinalizam ativação inflamatória sistêmica ou infecção subclínica, inibindo o tônus vagal parassimpático.",
        "Valida o ALVO 3 (Inflamação Sistêmica / HRV RMSSD < 38 ms por 4 dias consecutivos sem privação de sono nem álcool).",
        "TARGET_3_INFLAMMATION_HRV",
        ["pcr", "pcr_us", "pcr_ultrassensivel", "proteina_c_reativa", "crp", "30522-7", "1988-5"],
    ),
    "vhs": _make_entry(
        "vhs",
        "Velocidade de Hemossedimentação (VHS)",
        "4537-7",
        "mm/h",
        0.0,
        20.0,
        "Medida indireta de proteínas inflamatórias de fase aguda (especialmente fibrinogênio).",
        "VHS > 20 mm/h aponta atividade inflamatória sistêmica persistente.",
        "Correlaciona-se com a queda sustentada de HRV RMSSD no ALVO 3.",
        "TARGET_3_INFLAMMATION_HRV",
        ["vhs", "hemossedimentacao", "velocidade_de_hemossedimentacao", "4537-7"],
    ),
    "creatinina": _make_entry(
        "creatinina",
        "Creatinina Sérica",
        "2160-0",
        "mg/dL",
        0.6,
        1.2,
        "Subproduto do metabolismo muscular da creatina, utilizado para estimar a taxa de filtração glomerular renal.",
        "Elevações acima de 1.2 mg/dL sugerem redução da filtração glomerular ou desidratação pós-esforço.",
        "Deve ser interpretada junto aos minutos de exercício intenso (`workout_minutes`) do wearable.",
        "TARGET_2_METABOLIC_RISK",
        ["creatinina", "creatinina_serica", "creatinine", "2160-0"],
    ),
    "ureia": _make_entry(
        "ureia",
        "Ureia",
        "3094-0",
        "mg/dL",
        15.0,
        45.0,
        "Principal metabólito nitrogenado derivado da degradação hepática de proteínas, excretado pelos rins.",
        "Ureia > 45 mg/dL ocorre em desidratação, dieta hiperproteica, catabolismo muscular intenso ou disfunção renal.",
        "Ajuda a identificar desidratação como causa de taquicardia diurna no wearable (ALVO 4).",
        "TARGET_4_ANEMIA_LOAD",
        ["ureia", "ureia_serica", "bun", "3094-0"],
    ),
    "tfg": _make_entry(
        "tfg",
        "Taxa de Filtração Glomerular Estimada (TFG)",
        "33914-3",
        "mL/min/1.73m2",
        90.0,
        130.0,
        "Estimativa do volume de plasma filtrado pelos glomérulos renais por minuto (CKD-EPI).",
        "TFG < 60 mL/min/1.73m2 por mais de 3 meses define doença renal crônica.",
        "Correlaciona-se à saúde vascular e pressão hemodinâmica (ALVO 2).",
        "TARGET_2_METABOLIC_RISK",
        ["tfg", "ritmo_de_filtracao_glomerular", "ckd_epi", "egfr", "33914-3"],
    ),
    "acido_urico": _make_entry(
        "acido_urico",
        "Ácido Úrico",
        "3084-1",
        "mg/dL",
        2.5,
        7.0,
        "Produto final do catabolismo das purinas, fortemente associado à resistência insulínica e estresse oxidativo endotelial.",
        "Hiperuricemia (> 7.0 mg/dL) associa-se a gota, hipertensão e síndrome metabólica.",
        "Integra o perfil de risco cardiometabólico do ALVO 2 (RHR >= 72 bpm).",
        "TARGET_2_METABOLIC_RISK",
        ["acido_urico", "urato", "3084-1"],
    ),
    "tgo": _make_entry(
        "tgo",
        "TGO / AST (Aspartato Aminotransferase)",
        "1920-8",
        "U/L",
        5.0,
        40.0,
        "Enzima intracelular presente no fígado, miocárdio e músculo esquelético.",
        "Elevações ocorrem em lesão hepatocelular ou rabdomiólise/microtrauma muscular pós-exercício intenso.",
        "Deve ser cruzada com `workout_minutes` e `active_calories_kcal` do wearable para diferenciar treino intenso de hepatopatia.",
        "TARGET_3_INFLAMMATION_HRV",
        ["tgo", "ast", "aspartato_aminotransferase", "transaminase_oxalacetica", "1920-8"],
    ),
    "tgp": _make_entry(
        "tgp",
        "TGP / ALT (Alanina Aminotransferase)",
        "1742-6",
        "U/L",
        7.0,
        56.0,
        "Enzima predominantemente citoplasmática dos hepatócitos, marcador específico de integridade hepática.",
        "TGP > 56 U/L sugere esteatose hepática metabólica (MASLD) ou injúria hepatocelular.",
        "Conecta-se ao ALVO 2 (Risco Metabólico) e ao confundidor de consumo de álcool (`alcohol_units`).",
        "TARGET_2_METABOLIC_RISK",
        ["tgp", "alt", "alanina_aminotransferase", "transaminase_piruvica", "1742-6"],
    ),
    "gama_gt": _make_entry(
        "gama_gt",
        "Gama GT (GGT)",
        "2324-2",
        "U/L",
        8.0,
        61.0,
        "Enzima microssomal biliar e hepática induzível por álcool, medicamentos e estresse oxidativo.",
        "Elevações de GGT refletem sobrecarga hepatobiliar, consumo alcoólico ou síndrome metabólica.",
        "Valida objetivamente o confundidor comportamental de ingestão alcoólica nos ALVOS 1 e 3.",
        "TARGET_3_INFLAMMATION_HRV",
        ["gama_gt", "ggt", "gama_glutamil_transferase", "2324-2"],
    ),
    "fosfatase_alcalina": _make_entry(
        "fosfatase_alcalina",
        "Fosfatase Alcalina",
        "6768-6",
        "U/L",
        40.0,
        129.0,
        "Hidrolase presente nos canalículos biliares e osteoblastos ósseos.",
        "Elevações indicam colestase hepatobiliar ou aumento do remodelamento ósseo.",
        "Complementa o painel hepatometabólico (ALVO 2) e metabolismo ósseo/Vitamina D (ALVO 1).",
        "TARGET_2_METABOLIC_RISK",
        ["fosfatase_alcalina", "fa", "alp", "6768-6"],
    ),
    "bilirrubina_total": _make_entry(
        "bilirrubina_total",
        "Bilirrubina Total",
        "1975-2",
        "mg/dL",
        0.2,
        1.2,
        "Produto do catabolismo do grupamento heme da hemoglobina, conjugado pelo fígado.",
        "Hiperbilirrubinemia (> 1.2 mg/dL) ocorre em colestase, síndrome de Gilbert ou hemólise.",
        "Se associada a queda de hemoglobina, auxilia na investigação de anemia hemolítica no ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["bilirrubina_total", "bilirrubinas", "1975-2"],
    ),
    "bilirrubina_direta": _make_entry(
        "bilirrubina_direta",
        "Bilirrubina Direta",
        "1968-7",
        "mg/dL",
        0.0,
        0.3,
        "Fração conjugada da bilirrubina excretada pelas vias biliares.",
        "Valores > 0.3 mg/dL sugerem disfunção hepatocelular ou colestase.",
        "Integra a avaliação hepática correlacionada ao ALVO 3.",
        "TARGET_3_INFLAMMATION_HRV",
        ["bilirrubina_direta", "1968-7"],
    ),
    "bilirrubina_indireta": _make_entry(
        "bilirrubina_indireta",
        "Bilirrubina Indireta",
        "1971-1",
        "mg/dL",
        0.1,
        0.9,
        "Fração não-conjugada da bilirrubina resultante da renovação das hemácias.",
        "Eleva-se na síndrome de Gilbert (especialmente em jejum/estresse) e em hemólise.",
        "Relaciona-se ao turnover de hemoglobina avaliado no ALVO 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["bilirrubina_indireta", "1971-1"],
    ),
    "sodio": _make_entry(
        "sodio",
        "Sódio Sérico",
        "2951-2",
        "mEq/L",
        135.0,
        145.0,
        "Principal cátion extracelular determinante da osmolaridade plasmática e volemia.",
        "Hipernatremia (> 145 mEq/L) indica desidratação; hiponatremia (< 135 mEq/L) ocorre em perdas hidroeletrolíticas.",
        "Desidratação eleva o Índice de Carga Diurna (ICD) e a FC de repouso (ALVOS 2 e 4).",
        "TARGET_4_ANEMIA_LOAD",
        ["sodio", "sodio_serico", "na", "2951-2"],
    ),
    "potassio": _make_entry(
        "potassio",
        "Potássio Sérico",
        "2823-3",
        "mEq/L",
        3.5,
        5.1,
        "Principal cátion intracelular responsável pelo potencial de repouso e repolarização elétrica do miocárdio.",
        "Hipocalemia (< 3.5 mEq/L) e hipercalemia (> 5.1 mEq/L) predispõem a arritmias cardíacas e cãibras.",
        "Essencial na avaliação eletrofisiológica de alterações de FC e HRV (ALVOS 2 e 3).",
        "TARGET_2_METABOLIC_RISK",
        ["potassio", "potassio_serico", "k", "2823-3"],
    ),
    "calcio": _make_entry(
        "calcio",
        "Cálcio Total",
        "17861-6",
        "mg/dL",
        8.5,
        10.5,
        "Mineral essencial para acoplamento excitação-contração muscular, condução cardíaca e mineralização óssea.",
        "Desvios de calcemia relacionam-se a distúrbios da paratireoide (PTH) e Vitamina D.",
        "Correlaciona-se ao metabolismo de Vitamina D e recuperação neuromuscular (ALVO 1).",
        "TARGET_1_DEEP_SLEEP",
        ["calcio", "calcio_total", "17861-6"],
    ),
    "magnesio": _make_entry(
        "magnesio",
        "Magnésio Sérico",
        "19123-9",
        "mg/dL",
        1.6,
        2.6,
        "Cofator enzimático crucial para relaxamento neuromuscular, modulação GABAérgica do sono e tônus parassimpático.",
        "Hipomagnesemia (< 1.6 mg/dL) associa-se a redução do sono profundo N3, ansiedade, cãibras e queda de HRV.",
        "Relaciona-se diretamente ao ALVO 1 (Sono Profundo N3 < 16%) e ALVO 3 (HRV RMSSD).",
        "TARGET_1_DEEP_SLEEP",
        ["magnesio", "magnesio_serico", "mg", "19123-9"],
    ),
    "fosforo": _make_entry(
        "fosforo",
        "Fósforo Sérico",
        "2777-1",
        "mg/dL",
        2.5,
        4.5,
        "Íon fundamental para síntese de ATP e oxigenação tecidual via 2,3-DPG eritrocitário.",
        "Hipofosfatemia reduz a contratilidade muscular e a liberação periférica de oxigênio.",
        "Complementa a avaliação energética e de transporte de O2 nos ALVOS 1 e 4.",
        "TARGET_4_ANEMIA_LOAD",
        ["fosforo", "fosfato", "2777-1"],
    ),
    "cortisol": _make_entry(
        "cortisol",
        "Cortisol Basal",
        "2143-6",
        "ug/dL",
        5.0,
        25.0,
        "Principal glicocorticoide do eixo hipotálamo-hipófise-adrenal (HPA), marcador biológico de estresse fisiológico.",
        "Hipercortisolismo suprime o sono profundo (N3), reduz a HRV RMSSD e eleva a FC de repouso e glicemia.",
        "Conecta transversalmente os ALVOS 1 (Sono N3), 2 (RHR/Metabólico) e 3 (Queda de HRV).",
        "TARGET_3_INFLAMMATION_HRV",
        ["cortisol", "cortisol_basal", "cortisol_matinal", "2143-6"],
    ),
    "testosterona": _make_entry(
        "testosterona",
        "Testosterona Total",
        "2986-8",
        "ng/dL",
        240.0,
        950.0,
        "Hormônio esteroide anabólico regulador da massa muscular, eritropoiese e recuperação física.",
        "Reduções associam-se a fadiga, queda de recuperação pós-treino e restrição crônica de sono profundo/REM.",
        "A secreção endógena de testosterona depende diretamente da preservação do sono N3/REM (ALVO 1).",
        "TARGET_1_DEEP_SLEEP",
        ["testosterona", "testosterona_total", "2986-8"],
    ),
    "estradiol": _make_entry(
        "estradiol",
        "Estradiol (E2)",
        "2243-4",
        "pg/mL",
        15.0,
        350.0,
        "Principal estrogênio endógeno modulador da função endotelial, termorregulação e arquitetura do sono.",
        "Variações influenciam a temperatura basal e a eficiência do sono noturno.",
        "Contextualiza variações autonômicas e de sono nos ALVOS 1 e 3.",
        "TARGET_1_DEEP_SLEEP",
        ["estradiol", "17_beta_estradiol", "e2", "2243-4"],
    ),
    "psa": _make_entry(
        "psa",
        "PSA Total (Antígeno Prostático Específico)",
        "2857-1",
        "ng/mL",
        0.0,
        4.0,
        "Glicoproteína produzida pelo epitélio prostático utilizada no rastreamento urológico.",
        "Elevações acima de 4.0 ng/mL indicam hiperplasia, prostatite ou necessidade de investigação urológica.",
        "Marcador preventivo longitudinal integrado ao prontuário FHIR.",
        "TARGET_3_INFLAMMATION_HRV",
        ["psa", "psa_total", "antigeno_prostatico_especifico", "2857-1"],
    ),
    "albumina": _make_entry(
        "albumina",
        "Albumina Sérica",
        "1751-7",
        "g/dL",
        3.5,
        5.2,
        "Principal proteína plasmática sintetizada pelo fígado, determinante da pressão oncótica e proteína negativa de fase aguda.",
        "Hipoalbuminemia (< 3.5 g/dL) reflete inflamação sistêmica crônica, desnutrição ou disfunção hepática/renal.",
        "Relaciona-se ao estado nutricional e inflamatório avaliado no ALVO 3.",
        "TARGET_3_INFLAMMATION_HRV",
        ["albumina", "albumina_serica", "1751-7"],
    ),
    "lactato": _make_entry(
        "lactato",
        "Lactato (Ácido Lático)",
        "2524-7",
        "mmol/L",
        0.5,
        2.2,
        "Metabólito da glicólise anaeróbica, marcador de hipóxia tecidual ou esforço físico de alta intensidade.",
        "Elevações em repouso (> 2.2 mmol/L) sinalizam hipoperfusão/hipóxia tecidual ou disfunção mitocondrial.",
        "Correlaciona-se ao ALVO 4 (Déficit de transporte de O2 / ICD elevado) e intensidade de treino.",
        "TARGET_4_ANEMIA_LOAD",
        ["lactato", "acido_latico", "2524-7"],
    ),
}

# Regras ordenadas de extração (termos compostos/específicos ANTES dos termos curtos/gerais)
EXTRACTION_RULES: List[Tuple[str, str]] = [
    ("hba1c", r"(?:hemoglobina\s+glicada|glicohemoglobina|\bhba1c\b|4548-4)"),
    ("hemoglobina", r"(?:\bhemoglobina\b(?!\s*(?:glicada|corpuscular))|\bhb\b(?!\s*a1c)|718-7)"),
    ("hematocrito", r"(?:\bhemat[oó]crito\b|\bht\b|\bhct\b|4544-3)"),
    ("hemacias", r"(?:\bhem[aá]cias\b|\beritr[oó]citos\b|gl[oó]bulos\s+vermelhos|789-8)"),
    ("vcm", r"(?:\bvcm\b|volume\s+corpuscular\s+m[eé]dio|787-2)"),
    ("chcm", r"(?:\bchcm\b|786-4)"),
    ("hcm", r"(?:\bhcm\b|hemoglobina\s+corpuscular\s+m[eé]dia|785-6)"),
    ("rdw", r"(?:\brdw(?:-cv)?\b|anisocitose|788-0)"),
    ("leucocitos", r"(?:\bleuc[oó]citos(?:\s+totais)?\b|gl[oó]bulos\s+brancos|6690-2)"),
    ("neutrofilos", r"(?:\bneutr[oó]filos(?:\s+segmentados)?\b|\bsegmentados\b|751-8|768-2)"),
    ("linfocitos", r"(?:\blinf[oó]citos\b|731-0)"),
    ("monocitos", r"(?:\bmon[oó]citos\b|742-7)"),
    ("eosinofilos", r"(?:\beosin[oó]filos\b|711-2)"),
    ("basofilos", r"(?:\bbas[oó]filos\b|704-7)"),
    ("plaquetas", r"(?:\bplaquetas\b|\btromb[oó]citos\b|777-3)"),
    ("ferritina", r"(?:\bferritina(?:\s+s[eé]rica)?\b|2276-4)"),
    ("saturacao_transferrina", r"(?:satura[cç][aã]o\s+(?:de|da)\s+transferrina|\bist\b|2502-3)"),
    ("transferrina", r"(?:\btransferrina\b|3034-6)"),
    ("tibc", r"(?:\btibc\b|\bctlf\b|capacidade\s+total\s+de\s+(?:lig|fix)a[cç][aã]o\s+do\s+ferro|2500-7)"),
    ("ferro", r"(?:\bferro\s+s[eé]rico\b|\bdosagem\s+de\s+ferro\b|\bferro\b(?!\s*tina)|2498-4)"),
    ("vitamina_d", r"(?:vitamina\s*d(?:\s*\(?25[\s-]*oh\)?)?|25[\s-]*hidroxivitamina\s*d|\bcolecalciferol\b|1989-3)"),
    ("vitamina_b12", r"(?:vitamina\s*b\s*12|\bcobalamina\b|\bcianocobalamina\b|2132-9)"),
    ("acido_folico", r"(?:[aá]cido\s+f[oó]lico|\bfolato\b|vitamina\s*b9|2284-8)"),
    ("glicose", r"(?:\bglicose(?:\s+(?:de|em)\s+jejum)?\b|\bglicemia(?:\s+(?:de|em)\s+jejum)?\b|2345-7)"),
    ("homa_ir", r"(?:homa[\s-]*ir|[ií]ndice\s+homa|4024-6)"),
    ("insulina", r"(?:\binsulina(?:\s+basal|\s+jejum)?\b|\binsulinemia\b|20448-7)"),
    ("hdl", r"(?:colesterol\s*[-:]?\s*hdl|\bhdl\s*[-:]?\s*colesterol\b|\bhdl\b|2085-9)"),
    ("ldl", r"(?:colesterol\s*[-:]?\s*ldl|\bldl\s*[-:]?\s*colesterol\b|\bldl\b|13457-7)"),
    ("vldl", r"(?:colesterol\s*[-:]?\s*vldl|\bvldl\s*[-:]?\s*colesterol\b|\bvldl\b|13458-5)"),
    ("colesterol", r"(?:colesterol\s+total|\bcolesterol\b(?![\s:-]*(?:hdl|ldl|vldl|n[aã]o))|2093-3)"),
    ("triglicerideos", r"(?:\btriglicer[ií]deos\b|\btriglic[eé]rides\b|\btriglic[eé]rideos\b|2571-8)"),
    ("tsh", r"(?:\btsh(?:\s+ultra[\s-]*sens[ií]vel)?\b|\btireotrofina\b|horm[oô]nio\s+tireoestimulante|3016-3)"),
    ("t4_livre", r"(?:\bt4\s+livre\b|tiroxina\s+livre|\bft4\b|3024-7)"),
    ("t3_livre", r"(?:\bt3\s+livre\b|triiodotironina\s+livre|\bft3\b|3051-0)"),
    ("pcr", r"(?:prote[ií]na\s+c\s+reativa(?:\s+ultrassens[ií]vel)?|\bpcr(?:\s*[-_]?us|\s+ultrassens[ií]vel)?\b|30522-7|1988-5)"),
    ("vhs", r"(?:\bvhs\b|velocidade\s+de\s+hemossedimenta[cç][aã]o|4537-7)"),
    ("creatinina", r"(?:\bcreatinina(?:\s+s[eé]rica)?\b|2160-0)"),
    ("tfg", r"(?:taxa\s+de\s+filtra[cç][aã]o\s+glomerular|ritmo\s+de\s+filtra[cç][aã]o|\btfg\b|\begfr\b|33914-3)"),
    ("ureia", r"(?:\bureia(?:\s+s[eé]rica)?\b|3094-0)"),
    ("acido_urico", r"(?:[aá]cido\s+[uú]rico|\burato\b|3084-1)"),
    ("tgo", r"(?:\btgo\b|\bast\b|aspartato\s+aminotransferase|transaminase\s+oxalac[eé]tica|1920-8)"),
    ("tgp", r"(?:\btgp\b|\balt\b|alanina\s+aminotransferase|transaminase\s+pir[uú]vica|1742-6)"),
    ("gama_gt", r"(?:gama\s*[-]?gt|\bggt\b|gama\s+glutamil|2324-2)"),
    ("fosfatase_alcalina", r"(?:fosfatase\s+alcalina|6768-6)"),
    ("bilirrubina_direta", r"(?:bilirrubina\s+direta|1968-7)"),
    ("bilirrubina_indireta", r"(?:bilirrubina\s+indireta|1971-1)"),
    ("bilirrubina_total", r"(?:bilirrubina\s+total|\bbilirrubinas\b|1975-2)"),
    ("sodio", r"(?:\bs[oó]dio(?:\s+s[eé]rico)?\b|2951-2)"),
    ("potassio", r"(?:\bpot[aá]ssio(?:\s+s[eé]rico)?\b|2823-3)"),
    ("calcio", r"(?:\bc[aá]lcio(?:\s+total|\s+s[eé]rico)?\b(?!\s*i[oô]nico)|17861-6)"),
    ("magnesio", r"(?:\bmagn[eé]sio(?:\s+s[eé]rico)?\b|19123-9)"),
    ("fosforo", r"(?:\bf[oó]sforo(?:\s+s[eé]rico)?\b|\bfosfato\b|2777-1)"),
    ("cortisol", r"(?:\bcortisol(?:\s+basal|\s+matinal|\s+s[eé]rico)?\b|2143-6)"),
    ("testosterona", r"(?:\btestosterona(?:\s+total)?\b(?!\s*livre)|2986-8)"),
    ("estradiol", r"(?:\bestradiol\b|17[\s-]*beta[\s-]*estradiol|2243-4)"),
    ("psa", r"(?:\bpsa(?:\s+total)?\b(?!\s*livre)|ant[ií]geno\s+prost[aá]tico|2857-1)"),
    ("albumina", r"(?:\balbumina(?:\s+s[eé]rica)?\b(?!\s*uria)|1751-7)"),
    ("lactato", r"(?:\blactato\b|[aá]cido\s+l[aá]tico|2524-7)"),
]


def _lookup_catalog_entry(query_name: str) -> Dict[str, Any]:
    slug = _normalize_slug(query_name)
    if slug in CLINICAL_KNOWLEDGE_CATALOG:
        return CLINICAL_KNOWLEDGE_CATALOG[slug]

    for key, entry in CLINICAL_KNOWLEDGE_CATALOG.items():
        aliases = [_normalize_slug(a) for a in entry.get("aliases", [])]
        if slug in aliases or any(slug == a for a in aliases):
            return entry

    for key, regex in EXTRACTION_RULES:
        if re.search(regex, query_name or "", flags=re.IGNORECASE):
            return CLINICAL_KNOWLEDGE_CATALOG[key]

    # Consulta a base ontológica completa do monorepo se disponível em disco
    kb_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "02_backend"
        / "03_semantica_ontologias"
        / "base_conhecimento_exames_565.json"
    )
    if kb_path.exists():
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
            for code, item in kb_data.items():
                nome = item.get("nome_exame", "")
                if slug == _normalize_slug(code) or slug == _normalize_slug(item.get("codigo_loinc", "")) or (
                    len(slug) >= 3 and slug in _normalize_slug(nome)
                ):
                    faixa = item.get("faixa_referencia", {}) or {}
                    ref_min = float(faixa.get("min", 10.0) or 10.0)
                    ref_max = float(faixa.get("max", 100.0) or 100.0)
                    unit = item.get("unidade", "unid")
                    return _make_entry(
                        analito=slug,
                        name=nome or query_name.title(),
                        loinc=item.get("codigo_loinc", code),
                        unit=unit,
                        ref_min=ref_min,
                        ref_max=ref_max,
                        description=item.get("resumo_exame", f"Biomarcador laboratorial {nome}."),
                        clinical_significance=f"Avaliação laboratorial quantitativa de {nome} ({unit}) para correlação clínica.",
                        causal_relationship=(
                            "Integrado ao Motor de Inferência Causal Open Health para desambiguação "
                            "entre biomarcadores séricos e sinais fisiológicos contínuos de wearables."
                        ),
                    )
        except Exception as exc:
            logger.debug("Não foi possível consultar base_conhecimento_exames_565.json: %s", exc)

    clean_title = (query_name or "Biomarcador").replace("_", " ").replace("-", " ").strip().title()
    return _make_entry(
        analito=slug or "biomarcador",
        name=clean_title,
        loinc="LP-OPENHEALTH",
        unit="unid",
        ref_min=10.0,
        ref_max=100.0,
        description=f"Biomarcador laboratorial ({clean_title}) utilizado na avaliação clínica integrada Open Health.",
        clinical_significance=f"Alterações em {clean_title} devem ser interpretadas em conjunto com a história clínica e os sinais contínuos de wearables.",
        causal_relationship=(
            "Integrado ao Motor de Inferência Causal (DAG de 3 camadas) para separar confundidores "
            "comportamentais (sono, passos, cafeína, álcool, tela) de anomalias fisiológicas genuínas."
        ),
    )


def _classify_status(
    value: float,
    ref_min: Optional[float],
    ref_max: Optional[float],
) -> Tuple[Optional[str], Optional[str]]:
    """Retorna (status_en, cor_pt) frente à faixa de referência, ou (None, None) quando não houver referência."""
    if ref_min is None and ref_max is None:
        return None, None
    if ref_min is not None and value < ref_min:
        return "LOW", "AMARELO" if value >= ref_min * 0.6 else "VERMELHO"
    if ref_max is not None and value > ref_max:
        return "HIGH", "AMARELO" if value <= ref_max * 1.4 else "VERMELHO"
    return "NORMAL", "VERDE"


def _build_biomarker_item(
    entry: Dict[str, Any],
    value: float,
    custom_unit: Optional[str] = None,
    custom_ref_min: Optional[float] = None,
    custom_ref_max: Optional[float] = None,
    use_catalog_reference: bool = False,
) -> Dict[str, Any]:
    unit = (custom_unit or "").strip() or entry.get("unit", "unid")
    has_explicit_ref = custom_ref_min is not None or custom_ref_max is not None

    if has_explicit_ref:
        ref_min: Optional[float] = float(custom_ref_min) if custom_ref_min is not None else None
        ref_max: Optional[float] = float(custom_ref_max) if custom_ref_max is not None else None
        if ref_min is not None and ref_max is not None:
            ref_range: Optional[str] = f"{ref_min} a {ref_max} {unit}" if ref_min > 0 else f"< {ref_max} {unit}"
        elif ref_max is not None:
            ref_range = f"< {ref_max} {unit}"
        else:
            ref_range = f"> {ref_min} {unit}"
        status_en, status_pt = _classify_status(value, ref_min, ref_max)
    elif use_catalog_reference:
        ref_min = float(entry.get("reference_min", 0.0))
        ref_max = float(entry.get("reference_max", 100.0))
        if custom_unit:
            ref_range = f"{ref_min} a {ref_max} {unit}" if ref_min > 0 else f"< {ref_max} {unit}"
        else:
            ref_range = entry.get("reference_range", f"{ref_min} - {ref_max} {unit}")
        status_en, status_pt = _classify_status(value, ref_min, ref_max)
    else:
        ref_min = None
        ref_max = None
        ref_range = None
        status_en = None
        status_pt = None

    return {
        "name": entry["name"],
        "nome_exame": entry["nome_exame"],
        "analito": entry["analito"],
        "code": entry["codigo_loinc"],
        "codigo_loinc": entry["codigo_loinc"],
        "value": round(float(value), 2),
        "valor_numerico": round(float(value), 2),
        "unit": unit,
        "unidade": unit,
        "reference_min": ref_min,
        "reference_max": ref_max,
        "faixa_referencia_min": ref_min,
        "faixa_referencia_max": ref_max,
        "reference_range": ref_range,
        "status": status_en,
        "status_cor": status_pt,
        "causal_target_id": entry.get("causal_target_id"),
    }


NUMBER_TOKEN_REGEX = r"(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"
UNIT_TOKEN_REGEX = (
    r"(?:milh[oõ]es/mm3|mil/mm3|/mm3|10\^3/[uµ]L|10\^6/[uµ]L|mL/min/1[.,]73\s*m2|mL/min|"
    r"mg/dL|ng/mL|ng/dL|g/dL|pg/mL|ug/dL|µg/dL|mcg/dL|mg/L|g/L|"
    r"mUI/L|uUI/mL|µUI/mL|mUI/mL|UI/mL|UI/L|U/L|"
    r"mEq/L|mmol/L|umol/L|µmol/L|nmol/L|pmol/L|"
    r"mm/h|fL|pg|%)"
)


def _extract_number_and_unit_before_ref(segment: str) -> Tuple[Optional[float], Optional[str]]:
    """Extrai (valor_numerico, unidade_original_opcional) antes de qualquer 'Ref:' / 'Referência:'."""
    explicit_res = re.search(
        rf"(?:resultado|valor\s+obtido|dosagem\s+obtida|valor\s+encontrado)\s*[:=]?\s*[<>≤≥]?\s*"
        rf"(?P<val>{NUMBER_TOKEN_REGEX})(?:\s*(?P<unit>{UNIT_TOKEN_REGEX}))?",
        segment,
        flags=re.IGNORECASE,
    )
    if explicit_res:
        val = _parse_br_float(explicit_res.group("val"))
        if val is not None:
            return val, explicit_res.group("unit")

    before_ref = re.split(
        r"(?:valores\s+de\s+refer[eê]ncia|valor\s+de\s+refer[eê]ncia|refer[eê]ncia|\bref\.?\s*[:=]|\bvr\s*[:=]|desej[aá]vel\s*[:=]|\(\s*ref)",
        segment,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    cleaned = re.sub(r"\b\d{2}/\d{2}/\d{2,4}\b", " ", before_ref)
    cleaned = re.sub(r"\b\d{2}:\d{2}(?::\d{2})?\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{3,5}-\d\b", " ", cleaned)
    cleaned = re.sub(r"\(\s*25[\s-]*oh\s*\)", " ", cleaned, flags=re.IGNORECASE)

    num_match = re.search(
        rf"(?<![A-Za-z0-9_-])[<>≤≥]?\s*(?P<val>{NUMBER_TOKEN_REGEX})(?:\s*(?P<unit>{UNIT_TOKEN_REGEX}))?",
        cleaned,
        flags=re.IGNORECASE,
    )
    if num_match:
        return _parse_br_float(num_match.group("val")), num_match.group("unit")
    return None, None


def _extract_ref_from_segment(segment: str, after_result_only: bool = False) -> Tuple[Optional[float], Optional[float]]:
    if not segment or not segment.strip():
        return None, None

    # 1. Faixa explícita com rótulo (Ref:, VR:, Valor de Referência:, Referência:, Normal:, Desejável:)
    ref_labeled_range = re.search(
        rf"(?:valores\s+de\s+refer[eê]ncia|valor\s+de\s+refer[eê]ncia|refer[eê]ncia|\bref\.?|\bvr\b|normal|desej[aá]vel)\s*[:=]?\s*"
        rf"({NUMBER_TOKEN_REGEX})\s*(?:a|-|at[eé])\s*({NUMBER_TOKEN_REGEX})",
        segment,
        flags=re.IGNORECASE,
    )
    if ref_labeled_range:
        return _parse_br_float(ref_labeled_range.group(1)), _parse_br_float(ref_labeled_range.group(2))

    # 2. Limite superior explícito com rótulo (ex: Ref: < 190, VR: <= 5,0, Referência: inferior a 200)
    ref_labeled_upper = re.search(
        rf"(?:valores\s+de\s+refer[eê]ncia|valor\s+de\s+refer[eê]ncia|refer[eê]ncia|\bref\.?|\bvr\b|normal|desej[aá]vel)\s*[:=]?\s*"
        rf"(?:<|<=|≤|inferior\s+a|menor\s+que|at[eé])\s*({NUMBER_TOKEN_REGEX})",
        segment,
        flags=re.IGNORECASE,
    )
    if ref_labeled_upper:
        return None, _parse_br_float(ref_labeled_upper.group(1))

    # 3. Limite inferior explícito com rótulo (ex: Ref: > 40, VR: >= 60, Referência: superior a 40)
    ref_labeled_lower = re.search(
        rf"(?:valores\s+de\s+refer[eê]ncia|valor\s+de\s+refer[eê]ncia|refer[eê]ncia|\bref\.?|\bvr\b|normal|desej[aá]vel)\s*[:=]?\s*"
        rf"(?:>|>=|≥|superior\s+a|maior\s+que|acima\s+de)\s*({NUMBER_TOKEN_REGEX})",
        segment,
        flags=re.IGNORECASE,
    )
    if ref_labeled_lower:
        return _parse_br_float(ref_labeled_lower.group(1)), None

    # 4. Faixa sem rótulo explícito posicionada após o valor do exame (ex: "(70 - 99 mg/dL)", "(< 5.0)", "(> 40)")
    if after_result_only:
        cleaned = re.sub(r"\b\d{2}/\d{2}/\d{2,4}\b", " ", segment)
        cleaned = re.sub(r"\b\d{2}-\d{2}-\d{4}\b", " ", cleaned)
        cleaned = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", cleaned)
        cleaned = re.sub(r"\b\d{3,5}-\d\b", " ", cleaned)
        cleaned = re.sub(r"\(\s*25[\s-]*oh\s*\)", " ", cleaned, flags=re.IGNORECASE)

        unlabeled_range = re.search(
            rf"(?:\(\s*|\[\s*|\b)({NUMBER_TOKEN_REGEX})\s*(?:a|-|at[eé])\s*({NUMBER_TOKEN_REGEX})",
            cleaned,
            flags=re.IGNORECASE,
        )
        if unlabeled_range:
            return _parse_br_float(unlabeled_range.group(1)), _parse_br_float(unlabeled_range.group(2))

        unlabeled_upper = re.search(
            rf"(?:\(\s*|\[\s*|(?:^|\s))(?:<|<=|≤)\s*({NUMBER_TOKEN_REGEX})",
            cleaned,
            flags=re.IGNORECASE,
        )
        if unlabeled_upper:
            return None, _parse_br_float(unlabeled_upper.group(1))

        unlabeled_lower = re.search(
            rf"(?:\(\s*|\[\s*|(?:^|\s))(?:>|>=|≥)\s*({NUMBER_TOKEN_REGEX})",
            cleaned,
            flags=re.IGNORECASE,
        )
        if unlabeled_lower:
            return _parse_br_float(unlabeled_lower.group(1)), None

    return None, None


def _remainder_after_first_result(line: str) -> str:
    """Retorna o trecho da linha situado após o primeiro valor numérico (+ unidade opcional)."""
    cleaned = re.sub(r"\b\d{2}/\d{2}/\d{2,4}\b", " ", line)
    cleaned = re.sub(r"\b\d{2}:\d{2}(?::\d{2})?\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{3,5}-\d\b", " ", cleaned)
    cleaned = re.sub(r"\(\s*25[\s-]*oh\s*\)", " ", cleaned, flags=re.IGNORECASE)
    m = re.search(
        rf"(?<![A-Za-z0-9_-])[<>≤≥]?\s*(?P<val>{NUMBER_TOKEN_REGEX})(?:\s*(?P<unit>{UNIT_TOKEN_REGEX}))?",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not m:
        return ""
    return cleaned[m.end() :]


def _extract_value_from_window(
    window: str,
) -> Tuple[Optional[float], Optional[str], Optional[float], Optional[float]]:
    """
    Extrai (valor_resultado, unidade_pdf, ref_min_opcional, ref_max_opcional) da janela após o nome do exame.
    Prioriza a mesma linha (layout tabular/inline) e, se não houver número na mesma linha,
    inspeciona as linhas subsequentes do mesmo bloco (layout multi-linha) sem invadir o próximo exame.
    """
    if not window:
        return None, None, None, None

    raw_lines = window.splitlines()[:4]
    if not raw_lines:
        return None, None, None, None

    # 1. Tenta extrair na mesma linha em que o nome do exame apareceu (truncando em '|' se houver múltiplos exames na linha)
    first_line = raw_lines[0].split("|", 1)[0]
    val_same_line, unit_same_line = _extract_number_and_unit_before_ref(first_line)
    if val_same_line is not None:
        rmin, rmax = _extract_ref_from_segment(first_line)
        if rmin is None and rmax is None:
            remainder = _remainder_after_first_result(first_line)
            rmin, rmax = _extract_ref_from_segment(remainder, after_result_only=True)
        if rmin is None and rmax is None and len(raw_lines) > 1:
            next_stripped = raw_lines[1].split("|", 1)[0].strip()
            # Só busca referência na linha seguinte se ela for explicitamente uma linha de referência e não outro exame
            if re.match(
                r"^(?:\(?\s*(?:valores\s+de\s+refer[eê]ncia|valor\s+de\s+refer[eê]ncia|refer[eê]ncia|\bref\.?\b|\bvr\b|desej[aá]vel|normal)\b)",
                next_stripped,
                flags=re.IGNORECASE,
            ) and not any(re.search(pat, next_stripped, flags=re.IGNORECASE) for _, pat in EXTRACTION_RULES):
                rmin, rmax = _extract_ref_from_segment(next_stripped)
        return val_same_line, unit_same_line, rmin, rmax

    # 2. Layout multi-linha: percorre as linhas seguintes parando se encontrar outro nome de exame
    block_lines = [first_line]
    for next_line in raw_lines[1:]:
        stripped = next_line.strip()
        if not stripped:
            continue
        if not re.match(
            r"^(?:resultado|valor|dosagem|material|m[eé]todo|refer[eê]ncia|ref\b|vr\b|desej[aá]vel|normal|\d|[<>≤≥])",
            stripped,
            flags=re.IGNORECASE,
        ):
            if any(re.search(pat, stripped, flags=re.IGNORECASE) for _, pat in EXTRACTION_RULES):
                break
        block_lines.append(next_line.split("|", 1)[0])

    block_text = "\n".join(block_lines[1:])
    val_multi, unit_multi = _extract_number_and_unit_before_ref(block_text)
    rmin, rmax = _extract_ref_from_segment("\n".join(block_lines))
    if rmin is None and rmax is None:
        remainder_multi = _remainder_after_first_result(block_text)
        rmin, rmax = _extract_ref_from_segment(remainder_multi, after_result_only=True)
    return val_multi, unit_multi, rmin, rmax


def _extract_biomarkers_from_text(
    raw_text: str,
    use_catalog_reference: bool = False,
) -> List[Dict[str, Any]]:
    """Extrai biomarcadores estruturados de texto de PDF laboratorial, CSV ou texto livre."""
    if not raw_text or not raw_text.strip():
        return []

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    extracted_with_pos: List[Tuple[int, Dict[str, Any]]] = []
    seen_keys = set()

    # Camada 1: Catálogo de 60+ exames clínicos brasileiros (suporta linha única e blocos multi-linha)
    for key, pattern in EXTRACTION_RULES:
        if key in seen_keys:
            continue
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            prefix = text[max(0, match.start() - 25) : match.start()].lower()
            if "refer" in prefix:
                continue

            window = text[match.end() : match.end() + 220]
            val, pdf_unit, ref_min, ref_max = _extract_value_from_window(window)
            if val is not None:
                entry = CLINICAL_KNOWLEDGE_CATALOG[key]
                item = _build_biomarker_item(
                    entry,
                    val,
                    custom_unit=pdf_unit,
                    custom_ref_min=ref_min,
                    custom_ref_max=ref_max,
                    use_catalog_reference=use_catalog_reference,
                )
                extracted_with_pos.append((match.start(), item))
                seen_keys.add(key)
                break

    # Camada 2: Parser genérico por linha/bloco para capturar exames adicionais com unidade explícita no PDF
    generic_pattern = re.compile(
        rf"(?:^|\n)\s*(?P<name>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\-\(\)/]{{2,42}}?)"
        rf"(?:\s*[:.\-]+\s*|\s{{2,}}|\s+Resultado\s*[:=]?\s*)"
        rf"(?P<val>{NUMBER_TOKEN_REGEX})\s*"
        rf"(?P<unit>{UNIT_TOKEN_REGEX})"
        rf"(?:[^\n|]{{0,60}}?(?:Ref(?:er[eê]ncia)?|VR)?[\s:(\[]*(?P<rmin>{NUMBER_TOKEN_REGEX})\s*(?:a|-)\s*(?P<rmax>{NUMBER_TOKEN_REGEX}))?",
        flags=re.IGNORECASE,
    )
    ignored_generic_names = {
        "resultado", "resultados", "valor", "valores", "referencia", "valores_de_referencia",
        "metodo", "material", "paciente", "idade", "data", "coleta", "pagina",
    }

    for gmatch in generic_pattern.finditer(text):
        raw_name = gmatch.group("name").strip(" .:-")
        slug = _normalize_slug(raw_name)
        if not slug or len(slug) < 2 or slug in ignored_generic_names or any(w in slug for w in ("referencia", "metodo", "coleta", "material")):
            continue

        entry = _lookup_catalog_entry(raw_name)
        canonical_key = entry["analito"]
        if canonical_key in seen_keys or slug in seen_keys:
            continue

        val = _parse_br_float(gmatch.group("val"))
        if val is None:
            continue
        rmin = _parse_br_float(gmatch.group("rmin")) if gmatch.group("rmin") else None
        rmax = _parse_br_float(gmatch.group("rmax")) if gmatch.group("rmax") else None
        unit = gmatch.group("unit")
        item = _build_biomarker_item(
            entry,
            val,
            custom_unit=unit,
            custom_ref_min=rmin,
            custom_ref_max=rmax,
            use_catalog_reference=use_catalog_reference,
        )
        extracted_with_pos.append((gmatch.start(), item))
        seen_keys.add(canonical_key)
        seen_keys.add(slug)

    extracted_with_pos.sort(key=lambda pair: pair[0])
    return [item for _, item in extracted_with_pos]


def _normalize_biomarker_list(
    raw_list: List[Any],
    use_catalog_reference: bool = False,
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        raw_name = str(
            item.get("name")
            or item.get("nome_exame")
            or item.get("analito")
            or item.get("biomarker")
            or item.get("code")
            or item.get("codigo_loinc")
            or "Biomarcador"
        )
        raw_val = (
            item.get("value")
            if item.get("value") is not None
            else item.get("valor_numerico", item.get("result", item.get("resultado")))
        )
        val = _parse_br_float(str(raw_val)) if raw_val is not None else None
        if val is None:
            continue

        entry = dict(_lookup_catalog_entry(raw_name))
        if item.get("code") or item.get("codigo_loinc"):
            entry["codigo_loinc"] = str(item.get("code") or item.get("codigo_loinc"))
        rmin = (
            _parse_br_float(str(item.get("reference_min")))
            if item.get("reference_min") is not None
            else _parse_br_float(str(item.get("faixa_referencia_min")))
            if item.get("faixa_referencia_min") is not None
            else None
        )
        rmax = (
            _parse_br_float(str(item.get("reference_max")))
            if item.get("reference_max") is not None
            else _parse_br_float(str(item.get("faixa_referencia_max")))
            if item.get("faixa_referencia_max") is not None
            else None
        )
        custom_unit = item.get("unit") or item.get("unidade")
        built = _build_biomarker_item(
            entry,
            val,
            custom_unit=custom_unit,
            custom_ref_min=rmin,
            custom_ref_max=rmax,
            use_catalog_reference=use_catalog_reference,
        )
        if item.get("status"):
            built["status"] = str(item["status"]).upper()
        normalized.append(built)
    return normalized


def _extract_pdf_streams_fallback(raw_bytes: bytes) -> str:
    """Extrator de contingência para streams PDF (com ou sem FlateDecode) caso pypdf retorne vazio."""
    chunks: List[str] = []
    for smatch in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw_bytes, flags=re.DOTALL):
        stream_data = smatch.group(1)
        for candidate in (stream_data,):
            decoded = candidate
            try:
                decoded = zlib.decompress(candidate)
            except Exception:
                pass
            # Extrai literais de texto entre parênteses ( ... ) em operadores PDF Tj / TJ
            for lit in re.finditer(rb"\(([^()\\]*(?:\\.[^()\\]*)*)\)", decoded):
                raw_lit = lit.group(1)
                raw_lit = (
                    raw_lit.replace(rb"\n", b"\n")
                    .replace(rb"\r", b"\r")
                    .replace(rb"\(", b"(")
                    .replace(rb"\)", b")")
                    .replace(rb"\\", b"\\")
                )
                chunks.append(raw_lit.decode("latin-1", errors="ignore"))
    return "\n".join(chunks).strip()


def _extract_text_from_bytes(raw_bytes: bytes, filename: str = "") -> str:
    """Extrai texto real de bytes PDF (via pypdf.PdfReader) ou CSV/texto plano."""
    if not raw_bytes:
        return ""
    is_pdf = b"%PDF" in raw_bytes[:1024] or filename.lower().endswith(".pdf")
    if is_pdf:
        extracted_pages: List[str] = []
        try:
            from pypdf import PdfReader

            pdf_start = raw_bytes.find(b"%PDF")
            pdf_bytes = raw_bytes[pdf_start:] if pdf_start > 0 else raw_bytes
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                page_txt = page.extract_text() or ""
                if page_txt.strip():
                    extracted_pages.append(page_txt)
        except Exception as exc:
            logger.warning("Aviso ao ler PDF via pypdf (%s): %s", filename or "bytes", exc)

        full_pdf_text = "\n".join(extracted_pages).strip()
        if full_pdf_text:
            return full_pdf_text

        stream_text = _extract_pdf_streams_fallback(raw_bytes)
        if stream_text:
            return stream_text

    return raw_bytes.decode("utf-8", errors="ignore")


def _extract_multipart_files_raw(raw_body: bytes, content_type: str) -> List[Tuple[str, bytes]]:
    """Extrai arquivos de um corpo multipart/form-data bruto caso request.form() não seja usado."""
    files: List[Tuple[str, bytes]] = []
    bmatch = re.search(r"boundary=([^;\s]+)", content_type, flags=re.IGNORECASE)
    if not bmatch:
        return files
    boundary = bmatch.group(1).strip('"').encode("ascii", errors="ignore")
    parts = raw_body.split(b"--" + boundary)
    for part in parts[1:]:
        if part.startswith(b"--") or not part.strip():
            continue
        sep = b"\r\n\r\n" if b"\r\n\r\n" in part else b"\n\n"
        if sep not in part:
            continue
        header_bytes, content = part.split(sep, 1)
        if content.endswith(b"\r\n"):
            content = content[:-2]
        elif content.endswith(b"\n"):
            content = content[:-1]
        header_str = header_bytes.decode("latin-1", errors="ignore")
        fn_match = re.search(r'filename="([^"]*)"', header_str, flags=re.IGNORECASE)
        fname = fn_match.group(1) if fn_match else ""
        files.append((fname, content))
    return files


@router.get(
    "/api/conhecimento/{analito}",
    summary="Consultar base de conhecimento clínico e relação causal com wearables para um analito",
)
async def obter_conhecimento_analito(analito: str):
    entry = _lookup_catalog_entry(analito)
    return {
        "status": "success",
        "analito": entry["analito"],
        "name": entry["name"],
        "nome_exame": entry["nome_exame"],
        "code": entry["codigo_loinc"],
        "codigo_loinc": entry["codigo_loinc"],
        "unit": entry["unit"],
        "unidade": entry["unidade"],
        "reference_min": entry["reference_min"],
        "reference_max": entry["reference_max"],
        "reference_range": entry["reference_range"],
        "faixa_referencia": entry["faixa_referencia"],
        "description": entry["description"],
        "resumo_exame": entry["resumo_exame"],
        "clinical_significance": entry["clinical_significance"],
        "causal_relationship": entry["causal_relationship"],
        "causal_relationship_wearables": entry["causal_relationship"],
        "causal_target_id": entry.get("causal_target_id"),
        "faixas_5_niveis": entry.get("faixas_5_niveis", {}),
    }


def _extract_lab_name_from_text(raw_text: str, default_lab: Optional[str] = None) -> Optional[str]:
    """Extrai o nome do laboratório do cabeçalho do PDF (ex: Laboratório, Lab., Fleury, Dasa, Sabin, Einstein...). Retorna None se ausente."""
    if not raw_text or not raw_text.strip():
        return default_lab

    # 1. Rótulo explícito 'Laboratório: ...'
    explicit_lab = re.search(
        r"(?:^|\n)\s*Laborat[oó]rio\s*[:\-]\s*([^\n\r|]+)",
        raw_text,
        flags=re.IGNORECASE,
    )
    if explicit_lab:
        candidate = explicit_lab.group(1).strip()
        if candidate:
            return candidate

    # 2. Linha contendo 'Laboratório', 'Lab.' ou redes laboratoriais brasileiras conhecidas
    known_lab = re.search(
        r"(?:^|\n)\s*([^\n\r|]*?\b(?:Laborat[oó]rio|Lab\.|Fleury|Dasa|Lavoisier|Sabin|Einstein|Delboni|Hermes\s+Pardini|S[eé]rgio\s+Franco|A\+\s*Medicina|CientificaLab|Diagn[oó]sticos\s+da\s+Am[eé]rica)\b[^\n\r|]*)",
        raw_text,
        flags=re.IGNORECASE,
    )
    if known_lab:
        candidate = known_lab.group(1).strip(" -:|")
        if candidate:
            return candidate

    return default_lab


def _extract_collection_date_from_text(raw_text: str, default_date: Optional[str] = None) -> Optional[str]:
    """Extrai a data de coleta/exame do texto do PDF com suporte amplo a formatos brasileiros e ISO. Retorna None se ausente."""
    if not raw_text or not raw_text.strip():
        return default_date

    # 1. Rótulos explícitos (Data da coleta, Coleta, Data, Emissão, Liberado em, Realizado em)
    labeled_date = re.search(
        r"(?:Data\s+d[aeo]\s+Coleta|Data\s+d[eo]\s+Exame|Coleta|Emiss[aã]o|Liberado\s+em|Realizado\s+em|Data)\s*[:\-]?\s*"
        r"(\d{2}/\d{2}/\d{2,4}|\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})",
        raw_text,
        flags=re.IGNORECASE,
    )
    if labeled_date:
        return labeled_date.group(1).strip()

    # 2. Data avulsa no documento (excluindo datas de nascimento quando precedidas por 'Nascimento')
    for dmatch in re.finditer(r"\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})\b", raw_text):
        prefix = raw_text[max(0, dmatch.start() - 25) : dmatch.start()].lower()
        if "nasc" in prefix or "dn" in prefix:
            continue
        return dmatch.group(1).strip()

    return default_date


@router.post(
    "/api/extrair",
    summary="Extrair biomarcadores estruturados de laudo laboratorial (PDF, CSV, texto ou JSON)",
)
async def extrair_exames_endpoint(request: Request):
    content_type = (request.headers.get("content-type") or "").lower()
    extracted: List[Dict[str, Any]] = []
    raw_text = ""
    raw_file_bytes = b""
    patient_name: Optional[str] = None
    exam_date: Optional[str] = None
    lab_name: Optional[str] = None
    explicit_date_provided = False
    explicit_lab_provided = False
    has_real_input = False

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict):
            if body.get("patient_name") or body.get("paciente_nome"):
                patient_name = str(body.get("patient_name") or body.get("paciente_nome"))
            if body.get("date") or body.get("data_exame") or body.get("collection_date") or body.get("data_coleta"):
                exam_date = str(
                    body.get("collection_date")
                    or body.get("data_coleta")
                    or body.get("date")
                    or body.get("data_exame")
                )
                explicit_date_provided = True
            if body.get("laboratory") or body.get("laboratorio"):
                lab_name = str(body.get("laboratory") or body.get("laboratorio"))
                explicit_lab_provided = True

            # 1. Suporte a PDF/arquivo em Base64 no JSON (pdf_base64 / file_base64 / base64)
            b64_str = body.get("pdf_base64") or body.get("file_base64") or body.get("base64")
            if isinstance(b64_str, str) and b64_str.strip():
                has_real_input = True
                clean_b64 = b64_str.split(",", 1)[-1].strip()
                try:
                    decoded_bytes = base64.b64decode(clean_b64)
                    raw_file_bytes += decoded_bytes
                    raw_text += "\n" + _extract_text_from_bytes(decoded_bytes, "upload.pdf")
                except Exception as exc:
                    logger.warning("Falha ao decodificar base64 em /api/extrair: %s", exc)

            # 2. Lista pré-estruturada de biomarcadores
            raw_list = body.get("biomarkers") or body.get("exames") or body.get("lab_results") or body.get("results")
            if isinstance(raw_list, list) and len(raw_list) > 0:
                has_real_input = True
                extracted.extend(_normalize_biomarker_list(raw_list, use_catalog_reference=False))

            # 3. Texto do laudo (text / raw_text / content / texto)
            txt_field = (
                body.get("text")
                or body.get("raw_text")
                or body.get("content")
                or body.get("texto")
                or ""
            )
            if isinstance(txt_field, str) and txt_field.strip():
                has_real_input = True
                raw_text += "\n" + txt_field

            # 4. Chaves diretas de analitos no JSON
            direct_items = []
            reserved = {
                "text", "content", "raw_text", "texto", "pdf_base64", "file_base64", "base64",
                "biomarkers", "exames", "lab_results", "results", "patient_id", "patient_name",
                "paciente_nome", "date", "data_exame", "collection_date", "data_coleta",
                "laboratory", "laboratorio",
            }
            for k, v in body.items():
                if k in reserved:
                    continue
                if isinstance(v, (int, float)):
                    direct_items.append({"name": k, "value": float(v)})
            if direct_items:
                has_real_input = True
                extracted.extend(_normalize_biomarker_list(direct_items, use_catalog_reference=False))
        elif isinstance(body, list) and len(body) > 0:
            has_real_input = True
            extracted.extend(_normalize_biomarker_list(body, use_catalog_reference=False))
    else:
        # Multipart file upload (qualquer nome de campo: file, arquivo, pdf, document, etc.) ou corpo bruto
        form_parsed = False
        try:
            form = await request.form()
            form_parsed = True
            for key, item in form.multi_items():
                if hasattr(item, "read"):
                    file_bytes = await item.read()
                    if file_bytes:
                        has_real_input = True
                        raw_file_bytes += file_bytes
                        fname = getattr(item, "filename", "") or key
                        raw_text += "\n" + _extract_text_from_bytes(file_bytes, fname)
                elif isinstance(item, (bytes, bytearray)) and item:
                    has_real_input = True
                    raw_file_bytes += bytes(item)
                    raw_text += "\n" + _extract_text_from_bytes(bytes(item), key)
                elif isinstance(item, str) and item.strip():
                    if key.lower() in {"motor", "mode", "patient_id"}:
                        continue
                    has_real_input = True
                    raw_text += "\n" + item
        except Exception as exc:
            logger.debug("Fallback para leitura bruta do body em /api/extrair: %s", exc)

        if not form_parsed or (not has_real_input):
            raw_body = await request.body()
            if raw_body:
                has_real_input = True
                if "multipart/form-data" in content_type:
                    for fname, fbytes in _extract_multipart_files_raw(raw_body, content_type):
                        raw_file_bytes += fbytes
                        raw_text += "\n" + _extract_text_from_bytes(fbytes, fname)
                else:
                    raw_file_bytes += raw_body
                    raw_text += "\n" + _extract_text_from_bytes(raw_body)

    raw_text = raw_text.strip()
    if raw_text:
        pac_match = re.search(r"Paciente\s*:\s*([^\n\r|]+)", raw_text, flags=re.IGNORECASE)
        if pac_match:
            patient_name = pac_match.group(1).strip()
        if not explicit_date_provided:
            exam_date = _extract_collection_date_from_text(raw_text, None)
        if not explicit_lab_provided:
            lab_name = _extract_lab_name_from_text(raw_text, None)

        text_biomarkers = _extract_biomarkers_from_text(raw_text, use_catalog_reference=False)
        existing_codes = {b["code"] for b in extracted}
        for tb in text_biomarkers:
            if tb["code"] not in existing_codes:
                extracted.append(tb)
                existing_codes.add(tb["code"])

    # APENAS usa os 5 exames de demonstração quando a requisição NÃO enviou arquivo nem texto nem biomarcadores
    if not has_real_input and not extracted:
        extracted = [
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["ferritina"], 22.4, use_catalog_reference=False),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["hemoglobina"], 12.6, use_catalog_reference=False),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["glicose"], 94.0, use_catalog_reference=False),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["pcr"], 2.1, use_catalog_reference=False),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["vitamina_d"], 26.5, use_catalog_reference=False),
        ]

    hash_source = raw_file_bytes if raw_file_bytes else raw_text.encode("utf-8", errors="ignore")
    document_hash = hashlib.sha256(hash_source).hexdigest() if hash_source else None
    text_preview = raw_text[:500] if raw_text else ""

    return {
        "status": "success",
        "motor": "open_health_pdf_extractor_v3",
        "total_extracted": len(extracted),
        "document_hash": document_hash,
        "extracted_text_preview": text_preview,
        "laboratory": lab_name,
        "laboratorio": lab_name,
        "collection_date": exam_date,
        "data_coleta": exam_date,
        "cabecalho": {
            "paciente_nome": patient_name,
            "data_exame": exam_date,
            "data_coleta": exam_date,
            "collection_date": exam_date,
            "laboratorio": lab_name,
            "laboratory": lab_name,
            "document_hash": document_hash,
        },
        "biomarkers": extracted,
        "exames": extracted,
    }


@router.post(
    "/api/exams/interpret",
    summary="Interpretar exames laboratoriais cruzando com o Motor de Inferência Causal e métricas do wearable",
)
@router.post(
    "/exams/interpret",
    summary="Alias para interpretação clínica integrada de exames laboratoriais e wearables",
)
async def interpret_exams_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {"biomarkers": body if isinstance(body, list) else []}

    patient_id = str(
        body.get("patient_id")
        or body.get("user_id")
        or "e4a7a8d2-1b1e-4c7b-8b9a-112233445566"
    ).strip()

    # 1. Extrai/normaliza biomarcadores do payload (lista, texto ou campos diretos)
    biomarkers: List[Dict[str, Any]] = []
    raw_list = body.get("biomarkers") or body.get("exames") or body.get("lab_results") or body.get("results")
    if isinstance(raw_list, list):
        biomarkers.extend(_normalize_biomarker_list(raw_list, use_catalog_reference=True))

    if body.get("valor_numerico") is not None or body.get("value") is not None:
        single_name = body.get("nome_exame") or body.get("name") or body.get("analito") or body.get("codigo_loinc") or "ferritina"
        single_val = body.get("valor_numerico") if body.get("valor_numerico") is not None else body.get("value")
        biomarkers.extend(_normalize_biomarker_list([{"name": single_name, "value": single_val}], use_catalog_reference=True))

    if body.get("ferritin_ng_ml") is not None:
        biomarkers.extend(_normalize_biomarker_list([{"name": "ferritina", "value": body["ferritin_ng_ml"]}], use_catalog_reference=True))

    raw_text = str(body.get("text") or body.get("content") or body.get("raw_text") or "")
    if raw_text:
        existing_codes = {b["code"] for b in biomarkers}
        for tb in _extract_biomarkers_from_text(raw_text, use_catalog_reference=True):
            if tb["code"] not in existing_codes:
                biomarkers.append(tb)

    if not biomarkers:
        biomarkers = [
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["ferritina"], 24.0, use_catalog_reference=True),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["hemoglobina"], 12.4, use_catalog_reference=True),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["glicose"], 96.0, use_catalog_reference=True),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["pcr"], 1.8, use_catalog_reference=True),
        ]

    # 2. Obtém contexto de wearable (do payload ou do banco para o patient_id)
    wearable_ctx: Dict[str, Any] = {}
    nested_wearable = body.get("wearable_context") or body.get("wearable_metrics") or body.get("wearables")
    if isinstance(nested_wearable, dict):
        wearable_ctx.update(nested_wearable)

    for wk in (
        "steps",
        "resting_hr_bpm",
        "avg_hr_day_bpm",
        "hrv_rmssd_ms",
        "spo2_avg_pct",
        "sleep_duration_hours",
        "sleep_stage_deep_pct",
        "waso_min",
        "screen_time_min",
        "caffeine_mg",
        "alcohol_units",
    ):
        if body.get(wk) is not None:
            wearable_ctx[wk] = body[wk]

    stmt = (
        select(WearableDailyMetric)
        .where(WearableDailyMetric.patient_id == patient_id)
        .order_by(WearableDailyMetric.date.desc())
        .limit(14)
    )
    db_rows = list(reversed((await db.execute(stmt)).scalars().all()))

    base_today = {
        "date": date.today(),
        "steps": 4800,
        "resting_hr_bpm": 74.0,
        "avg_hr_day_bpm": 95.0,
        "hrv_rmssd_ms": 34.0,
        "spo2_avg_pct": 97.0,
        "sleep_duration_hours": 6.8,
        "sleep_stage_deep_pct": 0.14,
        "waso_min": 20.0,
        "screen_time_min": 50.0,
        "caffeine_mg": 25.0,
        "alcohol_units": 0.0,
    }
    if db_rows:
        latest = db_rows[-1]
        for k in base_today:
            val = getattr(latest, k, None)
            if val is not None:
                base_today[k] = val

    for k, v in wearable_ctx.items():
        if v is not None:
            base_today[k] = v

    if isinstance(base_today.get("sleep_stage_deep_pct"), (int, float)) and base_today["sleep_stage_deep_pct"] > 1.0:
        base_today["sleep_stage_deep_pct"] = round(float(base_today["sleep_stage_deep_pct"]) / 100.0, 4)

    history_dicts = [
        {
            "date": r.date,
            "steps": r.steps,
            "resting_hr_bpm": r.resting_hr_bpm,
            "avg_hr_day_bpm": r.avg_hr_day_bpm,
            "hrv_rmssd_ms": r.hrv_rmssd_ms,
            "sleep_duration_hours": r.sleep_duration_hours,
            "sleep_stage_deep_pct": r.sleep_stage_deep_pct,
            "waso_min": r.waso_min,
            "screen_time_min": r.screen_time_min,
            "caffeine_mg": r.caffeine_mg,
            "alcohol_units": r.alcohol_units,
        }
        for r in db_rows[:-1]
    ] + [base_today]

    # 3. Identifica Ferritina para ancorar o Alvo 4 no Motor de Inferência Causal
    ferritin_bm = next(
        (b for b in biomarkers if b["analito"] == "ferritina" or b["code"] == "2276-4"),
        None,
    )
    engine_to_use = causal_engine
    if ferritin_bm is not None:
        val_f = float(ferritin_bm["value"])

        class _InlineExamFHIRClient:
            async def get_biomarker_evolution(self, pid: str, loinc_code: str = "2276-4", limit: int = 10):
                return FHIRLabEvolutionResponse(
                    paciente_id=pid,
                    codigo_loinc=loinc_code,
                    nome_exame="Ferritina Sérica (Exame Interpretado)",
                    unidade="ng/mL",
                    serie_temporal=[
                        FHIRObservationPoint(
                            data=date.today().isoformat(),
                            valor_numerico=val_f,
                            status_classificacao="AMARELO" if val_f < 30.0 else "VERDE",
                        )
                    ],
                )

        engine_to_use = CausalInferenceEngine(
            fhir_client=_InlineExamFHIRClient(),
        )

    causal_results = await engine_to_use.evaluate_all_targets(
        patient_id,
        base_today,
        history_dicts,
    )

    # 4. Constrói achados (findings), incongruências causais e classificação de risco
    findings: List[Dict[str, Any]] = []
    incongruencies: List[str] = []
    abnormal_count = 0
    critical_count = 0

    for bm in biomarkers:
        entry = _lookup_catalog_entry(bm["analito"])
        status_label = bm["status"]
        if status_label != "NORMAL":
            abnormal_count += 1
            if bm.get("status_cor") == "VERMELHO":
                critical_count += 1

        if status_label == "LOW":
            interp = f"{bm['name']} abaixo da referência ({bm['value']} {bm['unit']}; ref {bm['reference_range']}). {entry['clinical_significance']}"
        elif status_label == "HIGH":
            interp = f"{bm['name']} acima da referência ({bm['value']} {bm['unit']}; ref {bm['reference_range']}). {entry['clinical_significance']}"
        else:
            interp = f"{bm['name']} dentro da faixa de referência ({bm['value']} {bm['unit']}; ref {bm['reference_range']})."

        findings.append({
            "biomarker": bm["name"],
            "code": bm["code"],
            "value": bm["value"],
            "unit": bm["unit"],
            "reference_range": bm["reference_range"],
            "status": status_label,
            "interpretation": interp,
            "causal_relationship": entry["causal_relationship"],
            "causal_target_id": bm.get("causal_target_id"),
        })

    for res in causal_results:
        if res.is_anomaly and res.is_confounded:
            incongruencies.append(
                f"[{res.title}] Sinal fisiológico alterado no wearable, porém explicado por confundidores "
                f"comportamentais ({', '.join(res.confounders_detected)}): {res.clinical_verdict}"
            )
        elif res.trigger_alert:
            abnormal_count += 1
            if res.alert_level in {"HIGH", "CRITICAL"}:
                critical_count += 1
            incongruencies.append(
                f"[{res.title}] Convergência clínica sem confundidor comportamental: {res.clinical_verdict}"
            )

    if ferritin_bm and ferritin_bm["status"] == "NORMAL" and float(base_today.get("avg_hr_day_bpm") or 0) > 92.0:
        incongruencies.append(
            f"Taquicardia diurna no wearable ({base_today['avg_hr_day_bpm']} bpm) com Ferritina normal "
            f"({ferritin_bm['value']} ng/mL): investigar causas não-ferroprivas (função tireoidiana/TSH, desidratação ou sobrecarga simpática)."
        )
    elif ferritin_bm and ferritin_bm["status"] == "LOW" and float(base_today.get("avg_hr_day_bpm") or 0) > 92.0:
        incongruencies.append(
            f"Correlação causal confirmada (Alvo 4): Ferritina baixa ({ferritin_bm['value']} ng/mL) explica "
            f"a elevação da FC média diurna ({base_today['avg_hr_day_bpm']} bpm) mesmo com baixo volume de passos ({base_today.get('steps')} passos)."
        )

    if not incongruencies:
        incongruencies.append(
            "Biomarcadores laboratoriais e telemetria contínua do wearable encontram-se fisiologicamente congruentes."
        )

    if critical_count >= 1 or abnormal_count >= 3:
        risk_level = "HIGH"
    elif abnormal_count >= 1:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    urgent_referral = bool(
        critical_count >= 1 or any(r.alert_level in {"HIGH", "CRITICAL"} and r.trigger_alert for r in causal_results)
    )

    summary_text = (
        f"Avaliação integrada de {len(biomarkers)} biomarcador(es) laboratorial(is) cruzada com telemetria "
        f"de wearable para o paciente {patient_id} (Risco: {risk_level}). "
        + (incongruencies[0] if incongruencies else "")
    )

    technical_notes = (
        "Inferência Causal em 3 Camadas (DAGs de Pearl + Backdoor Criterion): "
        "Alvo 1 (Sono N3 < 16% vs Passos/Álcool), Alvo 2 (RHR >= 72 bpm vs Tela/Cafeína), "
        "Alvo 3 (HRV RMSSD < 38 ms por 4 dias vs Sono/Álcool) e Alvo 4 (ICD Diurno + Ferritina LOINC 2276-4)."
    )

    return {
        "status": "success",
        "patient_id": patient_id,
        "risk_level": risk_level,
        "urgent_referral": urgent_referral,
        "summary": summary_text,
        "resumo_acessivel": summary_text,
        "findings": findings,
        "incongruencies": incongruencies,
        "technical_notes": technical_notes,
        "perguntas_para_o_medico": [
            "Meus sintomas e a frequência cardíaca medida pelo wearable podem estar relacionados aos níveis de ferritina/hemoglobina?",
            "Quais ajustes de estilo de vida ou suplementação são recomendados antes de repetir os exames laboratoriais?",
            "Existe necessidade de investigar marcadores inflamatórios ou tireoidianos adicionais diante da variação de HRV e FC de repouso?",
        ],
        "wearable_context_used": base_today,
        "causal_targets_evaluated": [r.model_dump() for r in causal_results],
    }
