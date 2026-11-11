import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def gerar_diagrama_conversa_tabelas(output_path="diagrama_conversa_tabelas.png"):
    # Configuração de alta resolução e estilo profissional
    fig, ax = plt.subplots(figsize=(15, 9.5), dpi=300)
    fig.patch.set_facecolor('#0f172a') # Dark slate moderno e elegante
    ax.set_facecolor('#0f172a')
    
    # Desabilita eixos
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    
    # Título Principal do Diagrama
    ax.text(50, 96, "ARQUITETURA RELACIONAL OPEN HEALTH — CONVERSA ENTRE AS TABELAS", 
            ha='center', va='center', color='#f8fafc', fontsize=18, weight='bold', fontfamily='sans-serif')
    ax.text(50, 93, "Interoperabilidade Semântica Baseada em HL7 FHIR (Perfil BR Core), LOINC e Governança LGPD", 
            ha='center', va='center', color='#94a3b8', fontsize=11, fontfamily='sans-serif')
    
    # Função para desenhar tabela estruturada (estilo Card de Banco de Dados)
    def desenhar_tabela(x, y, w, h, titulo, subtitulo, cor_header, campos, icone="TABLE"):
        # Sombra suave
        shadow = patches.FancyBboxPatch((x+0.5, y-0.5), w, h, boxstyle="round,pad=0.2,rounding_size=1.5",
                                       fc='#000000', ec='none', alpha=0.35, zorder=2)
        ax.add_patch(shadow)
        
        # Corpo do card
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.5",
                                      fc='#1e293b', ec='#334155', lw=1.5, zorder=3)
        ax.add_patch(card)
        
        # Cabeçalho da tabela
        h_header = 4.2
        header = patches.FancyBboxPatch((x, y + h - h_header), w, h_header,
                                        boxstyle="round,pad=0.2,rounding_size=1.2",
                                        fc=cor_header, ec='none', zorder=4)
        ax.add_patch(header)
        
        # Retângulo para cobrir a base arredondada do cabeçalho
        ax.add_patch(patches.Rectangle((x, y + h - h_header), w, 1.2, fc=cor_header, ec='none', zorder=4))
        
        # Texto do cabeçalho
        ax.text(x + 1.2, y + h - 1.8, titulo, color='#ffffff', fontsize=11, weight='bold', zorder=5)
        ax.text(x + 1.2, y + h - 3.2, subtitulo, color='#f1f5f9', fontsize=7.5, style='italic', zorder=5)
        
        # Linha divisória
        ax.plot([x, x + w], [y + h - h_header, y + h - h_header], color='#475569', lw=1, zorder=5)
        
        # Campos
        y_pos = y + h - h_header - 2.0
        for tipo, nome, tipo_dado, desc in campos:
            # Badge para PK/FK/UK
            if tipo == "PK":
                badge_c = '#e11d48'
                badge_t = 'PK'
            elif tipo == "FK":
                badge_c = '#0284c7'
                badge_t = 'FK'
            elif tipo == "UK":
                badge_c = '#d97706'
                badge_t = 'UK'
            else:
                badge_c = '#475569'
                badge_t = '  '
            
            if tipo in ["PK", "FK", "UK"]:
                bb = patches.FancyBboxPatch((x + 1.0, y_pos - 0.7), 2.2, 1.5, 
                                            boxstyle="round,pad=0.1,rounding_size=0.4",
                                            fc=badge_c, ec='none', zorder=5)
                ax.add_patch(bb)
                ax.text(x + 2.1, y_pos, badge_t, color='#ffffff', fontsize=6.5, weight='bold', ha='center', va='center', zorder=6)
            
            # Nome do Campo
            cor_nome = '#f8fafc' if tipo in ["PK", "FK"] else '#e2e8f0'
            peso = 'bold' if tipo in ["PK", "FK"] else 'normal'
            ax.text(x + 3.8, y_pos, nome, color=cor_nome, fontsize=7.8, weight=peso, va='center', zorder=5)
            
            # Tipo de Dado
            ax.text(x + w - 1.2, y_pos, tipo_dado, color='#94a3b8', fontsize=7.0, ha='right', va='center', 
                    fontfamily='monospace', zorder=5)
            
            y_pos -= 2.1

    # ==================== TABELAS ====================
    # 1. PATIENTS (Superior Esquerdo)
    campos_patients = [
        ("PK", "id", "UUID", "Chave Primária"),
        ("  ", "nome", "TEXT", "Nome Completo"),
        ("UK", "cpf", "VARCHAR(14)", "Identificador Único"),
        ("  ", "cns", "VARCHAR(15)", "Cartão Nac. Saúde"),
        ("  ", "data_nascimento", "DATE", "Data Nascimento"),
        ("  ", "sexo_biologico", "CHAR(1)", "'M' | 'F'"),
        ("  ", "created_at", "TIMESTAMPTZ", "Auditoria")
    ]
    desenhar_tabela(6, 60, 38, 26, "patients", "HL7 FHIR: Patient (Perfil BR Core)", "#0369a1", campos_patients)
    
    # 2. CONSENTS (Superior Direito)
    campos_consents = [
        ("PK", "id", "UUID", "Chave Primária"),
        ("FK", "patient_id", "UUID", "Ref: patients.id"),
        ("  ", "hospital_origem", "TEXT", "Entidade Custodiante"),
        ("  ", "hospital_destino", "TEXT", "Entidade Receptora"),
        ("  ", "escopo", "TEXT", "'exames_sangue'"),
        ("  ", "status", "VARCHAR(20)", "'ativo' | 'revogado'"),
        ("  ", "expira_em", "TIMESTAMPTZ", "Limite Validade"),
        ("  ", "created_at", "TIMESTAMPTZ", "Timestamp Concessão")
    ]
    desenhar_tabela(56, 58, 38, 28, "consents", "HL7 FHIR: Consent (Camada de Governança LGPD)", "#047857", campos_consents)
    
    # 3. DIAGNOSTIC_REPORTS (Inferior Esquerdo)
    campos_reports = [
        ("PK", "id", "UUID", "Chave Primária"),
        ("FK", "patient_id", "UUID", "Ref: patients.id"),
        ("  ", "laboratorio_origem", "TEXT", "Laboratório / Hospital"),
        ("  ", "data_coleta", "TIMESTAMPTZ", "Momento da Coleta"),
        ("  ", "data_emissao", "TIMESTAMPTZ", "Data da Liberação"),
        ("  ", "assinatura_hash", "TEXT", "Assinatura ICP-Brasil"),
        ("  ", "versao", "INTEGER", "Versionamento / Trilha"),
        ("  ", "created_at", "TIMESTAMPTZ", "Auditoria do Registro")
    ]
    desenhar_tabela(6, 17, 38, 28, "diagnostic_reports", "HL7 FHIR: DiagnosticReport (Laudo Pericial)", "#7c3aed", campos_reports)
    
    # 4. OBSERVATIONS (Inferior Direito)
    campos_observations = [
        ("PK", "id", "UUID", "Chave Primária"),
        ("FK", "report_id", "UUID", "Ref: diagnostic_reports.id"),
        ("  ", "codigo_loinc", "VARCHAR(20)", "Código LOINC Universal"),
        ("  ", "nome_exame", "TEXT", "Canônico / Exibição"),
        ("  ", "valor_numerico", "NUMERIC(14,4)", "Resultado Quantitativo"),
        ("  ", "valor_texto", "TEXT", "Resultado Qualitativo"),
        ("  ", "unidade", "VARCHAR(50)", "Padrão UCUM (mg/dL...)"),
        ("  ", "faixa_referencia_min", "NUMERIC(14,4)", "Limite Inferior"),
        ("  ", "faixa_referencia_max", "NUMERIC(14,4)", "Limite Superior")
    ]
    desenhar_tabela(56, 15, 38, 30, "observations", "HL7 FHIR: Observation (Formato Vertical EAV)", "#b45309", campos_observations)
    
    # ==================== CONVERSAS E RELACIONAMENTOS ====================
    
    # 1. Relacionamento: PATIENTS -> DIAGNOSTIC_REPORTS (1:N)
    # Linha vertical com conector
    ax.annotate('', xy=(25, 45.5), xytext=(25, 60),
                arrowprops=dict(arrowstyle="->, head_length=0.7, head_width=0.4",
                                color="#38bdf8", lw=2.2, linestyle='-'))
    # Cardinalidade
    ax.text(26.2, 58.5, "1", color="#38bdf8", fontsize=11, weight='bold')
    ax.text(26.2, 46.5, "N", color="#38bdf8", fontsize=11, weight='bold')
    
    # Balão de conversa 1
    box1 = patches.FancyBboxPatch((10, 50.5), 30, 4.0, boxstyle="round,pad=0.2,rounding_size=0.8",
                                 fc='#0f172a', ec='#38bdf8', lw=1.5, zorder=7)
    ax.add_patch(box1)
    ax.text(25, 53.0, "CONVERSA: IDENTIFICAÇÃO DO TITULAR", color='#38bdf8', fontsize=7.5, weight='bold', ha='center')
    ax.text(25, 51.5, "diagnostic_reports.patient_id = patients.id (Histórico Clínico Unificado)", 
            color='#e2e8f0', fontsize=6.5, ha='center')
    
    # 2. Relacionamento: PATIENTS -> CONSENTS (1:N)
    ax.annotate('', xy=(56, 74), xytext=(44, 74),
                arrowprops=dict(arrowstyle="->, head_length=0.7, head_width=0.4",
                                color="#34d399", lw=2.2, linestyle='-'))
    # Cardinalidade
    ax.text(44.8, 75.2, "1", color="#34d399", fontsize=11, weight='bold')
    ax.text(54.2, 75.2, "N", color="#34d399", fontsize=11, weight='bold')
    
    # Balão de conversa 2
    box2 = patches.FancyBboxPatch((41, 78.5), 23, 4.2, boxstyle="round,pad=0.2,rounding_size=0.8",
                                 fc='#0f172a', ec='#34d399', lw=1.5, zorder=7)
    ax.add_patch(box2)
    ax.text(52.5, 81.2, "CONVERSA: GOVERNANÇA LGPD", color='#34d399', fontsize=7.5, weight='bold', ha='center')
    ax.text(52.5, 79.7, "consents.patient_id = patients.id\n(Autorização de Trânsito entre Hospitais)", 
            color='#e2e8f0', fontsize=6.2, ha='center')

    # 3. Relacionamento: DIAGNOSTIC_REPORTS -> OBSERVATIONS (1:N)
    ax.annotate('', xy=(56, 30), xytext=(44, 30),
                arrowprops=dict(arrowstyle="->, head_length=0.7, head_width=0.4",
                                color="#f59e0b", lw=2.2, linestyle='-'))
    # Cardinalidade
    ax.text(44.8, 31.2, "1", color="#f59e0b", fontsize=11, weight='bold')
    ax.text(54.2, 31.2, "N", color="#f59e0b", fontsize=11, weight='bold')
    
    # Balão de conversa 3
    box3 = patches.FancyBboxPatch((38, 33.5), 24, 4.5, boxstyle="round,pad=0.2,rounding_size=0.8",
                                 fc='#0f172a', ec='#f59e0b', lw=1.5, zorder=7)
    ax.add_patch(box3)
    ax.text(50, 36.3, "CONVERSA: EXPLOSÃO VERTICAL (LOINC)", color='#f59e0b', fontsize=7.5, weight='bold', ha='center')
    ax.text(50, 34.6, "observations.report_id = diagnostic_reports.id\n(Cada métrica vira 1 linha com LOINC e UCUM)", 
            color='#e2e8f0', fontsize=6.2, ha='center')

    # 4. Relacionamento de Controle / Gatekeeper: CONSENTS -> OBSERVATIONS / REPORTS
    # Linha tracejada descendo de CONSENTS para validação de acesso
    ax.annotate('', xy=(75, 45.5), xytext=(75, 58),
                arrowprops=dict(arrowstyle="->, head_length=0.6, head_width=0.4",
                                color="#a855f7", lw=1.8, linestyle='--'))
    
    box4 = patches.FancyBboxPatch((64, 49), 24, 4.0, boxstyle="round,pad=0.2,rounding_size=0.8",
                                 fc='#0f172a', ec='#a855f7', lw=1.5, zorder=7)
    ax.add_patch(box4)
    ax.text(76, 51.5, "GATEKEEPER DE SEGURANÇA", color='#c084fc', fontsize=7.5, weight='bold', ha='center')
    ax.text(76, 50.0, "Consulta de dados liberada apenas se\nstatus='ativo' e expira_em > NOW()", 
            color='#e2e8f0', fontsize=6.0, ha='center')

    # Rodapé Técnico
    ax.text(50, 5.0, "PADRÕES EMBUTIDOS: HL7 FHIR Release 4 | LOINC v2.76 | UCUM | ICP-Brasil (SHA-256) | LGPD Art. 5º, 7º e 11", 
            ha='center', va='center', color='#64748b', fontsize=8.5, weight='bold', fontfamily='monospace')
    ax.text(50, 2.5, "Hackathon LEPoli — Coalizão Open Health Brasil — Modelo Relacional Normalizado de Alto Desempenho", 
            ha='center', va='center', color='#475569', fontsize=8.0, fontfamily='sans-serif')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Diagrama salvo com sucesso em: {output_path}")

if __name__ == '__main__':
    gerar_diagrama_conversa_tabelas()
