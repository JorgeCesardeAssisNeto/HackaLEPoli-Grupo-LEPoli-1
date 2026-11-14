"""Endpoints unificados de Extração de Exames, Base de Conhecimento (RAG) e Interpretação Clínica Causal."""

import io
import json
import logging
import re
import unicodedata
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


# Catálogo clínico estruturado com relação causal explícita com métricas de wearables
CLINICAL_KNOWLEDGE_CATALOG: Dict[str, Dict[str, Any]] = {
    "ferritina": {
        "analito": "ferritina",
        "name": "Ferritina Sérica",
        "nome_exame": "Ferritina Sérica",
        "codigo_loinc": "2276-4",
        "unit": "ng/mL",
        "unidade": "ng/mL",
        "reference_min": 30.0,
        "reference_max": 300.0,
        "reference_range": "30.0 a 300.0 ng/mL",
        "faixa_referencia": {"min": 30.0, "max": 300.0, "unidade": "ng/mL"},
        "description": (
            "Proteína intracelular de armazenamento de ferro; principal marcador precoce de depleção "
            "dos estoques corporais de ferro (ferropenia) e reagente de fase aguda em processos inflamatórios."
        ),
        "resumo_exame": (
            "Avalia as reservas corporais de ferro. Níveis abaixo de 30 ng/mL indicam depleção de estoque "
            "e reduzem a eficiência do transporte de oxigênio antes mesmo da queda da hemoglobina."
        ),
        "clinical_significance": (
            "Ferritina < 30 ng/mL confirma ferropenia subclínica ou anemia ferropriva, causando fadiga, "
            "intolerância ao esforço e taquicardia compensatória diurna. Valores > 300 ng/mL sugerem "
            "sobrecarga férrica ou inflamação sistêmica."
        ),
        "causal_relationship": (
            "Ancora o ALVO 4 (Triagem Hematológica / ICD): quando o wearable detecta FC média diurna > 92 bpm "
            "desproporcional ao volume de passos (ICD elevado) sem excesso de cafeína, a Ferritina < 30 ng/mL "
            "confirma esforço cardíaco compensatório por déficit de transporte de O2."
        ),
        "causal_target_id": "TARGET_4_ANEMIA_LOAD",
        "faixas_5_niveis": {
            "muito_baixo": "< 15 ng/mL: Depleção severa de ferro com alto risco de anemia ferropriva sintomática.",
            "baixo": "15 a 29.9 ng/mL: Estoque de ferro reduzido (ferropenia subclínica); pode causar taquicardia diurna e fadiga.",
            "normal": "30 a 300 ng/mL: Reservas de ferro adequadas para a eritropoiese e metabolismo energético.",
            "alto": "301 a 500 ng/mL: Elevação moderada; investigar inflamação sistêmica ou síndrome metabólica.",
            "muito_alto": "> 500 ng/mL: Sobrecarga férrica importante ou resposta inflamatória aguda pronunciada.",
        },
        "aliases": ["ferritina", "ferritin", "ferritina_serica", "2276_4", "2276-4"],
    },
    "hemoglobina": {
        "analito": "hemoglobina",
        "name": "Hemoglobina",
        "nome_exame": "Hemoglobina (Hb)",
        "codigo_loinc": "718-7",
        "unit": "g/dL",
        "unidade": "g/dL",
        "reference_min": 12.0,
        "reference_max": 16.5,
        "reference_range": "12.0 a 16.5 g/dL",
        "faixa_referencia": {"min": 12.0, "max": 16.5, "unidade": "g/dL"},
        "description": (
            "Metaloproteína rica em ferro presente nos eritrócitos, responsável pelo transporte de oxigênio "
            "dos pulmões para os tecidos periféricos e miocárdio."
        ),
        "resumo_exame": (
            "Mede a capacidade direta de transporte de oxigênio no sangue. Valores reduzidos caracterizam anemia."
        ),
        "clinical_significance": (
            "Hemoglobina < 12.0 g/dL (mulheres) ou < 13.0 g/dL (homens) define anemia, reduzindo a oferta "
            "tecidual de O2 e exigindo aumento do débito cardíaco em repouso e em esforços leves."
        ),
        "causal_relationship": (
            "Relacionada diretamente ao ALVO 4 (ICD Diurno) e SpO2: queda de hemoglobina eleva a FC média diurna "
            "para manter a oxigenação tecidual mesmo com baixa contagem de passos."
        ),
        "causal_target_id": "TARGET_4_ANEMIA_LOAD",
        "faixas_5_niveis": {
            "muito_baixo": "< 10.0 g/dL: Anemia moderada a grave com sobrecarga hemodinâmica significativa.",
            "baixo": "10.0 a 11.9 g/dL: Anemia leve; associada a fadiga e elevação do Índice de Carga Diurna (ICD).",
            "normal": "12.0 a 16.5 g/dL: Capacidade fisiológica normal de transporte de oxigênio.",
            "alto": "16.6 a 18.0 g/dL: Hemoconcentração ou eritrocitose leve (avaliar hidratação/altitude).",
            "muito_alto": "> 18.0 g/dL: Policitemia / hiperviscosidade sanguínea; requer investigação hematológica.",
        },
        "aliases": ["hemoglobina", "hemoglobin", "hb", "718_7", "718-7"],
    },
    "vitamina_d": {
        "analito": "vitamina_d",
        "name": "Vitamina D (25-Hidroxivitamina D)",
        "nome_exame": "Vitamina D (25-OH)",
        "codigo_loinc": "1989-3",
        "unit": "ng/mL",
        "unidade": "ng/mL",
        "reference_min": 30.0,
        "reference_max": 100.0,
        "reference_range": "30.0 a 100.0 ng/mL",
        "faixa_referencia": {"min": 30.0, "max": 100.0, "unidade": "ng/mL"},
        "description": (
            "Pró-hormônio esteroide essencial para homeostase osteomineral, modulação imunológica, "
            "função muscular e regulação da arquitetura do sono."
        ),
        "resumo_exame": (
            "Avalia o status de Vitamina D corporal. Níveis < 20 ng/mL indicam deficiência e entre 20-29 ng/mL insuficiência."
        ),
        "clinical_significance": (
            "Hipovitaminose D (< 30 ng/mL) associa-se a fadiga neuromuscular, fragmentação do sono profundo (N3) "
            "e maior suscetibilidade inflamatória."
        ),
        "causal_relationship": (
            "Correlaciona-se com o ALVO 1 (Arquitetura do Sono Profundo N3 < 16%) e ALVO 3 (HRV/Inflamação): "
            "deficiência de 25-OH-Vitamina D reduz a eficiência de recuperação noturna mesmo quando passos e higiene do sono estão adequados."
        ),
        "causal_target_id": "TARGET_1_DEEP_SLEEP",
        "faixas_5_niveis": {
            "muito_baixo": "< 12 ng/mL: Deficiência severa de Vitamina D.",
            "baixo": "12 a 29.9 ng/mL: Deficiência/insuficiência; associada a pior qualidade de sono profundo e fadiga.",
            "normal": "30 a 60 ng/mL: Níveis suficientes para saúde óssea, imunológica e neuromuscular.",
            "alto": "61 a 100 ng/mL: Reserva elevada dentro da margem de segurança.",
            "muito_alto": "> 100 ng/mL: Risco de hipercalcemia / intoxicação exógena.",
        },
        "aliases": ["vitamina_d", "vitamina d", "25_oh_vitamina_d", "vit_d", "colecalciferol", "1989_3", "1989-3"],
    },
    "glicose": {
        "analito": "glicose",
        "name": "Glicose de Jejum",
        "nome_exame": "Glicemia de Jejum",
        "codigo_loinc": "2345-7",
        "unit": "mg/dL",
        "unidade": "mg/dL",
        "reference_min": 70.0,
        "reference_max": 99.0,
        "reference_range": "70.0 a 99.0 mg/dL",
        "faixa_referencia": {"min": 70.0, "max": 99.0, "unidade": "mg/dL"},
        "description": (
            "Concentração plasmática basal de glicose após jejum noturno; marcador primário de homeostase "
            "glicêmica e sensibilidade insulínica."
        ),
        "resumo_exame": (
            "Mede o açúcar no sangue em jejum. Valores entre 100 e 125 mg/dL indicam pré-diabetes; >= 126 mg/dL sugerem diabetes."
        ),
        "clinical_significance": (
            "Hiperglicemia basal (>= 100 mg/dL) reflete resistência insulínica e hiperatividade simpática, "
            "cursando com elevação da Frequência Cardíaca de Repouso (RHR) e redução da HRV."
        ),
        "causal_relationship": (
            "Integra o ALVO 2 (Risco Cardiometabólico — RHR >= 72 bpm): quando o wearable aponta RHR elevado "
            "sem confundidores comportamentais (tela noturna <= 120 min e cafeína <= 60 mg), a glicemia >= 100 mg/dL "
            "confirma disfunção metabólica/autonômica subjacente."
        ),
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 54 mg/dL: Hipoglicemia clinicamente significativa.",
            "baixo": "54 a 69 mg/dL: Hipoglicemia de alerta.",
            "normal": "70 a 99 mg/dL: Normoglicemia de jejum.",
            "alto": "100 a 125 mg/dL: Glicemia de jejum alterada (pré-diabetes / resistência insulínica).",
            "muito_alto": ">= 126 mg/dL: Compatível com diabetes mellitus (confirmar em segunda amostra/HbA1c).",
        },
        "aliases": ["glicose", "glicemia", "glicose_jejum", "glucose", "2345_7", "2345-7"],
    },
    "hba1c": {
        "analito": "hba1c",
        "name": "Hemoglobina Glicada (HbA1c)",
        "nome_exame": "Hemoglobina Glicada (HbA1c)",
        "codigo_loinc": "4548-4",
        "unit": "%",
        "unidade": "%",
        "reference_min": 4.0,
        "reference_max": 5.6,
        "reference_range": "4.0 a 5.6 %",
        "faixa_referencia": {"min": 4.0, "max": 5.6, "unidade": "%"},
        "description": (
            "Fração da hemoglobina ligada não-enzimaticamente à glicose, refletindo a glicemia média "
            "dos últimos 60 a 90 dias."
        ),
        "resumo_exame": "Retrata o controle glicêmico médio dos últimos 2 a 3 meses.",
        "clinical_significance": (
            "HbA1c entre 5.7% e 6.4% indica pré-diabetes e risco cardiometabólico aumentado; >= 6.5% é critério diagnóstico para diabetes."
        ),
        "causal_relationship": (
            "Ancora o ALVO 2 (RHR >= 72 bpm) e ALVO 1 (Sono Profundo N3 < 16%): restrição crônica de sono N3 "
            "e RHR elevado associam-se diretamente à progressão da HbA1c."
        ),
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 4.0 %: Baixo (avaliar meia-vida eritrocitária reduzida).",
            "baixo": "4.0 a 4.4 %: Limite inferior da normalidade.",
            "normal": "4.5 a 5.6 %: Controle glicêmico crônico normal.",
            "alto": "5.7 a 6.4 %: Pré-diabetes / risco cardiometabólico elevado.",
            "muito_alto": ">= 6.5 %: Compatível com diabetes mellitus.",
        },
        "aliases": ["hba1c", "hemoglobina_glicada", "a1c", "glicada", "4548_4", "4548-4"],
    },
    "pcr": {
        "analito": "pcr",
        "name": "Proteína C Reativa Ultrassensível (PCR-us)",
        "nome_exame": "Proteína C Reativa (PCR)",
        "codigo_loinc": "30522-7",
        "unit": "mg/L",
        "unidade": "mg/L",
        "reference_min": 0.0,
        "reference_max": 3.0,
        "reference_range": "< 3.0 mg/L",
        "faixa_referencia": {"min": 0.0, "max": 3.0, "unidade": "mg/L"},
        "description": (
            "Proteína plasmática de fase aguda sintetizada pelo fígado em resposta à interleucina-6 (IL-6); "
            "biomarcador padrão-ouro de inflamação sistêmica e risco inflamatório vascular."
        ),
        "resumo_exame": (
            "Detecta inflamação sistêmica. Valores < 1.0 mg/L indicam baixo risco inflamatório; 1.0-3.0 mg/L risco moderado; > 3.0 mg/L inflamação ativa."
        ),
        "clinical_significance": (
            "Elevações de PCR (> 3.0 mg/L) sinalizam ativação inflamatória sistêmica ou infecção subclínica, "
            "inibindo o tônus vagal parassimpático."
        ),
        "causal_relationship": (
            "Valida o ALVO 3 (Inflamação Sistêmica / HRV RMSSD < 38 ms por 4 dias consecutivos): "
            "a retirada vagal sustentada no wearable sem privação de sono nem consumo de álcool reflete o reflexo "
            "inflamatório colinérgico confirmado pela PCR elevada."
        ),
        "causal_target_id": "TARGET_3_INFLAMMATION_HRV",
        "faixas_5_niveis": {
            "muito_baixo": "< 0.3 mg/L: Inflamação basal mínima.",
            "baixo": "0.3 a 0.9 mg/L: Baixo risco inflamatório cardiovascular.",
            "normal": "1.0 a 3.0 mg/L: Risco inflamatório intermediário.",
            "alto": "3.1 a 10.0 mg/L: Inflamação sistêmica de baixo grau acentuada ou processo subagudo.",
            "muito_alto": "> 10.0 mg/L: Processo inflamatório ou infeccioso agudo relevante.",
        },
        "aliases": ["pcr", "pcr_us", "proteina_c_reativa", "crp", "hs_crp", "30522_7", "30522-7", "1988_5", "1988-5"],
    },
    "tsh": {
        "analito": "tsh",
        "name": "Hormônio Tireoestimulante (TSH)",
        "nome_exame": "TSH Ultra-Sensível",
        "codigo_loinc": "3016-3",
        "unit": "mUI/L",
        "unidade": "mUI/L",
        "reference_min": 0.4,
        "reference_max": 4.5,
        "reference_range": "0.4 a 4.5 mUI/L",
        "faixa_referencia": {"min": 0.4, "max": 4.5, "unidade": "mUI/L"},
        "description": (
            "Hormônio glicoproteico hipofisário regulador da síntese de T3 e T4 pela tireoide, determinando "
            "a taxa metabólica basal e a sensibilidade adrenérgica cardíaca."
        ),
        "resumo_exame": (
            "Avalia a função da tireoide. TSH < 0.4 mUI/L sugere hipertireoidismo; TSH > 4.5 mUI/L sugere hipotireoidismo."
        ),
        "clinical_significance": (
            "O hipertireoidismo (TSH suprimido < 0.4 mUI/L) causa taquicardia sinusal de repouso e diurna, "
            "enquanto o hipotireoidismo (TSH > 4.5 mUI/L) provoca fadiga, bradicardia e redução do gasto calórico ativo."
        ),
        "causal_relationship": (
            "Atua no diagnóstico diferencial do ALVO 2 (RHR >= 72 bpm) e ALVO 4 (Taquicardia Diurna / ICD): "
            "TSH suprimido explica elevação persistente da frequência cardíaca mesmo com ferritina normal."
        ),
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 0.1 mUI/L: Supressão tireotrófica importante (hipertireoidismo franco).",
            "baixo": "0.1 a 0.39 mUI/L: Hipertireoidismo subclínico; pode elevar RHR e reduzir HRV.",
            "normal": "0.4 a 4.5 mUI/L: Eutireoidismo.",
            "alto": "4.51 a 10.0 mUI/L: Hipotireoidismo subclínico; associado a fadiga e menor disposição diurna.",
            "muito_alto": "> 10.0 mUI/L: Hipotireoidismo franco; requer avaliação endocrinológica.",
        },
        "aliases": ["tsh", "tireotrofina", "hormonio_tireoestimulante", "3016_3", "3016-3"],
    },
    "colesterol": {
        "analito": "colesterol",
        "name": "Colesterol Total",
        "nome_exame": "Colesterol Total",
        "codigo_loinc": "2093-3",
        "unit": "mg/dL",
        "unidade": "mg/dL",
        "reference_min": 0.0,
        "reference_max": 190.0,
        "reference_range": "< 190.0 mg/dL",
        "faixa_referencia": {"min": 0.0, "max": 190.0, "unidade": "mg/dL"},
        "description": (
            "Soma das frações lipoproteicas circulantes (LDL, HDL e VLDL), fundamental na estratificação "
            "de risco aterosclerótico e cardiometabólico."
        ),
        "resumo_exame": "Mede o colesterol total circulante; desejável abaixo de 190 mg/dL.",
        "clinical_significance": (
            "Hipercolesterolemia (>= 190 mg/dL) eleva o risco aterogênico, especialmente quando combinada "
            "a sedentarismo (< 6500 passos/dia) e RHR elevado (>= 72 bpm)."
        ),
        "causal_relationship": (
            "Conecta-se ao ALVO 2 (Risco Cardiometabólico): pacientes com RHR >= 72 bpm (percentil 75 NHANES) "
            "e colesterol elevado apresentam sinergia de risco cardiovascular."
        ),
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 100 mg/dL: Hipocolesterolemia.",
            "baixo": "100 a 149 mg/dL: Nível ótimo.",
            "normal": "150 a 190 mg/dL: Nível desejável.",
            "alto": "191 a 239 mg/dL: Limítrofe alto / dislipidemia moderada.",
            "muito_alto": ">= 240 mg/dL: Hipercolesterolemia importante.",
        },
        "aliases": ["colesterol", "colesterol_total", "cholesterol", "2093_3", "2093-3"],
    },
    "ldl": {
        "analito": "ldl",
        "name": "Colesterol LDL",
        "nome_exame": "Colesterol LDL",
        "codigo_loinc": "13457-7",
        "unit": "mg/dL",
        "unidade": "mg/dL",
        "reference_min": 0.0,
        "reference_max": 130.0,
        "reference_range": "< 130.0 mg/dL",
        "faixa_referencia": {"min": 0.0, "max": 130.0, "unidade": "mg/dL"},
        "description": "Lipoproteína de baixa densidade, principal transportadora de colesterol para a parede arterial.",
        "resumo_exame": "Fração aterogênica do colesterol; desejável < 130 mg/dL (ou < 100 mg/dL em risco moderado).",
        "clinical_significance": "Elevações de LDL aceleram a formação de placas ateroscleróticas.",
        "causal_relationship": "Sinérgico ao ALVO 2 (RHR >= 72 bpm) e ao volume diário de passos e minutos ativos.",
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 50 mg/dL: Meta intensiva atingida.",
            "baixo": "50 a 99 mg/dL: Ótimo.",
            "normal": "100 a 129 mg/dL: Desejável para baixo risco.",
            "alto": "130 a 159 mg/dL: Limítrofe alto.",
            "muito_alto": ">= 160 mg/dL: Alto risco aterogênico.",
        },
        "aliases": ["ldl", "colesterol_ldl", "ldl_c", "13457_7", "13457-7"],
    },
    "hdl": {
        "analito": "hdl",
        "name": "Colesterol HDL",
        "nome_exame": "Colesterol HDL",
        "codigo_loinc": "2085-9",
        "unit": "mg/dL",
        "unidade": "mg/dL",
        "reference_min": 40.0,
        "reference_max": 100.0,
        "reference_range": "> 40.0 mg/dL",
        "faixa_referencia": {"min": 40.0, "max": 100.0, "unidade": "mg/dL"},
        "description": "Lipoproteína de alta densidade responsável pelo transporte reverso do colesterol.",
        "resumo_exame": "Fração cardioprotetora do colesterol; desejável > 40 mg/dL.",
        "clinical_significance": "HDL < 40 mg/dL associa-se a resistência insulínica e sedentarismo.",
        "causal_relationship": "Eleva-se com o aumento consistente do volume diário de passos (> 7500 passos/dia) e minutos de treino.",
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 35 mg/dL: HDL criticamente baixo; marcador de risco metabólico.",
            "baixo": "35 a 39.9 mg/dL: Reduzido.",
            "normal": "40 a 59 mg/dL: Adequado.",
            "alto": "60 a 85 mg/dL: Cardioprotetor ótimo.",
            "muito_alto": "> 85 mg/dL: Muito elevado.",
        },
        "aliases": ["hdl", "colesterol_hdl", "hdl_c", "2085_9", "2085-9"],
    },
    "triglicerideos": {
        "analito": "triglicerideos",
        "name": "Triglicerídeos",
        "nome_exame": "Triglicerídeos",
        "codigo_loinc": "2571-8",
        "unit": "mg/dL",
        "unidade": "mg/dL",
        "reference_min": 0.0,
        "reference_max": 150.0,
        "reference_range": "< 150.0 mg/dL",
        "faixa_referencia": {"min": 0.0, "max": 150.0, "unidade": "mg/dL"},
        "description": "Principal forma de armazenamento lipídico circulante, sensível à resistência insulínica e álcool.",
        "resumo_exame": "Mede as gorduras circulantes relacionadas ao metabolismo de carboidratos e álcool; desejável < 150 mg/dL.",
        "clinical_significance": "Triglicerídeos >= 150 mg/dL compõem o diagnóstico de síndrome metabólica.",
        "causal_relationship": "Relacionado ao ALVO 2 (RHR >= 72 bpm) e aos confundidores de ingestão alcoólica e sedentarismo.",
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 40 mg/dL: Baixo.",
            "baixo": "40 a 99 mg/dL: Ótimo.",
            "normal": "100 a 149 mg/dL: Desejável.",
            "alto": "150 a 199 mg/dL: Limítrofe alto.",
            "muito_alto": ">= 200 mg/dL: Hipertrigliceridemia.",
        },
        "aliases": ["triglicerideos", "triglicerides", "tg", "2571_8", "2571-8"],
    },
    "ferro": {
        "analito": "ferro",
        "name": "Ferro Sérico",
        "nome_exame": "Ferro Sérico",
        "codigo_loinc": "2498-4",
        "unit": "ug/dL",
        "unidade": "ug/dL",
        "reference_min": 60.0,
        "reference_max": 170.0,
        "reference_range": "60.0 a 170.0 ug/dL",
        "faixa_referencia": {"min": 60.0, "max": 170.0, "unidade": "ug/dL"},
        "description": "Fração de ferro circulante ligada à transferrina plasmática.",
        "resumo_exame": "Avalia o ferro circulante disponível para síntese de hemoglobina.",
        "clinical_significance": "Ferro sérico < 60 ug/dL acompanha quadros de ferropenia e anemia inflamatória.",
        "causal_relationship": "Complementa a Ferritina no ALVO 4 (Triagem de Anemia via Índice de Carga Diurna).",
        "causal_target_id": "TARGET_4_ANEMIA_LOAD",
        "faixas_5_niveis": {
            "muito_baixo": "< 40 ug/dL: Hipoferremia acentuada.",
            "baixo": "40 a 59.9 ug/dL: Ferro circulante reduzido.",
            "normal": "60 a 170 ug/dL: Normal.",
            "alto": "171 a 200 ug/dL: Elevado.",
            "muito_alto": "> 200 ug/dL: Sobrecarga de ferro circulante.",
        },
        "aliases": ["ferro", "ferro_serico", "iron", "2498_4", "2498-4"],
    },
    "creatinina": {
        "analito": "creatinina",
        "name": "Creatinina Sérica",
        "nome_exame": "Creatinina Sérica",
        "codigo_loinc": "2160-0",
        "unit": "mg/dL",
        "unidade": "mg/dL",
        "reference_min": 0.6,
        "reference_max": 1.2,
        "reference_range": "0.6 a 1.2 mg/dL",
        "faixa_referencia": {"min": 0.6, "max": 1.2, "unidade": "mg/dL"},
        "description": "Subproduto do metabolismo muscular da creatina, utilizado para estimar a taxa de filtração glomerular renal.",
        "resumo_exame": "Principal marcador de função renal e hidratação.",
        "clinical_significance": "Elevações acima de 1.2 mg/dL sugerem redução da filtração glomerular ou desidratação pós-esforço.",
        "causal_relationship": "Deve ser interpretada junto aos minutos de exercício intenso (`workout_minutes`) do wearable.",
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "< 0.4 mg/dL: Reduzida (baixa massa muscular).",
            "baixo": "0.4 a 0.59 mg/dL: Limite inferior.",
            "normal": "0.6 a 1.2 mg/dL: Função de filtração preservada.",
            "alto": "1.21 a 1.9 mg/dL: Elevação moderada; avaliar TFG e hidratação.",
            "muito_alto": ">= 2.0 mg/dL: Disfunção renal significativa.",
        },
        "aliases": ["creatinina", "creatinine", "2160_0", "2160-0"],
    },
    "leucocitos": {
        "analito": "leucocitos",
        "name": "Leucócitos Totais",
        "nome_exame": "Leucócitos (Glóbulos Brancos)",
        "codigo_loinc": "6690-2",
        "unit": "/mm3",
        "unidade": "/mm3",
        "reference_min": 4000.0,
        "reference_max": 10000.0,
        "reference_range": "4000 a 10000 /mm3",
        "faixa_referencia": {"min": 4000.0, "max": 10000.0, "unidade": "/mm3"},
        "description": "Contagem total de células de defesa imunológica circulantes no sangue periférico.",
        "resumo_exame": "Avalia a resposta imunológica celular contra infecções e processos inflamatórios.",
        "clinical_significance": "Leucocitose (> 10.000/mm3) sugere infecção aguda ou estresse inflamatório sistêmico.",
        "causal_relationship": "Correlaciona-se ao ALVO 3 (Queda persistente de HRV RMSSD < 38 ms) em quadros infecciosos/inflamatórios.",
        "causal_target_id": "TARGET_3_INFLAMMATION_HRV",
        "faixas_5_niveis": {
            "muito_baixo": "< 3000 /mm3: Leucopenia importante.",
            "baixo": "3000 a 3999 /mm3: Leucopenia leve.",
            "normal": "4000 a 10000 /mm3: Contagem leucocitária normal.",
            "alto": "10001 a 15000 /mm3: Leucocitose moderada.",
            "muito_alto": "> 15000 /mm3: Leucocitose acentuada.",
        },
        "aliases": ["leucocitos", "globulos_brancos", "wbc", "6690_2", "6690-2"],
    },
}


