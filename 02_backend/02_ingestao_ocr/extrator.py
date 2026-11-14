# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import os
import sys
import json
import argparse
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Carrega variáveis de ambiente do .env na pasta local ou pasta pai
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(_paths.REPO_ROOT, ".env"))
load_dotenv()

class ItemExame(BaseModel):
    analito: str = Field(description="Nome do exame ou analito (ex: Ferritina Sérica, Hemoglobina, Glicose em Jejum)")
    material: Optional[str] = Field(default=None, description="Material biológico analisado (ex: Soro, Sangue Total, Plasma Fluoretado)")
    metodo: Optional[str] = Field(default=None, description="Método utilizado (ex: Quimioluminescência, Automatizado, Enzimático)")
    resultado_bruto: str = Field(description="Resultado textual exatamente como aparece no laudo (ex: '14,0 ng/mL', 'Não Reagente')")
    valor_numerico: Optional[float] = Field(default=None, description="Valor numérico isolado se aplicável, com ponto decimal (ex: 14.0)")
    unidade: Optional[str] = Field(default=None, description="Unidade de medida isolada se aplicável (ex: 'ng/mL', 'mg/dL', 'g/dL')")
    valores_referencia: Optional[str] = Field(default=None, description="Faixa ou critério de referência (ex: '30,0 a 300,0 ng/mL')")
    status_alterado: Optional[bool] = Field(
        default=None, 
        description="True se o resultado estiver fora da faixa normal de referência, False se estiver normal, None se indeterminado"
    )

class CabecalhoLaudo(BaseModel):
    laboratorio: Optional[str] = Field(default=None, description="Nome do laboratório ou instituição")
    protocolo: Optional[str] = Field(default=None, description="Número de protocolo ou pedido")
    paciente: Optional[str] = Field(default=None, description="Nome completo do paciente")
    cpf: Optional[str] = Field(default=None, description="CPF do paciente")
    data_nascimento: Optional[str] = Field(default=None, description="Data de nascimento do paciente")
    data_coleta: Optional[str] = Field(default=None, description="Data da coleta da amostra")
    data_liberacao: Optional[str] = Field(default=None, description="Data de liberação do laudo")
    medico_solicitante: Optional[str] = Field(default=None, description="Nome do médico solicitante")
    responsavel_tecnico: Optional[str] = Field(default=None, description="Nome e registro do responsável técnico")
    observacoes: Optional[str] = Field(default=None, description="Observações clínicas ou notas de rodapé relevantes")

class LaudoCompleto(BaseModel):
    cabecalho: CabecalhoLaudo
    exames: List[ItemExame] = Field(description="Lista de todos os analitos/exames identificados no laudo")


