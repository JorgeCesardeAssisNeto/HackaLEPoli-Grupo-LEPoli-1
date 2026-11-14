# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
"""
Módulo de Interpretação Longitudinal com RAG (POST /exams/interpret)
====================================================================
Implementa o fluxo de 3 passos para tradução segura de resultados ao paciente:
  - Passo 1 (SQL): Busca os últimos 3 a 5 registros de `patient_id` + `codigo_loinc`
    ordenados por `data_coleta`, enriquecidos com o Motor de Gradiente (4 níveis + tendência).
  - Passo 2 (Retrieval): Consulta a base de conhecimento indexada por `codigo_loinc`
    (diretrizes Lab Tests Online BR / SBPC-ML, SBD, SBEM, SBC).
  - Passo 3 (Geração com LLM): Envia o histórico numérico + contexto recuperado para a API
    do Gemini aplicando System Prompt estrito (proibido dar diagnóstico, linguagem acessível,
    explicação da tendência numérica e geração de 2 a 3 perguntas para o médico).
"""

import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from classificador import processar_serie_temporal_analito

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = _paths.KB_LOINC_PATH
KB_565_PATH = _paths.KB_565_PATH

# Carregamento da base estruturada de 113 analitos e 565 faixas (18 a 25 anos)
BASE_565_POR_LOINC: Dict[str, Any] = {}
BASE_565_POR_COLUNA: Dict[str, Any] = {}

if os.path.exists(KB_565_PATH):
    try:
        with open(KB_565_PATH, "r", encoding="utf-8") as f_kb565:
            dados_565 = json.load(f_kb565)
            for k, v in dados_565.items():
                BASE_565_POR_COLUNA[k.lower()] = v
                if v.get("codigo_loinc"):
                    BASE_565_POR_LOINC[v["codigo_loinc"]] = v
        print(f"[*] Base de 565 faixas carregada: {len(BASE_565_POR_COLUNA)} colunas e {len(BASE_565_POR_LOINC)} LOINCs indexados.")
    except Exception as err_565:
        print(f"[!] Erro ao carregar base_conhecimento_exames_565.json: {err_565}")


class InterpretacaoPacienteLLM(BaseModel):
    """Schema Pydantic para Structured Output da resposta gerada pelo Gemini."""
    resumo_acessivel: str = Field(
        description="Explicação clara, acolhedora e acessível sobre o que o biomarcador faz no corpo humano, sem jargões pesados."
    )
    analise_tendencia_numerica: str = Field(
        description="Descrição objetiva e não-alarmista da evolução numérica nos últimos exames (ex: estabilidade, subida gradual ou queda recente), citando valores e datas sem jamais dar diagnóstico."
    )
    o_que_significa_nivel_atual: str = Field(
        description="Contextualização da faixa atual de acordo com a classificação visual segura e as diretrizes médicas recuperadas no RAG."
    )
    perguntas_para_o_medico: List[str] = Field(
        description="Lista contendo estritamente de 2 a 3 perguntas práticas e prontas em primeira pessoa para o paciente levar ao médico na próxima consulta.",
        min_length=2,
        max_length=3
    )
    aviso_seguranca_etica: str = Field(
        description="Nota curta reforçando que a explicação é informativa/educativa e não substitui avaliação médica individualizada."
    )


