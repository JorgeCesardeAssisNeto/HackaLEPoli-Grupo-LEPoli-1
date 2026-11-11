-- ==============================================================================
-- SCHEMA OPEN HEALTH - EXAMES DE SANGUE (HL7 FHIR BR Core / LOINC / LGPD)
-- Compatível com: PostgreSQL 14+ / Supabase
-- Arquitetura: Modelo Relacional Normalizado com Métrica Verticalizada (Observation)
-- ==============================================================================

-- Habilita extensão para geração de UUID caso necessário (no PostgreSQL 13+ gen_random_uuid() é nativo)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. TABELA: patients
-- Recurso HL7 FHIR: Patient (Perfil BR Core)
-- Finalidade: Armazena os dados demográficos mínimos e identificadores nacionais
-- ==============================================================================
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    cns VARCHAR(15), -- Cartão Nacional de Saúde (15 dígitos)
    data_nascimento DATE,
    sexo_biologico CHAR(1) CHECK (sexo_biologico IN ('M', 'F')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Comentários de Governança e Metadados (FHIR / LGPD)
COMMENT ON TABLE patients IS 'Recurso Patient (BR Core) - Cadastro do titular de dados conforme Art. 11 da LGPD';
COMMENT ON COLUMN patients.cpf IS 'CPF do paciente com unicidade garantida (Identificador primário civil)';
COMMENT ON COLUMN patients.cns IS 'Cartão Nacional de Saúde (CNS - Padrão DATASUS / ConecteSUS)';
COMMENT ON COLUMN patients.sexo_biologico IS 'Sexo biológico de nascimento (M/F) para referência de parâmetros laboratoriais';

-- Índices de Alta Performance
CREATE INDEX IF NOT EXISTS idx_patients_cpf ON patients (cpf);
CREATE INDEX IF NOT EXISTS idx_patients_cns ON patients (cns) WHERE cns IS NOT NULL;


-- ==============================================================================
-- 2. TABELA: diagnostic_reports
-- Recurso HL7 FHIR: DiagnosticReport
-- Finalidade: Representa o documento/laudo emitido pelo laboratório (metadados e auditoria)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    laboratorio_origem TEXT NOT NULL,
    data_coleta TIMESTAMPTZ,
    data_emissao TIMESTAMPTZ,
    assinatura_hash TEXT, -- Simulação de hash SHA-256 de validação do laudo ICP-Brasil
    versao INTEGER NOT NULL DEFAULT 1, -- Versionamento para imutabilidade e trilha de auditoria
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE diagnostic_reports IS 'Recurso DiagnosticReport - Cabeçalho e metadados de emissão e auditoria de cada laudo';
COMMENT ON COLUMN diagnostic_reports.assinatura_hash IS 'Hash criptográfico (SHA-256) garantindo integridade e conformidade ICP-Brasil';
COMMENT ON COLUMN diagnostic_reports.versao IS 'Versão do laudo para suportar retificações sem sobrescrever o histórico médico';

-- Índices
CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_patient_id ON diagnostic_reports (patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_data_coleta ON diagnostic_reports (data_coleta DESC);


-- ==============================================================================
-- 3. TABELA: observations
-- Recurso HL7 FHIR: Observation (Laboratório / Analitos)
-- Finalidade: Estrutura verticalizada (EAV otimizado) onde cada métrica de exame
--             representa uma linha identificada formalmente pelo código LOINC
-- ==============================================================================
CREATE TABLE IF NOT EXISTS observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES diagnostic_reports(id) ON DELETE CASCADE,
    codigo_loinc VARCHAR(20) NOT NULL, -- Código universal LOINC (ex: 718-7, 2276-4)
    nome_exame TEXT NOT NULL,          -- Nome canônico ou de exibição clínica (ex: Hemoglobina)
    valor_numerico NUMERIC(14, 4),     -- Preenchido quando o resultado for quantitativo
    valor_texto TEXT,                  -- Preenchido quando o resultado for qualitativo (ex: Reagente/Negativo)
    unidade VARCHAR(50),               -- Unidade de medida padronizada (Padrão UCUM, ex: g/dL, mg/dL)
    faixa_referencia_min NUMERIC(14, 4),
    faixa_referencia_max NUMERIC(14, 4),
    
    -- Validação: deve conter ao menos um valor (numérico ou textual)
    CONSTRAINT chk_observation_valor CHECK (valor_numerico IS NOT NULL OR valor_texto IS NOT NULL)
);

COMMENT ON TABLE observations IS 'Recurso Observation (FHIR) - Cada analito laboratorial normalizado com código LOINC e UCUM';
COMMENT ON COLUMN observations.codigo_loinc IS 'Código internacional padronizado LOINC da métrica';
COMMENT ON COLUMN observations.unidade IS 'Unidade de medida aderente ao padrão UCUM (Unified Code for Units of Measure)';

-- Índices de Consulta Clínica e Temporal
CREATE INDEX IF NOT EXISTS idx_observations_report_id ON observations (report_id);
CREATE INDEX IF NOT EXISTS idx_observations_codigo_loinc ON observations (codigo_loinc);
CREATE INDEX IF NOT EXISTS idx_observations_loinc_report ON observations (codigo_loinc, report_id);


-- ==============================================================================
-- 4. TABELA: consents
-- Recurso HL7 FHIR: Consent (Camada de Governança & LGPD)
-- Finalidade: Rastreia a base legal do compartilhamento de dados sensíveis de saúde
-- ==============================================================================
CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    hospital_origem TEXT NOT NULL,
    hospital_destino TEXT NOT NULL,
    escopo TEXT NOT NULL DEFAULT 'exames_sangue',
    status VARCHAR(20) NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'revogado')),
    expira_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE consents IS 'Recurso Consent (FHIR / LGPD Art. 7º e 11) - Gestão do ciclo de vida da autorização de interoperabilidade';
COMMENT ON COLUMN consents.status IS 'Estado atual do consentimento: ativo ou revogado explicitamente pelo paciente';
COMMENT ON COLUMN consents.expira_em IS 'Data limite de expiração da concessão de compartilhamento';

-- Índices de Auditoria e Verificação Rápida de Autorização
CREATE INDEX IF NOT EXISTS idx_consents_patient_status ON consents (patient_id, status);
CREATE INDEX IF NOT EXISTS idx_consents_expira_em ON consents (expira_em) WHERE status = 'ativo';
