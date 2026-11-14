# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import os
import sqlite3
import uuid
import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = _paths.DB_SQLITE_PATH
MAPA_LOINC_PATH = _paths.MAPA_LOINC_PATH

# Carrega o mapa oficial de coluna -> código LOINC gerado a partir da planilha oficial
MAPA_LOINC: Dict[str, str] = {}
if os.path.exists(MAPA_LOINC_PATH):
    try:
        with open(MAPA_LOINC_PATH, "r", encoding="utf-8") as f:
            MAPA_LOINC = json.load(f)
    except Exception as e:
        print(f"[!] Erro ao carregar mapa_colunas_loinc.json: {e}")

def get_db_connection():
    """Retorna uma conexão ativa com o banco SQLite configurado com Row Factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Habilita suporte a chaves estrangeiras no SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def inicializar_banco():
    """Cria as 4 tabelas do schema Open Health com chaves primárias, estrangeiras e índices."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabela patients (HL7 FHIR: Patient - Perfil BR Core)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            cns TEXT,
            data_nascimento TEXT,
            sexo_biologico TEXT CHECK (sexo_biologico IN ('M', 'F', NULL)),
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_cpf ON patients (cpf);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_cns ON patients (cns);")

    # 2. Tabela diagnostic_reports (HL7 FHIR: DiagnosticReport)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnostic_reports (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            laboratorio_origem TEXT NOT NULL,
            data_coleta TEXT,
            data_emissao TEXT,
            assinatura_hash TEXT,
            versao INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_patient ON diagnostic_reports (patient_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_coleta ON diagnostic_reports (data_coleta);")

    # 3. Tabela observations (HL7 FHIR: Observation - Métrica Verticalizada em Linhas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            codigo_loinc TEXT NOT NULL,
            nome_exame TEXT NOT NULL,
            valor_numerico REAL,
            valor_texto TEXT,
            unidade TEXT,
            faixa_referencia_min REAL,
            faixa_referencia_max REAL,
            FOREIGN KEY (report_id) REFERENCES diagnostic_reports(id) ON DELETE CASCADE,
            CHECK (valor_numerico IS NOT NULL OR valor_texto IS NOT NULL)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_observations_report ON observations (report_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_observations_loinc ON observations (codigo_loinc);")

    # 4. Tabela consents (HL7 FHIR: Consent - Governança LGPD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consents (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            hospital_origem TEXT NOT NULL,
            hospital_destino TEXT NOT NULL,
            escopo TEXT NOT NULL DEFAULT 'exames_sangue',
            status TEXT NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'revogado')),
            expira_em TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_consents_patient_status ON consents (patient_id, status);")

    conn.commit()
    conn.close()

def extrair_faixas_min_max(ref_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """Extrai faixa_referencia_min e faixa_referencia_max de textos como '12,0 a 16,0', '< 100', '> 50'."""
    if not ref_str:
        return None, None
    
    # Faixa min a max
    match_faixa = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:a|-)\s*(\d+(?:[.,]\d+)?)", ref_str)
    if match_faixa:
        try:
            min_val = float(match_faixa.group(1).replace(",", "."))
            max_val = float(match_faixa.group(2).replace(",", "."))
            return min_val, max_val
        except ValueError:
            pass

    # Menor que (< max)
    match_menor = re.search(r"(?:<|menor que|at[eé])\s*(\d+(?:[.,]\d+)?)", ref_str, re.IGNORECASE)
    if match_menor:
        try:
            return None, float(match_menor.group(1).replace(",", "."))
        except ValueError:
            pass

    # Maior que (> min)
    match_maior = re.search(r"(?:>|maior que|superior a)\s*(\d+(?:[.,]\d+)?)", ref_str, re.IGNORECASE)
    if match_maior:
        try:
            return float(match_maior.group(1).replace(",", ".")), None
        except ValueError:
            pass

    return None, None

