# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import re
import json
from typing import Dict, Any, Optional, Tuple
import pdfplumber

def avaliar_referencia(valor: Optional[float], ref_str: str) -> Optional[bool]:
    """
    Avalia se o valor numérico está dentro da faixa de referência informada.
    Exemplos: '30,0 a 300,0', '70 a 99', '12,0 a 16,0', '< 100', 'superior a 50'.
    Retorna True se alterado, False se normal, None se não puder determinar.
    """
    if valor is None or not ref_str:
        return None
    
    # Caso 1: Faixa 'min a max' ou 'min - max'
    match_faixa = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:a|-)\s*(\d+(?:[.,]\d+)?)", ref_str)
    if match_faixa:
        try:
            min_val = float(match_faixa.group(1).replace(",", "."))
            max_val = float(match_faixa.group(2).replace(",", "."))
            return valor < min_val or valor > max_val
        except ValueError:
            pass

    # Caso 2: Limite superior (< max, menor que max, ate max)
    match_menor = re.search(r"(?:<|menor que|at[eé])\s*(\d+(?:[.,]\d+)?)", ref_str, re.IGNORECASE)
    if match_menor:
        try:
            max_val = float(match_menor.group(1).replace(",", "."))
            return valor > max_val
        except ValueError:
            pass

    # Caso 3: Limite inferior (> min, maior que min, superior a min)
    match_maior = re.search(r"(?:>|maior que|superior a)\s*(\d+(?:[.,]\d+)?)", ref_str, re.IGNORECASE)
    if match_maior:
        try:
            min_val = float(match_maior.group(1).replace(",", "."))
            return valor < min_val
        except ValueError:
            pass

    return None

def separar_valor_unidade(resultado_str: str) -> Tuple[str, Optional[float], Optional[str]]:
    """Separa '14,0 ng/mL' em ('14,0 ng/mL', 14.0, 'ng/mL')."""
    if not resultado_str:
        return "", None, None
    
    limpo = resultado_str.strip()
    match = re.match(r"^([<>≤≥]?\s*\d+(?:[.,]\d+)?)\s*(.*)$", limpo)
    if match:
        val_str = match.group(1).replace(" ", "").replace(",", ".")
        unidade = match.group(2).strip() or None
        try:
            val_num = float(val_str)
            return limpo, val_num, unidade
        except ValueError:
            return limpo, None, unidade
            
    return limpo, None, None

def extrair_metadados_cabecalho(texto_completo: str) -> Dict[str, Optional[str]]:
    padroes = {
        "laboratorio": r"(?:^|\n)(Laborat[oó]rio[^\n\r]+)",
        "protocolo": r"Protocolo:\s*([^\n\r\|\[\]]+|\[[^\]]+\])",
        "paciente": r"Paciente:\s*([^\n\r\|\[\]]+|\[[^\]]+\])",
        "cpf": r"CPF:\s*([\d\.\-]+|\[[^\]]+\])",
        "data_nascimento": r"Data de Nascimento:\s*([^\n\r\|\[\]]+|\[[^\]]+\])",
        "data_coleta": r"Data da Coleta:\s*([\d\/]+)",
        "data_liberacao": r"Libera[çc][ãa]o:\s*([\d\/]+)",
        "medico_solicitante": r"M[eé]dico(?:\s*Solicitante)?:\s*([^\n\r\|\[\]]+|\[[^\]]+\])"
    }
    
    dados = {}
    for chave, padrao in padroes.items():
        match = re.search(padrao, texto_completo, re.IGNORECASE)
        dados[chave] = match.group(1).strip() if match else None
        
    return dados

def extrair_local_offline(caminho_pdf: str) -> Dict[str, Any]:
    """
    Extrator 100% local, offline, sem dependência de DLLs externas ou placas de vídeo,
    consumindo apenas ~20MB de RAM e rodando instantaneamente.
    """
    resultado = {
        "cabecalho": {},
        "exames": [],
        "motor": "Local Offline (Algoritmo Leve / Zero RAM)"
    }

    texto_acumulado = ""
    linhas_tabela = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            txt = pagina.extract_text() or ""
            texto_acumulado += txt + "\n"

            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    linha_limpa = [celula.replace("\n", " ").strip() if celula else "" for celula in linha]
                    if any(linha_limpa):
                        linhas_tabela.append(linha_limpa)

    resultado["cabecalho"] = extrair_metadados_cabecalho(texto_acumulado)

    # Mapeamento dinâmico de colunas
    idx_colunas = {}
    for linha in linhas_tabela:
        linha_lower = [col.lower() for col in linha]

        if any("exame" in c or "analito" in c for c in linha_lower) and any("resultado" in c for c in linha_lower):
            for i, col in enumerate(linha_lower):
                if "exame" in col or "analito" in col:
                    idx_colunas["analito"] = i
                elif "material" in col or "m[eé]todo" in col or "método" in col:
                    idx_colunas["metodo"] = i
                elif "resultado" in col:
                    idx_colunas["resultado"] = i
                elif "refer" in col or "valor" in col:
                    idx_colunas["referencia"] = i
            continue

        if "analito" in idx_colunas and "resultado" in idx_colunas:
            if len(linha) <= max(idx_colunas.values()):
                continue

            analito = linha[idx_colunas["analito"]]
            res_bruto = linha[idx_colunas["resultado"]]
            metodo_str = linha[idx_colunas["metodo"]] if "metodo" in idx_colunas else ""
            ref_str = linha[idx_colunas["referencia"]] if "referencia" in idx_colunas else ""

            if analito and res_bruto:
                bruto, val_num, unidade = separar_valor_unidade(res_bruto)
                status_alt = avaliar_referencia(val_num, ref_str)

                # Separa material e método se estiverem juntos
                partes_metodo = [p.strip() for p in metodo_str.split("/") if p.strip()]
                material = partes_metodo[0] if len(partes_metodo) > 0 else None
                metodo = partes_metodo[1] if len(partes_metodo) > 1 else (partes_metodo[0] if len(partes_metodo) == 1 else None)

                resultado["exames"].append({
                    "analito": analito,
                    "material": material,
                    "metodo": metodo,
                    "resultado_bruto": bruto,
                    "valor_numerico": val_num,
                    "unidade": unidade,
                    "valores_referencia": ref_str,
                    "status_alterado": status_alt
                })

    return resultado