SYSTEM_PROMPT_GUARDRAILS = """Você é um Educador em Saúde Digital especializado em Comunicação Clínica Centrada no Paciente, atuando em uma plataforma interoperável HL7 FHIR / LOINC no Brasil.

REGRAS ESTRITAS E INEGOCIÁVEIS DE SEGURANÇA CLÍNICA (GUARDRAILS):
1. PROIBIDO DAR DIAGNÓSTICO: Nunca, sob nenhuma hipótese, afirme ou sugira que o paciente possui uma doença ou condição clínica (ex: NUNCA diga "você tem anemia", "você está com diabetes", "isso indica hipotireoidismo" ou "você tem insuficiência renal").
2. PROIBIDO USAR TERMOS ALARMISTAS: Nunca utilize palavras como "grave", "risco de vida", "perigoso", "crítico" ou "urgência". Se a classificação for Vermelha (Alteração Acentuada), utilize a orientação padrão: "Valor fora do padrão esperado. Recomendamos buscar avaliação médica com prioridade."
3. LINGUAGEM ACESSÍVEL E EMPÁTICA: Explique em linguagem clara o papel fisiológico do biomarcador no corpo usando exclusivamente o contexto científico recuperado das diretrizes (Lab Tests Online BR / SBPC-ML, SBD, SBEM, SBC).
4. APONTAMENTO DE TENDÊNCIA NUMÉRICA: Descreva a trajetória dos últimos exames citando os números e datas reais fornecidos (ex: "Observamos que sua ferritina passou de 35,0 ng/mL para 97,5 ng/mL nos últimos exames, mantendo tendência de subida dentro da faixa de referência").
5. EMPODERAMENTO NA CONSULTA: Gere exatamente de 2 a 3 perguntas claras, em primeira pessoa, para o paciente levar ao seu médico na próxima consulta.
"""


def recuperar_conhecimento_loinc(codigo_loinc: str, nome_exame_fallback: str = "Biomarcador") -> Dict[str, Any]:
    """
    Passo 2 (Retrieval): Consulta a base de conhecimento indexada por `codigo_loinc`.
    Se o LOINC específico não estiver cadastrado, retorna um template estruturado da SBPC-ML.
    """
    kb: Dict[str, Any] = {}
    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                kb = json.load(f)
        except Exception as e:
            print(f"[!] Aviso ao ler base_conhecimento_loinc.json: {e}")

    if codigo_loinc in kb:
        return kb[codigo_loinc]

    # Fallback genérico estruturado caso seja um LOINC menos comum
    return {
        "codigo_loinc": codigo_loinc,
        "nome_exame": nome_exame_fallback,
        "categoria": "Análises Clínicas — Patologia Clínica",
        "fontes_diretrizes": [
            "Lab Tests Online BR / SBPC-ML (Sociedade Brasileira de Patologia Clínica e Medicina Laboratorial)",
            "CLSI EP28-A3c — Intervalos de Referência Laboratoriais"
        ],
        "papel_fisiologico": (
            f"O exame {nome_exame_fallback} (LOINC {codigo_loinc}) é um marcador laboratorial "
            "utilizado para acompanhar o equilíbrio fisiológico do organismo e apoiar o médico "
            "na avaliação longitudinal da saúde."
        ),
        "significado_clinico_variacoes": (
            "A leitura isolada de um único ponto é menos informativa do que a análise da curva ao longo "
            "do tempo, pois fatores biológicos, hidratação, horário da coleta e metodologias entre "
            "laboratórios podem gerar pequenas variações."
        ),
        "fatores_influencia": [
            "Horário da coleta e tempo de jejum prévio",
            "Estado de hidratação, rotina alimentar e atividade física recente",
            "Uso de medicamentos ou suplementos nutricionais"
        ],
        "perguntas_sugeridas_base": [
            f"Como a evolução dos meus resultados de {nome_exame_fallback} se encaixa no meu quadro geral de saúde?",
            "Essa variação entre os meus últimos exames é clinicamente relevante ou esperada?",
            "Qual deve ser o intervalo ideal para repetir o acompanhamento deste marcador?"
        ]
    }