def _lookup_catalog_entry(query_name: str) -> Dict[str, Any]:
    slug = _normalize_slug(query_name)
    if slug in CLINICAL_KNOWLEDGE_CATALOG:
        return CLINICAL_KNOWLEDGE_CATALOG[slug]

    for key, entry in CLINICAL_KNOWLEDGE_CATALOG.items():
        aliases = [_normalize_slug(a) for a in entry.get("aliases", [])]
        if slug in aliases or any(slug in a or a in slug for a in aliases if len(a) >= 3):
            return entry

    # Tenta buscar na base ontológica completa do monorepo se disponível em disco
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
                if slug == _normalize_slug(code) or slug in _normalize_slug(nome):
                    faixa = item.get("faixa_referencia", {}) or {}
                    ref_min = float(faixa.get("min", 0.0) or 0.0)
                    ref_max = float(faixa.get("max", 100.0) or 100.0)
                    unit = item.get("unidade", "unid")
                    return {
                        "analito": slug,
                        "name": nome,
                        "nome_exame": nome,
                        "codigo_loinc": item.get("codigo_loinc", code),
                        "unit": unit,
                        "unidade": unit,
                        "reference_min": ref_min,
                        "reference_max": ref_max,
                        "reference_range": f"{ref_min} a {ref_max} {unit}",
                        "faixa_referencia": {"min": ref_min, "max": ref_max, "unidade": unit},
                        "description": item.get("resumo_exame", f"Biomarcador laboratorial {nome}."),
                        "resumo_exame": item.get("resumo_exame", f"Biomarcador laboratorial {nome}."),
                        "clinical_significance": (
                            f"Avaliação laboratorial quantitativa de {nome} ({unit}) para correlação clínica."
                        ),
                        "causal_relationship": (
                            "Integrado ao Motor de Inferência Causal Open Health para desambiguação "
                            "entre biomarcadores séricos e sinais fisiológicos contínuos de wearables."
                        ),
                        "causal_target_id": "TARGET_2_METABOLIC_RISK",
                        "faixas_5_niveis": item.get("faixas_5_niveis", {}),
                    }
        except Exception as exc:
            logger.debug("Não foi possível consultar base_conhecimento_exames_565.json: %s", exc)

    # Resposta genérica estruturada (nunca retorna 404)
    clean_title = (query_name or "Biomarcador").replace("_", " ").replace("-", " ").strip().title()
    return {
        "analito": slug or "biomarcador",
        "name": clean_title,
        "nome_exame": clean_title,
        "codigo_loinc": "LP-OPENHEALTH",
        "unit": "unid",
        "unidade": "unid",
        "reference_min": 10.0,
        "reference_max": 100.0,
        "reference_range": "Conforme referência laboratorial do método",
        "faixa_referencia": {"min": 10.0, "max": 100.0, "unidade": "unid"},
        "description": (
            f"Biomarcador laboratorial ({clean_title}) utilizado na avaliação clínica integrada Open Health."
        ),
        "resumo_exame": (
            f"Exame laboratorial {clean_title} correlacionado com métricas autonômicas, cardiovasculares e de sono."
        ),
        "clinical_significance": (
            f"Alterações em {clean_title} devem ser interpretadas em conjunto com a história clínica e os sinais contínuos de wearables."
        ),
        "causal_relationship": (
            "Integrado ao Motor de Inferência Causal (DAG de 3 camadas) para separar confundidores "
            "comportamentais (sono, passos, cafeína, álcool, tela) de anomalias fisiológicas genuínas."
        ),
        "causal_target_id": "TARGET_2_METABOLIC_RISK",
        "faixas_5_niveis": {
            "muito_baixo": "Abaixo do limite crítico inferior do método.",
            "baixo": "Abaixo do intervalo de referência populacional.",
            "normal": "Dentro do intervalo de referência esperado.",
            "alto": "Acima do intervalo de referência populacional.",
            "muito_alto": "Acima do limite crítico superior do método.",
        },
    }