def normalizar_loinc_por_analito(nome_analito: str) -> Tuple[str, str]:
    """Descobre o código LOINC aproximado e o nome limpo baseado no analito."""
    nome_norm = nome_analito.lower().strip()
    
    # Mapa rápido de emergência caso não venha direto da coluna oficial
    MAPEAMENTO_RAPIDO = [
        ("hemoglobina glicada", "4548-4", "Hemoglobina Glicada (HbA1c)"),
        ("hemoglobina", "718-7", "Hemoglobina"),
        ("hemacias", "789-8", "Hemácias"),
        ("eritrocitos", "789-8", "Hemácias"),
        ("hematocrito", "4544-3", "Hematócrito"),
        ("vcm", "787-2", "Volume Corpuscular Médio (VCM)"),
        ("hcm", "785-6", "Hemoglobina Corpuscular Média (HCM)"),
        ("chcm", "786-4", "Conc. Hemoglobina Corpuscular Média (CHCM)"),
        ("rdw", "788-0", "RDW - Amplitude de Distribuição dos Glóbulos"),
        ("leucocitos", "6690-2", "Leucócitos Totais"),
        ("plaquetas", "777-3", "Plaquetas"),
        ("glicose", "2345-7", "Glicose de Jejum"),
        ("glicemia", "2345-7", "Glicose de Jejum"),
        ("creatinina", "2160-0", "Creatinina"),
        ("ureia", "3094-0", "Ureia"),
        ("acido urico", "3084-1", "Ácido Úrico"),
        ("colesterol total", "2093-3", "Colesterol Total"),
        ("colesterol hdl", "2085-9", "Colesterol HDL"),
        ("colesterol ldl", "13457-7", "Colesterol LDL"),
        ("triglicerideos", "2571-8", "Triglicerídeos"),
        ("tgo", "1920-8", "TGO / AST"),
        ("ast", "1920-8", "TGO / AST"),
        ("tgp", "1742-6", "TGP / ALT"),
        ("alt", "1742-6", "TGP / ALT"),
        ("gama gt", "2324-2", "Gama GT"),
        ("fosfatase alcalina", "6768-6", "Fosfatase Alcalina"),
        ("tsh", "3016-3", "TSH - Hormônio Tireoestimulante"),
        ("t4 livre", "3024-7", "T4 Livre"),
        ("ferritina", "2276-4", "Ferritina"),
        ("ferro serico", "2498-4", "Ferro Sérico"),
        ("vitamina d", "1989-3", "Vitamina D (25-Hidroxi)"),
        ("vitamina b12", "2132-9", "Vitamina B12"),
        ("pcr", "30522-7", "Proteína C-Reativa (PCR)"),
        ("vhs", "4537-7", "Velocidade de Hemossedimentação (VHS)"),
        ("sodio", "2951-2", "Sódio"),
        ("potassio", "2823-3", "Potássio"),
        ("calcio", "17861-6", "Cálcio Total"),
    ]

    for chave, loinc, label in MAPEAMENTO_RAPIDO:
        if chave in nome_norm:
            return loinc, label
            
    return "0000-0", nome_analito.title()

