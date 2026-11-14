# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
"""
Motor de Classificação e Gradiente de Resultados Laboratoriais (Open Health)
============================================================================
Implementa a Norma de 5 Classificações Clínicas baseada em:
  - CLSI EP28-A3c (Intervalos de Referência Laboratoriais e Zonas de Fronteira)
  - NCI CTCAE v5.0 (Common Terminology Criteria for Adverse Events - Graus 1 a 4)
  - CAP Critical Values (Colégio Americano de Patologistas)

E fornece o mapeamento seguro tanto para os 5 Estados Clínicos quanto para
os 4 Níveis Visuais de UX Segura do Paciente, além do cálculo de Tendência Temporal (↗ / ↘).
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


# ==============================================================================
# 1. NORMA DE 5 CLASSIFICAÇÕES CLÍNICAS (CLSI EP28-A3c / CTCAE Graus 1–4 / CAP)
# ==============================================================================
NIVEIS_5_CLASSIFICACOES = {
    "NORMAL": {
        "nivel": 1,
        "codigo": "NORMAL",
        "rotulo": "Normal",
        "rotulo_detalhado": "Normal (Zona Central)",
        "cor_nome": "Verde",
        "cor_hex": "#10b981",
        "cor_bg": "rgba(16, 185, 129, 0.14)",
        "cor_borda": "rgba(16, 185, 129, 0.40)",
        "criterio_matematico": "Dentro da faixa de referência, entre 10% e 90% da largura (0.10 <= Posição <= 0.90)",
        "equivalencia_clinica": "CLSI EP28-A3c (Zona Central do Intervalo de Referência)",
        "mensagem_paciente": "Resultado dentro da faixa central esperada para o exame."
    },
    "LIMITROFE": {
        "nivel": 2,
        "codigo": "LIMITROFE",
        "rotulo": "Limítrofe / Fronteira",
        "rotulo_detalhado": "Limítrofe (Zona de Fronteira Interna)",
        "cor_nome": "Amarelo",
        "cor_hex": "#eab308",
        "cor_bg": "rgba(234, 179, 8, 0.15)",
        "cor_borda": "rgba(234, 179, 8, 0.45)",
        "criterio_matematico": "Dentro da faixa, nos 10% das extremidades internas (Posição < 10% ou Posição > 90%)",
        "equivalencia_clinica": "CLSI EP28-A3c (Zona de Fronteira Interna — percentis 2,5°–10° ou 90°–97,5°)",
        "mensagem_paciente": "Valor dentro da faixa, porém próximo ao limite de referência. Vale acompanhar a evolução."
    },
    "ALTERADO_LEVE": {
        "nivel": 3,
        "codigo": "ALTERADO_LEVE",
        "rotulo": "Alterado Leve (Grau 1)",
        "rotulo_detalhado": "Alterado Leve (CTCAE Grau 1)",
        "cor_nome": "Âmbar",
        "cor_hex": "#f59e0b",
        "cor_bg": "rgba(245, 158, 11, 0.16)",
        "cor_borda": "rgba(245, 158, 11, 0.48)",
        "criterio_matematico": "Fora da faixa com Desvio de até 15% além da borda (0 < Desvio <= 0.15)",
        "equivalencia_clinica": "NCI CTCAE Grau 1 (Alteração discreta / assintomática)",
        "mensagem_paciente": "Discretamente fora da faixa esperada (até 15% de desvio). Recomendamos acompanhamento de rotina."
    },
    "ALTERADO_MODERADO": {
        "nivel": 4,
        "codigo": "ALTERADO_MODERADO",
        "rotulo": "Alterado Moderado (Grau 2)",
        "rotulo_detalhado": "Alterado Moderado (CTCAE Grau 2)",
        "cor_nome": "Laranja",
        "cor_hex": "#f97316",
        "cor_bg": "rgba(249, 115, 22, 0.16)",
        "cor_borda": "rgba(249, 115, 22, 0.48)",
        "criterio_matematico": "Fora da faixa com Desvio entre 15% e 50% além da borda (0.15 < Desvio <= 0.50)",
        "equivalencia_clinica": "NCI CTCAE Grau 2 (Alteração moderada requerendo investigação clínica)",
        "mensagem_paciente": "Resultado moderadamente fora da faixa de referência. Recomendamos avaliação médica para contextualizar este achado."
    },
    "ALTERACAO_ACENTUADA": {
        "nivel": 5,
        "codigo": "ALTERACAO_ACENTUADA",
        "rotulo": "Alteração Acentuada (Grau 3–4)",
        "rotulo_detalhado": "Alteração Acentuada (CTCAE Graus 3–4 / CAP)",
        "cor_nome": "Vermelho",
        "cor_hex": "#ef4444",
        "cor_bg": "rgba(239, 68, 68, 0.17)",
        "cor_borda": "rgba(239, 68, 68, 0.55)",
        "criterio_matematico": "Fora da faixa com Desvio > 50% além da borda (Desvio > 0.50)",
        "equivalencia_clinica": "NCI CTCAE Graus 3–4 / Valores Críticos CAP",
        # REGRA ESTRITA DE UX: Nunca exibir termos alarmistas como "Risco de vida" ou "Grave"
        "mensagem_paciente": "Valor fora do padrão esperado. Recomendamos buscar avaliação médica com prioridade."
    },
    "INDETERMINADO": {
        "nivel": 0,
        "codigo": "INDETERMINADO",
        "rotulo": "Sem Faixa Numérica",
        "rotulo_detalhado": "Sem Faixa Numérica Definida",
        "cor_nome": "Cinza",
        "cor_hex": "#94a3b8",
        "cor_bg": "rgba(148, 163, 184, 0.12)",
        "cor_borda": "rgba(148, 163, 184, 0.30)",
        "criterio_matematico": "Parâmetro qualitativo ou faixa de referência numérica ausente",
        "equivalencia_clinica": "Parâmetro qualitativo ou faixa de referência não especificada",
        "mensagem_paciente": "Consulte a referência textual do laudo com seu médico assistente."
    }
}


# ==============================================================================
# 2. MAPEAMENTO PARA OS 4 NÍVEIS VISUAIS SEGUROS DO PACIENTE
# ==============================================================================
NIVEIS_4_VISUAIS_PACIENTE = {
    "NORMAL": {
        "nivel_4": 1,
        "codigo_4": "NORMAL",
        "rotulo_4": "Normal",
        "cor_nome_4": "Verde",
        "cor_hex_4": "#10b981",
        "mensagem_4": "Resultado dentro da faixa central esperada para o exame."
    },
    "LIMITROFE": {
        "nivel_4": 2,
        "codigo_4": "LIMITROFE",
        "rotulo_4": "Limítrofe / Atenção",
        "cor_nome_4": "Amarelo",
        "cor_hex_4": "#f59e0b",
        "mensagem_4": "Valor próximo ao limite da faixa de referência. Vale acompanhar a evolução com seu médico."
    },
    "ALTERADO_MODERADO": {
        "nivel_4": 3,
        "codigo_4": "ALTERADO_MODERADO",
        "rotulo_4": "Alterado Moderado",
        "cor_nome_4": "Laranja",
        "cor_hex_4": "#f97316",
        "mensagem_4": "Resultado moderadamente fora da faixa de referência. Recomendamos avaliação médica para contextualizar este achado."
    },
    "ALTERACAO_ACENTUADA": {
        "nivel_4": 4,
        "codigo_4": "ALTERACAO_ACENTUADA",
        "rotulo_4": "Alteração Acentuada",
        "cor_nome_4": "Vermelho",
        "cor_hex_4": "#ef4444",
        "mensagem_4": "Valor fora do padrão esperado. Recomendamos buscar avaliação médica com prioridade."
    },
    "INDETERMINADO": {
        "nivel_4": 0,
        "codigo_4": "INDETERMINADO",
        "rotulo_4": "Sem Faixa",
        "cor_nome_4": "Cinza",
        "cor_hex_4": "#94a3b8",
        "mensagem_4": "Consulte a referência textual do laudo com seu médico assistente."
    }
}

# Compatibilidade retroativa com código existente
NIVEIS_VISUAIS = NIVEIS_5_CLASSIFICACOES


def _normalizar_faixas_unilaterais(
    ref_min: Optional[float],
    ref_max: Optional[float]
) -> Tuple[Optional[float], Optional[float], bool, bool]:
    """
    Trata faixas bilaterais (ex: 70 a 99) e unilaterais (ex: Colesterol < 190 ou HDL > 40).
    Retorna (min_efetivo, max_efetivo, tem_borda_inferior_real, tem_borda_superior_real).
    """
    if ref_min is not None and ref_max is not None and ref_max > ref_min:
        return float(ref_min), float(ref_max), True, True
    if ref_min is None and ref_max is not None and ref_max > 0:
        return 0.0, float(ref_max), False, True
    if ref_min is not None and ref_max is None and ref_min > 0:
        return float(ref_min), float(ref_min) * 2.0, True, False
    return None, None, False, False


def classificar_resultado_gradiente(
    valor_numerico: Optional[float],
    faixa_referencia_min: Optional[float],
    faixa_referencia_max: Optional[float]
) -> Dict[str, Any]:
    """
    Executa a classificação padronizada para qualquer analito da tabela `observations`:
      - Largura = faixa_referencia_max - faixa_referencia_min
      - Se dentro da faixa: Posição = (valor - min) / Largura
      - Se fora da faixa:   Desvio  = distância_até_a_borda / Largura

    Norma de 5 Classificações:
      1. Normal (Verde): Posição entre 10% (0.10) e 90% (0.90) da largura.
      2. Limítrofe (Amarelo): Posição < 10% ou > 90% da largura (extremidades internas).
      3. Alterado Leve (Âmbar): Fora da faixa com Desvio <= 15% (0 < Desvio <= 0.15).
      4. Alterado Moderado (Laranja): Fora da faixa com 15% < Desvio <= 50% (0.15 < Desvio <= 0.50).
      5. Alteração Acentuada (Vermelho): Fora da faixa com Desvio > 50% (Desvio > 0.50).
    """
    if valor_numerico is None:
        indet_5 = NIVEIS_5_CLASSIFICACOES["INDETERMINADO"]
        indet_4 = NIVEIS_4_VISUAIS_PACIENTE["INDETERMINADO"]
        return {
            **indet_5,
            **indet_4,
            "norma_5_classificacoes": indet_5,
            "norma_4_niveis": indet_4,
            "dentro_faixa": None,
            "direcao_desvio": "N/A",
            "largura_faixa": None,
            "posicao_relativa": None,
            "posicao_percentual": None,
            "desvio_relativo": None,
            "desvio_percentual": None,
        }

    min_ef, max_ef, tem_min_real, tem_max_real = _normalizar_faixas_unilaterais(
        faixa_referencia_min, faixa_referencia_max
    )

    if min_ef is None or max_ef is None or (max_ef - min_ef) <= 0:
        indet_5 = NIVEIS_5_CLASSIFICACOES["INDETERMINADO"]
        indet_4 = NIVEIS_4_VISUAIS_PACIENTE["INDETERMINADO"]
        return {
            **indet_5,
            **indet_4,
            "norma_5_classificacoes": indet_5,
            "norma_4_niveis": indet_4,
            "dentro_faixa": None,
            "direcao_desvio": "N/A",
            "largura_faixa": None,
            "posicao_relativa": None,
            "posicao_percentual": None,
            "desvio_relativo": None,
            "desvio_percentual": None,
        }

    valor = float(valor_numerico)
    largura = max_ef - min_ef

    abaixo_min = tem_min_real and (valor < min_ef)
    acima_max = tem_max_real and (valor > max_ef)
    dentro_faixa = not (abaixo_min or acima_max)

    if dentro_faixa:
        posicao = (valor - min_ef) / largura
        desvio = 0.0
        direcao = "CENTRAL"

        limitrofe_inf = tem_min_real and (posicao < 0.10)
        limitrofe_sup = tem_max_real and (posicao > 0.90)

        if limitrofe_inf:
            nivel_5 = NIVEIS_5_CLASSIFICACOES["LIMITROFE"]
            nivel_4 = NIVEIS_4_VISUAIS_PACIENTE["LIMITROFE"]
            direcao = "BORDA_INFERIOR_INTERNA"
        elif limitrofe_sup:
            nivel_5 = NIVEIS_5_CLASSIFICACOES["LIMITROFE"]
            nivel_4 = NIVEIS_4_VISUAIS_PACIENTE["LIMITROFE"]
            direcao = "BORDA_SUPERIOR_INTERNA"
        else:
            nivel_5 = NIVEIS_5_CLASSIFICACOES["NORMAL"]
            nivel_4 = NIVEIS_4_VISUAIS_PACIENTE["NORMAL"]

        return {
            **nivel_5,
            **nivel_4,
            "norma_5_classificacoes": nivel_5,
            "norma_4_niveis": nivel_4,
            "dentro_faixa": True,
            "direcao_desvio": direcao,
            "largura_faixa": round(largura, 4),
            "posicao_relativa": round(posicao, 4),
            "posicao_percentual": round(posicao * 100, 1),
            "desvio_relativo": 0.0,
            "desvio_percentual": 0.0,
        }

    # Fora da faixa de referência
    if abaixo_min:
        distancia_borda = min_ef - valor
        direcao = "ABAIXO_DO_MINIMO"
        posicao = (valor - min_ef) / largura
    else:
        distancia_borda = valor - max_ef
        direcao = "ACIMA_DO_MAXIMO"
        posicao = (valor - min_ef) / largura

    desvio = distancia_borda / largura

    if desvio <= 0.15:
        # Norma de 5: Nível 3 - Alterado Leve (CTCAE Grau 1)
        # Mapeamento de 4 Níveis: Limítrofe / Atenção (Amarelo)
        nivel_5 = NIVEIS_5_CLASSIFICACOES["ALTERADO_LEVE"]
        nivel_4 = NIVEIS_4_VISUAIS_PACIENTE["LIMITROFE"]
    elif desvio <= 0.50:
        # Norma de 5: Nível 4 - Alterado Moderado (CTCAE Grau 2)
        # Mapeamento de 4 Níveis: Alterado Moderado (Laranja)
        nivel_5 = NIVEIS_5_CLASSIFICACOES["ALTERADO_MODERADO"]
        nivel_4 = NIVEIS_4_VISUAIS_PACIENTE["ALTERADO_MODERADO"]
    else:
        # Norma de 5: Nível 5 - Alteração Acentuada (CTCAE Graus 3-4 / CAP)
        # Mapeamento de 4 Níveis: Alteração Acentuada (Vermelho)
        nivel_5 = NIVEIS_5_CLASSIFICACOES["ALTERACAO_ACENTUADA"]
        nivel_4 = NIVEIS_4_VISUAIS_PACIENTE["ALTERACAO_ACENTUADA"]

    return {
        **nivel_5,
        **nivel_4,
        "norma_5_classificacoes": nivel_5,
        "norma_4_niveis": nivel_4,
        "dentro_faixa": False,
        "direcao_desvio": direcao,
        "distancia_borda": round(distancia_borda, 4),
        "largura_faixa": round(largura, 4),
        "posicao_relativa": round(posicao, 4),
        "posicao_percentual": round(posicao * 100, 1),
        "desvio_relativo": round(desvio, 4),
        "desvio_percentual": round(desvio * 100, 1),
    }


def calcular_tendencia_temporal(
    valor_atual: Optional[float],
    valor_anterior: Optional[float],
    faixa_referencia_min: Optional[float],
    faixa_referencia_max: Optional[float]
) -> Dict[str, Any]:
    """
    Compara o último resultado com o exame anterior do mesmo `codigo_loinc` (ordenado por `data_coleta`).
    Se houver variação > 20% em direção a uma das bordas (inferior ou superior),
    exibe um badge de tendência (`↗` ou `↘`) mesmo que o exame ainda esteja Verde.
    """
    if valor_atual is None or valor_anterior is None or valor_anterior == 0:
        return {
            "possui_historico": False,
            "seta": None,
            "variacao_absoluta": None,
            "variacao_percentual": None,
            "variacao_largura_pct": None,
            "em_direcao_borda": False,
            "borda_alvo": None,
            "exibir_badge_tendencia": False,
            "texto_tendencia": "Primeiro registro disponível para este marcador."
        }

    atual = float(valor_atual)
    anterior = float(valor_anterior)
    delta = atual - anterior
    var_pct = (delta / abs(anterior)) * 100.0

    min_ef, max_ef, tem_min_real, tem_max_real = _normalizar_faixas_unilaterais(
        faixa_referencia_min, faixa_referencia_max
    )

    largura = (max_ef - min_ef) if (min_ef is not None and max_ef is not None and max_ef > min_ef) else None
    var_largura_pct = ((delta / largura) * 100.0) if largura else None

    if abs(delta) < 1e-9:
        return {
            "possui_historico": True,
            "seta": "→",
            "variacao_absoluta": 0.0,
            "variacao_percentual": 0.0,
            "variacao_largura_pct": 0.0,
            "em_direcao_borda": False,
            "borda_alvo": None,
            "exibir_badge_tendencia": False,
            "texto_tendencia": "Estável em relação ao exame anterior (0,0%)."
        }

    seta = "↗" if delta > 0 else "↘"

    em_direcao_borda = False
    borda_alvo = None

    if min_ef is not None and max_ef is not None:
        centro = (min_ef + max_ef) / 2.0
        if delta > 0 and tem_max_real:
            if anterior >= min_ef or atual > centro:
                em_direcao_borda = True
                borda_alvo = "SUPERIOR"
        elif delta < 0 and tem_min_real:
            if anterior <= max_ef or atual < centro:
                em_direcao_borda = True
                borda_alvo = "INFERIOR"
    else:
        em_direcao_borda = True
        borda_alvo = "SUPERIOR" if delta > 0 else "INFERIOR"

    magnitude_acima_20 = (abs(var_pct) > 20.0) or (
        var_largura_pct is not None and abs(var_largura_pct) > 20.0
    )

    exibir_badge = bool(magnitude_acima_20 and em_direcao_borda)

    sinal_str = "+" if var_pct > 0 else ""
    if exibir_badge:
        borda_txt = "limite superior" if borda_alvo == "SUPERIOR" else "limite inferior"
        texto = f"Tendência {seta} ({sinal_str}{var_pct:.1f}% em direção ao {borda_txt})"
    else:
        texto = f"Variação de {sinal_str}{var_pct:.1f}% em relação ao exame anterior"

    return {
        "possui_historico": True,
        "seta": seta,
        "variacao_absoluta": round(delta, 4),
        "variacao_percentual": round(var_pct, 1),
        "variacao_largura_pct": round(var_largura_pct, 1) if var_largura_pct is not None else None,
        "em_direcao_borda": em_direcao_borda,
        "borda_alvo": borda_alvo,
        "exibir_badge_tendencia": exibir_badge,
        "texto_tendencia": texto
    }


def parse_data_coleta_iso(data_str: Optional[str]) -> str:
    """Converte datas em formatos variados para 'YYYY-MM-DD'."""
    if not data_str:
        return "1900-01-01"
    limpa = str(data_str).strip().split(" ")[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(limpa, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return limpa


def processar_serie_temporal_analito(registros: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordena cronologicamente por `data_coleta` e enriquece com as 5 classificações e tendência temporal."""
    ordenados = sorted(
        registros,
        key=lambda r: parse_data_coleta_iso(r.get("data_coleta") or r.get("created_at"))
    )

    serie_enriquecida: List[Dict[str, Any]] = []
    valor_anterior: Optional[float] = None

    for item in ordenados:
        val_num = item.get("valor_numerico")
        ref_min = item.get("faixa_referencia_min")
        ref_max = item.get("faixa_referencia_max")

        classificacao = classificar_resultado_gradiente(val_num, ref_min, ref_max)
        tendencia = calcular_tendencia_temporal(val_num, valor_anterior, ref_min, ref_max)

        item_enriquecido = {
            **item,
            "data_coleta_iso": parse_data_coleta_iso(item.get("data_coleta")),
            "classificacao": classificacao,
            "tendencia": tendencia,
        }
        serie_enriquecida.append(item_enriquecido)

        if val_num is not None:
            valor_anterior = float(val_num)

    return serie_enriquecida