def extrair_informacoes_laudo(
    caminho_arquivo: str, 
    api_key: Optional[str] = None,
    modelo: str = "gemini-2.5-flash"
) -> LaudoCompleto:
    """
    Envia o arquivo (PDF ou imagem escaneada) para o Gemini e retorna os dados
    estritamente validados no schema Pydantic.
    """
    from google import genai
    from google.genai import types

    chave = api_key or os.getenv("GEMINI_API_KEY")
    if not chave:
        raise ValueError(
            "Chave de API não informada! Defina GEMINI_API_KEY no arquivo .env "
            "ou passe via argumento --api-key."
        )

    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    client = genai.Client(api_key=chave, http_options={'api_version': 'v1beta'})

    print(f"[*] Fazendo upload do arquivo para análise: {caminho_arquivo}...")
    arquivo_remoto = client.files.upload(file=caminho_arquivo)

    prompt_instrucao = (
        "Você é um especialista em interpretação e extração de dados de laudos laboratoriais e exames de sangue.\n"
        "Analise minuciosamente o documento anexado (seja PDF digital, escaneado ou foto) e extraia:\n"
        "1. Todos os dados cadastrais (laboratório, protocolo, paciente, datas, médico, etc).\n"
        "2. Todos os exames e analitos realizados, separando claramente o resultado bruto, o valor numérico, a unidade e o valor de referência.\n"
        "3. Avalie se o resultado está dentro ou fora da faixa de referência indicada e preencha status_alterado (True/False).\n"
        "4. Preencha o dicionário 'campos_planilha' mapeando os analitos encontrados para o nome da coluna no padrão BR CORE / LOINC. Exemplos de chaves possíveis:\n"
        "   - hemacias_10e6_uL, hemoglobina_g_dL, hematocrito_pct, leucocitos_totais_10e3_uL, plaquetas_10e3_uL\n"
        "   - glicose_jejum_mg_dL, hemoglobina_glicada_hba1c_pct, insulina_basal_uIU_mL\n"
        "   - colesterol_total_mg_dL, colesterol_hdl_mg_dL, colesterol_ldl_mg_dL, triglicerideos_mg_dL\n"
        "   - creatinina_mg_dL, ureia_mg_dL, acido_urico_mg_dL, sodio_mEq_L, potassio_mEq_L\n"
        "   - tgo_ast_U_L, tgp_alt_U_L, gama_gt_ggt_U_L, bilirrubina_total_mg_dL\n"
        "   - tsh_uIU_mL, t4_livre_ng_dL, ferritina_ng_mL, ferro_serico_ug_dL, vitamina_d_25oh_ng_mL, vitamina_b12_pg_mL\n"
        "   - pcr_ultrassensivel_mg_L, vhs_mm_h, troponina_i_alta_sensibilidade_ng_L, etc.\n"
        "Mantenha rigor absoluto na transcrição dos números e unidades."
    )

    print(f"[*] Enviando para o modelo {modelo} com Structured Outputs...")
    resposta = client.models.generate_content(
        model=modelo,
        contents=[arquivo_remoto, prompt_instrucao],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LaudoCompleto,
            temperature=0.1,
        ),
    )

    # Converte o JSON gerado no modelo tipado Pydantic
    return LaudoCompleto.model_validate_json(resposta.text)


def formatar_tabela_terminal(laudo: LaudoCompleto):
    """Exibe um resumo elegante no terminal."""
    cab = laudo.cabecalho
    print("\n" + "=" * 80)
    print(" INFORMAÇÕES DO LAUDO LABORATORIAL ".center(80, "="))
    print("=" * 80)
    print(f" Laboratório: {cab.laboratorio or 'N/A'}")
    print(f" Protocolo:   {cab.protocolo or 'N/A'} | Coleta: {cab.data_coleta or 'N/A'} | Liberação: {cab.data_liberacao or 'N/A'}")
    print(f" Paciente:    {cab.paciente or 'N/A'} | CPF: {cab.cpf or 'N/A'} | Nasc: {cab.data_nascimento or 'N/A'}")
    print(f" Médico:      {cab.medico_solicitante or 'N/A'}")
    print("-" * 80)
    print(f"{'EXAME / ANALITO':<24} {'RESULTADO':<15} {'REF. / NORMAL':<22} {'STATUS':<10}")
    print("-" * 80)

    for ex in laudo.exames:
        status_tag = ""
        if ex.status_alterado is True:
            status_tag = "[ALTERADO]"
        elif ex.status_alterado is False:
            status_tag = "[OK]"

        resultado_formatado = f"{ex.valor_numerico or ex.resultado_bruto} {ex.unidade or ''}".strip()
        ref = ex.valores_referencia or "-"
        print(f"{ex.analito:<24} {resultado_formatado:<15} {ref:<22} {status_tag:<10}")

    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extrator universal de exames de sangue em PDF via Gemini")
    parser.add_argument("pdf", help="Caminho para o arquivo PDF ou imagem do exame")
    parser.add_argument("--saida", "-o", help="Caminho do arquivo JSON para salvar os resultados", default=None)
    parser.add_argument("--modelo", "-m", help="Nome do modelo Gemini", default="gemini-2.5-flash")
    parser.add_argument("--api-key", help="Chave de API do Gemini (opcional, pode vir do .env)", default=None)

    args = parser.parse_args()

    try:
        resultado = extrair_informacoes_laudo(
            caminho_arquivo=args.pdf,
            api_key=args.api_key,
            modelo=args.modelo
        )

        formatar_tabela_terminal(resultado)

        if args.saida:
            with open(args.saida, "w", encoding="utf-8") as f:
                f.write(resultado.model_dump_json(indent=2))
            print(f"[OK] Dados salvos com sucesso em: {args.saida}")
        else:
            # Imprime o JSON puro se solicitado via pipe
            pass

    except Exception as e:
        print(f"[ERRO] Falha ao processar laudo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