def salvar_laudo_relacional(dados_extracao: Dict[str, Any], linha_planilha: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Recebe os dados extraídos do laudo em PDF e persiste no banco relacional
    preenchendo exatamente as 4 tabelas:
    1. patients
    2. diagnostic_reports
    3. observations (1 registro para cada métrica com LOINC)
    4. consents (LGPD)
    """
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()

    cabecalho = dados_extracao.get("cabecalho", {})
    linha = linha_planilha or dados_extracao.get("linha_planilha", {})
    exames = dados_extracao.get("exames", [])

    # 1. DADOS DO PACIENTE (BR Core)
    nome_paciente = linha.get("nome_paciente") or cabecalho.get("paciente") or "Paciente Não Informado"
    cpf_paciente = linha.get("cpf_paciente") or cabecalho.get("cpf") or ""
    cpf_limpo = re.sub(r'[^0-9]', '', str(cpf_paciente))
    
    # Caso CPF não seja informado ou venha mascarado/anonimizado
    if not cpf_limpo or len(cpf_limpo) < 3 or "protegido" in str(cpf_paciente).lower():
        hash_nome = hashlib.md5(nome_paciente.encode('utf-8')).hexdigest()[:11]
        cpf_paciente = f"DOC-{hash_nome}"
    else:
        cpf_paciente = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}" if len(cpf_limpo) == 11 else cpf_limpo

    cns_paciente = linha.get("cns_paciente") or cabecalho.get("cns")
    data_nascimento = linha.get("data_nascimento") or cabecalho.get("data_nascimento")
    sexo_biologico = (linha.get("sexo_biologico") or cabecalho.get("sexo_biologico") or "").upper()
    if sexo_biologico not in ('M', 'F'):
        sexo_biologico = None

    # Verifica se paciente já existe por CPF ou por Nome aproximado
    cursor.execute("SELECT id FROM patients WHERE cpf = ? OR lower(trim(nome)) = lower(trim(?))", (cpf_paciente, nome_paciente))
    row_paciente = cursor.fetchone()
    if row_paciente:
        patient_id = row_paciente["id"]
        # Atualiza dados se houver novidades
        cursor.execute("""
            UPDATE patients 
            SET nome = coalesce(?, nome),
                cns = coalesce(?, cns),
                data_nascimento = coalesce(?, data_nascimento),
                sexo_biologico = coalesce(?, sexo_biologico)
            WHERE id = ?
        """, (nome_paciente, cns_paciente, data_nascimento, sexo_biologico, patient_id))
    else:
        patient_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO patients (id, nome, cpf, cns, data_nascimento, sexo_biologico)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id, nome_paciente, cpf_paciente, cns_paciente, data_nascimento, sexo_biologico))

    # 2. DADOS DO LAUDO (DiagnosticReport)
    report_id = str(uuid.uuid4())
    laboratorio = linha.get("laboratorio_origem") or cabecalho.get("laboratorio") or "Laboratório Clínico"
    data_coleta = linha.get("data_coleta") or cabecalho.get("data_coleta")
    data_emissao = linha.get("data_emissao") or cabecalho.get("data_liberacao") or datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Gera assinatura hash ICP-Brasil simulada (SHA-256 de integridade)
    conteudo_assinatura = f"{patient_id}|{laboratorio}|{data_coleta}|{data_emissao}|{len(exames)}"
    assinatura_hash = hashlib.sha256(conteudo_assinatura.encode('utf-8')).hexdigest()

    cursor.execute("""
        INSERT INTO diagnostic_reports (id, patient_id, laboratorio_origem, data_coleta, data_emissao, assinatura_hash, versao)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (report_id, patient_id, laboratorio, data_coleta, data_emissao, assinatura_hash))

    # 3. OBSERVATIONS (Métricas individuais normalizadas com LOINC)
    observacoes_inseridas = 0

    # Primeiro, percorremos a lista rica de 'exames' extraídos pelo motor
    analitos_processados = set()
    for ex in exames:
        nome_analito = ex.get("analito", "").strip()
        if not nome_analito or nome_analito.lower() in analitos_processados:
            continue
        analitos_processados.add(nome_analito.lower())

        loinc, nome_formatado = normalizar_loinc_por_analito(nome_analito)
        valor_num = ex.get("valor_numerico")
        resultado_bruto = ex.get("resultado_bruto", "")
        valor_texto = str(resultado_bruto) if (valor_num is None and resultado_bruto) else None
        unidade = ex.get("unidade") or ""
        ref_str = ex.get("valores_referencia", "")
        min_ref, max_ref = extrair_faixas_min_max(ref_str)

        obs_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO observations (id, report_id, codigo_loinc, nome_exame, valor_numerico, valor_texto, unidade, faixa_referencia_min, faixa_referencia_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (obs_id, report_id, loinc, nome_formatado, valor_num, valor_texto, unidade, min_ref, max_ref))
        observacoes_inseridas += 1

    # Caso tenhamos colunas mapeadas na planilha que não estavam na lista de exames, inserimos também
    ignorar_cols = {'id_laudo', 'cpf_paciente', 'cns_paciente', 'nome_paciente', 'data_nascimento', 'sexo_biologico', 'laboratorio_origem', 'data_coleta', 'data_emissao'}
    for col, val in linha.items():
        if col in ignorar_cols or val is None or val == "":
            continue
        col_loinc = MAPA_LOINC.get(col, "0000-0")
        
        # Se esse LOINC ainda não foi inserido neste relatório:
        cursor.execute("SELECT id FROM observations WHERE report_id = ? AND codigo_loinc = ?", (report_id, col_loinc))
        if not cursor.fetchone():
            nome_exame = col.replace("_", " ").title()
            val_num = None
            val_txt = None
            try:
                val_num = float(str(val).replace(",", "."))
            except (ValueError, TypeError):
                val_txt = str(val)

            obs_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO observations (id, report_id, codigo_loinc, nome_exame, valor_numerico, valor_texto, unidade, faixa_referencia_min, faixa_referencia_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (obs_id, report_id, col_loinc, nome_exame, val_num, val_txt, "", None, None))
            observacoes_inseridas += 1

    # 4. CONSENTS (Governança LGPD)
    cursor.execute("SELECT id FROM consents WHERE patient_id = ? AND status = 'ativo'", (patient_id,))
    consent_row = cursor.fetchone()
    if not consent_row:
        consent_id = str(uuid.uuid4())
        data_expira = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO consents (id, patient_id, hospital_origem, hospital_destino, escopo, status, expira_em)
            VALUES (?, ?, ?, ?, 'exames_sangue', 'ativo', ?)
        """, (consent_id, patient_id, laboratorio, "Rede Open Health Brasil", data_expira))

    conn.commit()
    conn.close()

    return {
        "status": "sucesso",
        "patient_id": patient_id,
        "report_id": report_id,
        "observacoes_inseridas": observacoes_inseridas,
        "assinatura_hash": assinatura_hash
    }

def obter_dados_tabelas():
    """Retorna todas as 4 tabelas como listas de dicionários para exibição no dashboard."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients ORDER BY created_at DESC LIMIT 50;")
    patients = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT dr.*, p.nome as nome_paciente, p.cpf as cpf_paciente
        FROM diagnostic_reports dr
        JOIN patients p ON p.id = dr.patient_id
        ORDER BY dr.created_at DESC LIMIT 50;
    """)
    reports = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT obs.*, dr.laboratorio_origem, dr.data_coleta, p.nome as nome_paciente
        FROM observations obs
        JOIN diagnostic_reports dr ON dr.id = obs.report_id
        JOIN patients p ON p.id = dr.patient_id
        ORDER BY obs.codigo_loinc ASC LIMIT 100;
    """)
    observations = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.*, p.nome as nome_paciente, p.cpf as cpf_paciente
        FROM consents c
        JOIN patients p ON p.id = c.patient_id
        ORDER BY c.created_at DESC LIMIT 50;
    """)
    consents = [dict(r) for r in cursor.fetchall()]

    # Contagens gerais
    cursor.execute("SELECT count(*) as total FROM patients;")
    total_pacientes = cursor.fetchone()["total"]

    cursor.execute("SELECT count(*) as total FROM diagnostic_reports;")
    total_laudos = cursor.fetchone()["total"]

    cursor.execute("SELECT count(*) as total FROM observations;")
    total_observacoes = cursor.fetchone()["total"]

    cursor.execute("SELECT count(*) as total FROM consents;")
    total_consentimentos = cursor.fetchone()["total"]

    conn.close()

    return {
        "patients": patients,
        "diagnostic_reports": reports,
        "observations": observations,
        "consents": consents,
        "stats": {
            "total_pacientes": total_pacientes,
            "total_laudos": total_laudos,
            "total_observacoes": total_observacoes,
            "total_consentimentos": total_consentimentos
        }
    }

def obter_pacientes_completo():
    """Retorna lista de pacientes com totais de laudos e consentimentos para a tela principal."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.*,
            (SELECT COUNT(*) FROM diagnostic_reports dr WHERE dr.patient_id = p.id) as total_reports,
            (SELECT COUNT(*) FROM consents c WHERE c.patient_id = p.id AND c.status = 'ativo') as total_consents_ativos,
            (SELECT COUNT(*) FROM consents c WHERE c.patient_id = p.id) as total_consents
        FROM patients p
        ORDER BY p.created_at DESC;
    """)
    pacientes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return pacientes

def obter_detalhes_paciente(patient_id: str):
    """Retorna os dados cadastrais do paciente, seus consentimentos (LGPD) e seus laudos (DiagnosticReports)."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE id = ?;", (patient_id,))
    paciente_row = cursor.fetchone()
    if not paciente_row:
        conn.close()
        return None

    paciente = dict(paciente_row)

    # Laudos deste paciente com contagem de observações
    cursor.execute("""
        SELECT 
            dr.*,
            (SELECT COUNT(*) FROM observations obs WHERE obs.report_id = dr.id) as total_observacoes
        FROM diagnostic_reports dr
        WHERE dr.patient_id = ?
        ORDER BY dr.data_coleta DESC, dr.created_at DESC;
    """, (patient_id,))
    reports = [dict(r) for r in cursor.fetchall()]

    # Consentimentos deste paciente (anexados ao paciente)
    cursor.execute("""
        SELECT * FROM consents
        WHERE patient_id = ?
        ORDER BY created_at DESC;
    """, (patient_id,))
    consents = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "paciente": paciente,
        "reports": reports,
        "consents": consents
    }