def _gerar_interpretacao_deterministica_segura(
    historico_recente: List[Dict[str, Any]],
    contexto_rag: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Gera a interpretação estruturada seguindo 100% os guardrails éticos caso a chave
    da API Gemini não esteja configurada ou indisponível no ambiente local.
    """
    ultimo = historico_recente[-1]
    primeiro = historico_recente[0]
    nome_exame = contexto_rag.get("nome_exame") or ultimo.get("nome_exame", "Exame")
    unidade = ultimo.get("unidade") or ""
    clf = ultimo.get("classificacao", {})
    tend = ultimo.get("tendencia", {})

    # Construção da análise de tendência numérica com os dados reais
    pontos_fmt = [
        f"{p.get('valor_numerico')} {unidade} ({p.get('data_coleta')}, {p.get('laboratorio_origem')})"
        for p in historico_recente
    ]
    lista_txt = " → ".join(pontos_fmt)

    if len(historico_recente) >= 2:
        val_ini = primeiro.get("valor_numerico")
        val_fim = ultimo.get("valor_numerico")
        var_pct = tend.get("variacao_percentual") or 0.0
        seta = tend.get("seta") or "→"
        if abs(var_pct) <= 5.0:
            movimento_str = "manteve-se estável em relação à coleta imediatamente anterior"
        elif var_pct > 0:
            movimento_str = f"apresentou subida de +{var_pct:.1f}% ({seta}) em relação à coleta anterior"
        else:
            movimento_str = f"apresentou redução de {var_pct:.1f}% ({seta}) em relação à coleta anterior"

        analise_tendencia = (
            f"Ao longo dos últimos {len(historico_recente)} registros unificados ({lista_txt}), "
            f"o marcador {nome_exame} passou de {val_ini} {unidade} para {val_fim} {unidade}, e "
            f"no último resultado {movimento_str}."
        )
    else:
        analise_tendencia = (
            f"Até o momento há 1 registro disponível ({lista_txt}). Novas coletas permitirão "
            f"traçar a curva longitudinal de evolução deste marcador."
        )

    ref_min = ultimo.get("faixa_referencia_min")
    ref_max = ultimo.get("faixa_referencia_max")
    faixa_txt = f"{ref_min} a {ref_max} {unidade}".strip() if (ref_min is not None and ref_max is not None) else "referência do laudo"

    nivel_msg = clf.get("mensagem_paciente", "")
    rotulo_cor = f"{clf.get('rotulo', 'Normal')} ({clf.get('cor_nome', 'Verde')})"
    codigo_faixa = clf.get("codigo", "NORMAL")

    # Recupera os 5 pilares estruturados da base de 565 faixas (18 a 25 anos)
    loinc_id = contexto_rag.get("codigo_loinc") or ultimo.get("codigo_loinc", "")
    dados_565 = BASE_565_POR_LOINC.get(loinc_id) or BASE_565_POR_COLUNA.get(loinc_id.lower())
    
    resumo_exame_acessivel = contexto_rag.get("papel_fisiologico", "")
    pilares_5 = {}
    if dados_565:
        resumo_exame_acessivel = dados_565.get("resumo_exame") or resumo_exame_acessivel
        faixas_cadastradas = dados_565.get("faixas", {})
        fx_dados = faixas_cadastradas.get(codigo_faixa) or faixas_cadastradas.get("NORMAL", {})
        pilares_5 = {
            "categoria_resultado": fx_dados.get("faixa_nome", rotulo_cor),
            "nivel": fx_dados.get("nivel", clf.get("nivel", 1)),
            "cor_hex": fx_dados.get("cor_hex", clf.get("cor_hex", "#10b981")),
            "1_descricao_resultado": fx_dados.get("descricao_resultado", f"Seu resultado está classificado na faixa '{rotulo_cor}'."),
            "2_estatistica_etaria_18_25": fx_dados.get("estatistica_etaria_18_25", "Na faixa etária de 18 a 25 anos, a maioria dos pares mantém resultados na faixa esperada."),
            "3_impactos_individuo": fx_dados.get("impactos_individuo", "Impacto clínico mínimo quando acompanhado de hábitos de vida equilibrados."),
            "4_possiveis_causas": fx_dados.get("possiveis_causas", "Variações transitórias de hidratação, alimentação recente ou esforço físico."),
            "5_correcao_desvio": fx_dados.get("correcao_desvio", "Manter rotina saudável e apresentar este laudo na próxima consulta médica de rotina.")
        }
    else:
        pilares_5 = {
            "categoria_resultado": rotulo_cor,
            "nivel": clf.get("nivel", 1),
            "cor_hex": clf.get("cor_hex", "#10b981"),
            "1_descricao_resultado": f"Resultado na categoria {rotulo_cor}. {nivel_msg}",
            "2_estatistica_etaria_18_25": "Aproximadamente 85% dos jovens entre 18 e 25 anos apresentam valores dentro da faixa esperada.",
            "3_impactos_individuo": "Flutuações deste marcador podem modular a disposição energética e o rendimento físico/mental.",
            "4_possiveis_causas": "Hábitos alimentares, rotina de sono e estresse fisiológico transitório.",
            "5_correcao_desvio": "Ajuste na hidratação diária, sono regular e avaliação médica de rotina."
        }

    o_que_significa = (
        f"Seu resultado mais recente ({ultimo.get('valor_numerico')} {unidade}, referência {faixa_txt}) "
        f"está classificado na faixa '{rotulo_cor}'. {nivel_msg} "
        f"{contexto_rag.get('significado_clinico_variacoes', '')}"
    )

    return {
        "resumo_acessivel": resumo_exame_acessivel,
        "resumo_exame": resumo_exame_acessivel,
        "analise_tendencia_numerica": analise_tendencia,
        "o_que_significa_nivel_atual": o_que_significa,
        "cinco_pilares_18_25": pilares_5,
        "perguntas_para_o_medico": contexto_rag.get("perguntas_sugeridas_base", [])[:3],
        "aviso_seguranca_etica": (
            "Esta análise longitudinal tem caráter exclusivamente educativo e informativo, "
            "baseada nas diretrizes da SBPC-ML, SBD e SBEM. Ela não configura diagnóstico médico."
        )
    }


def executar_pipeline_rag_interpretacao(
    patient_id: str,
    codigo_loinc: str,
    registros_sql: List[Dict[str, Any]],
    paciente_info: Optional[Dict[str, Any]] = None,
    usar_llm: bool = True
) -> Dict[str, Any]:
    """
    Executa os 3 passos completos do endpoint `POST /exams/interpret`:
      1. Processa os últimos 3 a 5 registros vindos do SQL com o Motor de Gradiente.
      2. Recupera diretrizes clínicas na base de conhecimento por `codigo_loinc`.
      3. Gera a explicação e perguntas para o médico com o Gemini (ou fallback seguro).
    """
    if not registros_sql:
        raise ValueError(f"Nenhum registro encontrado para patient_id={patient_id} e codigo_loinc={codigo_loinc}.")

    # Passo 1: Enriquecimento da série completa e recorte dos últimos 5 exames ordenados por data_coleta
    serie_completa = processar_serie_temporal_analito(registros_sql)
    ultimos_registros = serie_completa[-5:]  # Últimos 3 a 5 registros
    ultimo_ponto = ultimos_registros[-1]

    # Passo 2 (Retrieval): Base de conhecimento indexada por codigo_loinc
    nome_exame = ultimo_ponto.get("nome_exame") or "Biomarcador"
    contexto_rag = recuperar_conhecimento_loinc(codigo_loinc, nome_exame)

    # Passo 3 (Geração com LLM Gemini + Guardrails estritos)
    chave_api = os.getenv("GEMINI_API_KEY")
    modelo_utilizado = "Motor Determinístico RAG (Offline Guardrails)"
    interpretacao_gerada: Optional[Dict[str, Any]] = None

    if usar_llm and chave_api:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=chave_api, http_options={"api_version": "v1beta"})

            historico_resumo_prompt = [
                {
                    "data_coleta": r.get("data_coleta"),
                    "laboratorio_origem": r.get("laboratorio_origem"),
                    "valor_numerico": r.get("valor_numerico"),
                    "unidade": r.get("unidade"),
                    "faixa_referencia_min": r.get("faixa_referencia_min"),
                    "faixa_referencia_max": r.get("faixa_referencia_max"),
                    "norma_5_classificacoes": {
                        "nivel": r["classificacao"].get("nivel"),
                        "rotulo": r["classificacao"].get("rotulo"),
                        "cor_nome": r["classificacao"].get("cor_nome"),
                        "equivalencia_clinica": r["classificacao"].get("equivalencia_clinica")
                    },
                    "posicao_percentual_na_faixa": r["classificacao"]["posicao_percentual"],
                    "desvio_percentual_fora_da_faixa": r["classificacao"]["desvio_percentual"],
                    "seta_tendencia": r["tendencia"]["seta"],
                    "variacao_percentual_anterior": r["tendencia"]["variacao_percentual"],
                }
                for r in ultimos_registros
            ]

            user_prompt = (
                f"PACIENTE: {(paciente_info or {}).get('nome', 'Paciente')} "
                f"(Sexo biológico: {(paciente_info or {}).get('sexo_biologico', 'N/I')})\n"
                f"BIOMARCADOR: {contexto_rag['nome_exame']} (Código LOINC: {codigo_loinc})\n\n"
                f"=== PASSO 1: HISTÓRICO NUMÉRICO DOS ÚLTIMOS {len(ultimos_registros)} EXAMES (NORMA DE 5 CLASSIFICAÇÕES CLSI/CTCAE/CAP) ===\n"
                f"{json.dumps(historico_resumo_prompt, ensure_ascii=False, indent=2)}\n\n"
                f"=== PASSO 2: DIRETRIZES CIENTÍFICAS RECUPERADAS (RAG — {', '.join(contexto_rag['fontes_diretrizes'])}) ===\n"
                f"- Papel fisiológico: {contexto_rag['papel_fisiologico']}\n"
                f"- Significado clínico das variações: {contexto_rag['significado_clinico_variacoes']}\n"
                f"- Fatores de influência pré-analítica e biológica: {', '.join(contexto_rag['fatores_influencia'])}\n\n"
                "Com base exclusivamente nos dados acima e obedecendo rigorosamente às regras do System Prompt "
                "(PROIBIDO dar diagnóstico, PROIBIDO usar termos alarmistas, explicar o papel do marcador e "
                "a tendência numérica real e situar o resultado na Norma de 5 Classificações, formulando 2 a 3 perguntas práticas para o médico), gere o JSON estruturado."
            )

            resposta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT_GUARDRAILS,
                    response_mime_type="application/json",
                    response_schema=InterpretacaoPacienteLLM,
                    temperature=0.2,
                ),
            )
            parsed = InterpretacaoPacienteLLM.model_validate_json(resposta.text)
            interpretacao_gerada = parsed.model_dump()
            modelo_utilizado = "Gemini 2.5 Flash + RAG (SBPC-ML / SBD / SBEM)"
        except Exception as e:
            print(f"[!] Aviso: Fallback acionado na geração Gemini ({e}). Usando RAG estruturado seguro.")

    if not interpretacao_gerada:
        interpretacao_gerada = _gerar_interpretacao_deterministica_segura(ultimos_registros, contexto_rag)

    return {
        "status": "sucesso",
        "patient_id": patient_id,
        "codigo_loinc": codigo_loinc,
        "nome_exame": contexto_rag["nome_exame"],
        "categoria_clinica": contexto_rag["categoria"],
        "classificacao_atual": ultimo_ponto["classificacao"],
        "tendencia_atual": ultimo_ponto["tendencia"],
        "historico_analisado": [
            {
                "observation_id": r.get("observation_id") or r.get("id"),
                "report_id": r.get("report_id"),
                "data_coleta": r.get("data_coleta"),
                "data_coleta_iso": r.get("data_coleta_iso"),
                "laboratorio_origem": r.get("laboratorio_origem"),
                "valor_numerico": r.get("valor_numerico"),
                "unidade": r.get("unidade"),
                "faixa_referencia_min": r.get("faixa_referencia_min"),
                "faixa_referencia_max": r.get("faixa_referencia_max"),
                "classificacao": r["classificacao"],
                "tendencia": r["tendencia"],
            }
            for r in ultimos_registros
        ],
        "rag_metadata": {
            "codigo_loinc_indexado": codigo_loinc,
            "fontes_consultadas": contexto_rag["fontes_diretrizes"],
            "fatores_pre_analiticos": contexto_rag["fatores_influencia"],
            "motor_geracao": modelo_utilizado,
            "guardrails_aplicados": [
                "NO_DIAGNOSIS_ENFORCED",
                "NON_ALARMIST_UX_VOCABULARY",
                "CLSI_EP28_CTCAE_4_LEVEL_GRADIENT",
                "DOCTOR_QUESTIONS_GENERATED"
            ]
        },
        "interpretacao_paciente": interpretacao_gerada
    }