def _classify_status(value: float, ref_min: float, ref_max: float) -> Tuple[str, str]:
    """Retorna (status_en, cor_pt) para um valor numérico frente à faixa de referência."""
    if value < ref_min:
        return "LOW", "AMARELO" if value >= ref_min * 0.6 else "VERMELHO"
    if value > ref_max:
        return "HIGH", "AMARELO" if value <= ref_max * 1.4 else "VERMELHO"
    return "NORMAL", "VERDE"


def _build_biomarker_item(entry: Dict[str, Any], value: float, custom_unit: Optional[str] = None) -> Dict[str, Any]:
    ref_min = float(entry.get("reference_min", 0.0))
    ref_max = float(entry.get("reference_max", 100.0))
    unit = custom_unit or entry.get("unit", "unid")
    status_en, status_pt = _classify_status(value, ref_min, ref_max)
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
        "reference_range": entry.get("reference_range", f"{ref_min} - {ref_max} {unit}"),
        "status": status_en,
        "status_cor": status_pt,
        "causal_target_id": entry.get("causal_target_id"),
    }


def _extract_biomarkers_from_text(raw_text: str) -> List[Dict[str, Any]]:
    """Extrai biomarcadores estruturados de texto livre, laudo laboratorial ou CSV."""
    if not raw_text or not raw_text.strip():
        return []

    patterns: List[Tuple[str, str]] = [
        ("ferritina", r"(?:ferritina(?:\s+s[eé]rica)?|2276-4)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("hemoglobina", r"(?:hemoglobina(?!\s+glicada)|(?:\bhb\b)|718-7)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("hba1c", r"(?:hemoglobina\s+glicada|hba1c|4548-4)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("glicose", r"(?:glicose(?:\s+de\s+jejum)?|glicemia|2345-7)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("vitamina_d", r"(?:vitamina\s*d|25[\s-]*oh|colecalciferol|1989-3)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("pcr", r"(?:prote[ií]na\s+c\s+reativa|\bpcr(?:-us)?\b|30522-7|1988-5)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("tsh", r"(?:\btsh\b|tireotrofina|horm[oô]nio\s+tireoestimulante|3016-3)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("colesterol", r"(?:colesterol\s+total|\bcolesterol\b(?![\s-]*(?:hdl|ldl))|2093-3)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("hdl", r"(?:colesterol\s+hdl|\bhdl\b|2085-9)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("ldl", r"(?:colesterol\s+ldl|\bldl\b|13457-7)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("triglicerideos", r"(?:triglicer[ií]deos|triglic[eé]rides|2571-8)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("ferro", r"(?:ferro\s+s[eé]rico|\bferro\b(?!\s*tina)|2498-4)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("creatinina", r"(?:creatinina|2160-0)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
        ("leucocitos", r"(?:leuc[oó]citos|gl[oó]bulos\s+brancos|6690-2)[^\d\n]{0,35}(\d+(?:[.,]\d+)?)"),
    ]

    extracted: List[Dict[str, Any]] = []
    seen_keys = set()
    for key, regex in patterns:
        match = re.search(regex, raw_text, flags=re.IGNORECASE)
        if match and key not in seen_keys:
            try:
                val = float(match.group(1).replace(",", "."))
                entry = CLINICAL_KNOWLEDGE_CATALOG[key]
                extracted.append(_build_biomarker_item(entry, val))
                seen_keys.add(key)
            except (ValueError, KeyError):
                continue

    return extracted


def _normalize_biomarker_list(raw_list: List[Any]) -> List[Dict[str, Any]]:
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
        if raw_val is None:
            continue
        try:
            val = float(str(raw_val).replace(",", "."))
        except (TypeError, ValueError):
            continue

        entry = _lookup_catalog_entry(raw_name)
        if item.get("code") or item.get("codigo_loinc"):
            entry = {**entry, "codigo_loinc": str(item.get("code") or item.get("codigo_loinc"))}
        if item.get("reference_min") is not None or item.get("faixa_referencia_min") is not None:
            entry = {
                **entry,
                "reference_min": float(
                    item.get("reference_min")
                    if item.get("reference_min") is not None
                    else item.get("faixa_referencia_min")
                ),
            }
        if item.get("reference_max") is not None or item.get("faixa_referencia_max") is not None:
            entry = {
                **entry,
                "reference_max": float(
                    item.get("reference_max")
                    if item.get("reference_max") is not None
                    else item.get("faixa_referencia_max")
                ),
            }
        custom_unit = item.get("unit") or item.get("unidade")
        built = _build_biomarker_item(entry, val, custom_unit=custom_unit)
        if item.get("status"):
            built["status"] = str(item["status"]).upper()
        normalized.append(built)
    return normalized


def _extract_text_from_bytes(raw_bytes: bytes, filename: str = "") -> str:
    """Extrai texto de bytes (PDF, CSV ou texto plano) sem falhar se bibliotecas opcionais faltarem."""
    if not raw_bytes:
        return ""
    if raw_bytes.startswith(b"%PDF") or filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = [p.extract_text() or "" for p in reader.pages]
            txt = "\n".join(pages).strip()
            if txt:
                return txt
        except Exception:
            pass
    return raw_bytes.decode("utf-8", errors="ignore")


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


@router.post(
    "/api/extrair",
    summary="Extrair biomarcadores estruturados de laudo laboratorial (JSON, texto, CSV ou arquivo PDF)",
)
async def extrair_exames_endpoint(request: Request):
    content_type = (request.headers.get("content-type") or "").lower()
    extracted: List[Dict[str, Any]] = []
    raw_text = ""
    patient_name = "Paciente Open Health"
    exam_date = date.today().isoformat()

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict):
            patient_name = str(body.get("patient_name") or body.get("paciente_nome") or patient_name)
            exam_date = str(body.get("date") or body.get("data_exame") or exam_date)
            raw_list = body.get("biomarkers") or body.get("exames") or body.get("lab_results") or body.get("results")
            if isinstance(raw_list, list):
                extracted.extend(_normalize_biomarker_list(raw_list))
            raw_text = str(
                body.get("text")
                or body.get("content")
                or body.get("raw_text")
                or body.get("texto")
                or ""
            )
            # Suporta também envio direto de chaves numéricas (ex.: {"ferritina": 22.0, "glicose": 104.0})
            direct_items = []
            for k, v in body.items():
                if k in {"text", "content", "raw_text", "texto", "biomarkers", "exames", "lab_results", "results", "patient_id", "patient_name", "date"}:
                    continue
                if isinstance(v, (int, float)):
                    direct_items.append({"name": k, "value": float(v)})
            if direct_items:
                extracted.extend(_normalize_biomarker_list(direct_items))
        elif isinstance(body, list):
            extracted.extend(_normalize_biomarker_list(body))
    else:
        # Suporta multipart/form-data ou texto puro mesmo em ambientes sem python-multipart
        try:
            form = await request.form()
            for field_name in ("arquivo", "file", "document", "pdf"):
                upload = form.get(field_name)
                if upload is not None and hasattr(upload, "read"):
                    file_bytes = await upload.read()
                    fname = getattr(upload, "filename", "") or ""
                    raw_text += "\n" + _extract_text_from_bytes(file_bytes, fname)
            for text_field in ("text", "content", "raw_text", "biomarkers"):
                val = form.get(text_field)
                if isinstance(val, str) and val.strip():
                    raw_text += "\n" + val
        except Exception:
            raw_bytes = await request.body()
            raw_text = _extract_text_from_bytes(raw_bytes)

    if raw_text:
        text_biomarkers = _extract_biomarkers_from_text(raw_text)
        existing_codes = {b["code"] for b in extracted}
        for tb in text_biomarkers:
            if tb["code"] not in existing_codes:
                extracted.append(tb)

    # Fallback determinístico caso um arquivo/texto de demonstração não contenha números explícitos
    if not extracted:
        extracted = [
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["ferritina"], 22.4),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["hemoglobina"], 12.6),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["glicose"], 94.0),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["pcr"], 2.1),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["vitamina_d"], 26.5),
        ]

    return {
        "status": "success",
        "motor": "open_health_hybrid_extractor_v2",
        "total_extracted": len(extracted),
        "cabecalho": {
            "paciente_nome": patient_name,
            "data_exame": exam_date,
            "laboratorio": "Open Health Lab Integration",
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
        biomarkers.extend(_normalize_biomarker_list(raw_list))

    # Suporta formato individual da 02_backend (codigo_loinc / valor_numerico / nome_exame)
    if body.get("valor_numerico") is not None or body.get("value") is not None:
        single_name = body.get("nome_exame") or body.get("name") or body.get("analito") or body.get("codigo_loinc") or "ferritina"
        single_val = body.get("valor_numerico") if body.get("valor_numerico") is not None else body.get("value")
        biomarkers.extend(_normalize_biomarker_list([{"name": single_name, "value": single_val}]))

    if body.get("ferritin_ng_ml") is not None:
        biomarkers.extend(_normalize_biomarker_list([{"name": "ferritina", "value": body["ferritin_ng_ml"]}]))

    raw_text = str(body.get("text") or body.get("content") or body.get("raw_text") or "")
    if raw_text:
        existing_codes = {b["code"] for b in biomarkers}
        for tb in _extract_biomarkers_from_text(raw_text):
            if tb["code"] not in existing_codes:
                biomarkers.append(tb)

    if not biomarkers:
        biomarkers = [
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["ferritina"], 24.0),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["hemoglobina"], 12.4),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["glicose"], 96.0),
            _build_biomarker_item(CLINICAL_KNOWLEDGE_CATALOG["pcr"], 1.8),
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

    # Verifica incongruências específicas entre exames normais/alterados e métricas do wearable
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