def obter_observacoes_laudo_colunas(report_id: str):
    """
    Retorna as observações de um laudo formatadas por colunas,
    incluindo todas as 113 colunas padronizadas do catálogo BR Core / LOINC (inclusive as vazias).
    """
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Informações do laudo e do paciente
    cursor.execute("""
        SELECT dr.*, p.nome as nome_paciente, p.cpf as cpf_paciente, p.sexo_biologico, p.data_nascimento
        FROM diagnostic_reports dr
        JOIN patients p ON p.id = dr.patient_id
        WHERE dr.id = ?;
    """, (report_id,))
    laudo_row = cursor.fetchone()
    if not laudo_row:
        conn.close()
        return None

    laudo = dict(laudo_row)

    # Observações salvas no banco para este laudo
    cursor.execute("SELECT * FROM observations WHERE report_id = ?;", (report_id,))
    obs_salvas = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Mapa rápido por código LOINC e por nome de exame para busca
    obs_por_loinc = {}
    obs_por_nome = {}
    for obs in obs_salvas:
        cod_loinc = (obs.get("codigo_loinc") or "").strip()
        if cod_loinc and cod_loinc != "0000-0":
            obs_por_loinc[cod_loinc] = obs
        nome_limpo = (obs.get("nome_exame") or "").lower().strip()
        obs_por_nome[nome_limpo] = obs

    # Carrega o catálogo completo das 113 colunas oficiais
    catalogo_path = os.path.join(BASE_DIR, "catalogo_colunas_completo.json")
    catalogo = []
    if os.path.exists(catalogo_path):
        with open(catalogo_path, "r", encoding="utf-8") as f:
            catalogo = json.load(f)

    # Constrói a matriz completa de colunas (preenchidas e vazias)
    colunas_resultado = []
    ids_obs_usadas = set()

    for item in catalogo:
        coluna_nome = item["coluna"]
        loinc = item["loinc"]
        categoria = item["categoria"]

        # Formata o nome amigável da coluna (ex: hemoglobina_g_dL -> Hemoglobina)
        partes = coluna_nome.split("_")
        nome_exibicao = " ".join([p.capitalize() for p in partes])

        # Verifica se essa coluna tem observação correspondente por LOINC ou por chave
        obs_match = None
        if loinc in obs_por_loinc:
            obs_match = obs_por_loinc[loinc]
        else:
            # Tenta encontrar por similaridade do nome da coluna
            for n_ex, obs_item in obs_por_nome.items():
                if n_ex in coluna_nome.lower() or coluna_nome.lower() in n_ex:
                    obs_match = obs_item
                    break

        if obs_match:
            ids_obs_usadas.add(obs_match.get("id"))
            val_num = obs_match.get("valor_numerico")
            val_txt = obs_match.get("valor_texto")
            unidade = obs_match.get("unidade") or ""
            ref_min = obs_match.get("faixa_referencia_min")
            ref_max = obs_match.get("faixa_referencia_max")

            # Avalia status clínico se houver faixa
            status_clinico = "normal"
            if val_num is not None:
                if ref_min is not None and val_num < ref_min:
                    status_clinico = "baixo"
                elif ref_max is not None and val_num > ref_max:
                    status_clinico = "alto"

            colunas_resultado.append({
                "coluna": coluna_nome,
                "loinc": loinc,
                "categoria": categoria,
                "nome_exibicao": obs_match.get("nome_exame") or nome_exibicao,
                "preenchida": True,
                "valor": val_num if val_num is not None else val_txt,
                "valor_formatado": f"{val_num} {unidade}".strip() if val_num is not None else str(val_txt),
                "unidade": unidade,
                "faixa_min": ref_min,
                "faixa_max": ref_max,
                "faixa_referencia_formatada": f"{ref_min} - {ref_max} {unidade}".strip() if (ref_min is not None or ref_max is not None) else "-",
                "status_clinico": status_clinico,
                "observation_id": obs_match.get("id")
            })
        else:
            # Coluna VAZIA (conforme pedido expresso do usuário!)
            colunas_resultado.append({
                "coluna": coluna_nome,
                "loinc": loinc,
                "categoria": categoria,
                "nome_exibicao": nome_exibicao,
                "preenchida": False,
                "valor": None,
                "valor_formatado": "—",
                "unidade": "",
                "faixa_min": None,
                "faixa_max": None,
                "faixa_referencia_formatada": "—",
                "status_clinico": "vazio",
                "observation_id": None
            })

    # Observações extras do laudo que porventura não estejam nas 113 colunas padrão
    observacoes_extras = []
    for obs in obs_salvas:
        if obs.get("id") not in ids_obs_usadas:
            observacoes_extras.append(obs)

    total_preenchidas = sum(1 for c in colunas_resultado if c["preenchida"])
    total_vazias = sum(1 for c in colunas_resultado if not c["preenchida"])

    return {
        "laudo": laudo,
        "total_colunas": len(colunas_resultado),
        "total_preenchidas": total_preenchidas,
        "total_vazias": total_vazias,
        "colunas": colunas_resultado,
        "observacoes_extras": observacoes_extras
    }

def alternar_status_consentimento(consent_id: str):
    """Alterna o status do consentimento entre 'ativo' e 'revogado'."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM consents WHERE id = ?;", (consent_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    novo_status = 'revogado' if row["status"] == 'ativo' else 'ativo'
    cursor.execute("UPDATE consents SET status = ? WHERE id = ?;", (novo_status, consent_id))
    conn.commit()
    conn.close()
    return {"consent_id": consent_id, "novo_status": novo_status}

def criar_consentimento_paciente(patient_id: str, hospital_origem: str, hospital_destino: str, escopo: str = "exames_sangue", dias_validade: int = 365):
    """Cria um novo consentimento LGPD para um paciente específico."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()
    cid = str(uuid.uuid4())
    data_expira = (datetime.now() + timedelta(days=dias_validade)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO consents (id, patient_id, hospital_origem, hospital_destino, escopo, status, expira_em)
        VALUES (?, ?, ?, ?, ?, 'ativo', ?);
    """, (cid, patient_id, hospital_origem, hospital_destino, escopo, data_expira))
    conn.commit()
    conn.close()
    return {"id": cid, "status": "criado"}

def limpar_todas_tabelas():
    """Zera os dados de teste das 4 tabelas."""
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM observations;")
    cursor.execute("DELETE FROM consents;")
    cursor.execute("DELETE FROM diagnostic_reports;")
    cursor.execute("DELETE FROM patients;")
    conn.commit()
    conn.close()
    return {"status": "banco_limpo"}


# ==============================================================================
# MÓDULO DE CLASSIFICAÇÃO, HISTÓRICO LONGITUDINAL E DISPLAY PARA O PACIENTE
# ==============================================================================

# Faixas de referência clínicas bilaterais padrão (CLSI EP28-A3c / SBPC-ML)
# Garantem que todo biomarcador possua faixa_referencia_min e faixa_referencia_max
# para renderização da faixa sombreada translúcida e cálculo do gradiente de 4 cores.
FAIXAS_PADRAO_LOINC: Dict[str, Tuple[float, float, str, str]] = {
    "2276-4": (15.0, 150.0, "ng/mL", "Ferritina"),
    "718-7": (12.0, 15.0, "g/dL", "Hemoglobina"),
    "3016-3": (0.40, 4.30, "µUI/mL", "TSH Ultra-Sensível"),
    "2345-7": (70.0, 99.0, "mg/dL", "Glicose de Jejum"),
    "4548-4": (4.0, 5.6, "%", "Hemoglobina Glicada (HbA1c)"),
    "1989-3": (20.0, 60.0, "ng/mL", "Vitamina D (25-Hidroxi)"),
    "13457-7": (50.0, 100.0, "mg/dL", "Colesterol LDL"),
    "2093-3": (100.0, 190.0, "mg/dL", "Colesterol Total"),
    "2085-9": (40.0, 80.0, "mg/dL", "Colesterol HDL"),
    "2571-8": (40.0, 150.0, "mg/dL", "Triglicerídeos"),
    "20448-7": (2.5, 13.1, "µUI/mL", "Insulina Basal"),
    "72115-9": (0.5, 2.7, "índice", "Índice HOMA-IR"),
    "2498-4": (50.0, 170.0, "µg/dL", "Ferro Sérico"),
    "30522-7": (0.01, 0.30, "mg/dL", "PCR Ultrassensível"),
    "2160-0": (0.55, 1.02, "mg/dL", "Creatinina"),
    "3094-0": (19.0, 49.0, "mg/dL", "Ureia"),
    "3084-1": (2.8, 6.7, "mg/dL", "Ácido Úrico"),
    "1920-8": (10.0, 34.0, "U/L", "TGO / AST"),
    "1742-6": (10.0, 49.0, "U/L", "TGP / ALT"),
    "2324-2": (8.0, 38.0, "U/L", "Gama GT"),
    "6768-6": (46.0, 116.0, "U/L", "Fosfatase Alcalina"),
    "3024-7": (0.89, 1.76, "ng/dL", "T4 Livre"),
    "2823-3": (3.5, 5.1, "mmol/L", "Potássio"),
    "5763-8": (70.0, 120.0, "µg/dL", "Zinco Sérico"),
    "789-8": (3.80, 4.80, "10^6/µL", "Hemácias"),
    "4544-3": (36.0, 46.0, "%", "Hematócrito"),
    "787-2": (83.0, 101.0, "fL", "Volume Corpuscular Médio (VCM)"),
    "785-6": (27.0, 32.0, "pg", "Hemoglobina Corpuscular Média (HCM)"),
    "786-4": (31.0, 35.0, "g/dL", "CHCM"),
    "788-0": (11.6, 14.0, "%", "RDW"),
    "6690-2": (4.0, 10.0, "10^3/µL", "Leucócitos Totais"),
    "777-3": (150.0, 450.0, "10^3/µL", "Plaquetas"),
}


def _extrair_numero_e_unidade(resultado_str: str) -> Tuple[Optional[float], str]:
    """Extrai valor numérico e unidade de strings como '13,9 g/dL', '285.000 /µL', '4.970 /µL (70,0 %)'."""
    if not resultado_str:
        return None, ""
    limpo = str(resultado_str).strip()
    # Remove porcentagem secundária entre parênteses como "(70,0 %)"
    limpo_sem_parenteses = re.sub(r"\([^)]*\)", "", limpo).strip()
    m = re.search(r"(\d+(?:\.\d{3})*(?:,\d+)?|\d+(?:\.\d+)?)", limpo_sem_parenteses)
    if not m:
        return None, ""
    num_raw = m.group(1)
    # Se tiver ponto de milhar (ex: 7.100 ou 285.000) e não for decimal curto
    if re.match(r"^\d{1,3}\.\d{3}$", num_raw):
        val = float(num_raw.replace(".", ""))
    else:
        val = float(num_raw.replace(",", "."))
    unidade = limpo_sem_parenteses[m.end():].strip()
    return val, unidade


def popular_historico_longitudinal_3_anos(forcar: bool = False) -> Dict[str, Any]:
    """
    Garante que o banco relacional possua a série longitudinal completa de 10 laudos
    (2023–2026) da paciente Janaina de Assis a partir de `retrospectiva_3_anos_janaina.json`,
    unificando diferentes laboratórios (Frischmann Aisengart / DASA, Fleury Medicina e Saúde,
    Hermes Pardini, Hospital Israelita Albert Einstein e Sabin) para demonstrar a interoperabilidade.
    """
    inicializar_banco()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM diagnostic_reports;")
    total_atual = cursor.fetchone()["total"]

    retrospectiva_path = _paths.RETROSPECTIVA_JSON_PATH
    if not os.path.exists(retrospectiva_path):
        conn.close()
        return {"status": "ignorado", "motivo": "Arquivo retrospectiva_3_anos_janaina.json não encontrado."}

    if total_atual >= 8 and not forcar:
        # Apenas normaliza eventuais faixas de referência nulas no banco atual
        for loinc, (rmin, rmax, unid, _) in FAIXAS_PADRAO_LOINC.items():
            cursor.execute("""
                UPDATE observations
                SET faixa_referencia_min = COALESCE(faixa_referencia_min, ?),
                    faixa_referencia_max = COALESCE(faixa_referencia_max, ?),
                    unidade = CASE WHEN unidade IS NULL OR unidade = '' THEN ? ELSE unidade END
                WHERE codigo_loinc = ?;
            """, (rmin, rmax, unid, loinc))
        conn.commit()
        conn.close()
        return {"status": "ja_populado", "total_reports": total_atual}

    with open(retrospectiva_path, "r", encoding="utf-8") as f:
        laudos_json = json.load(f)

    # Limpa registros incompletos anteriores para inserir os 10 laudos limpos e deduplicados
    cursor.execute("DELETE FROM observations;")
    cursor.execute("DELETE FROM diagnostic_reports;")

    cursor.execute("SELECT id FROM patients WHERE nome LIKE '%Janaina%' LIMIT 1;")
    row_pac = cursor.fetchone()
    if row_pac:
        patient_id = row_pac["id"]
        cursor.execute("""
            UPDATE patients
            SET data_nascimento = '24/06/1980', sexo_biologico = 'F', cns = '700401928374651'
            WHERE id = ?;
        """, (patient_id,))
    else:
        patient_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO patients (id, nome, cpf, cns, data_nascimento, sexo_biologico)
            VALUES (?, 'Janaina de Assis', '284.591.038-44', '700401928374651', '24/06/1980', 'F');
        """, (patient_id,))

    # Laboratórios distintos para evidenciar a unificação interoperável de laudos no gráfico
    laboratorios_rede = [
        "Frischmann Aisengart (DASA)",
        "Fleury Medicina e Saúde",
        "Laboratório Hermes Pardini",
        "Frischmann Aisengart (DASA)",
        "Hospital Israelita Albert Einstein",
        "Fleury Medicina e Saúde",
        "Sabin Medicina Diagnóstica",
        "Laboratório Hermes Pardini",
        "Frischmann Aisengart (DASA)",
        "Hospital Israelita Albert Einstein"
    ]

    laudos_inseridos = 0
    obs_inseridas = 0

    for idx, item_laudo in enumerate(laudos_json):
        report_id = str(uuid.uuid4())
        lab_origem = laboratorios_rede[idx % len(laboratorios_rede)]
        data_coleta = item_laudo.get("data_coleta")
        data_emissao = item_laudo.get("data_liberacao")
        hash_str = f"{patient_id}|{lab_origem}|{data_coleta}|{idx + 1}"
        assinatura_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

        cursor.execute("""
            INSERT INTO diagnostic_reports (id, patient_id, laboratorio_origem, data_coleta, data_emissao, assinatura_hash, versao)
            VALUES (?, ?, ?, ?, ?, ?, 1);
        """, (report_id, patient_id, lab_origem, data_coleta, data_emissao, assinatura_hash))
        laudos_inseridos += 1

        # Achatamento de exames e subitens (Hemograma, HOMA-IR, etc.)
        itens_planos = []
        for ex in item_laudo.get("exames", []):
            if ex.get("subitens"):
                for sub in ex["subitens"]:
                    itens_planos.append(sub)
                # Se o próprio exame pai também tiver valor numérico (ex: Insulina Basal), adiciona-o
                if ex.get("resultado") and any(ch.isdigit() for ch in str(ex.get("resultado"))):
                    itens_planos.append(ex)
            else:
                itens_planos.append(ex)

        loincs_no_laudo = set()
        for ex_item in itens_planos:
            nome_raw = ex_item.get("nome", "").strip()
            res_raw = ex_item.get("resultado", "").strip()
            ref_raw = ex_item.get("referencia", "").strip()

            loinc, nome_padrao = normalizar_loinc_por_analito(nome_raw)
            if nome_raw.upper() == "HOMA-IR":
                loinc, nome_padrao = "72115-9", "Índice HOMA-IR"
            elif "insulina" in nome_raw.lower():
                loinc, nome_padrao = "20448-7", "Insulina Basal"
            elif "zinco" in nome_raw.lower():
                loinc, nome_padrao = "5763-8", "Zinco Sérico"

            if loinc == "0000-0" or loinc in loincs_no_laudo:
                continue

            val_num, unidade_ext = _extrair_numero_e_unidade(res_raw)
            if val_num is None:
                continue

            # Converte Leucócitos e Plaquetas se vierem em /µL (ex: 7100 -> 7.1 10^3/µL)
            if loinc in ("6690-2", "777-3") and val_num > 1000:
                val_num = round(val_num / 1000.0, 2)
                unidade_ext = "10^3/µL"

            rmin, rmax = extrair_faixas_min_max(ref_raw)
            if loinc in FAIXAS_PADRAO_LOINC:
                def_min, def_max, def_unid, def_nome = FAIXAS_PADRAO_LOINC[loinc]
                if rmin is None or rmax is None:
                    rmin, rmax = def_min, def_max
                if not unidade_ext:
                    unidade_ext = def_unid
                nome_padrao = def_nome

            obs_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO observations (
                    id, report_id, codigo_loinc, nome_exame, valor_numerico,
                    valor_texto, unidade, faixa_referencia_min, faixa_referencia_max
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?);
            """, (obs_id, report_id, loinc, nome_padrao, val_num, unidade_ext, rmin, rmax))
            loincs_no_laudo.add(loinc)
            obs_inseridas += 1

    # Garante consentimento ativo para a rede Open Health
    cursor.execute("SELECT id FROM consents WHERE patient_id = ? AND status = 'ativo';", (patient_id,))
    if not cursor.fetchone():
        cid = str(uuid.uuid4())
        exp = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO consents (id, patient_id, hospital_origem, hospital_destino, escopo, status, expira_em)
            VALUES (?, ?, 'Rede Laboratorial Integrada (DASA / Fleury / Pardini)', 'Portal do Paciente Open Health', 'exames_sangue', 'ativo', ?);
        """, (cid, patient_id, exp))

    conn.commit()
    conn.close()
    return {
        "status": "populado",
        "patient_id": patient_id,
        "laudos_inseridos": laudos_inseridos,
        "observacoes_inseridas": obs_inseridas
    }


def listar_biomarcadores_paciente(patient_id: str) -> List[Dict[str, Any]]:
    """
    Lista todos os biomarcadores (`codigo_loinc`) que possuem resultados numéricos para o paciente,
    trazendo a classificação atual do Motor de Gradiente e o Indicador de Tendência Temporal (↗/↘).
    Prioriza na ordenação os marcadores em destaque:
      - Ferritina (2276-4)
      - Hemoglobina (718-7)
      - TSH (3016-3)
      - Glicose (2345-7)
    """
    from classificador import processar_serie_temporal_analito

    inicializar_banco()
    popular_historico_longitudinal_3_anos(forcar=False)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            obs.id as observation_id,
            obs.report_id,
            obs.codigo_loinc,
            obs.nome_exame,
            obs.valor_numerico,
            obs.unidade,
            obs.faixa_referencia_min,
            obs.faixa_referencia_max,
            dr.laboratorio_origem,
            dr.data_coleta,
            dr.data_emissao
        FROM observations obs
        JOIN diagnostic_reports dr ON dr.id = obs.report_id
        WHERE dr.patient_id = ?
          AND obs.valor_numerico IS NOT NULL
          AND obs.codigo_loinc != '0000-0';
    """, (patient_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    por_loinc: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        loinc = r["codigo_loinc"]
        if loinc in FAIXAS_PADRAO_LOINC:
            dmin, dmax, dunid, dnome = FAIXAS_PADRAO_LOINC[loinc]
            if r.get("faixa_referencia_min") is None or r.get("faixa_referencia_max") is None:
                r["faixa_referencia_min"] = dmin
                r["faixa_referencia_max"] = dmax
            if not r.get("unidade"):
                r["unidade"] = dunid
            r["nome_exame"] = dnome
        por_loinc.setdefault(loinc, []).append(r)

    prioridade_loinc = {
        "2276-4": 1,   # Ferritina
        "718-7": 2,    # Hemoglobina
        "3016-3": 3,   # TSH
        "2345-7": 4,   # Glicose de Jejum
        "4548-4": 5,   # HbA1c
        "1989-3": 6,   # Vitamina D
        "13457-7": 7,  # Colesterol LDL
        "20448-7": 8,  # Insulina Basal
        "30522-7": 9,  # PCR Ultrassensível
        "2160-0": 10,  # Creatinina
    }

    resumo_marcadores = []
    for loinc, lista in por_loinc.items():
        serie = processar_serie_temporal_analito(lista)
        ultimo = serie[-1]
        resumo_marcadores.append({
            "codigo_loinc": loinc,
            "nome_exame": ultimo["nome_exame"],
            "unidade": ultimo.get("unidade") or "",
            "total_coletas": len(serie),
            "ultimo_valor": ultimo["valor_numerico"],
            "ultima_data_coleta": ultimo.get("data_coleta"),
            "ultimo_laboratorio": ultimo.get("laboratorio_origem"),
            "faixa_referencia_min": ultimo.get("faixa_referencia_min"),
            "faixa_referencia_max": ultimo.get("faixa_referencia_max"),
            "classificacao_atual": ultimo["classificacao"],
            "tendencia_atual": ultimo["tendencia"],
            "destaque_menu": loinc in ("2276-4", "718-7", "3016-3", "2345-7"),
            "ordem_prioridade": prioridade_loinc.get(loinc, 99),
        })

    resumo_marcadores.sort(key=lambda x: (x["ordem_prioridade"], x["nome_exame"]))
    return resumo_marcadores


def obter_evolucao_biomarcador_paciente(patient_id: str, codigo_loinc: str) -> Optional[Dict[str, Any]]:
    """
    Retorna a série temporal completa de um `codigo_loinc` para um `patient_id`,
    enriquecida com os 4 níveis visuais do Motor de Gradiente e o Indicador de Tendência (↗/↘).
    """
    from classificador import processar_serie_temporal_analito

    inicializar_banco()
    popular_historico_longitudinal_3_anos(forcar=False)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE id = ?;", (patient_id,))
    pac_row = cursor.fetchone()
    if not pac_row:
        conn.close()
        return None
    paciente = dict(pac_row)

    cursor.execute("""
        SELECT
            obs.id as observation_id,
            obs.report_id,
            obs.codigo_loinc,
            obs.nome_exame,
            obs.valor_numerico,
            obs.unidade,
            obs.faixa_referencia_min,
            obs.faixa_referencia_max,
            dr.laboratorio_origem,
            dr.data_coleta,
            dr.data_emissao,
            dr.assinatura_hash
        FROM observations obs
        JOIN diagnostic_reports dr ON dr.id = obs.report_id
        WHERE dr.patient_id = ?
          AND obs.codigo_loinc = ?
          AND obs.valor_numerico IS NOT NULL;
    """, (patient_id, codigo_loinc))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not rows:
        return None

    for r in rows:
        if codigo_loinc in FAIXAS_PADRAO_LOINC:
            dmin, dmax, dunid, dnome = FAIXAS_PADRAO_LOINC[codigo_loinc]
            if r.get("faixa_referencia_min") is None or r.get("faixa_referencia_max") is None:
                r["faixa_referencia_min"] = dmin
                r["faixa_referencia_max"] = dmax
            if not r.get("unidade"):
                r["unidade"] = dunid
            r["nome_exame"] = dnome

    serie = processar_serie_temporal_analito(rows)
    ultimo = serie[-1]
    laboratorios_distintos = sorted(list({s.get("laboratorio_origem") for s in serie if s.get("laboratorio_origem")}))

    return {
        "paciente": paciente,
        "codigo_loinc": codigo_loinc,
        "nome_exame": ultimo["nome_exame"],
        "unidade": ultimo.get("unidade") or "",
        "faixa_referencia_min": ultimo.get("faixa_referencia_min"),
        "faixa_referencia_max": ultimo.get("faixa_referencia_max"),
        "total_registros": len(serie),
        "laboratorios_unificados": laboratorios_distintos,
        "ultimo_resultado": ultimo,
        "serie_temporal": serie,
    }


if __name__ == "__main__":
    inicializar_banco()
    print("[OK] Banco SQLite open_health.db inicializado com sucesso!")
