
        let motorSelecionado = 'nuvem';
        let arquivoSelecionado = null;
        let pacienteAtualId = null;
        let laudoAtualId = null;
        let listaPacientesCache = [];
        let dadosLaudoColunasCache = null;
        let filtroColunaAtual = 'todas';
        let modoExibicaoAtual = 'matrix';

        // Inicialização com Abertura Direta do Prontuário
        document.addEventListener('DOMContentLoaded', async () => {
            await carregarListaPacientes();
            // Se existir paciente (Janaina de Assis), abre automaticamente seu prontuário com os 10 laudos e o gráfico longitudinal!
            if (listaPacientesCache && listaPacientesCache.length > 0) {
                const pacDefault = listaPacientesCache.find(p => p.nome.includes('Janaina')) || listaPacientesCache[0];
                await abrirPaciente(pacDefault.id);
            }
        });

        // Alternância do painel de upload
        function alternarPainelUpload() {
            const body = document.getElementById('upload-body');
            const icon = document.getElementById('upload-toggle-icon');
            if (body.classList.contains('open')) {
                body.classList.remove('open');
                icon.innerText = '▼';
            } else {
                body.classList.add('open');
                icon.innerText = '▲';
            }
        }

        function selecionarMotor(tipo) {
            motorSelecionado = tipo;
            document.querySelectorAll('.engine-option').forEach(el => el.classList.remove('active'));
            document.getElementById('opt-' + tipo).classList.add('active');
        }

        // Drag & Drop com Auto-Envio Imediato
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const btnProcessar = document.getElementById('btn-processar');

        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                arquivoSelecionado = e.dataTransfer.files[0];
                atualizarInterfaceArquivo();
                enviarArquivo();
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                arquivoSelecionado = fileInput.files[0];
                atualizarInterfaceArquivo();
                enviarArquivo();
            }
        });

        function atualizarInterfaceArquivo() {
            document.getElementById('upload-title').innerHTML = `Arquivo Selecionado: <strong>${arquivoSelecionado.name}</strong>`;
            document.getElementById('upload-subtitle').innerText = `Tamanho: ${(arquivoSelecionado.size / 1024).toFixed(1)} KB — Processando...`;
            btnProcessar.disabled = false;
        }

        async function enviarArquivo() {
            if (!arquivoSelecionado) return;
            document.getElementById('loading-box').style.display = 'block';
            btnProcessar.disabled = true;

            const formData = new FormData();
            formData.append('arquivo', arquivoSelecionado);
            formData.append('motor', motorSelecionado);

            try {
                const response = await fetch('/api/extrair', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.erro || 'Falha ao processar o exame');

                const msgMotor = data.motor || 'Padrão';
                const totalMetricas = (data.db_status && data.db_status.observacoes_inseridas) ? data.db_status.observacoes_inseridas : (data.exames ? data.exames.length : 0);
                alert(`✅ Sucesso! Exame processado e inserido no banco relacional.\nMotor: ${msgMotor}\nTotal de métricas LOINC: ${totalMetricas}\nAtualizando prontuário...`);
                // Redireciona e atualiza a visão do paciente
                await carregarListaPacientes();
                const targetPatient = (data.db_status && data.db_status.patient_id) || pacienteAtualId;
                if (targetPatient) {
                    await abrirPaciente(targetPatient);
                }
            } catch (err) {
                alert('Erro ao processar: ' + err.message);
            } finally {
                document.getElementById('loading-box').style.display = 'none';
                btnProcessar.disabled = false;
                if (fileInput) fileInput.value = '';
                arquivoSelecionado = null;
            }
        }

        // ==========================================
        // NAVEGAÇÃO ENTRE OS 3 NÍVEIS
        // ==========================================
        function navegarParaPacientes() {
            document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
            document.getElementById('view-pacientes').classList.add('active');
            
            document.getElementById('bc-sep-1').style.display = 'none';
            document.getElementById('bc-paciente').style.display = 'none';
            document.getElementById('bc-sep-2').style.display = 'none';
            document.getElementById('bc-laudo').style.display = 'none';
            
            pacienteAtualId = null;
            laudoAtualId = null;
            carregarListaPacientes();
        }

        function voltarParaPacienteAtual() {
            if (pacienteAtualId) {
                abrirPaciente(pacienteAtualId);
            }
        }

        // ==========================================
        // NÍVEL 1: CARREGAR LISTA DE PACIENTES
        // ==========================================
        let todosLaudosGeralCache = [];

        function abrirPacientePrincipal() {
            if (listaPacientesCache.length > 0) {
                const pac = listaPacientesCache.find(p => p.nome.includes('Janaina')) || listaPacientesCache[0];
                abrirPaciente(pac.id);
            } else {
                alert("Nenhum paciente encontrado.");
            }
        }

        async function carregarListaPacientes() {
            try {
                const res = await fetch('/api/pacientes');
                const pacientes = await res.json();
                listaPacientesCache = pacientes;
                document.getElementById('badge-total-pacientes').innerText = `${pacientes.length} Pacientes Cadastrados`;

                renderizarTabelaPacientes(pacientes);

                // Carrega também a lista unificada de todos os laudos na tela principal
                await carregarTodosLaudosGeral();
            } catch (e) {
                console.error("Erro ao listar pacientes:", e);
            }
        }

        async function carregarTodosLaudosGeral() {
            try {
                const res = await fetch('/api/todos_laudos');
                const laudos = await res.json();
                todosLaudosGeralCache = Array.isArray(laudos) ? laudos : [];

                const badgeTotal = document.getElementById('badge-total-laudos-geral');
                if (badgeTotal) badgeTotal.innerText = `${todosLaudosGeralCache.length} Laudos Unificados`;

                const tbody = document.getElementById('tbody-todos-laudos-geral');
                if (!tbody) return;

                if (todosLaudosGeralCache.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Nenhum laudo encontrado no banco relacional.</td></tr>`;
                    return;
                }

                tbody.innerHTML = todosLaudosGeralCache.map(r => `
                    <tr>
                        <td><strong>${r.nome_paciente}</strong></td>
                        <td><span style="color:var(--primary); font-weight:700;">🏥 ${r.laboratorio_origem}</span></td>
                        <td><strong>${r.data_coleta || '—'}</strong></td>
                        <td>${r.data_emissao || '—'}</td>
                        <td><span style="font-weight:700; color:var(--primary);">v${r.versao}</span></td>
                        <td><span class="hash-code" title="${r.assinatura_hash}">${r.assinatura_hash}</span></td>
                        <td><span class="badge badge-active">${r.total_observacoes} Métricas LOINC</span></td>
                        <td style="text-align: right; white-space: nowrap;">
                            <button class="btn-action btn-sm" onclick="abrirPaciente('${r.patient_id}')" style="margin-right:4px;">
                                📈 Ver no Gráfico
                            </button>
                            <button class="btn-secondary btn-sm" onclick="abrirLaudoObservacoes('${r.id}')">
                                🔬 Colunas LOINC
                            </button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error("Erro ao carregar todos os laudos:", err);
            }
        }

        function renderizarTabelaPacientes(pacientes) {
            const tbody = document.getElementById('tbody-pacientes');
            if (!pacientes || pacientes.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="empty-state"><div class="empty-state-icon">👤</div>Nenhum paciente cadastrado ainda. Envie um laudo em PDF para criar o primeiro!</td></tr>`;
                return;
            }

            tbody.innerHTML = pacientes.map(p => {
                const badgeConsent = p.total_consents_ativos > 0 
                    ? `<span class="badge badge-active">Ativo (${p.total_consents_ativos})</span>`
                    : `<span class="badge badge-revoked">Nenhum Ativo</span>`;

                return `
                    <tr>
                        <td><strong>${p.nome}</strong></td>
                        <td><code>${p.cpf}</code></td>
                        <td>${p.cns || '—'}</td>
                        <td>${p.data_nascimento || '—'}</td>
                        <td>${p.sexo_biologico || '—'}</td>
                        <td><span style="font-weight:700; color:var(--primary);">${p.total_reports} Laudo(s)</span></td>
                        <td>${badgeConsent}</td>
                        <td style="text-align: right;">
                            <button class="btn-action btn-sm" onclick="abrirPaciente('${p.id}')">
                                📂 Entrar no Paciente →
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function filtrarPacientes() {
            const q = document.getElementById('search-paciente').value.toLowerCase();
            const filtrados = listaPacientesCache.filter(p => 
                (p.nome && p.nome.toLowerCase().includes(q)) || 
                (p.cpf && p.cpf.toLowerCase().includes(q))
            );
            renderizarTabelaPacientes(filtrados);
        }

        // ==========================================
        // NÍVEL 2: ABRIR DETALHES DO PACIENTE
        // ==========================================
        async function abrirPaciente(patientId) {
            pacienteAtualId = patientId;
            try {
                const res = await fetch(`/api/paciente/${patientId}`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.erro || 'Falha ao buscar detalhes do paciente');

                const pac = data.paciente;
                const reports = data.reports || [];
                const consents = data.consents || [];

                // Atualiza Breadcrumbs
                document.getElementById('bc-sep-1').style.display = 'inline-block';
                const bcPac = document.getElementById('bc-paciente');
                bcPac.style.display = 'inline-flex';
                bcPac.innerHTML = `👤 <strong>${pac.nome}</strong>`;
                document.getElementById('bc-sep-2').style.display = 'none';
                document.getElementById('bc-laudo').style.display = 'none';

                // Banner de Informações do Paciente
                document.getElementById('banner-paciente-info').innerHTML = `
                    <div class="info-col"><label>Nome do Paciente</label><div>${pac.nome}</div></div>
                    <div class="info-col"><label>CPF (BR Core)</label><div>${pac.cpf}</div></div>
                    <div class="info-col"><label>CNS (SUS)</label><div>${pac.cns || '—'}</div></div>
                    <div class="info-col"><label>Data Nascimento</label><div>${pac.data_nascimento || '—'}</div></div>
                    <div class="info-col"><label>Sexo Biológico</label><div>${pac.sexo_biologico || '—'}</div></div>
                    <div class="info-col"><label>UUID Paciente (PK)</label><div><span class="uuid-code" title="${pac.id}">${pac.id}</span></div></div>
                `;

                // Tabela de Consentimentos Anexados ao Paciente
                document.getElementById('badge-total-consents').innerText = `${consents.length} Consentimentos`;
                const tbodyConsents = document.getElementById('tbody-consents-paciente');
                if (consents.length === 0) {
                    tbodyConsents.innerHTML = `<tr><td colspan="7" class="empty-state">Nenhum consentimento cadastrado para este paciente.</td></tr>`;
                } else {
                    tbodyConsents.innerHTML = consents.map(c => `
                        <tr>
                            <td><strong>${c.hospital_origem}</strong></td>
                            <td>${c.hospital_destino}</td>
                            <td><code>${c.escopo}</code></td>
                            <td><span class="badge ${c.status === 'ativo' ? 'badge-active' : 'badge-revoked'}">${c.status.toUpperCase()}</span></td>
                            <td>${c.expira_em || 'Indeterminado'}</td>
                            <td><span class="uuid-code" title="${c.id}">${c.id}</span></td>
                            <td style="text-align: right;">
                                <button class="btn-secondary btn-sm" onclick="alternarConsentimento('${c.id}')">
                                    ${c.status === 'ativo' ? 'Revogar Autorização' : 'Reativar'}
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }

                // Tabela de DiagnosticReports do Paciente
                document.getElementById('badge-total-reports').innerText = `${reports.length} Laudos`;
                const tbodyReports = document.getElementById('tbody-reports-paciente');
                if (reports.length === 0) {
                    tbodyReports.innerHTML = `<tr><td colspan="7" class="empty-state">Nenhum laudo emitido para este paciente.</td></tr>`;
                } else {
                    tbodyReports.innerHTML = reports.map(r => `
                        <tr>
                            <td><strong>${r.laboratorio_origem}</strong></td>
                            <td>${r.data_coleta || '—'}</td>
                            <td>${r.data_emissao || '—'}</td>
                            <td><span style="font-weight:700; color:var(--primary);">v${r.versao}</span></td>
                            <td><span class="hash-code" title="${r.assinatura_hash}">${r.assinatura_hash}</span></td>
                            <td><span class="badge badge-active">${r.total_observacoes} Métricas LOINC</span></td>
                            <td style="text-align: right;">
                                <button class="btn-action btn-sm" onclick="abrirLaudoObservacoes('${r.id}')">
                                    🔬 Entrar nas Observações (Ver por Colunas) →
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }

                // Alterna visualização
                document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
                document.getElementById('view-paciente-detalhe').classList.add('active');

                // Carrega o Módulo Parte 1: Evolução Longitudinal & Classificação por Gradiente
                await carregarBiomarcadoresPaciente(patientId);

            } catch (e) {
                alert("Erro ao carregar detalhes do paciente: " + e.message);
            }
        }

        // =========================================================================
        // MÓDULO PARTE 1: EVOLUÇÃO LONGITUDINAL, NORMA DE 5 CLASSIFICAÇÕES E RAG
        // =========================================================================
        let biomarcadoresCache = [];
        let loincSelecionadoAtual = '2276-4';
        let evolucaoAtualCache = null;
        let modoNormaAtual = '5'; // '5': Norma de 5 Classificações Clínicas | '4': 4 Níveis Simplificados UX

        function alternarModoNorma(modo) {
            modoNormaAtual = modo;
            const btn5 = document.getElementById('btn-norma-5');
            const btn4 = document.getElementById('btn-norma-4');
            if (btn5) btn5.classList.toggle('active', modo === '5');
            if (btn4) btn4.classList.toggle('active', modo === '4');

            const thClass = document.getElementById('th-col-classificacao');
            if (thClass) {
                thClass.innerText = modo === '5' ? 'Classificação (Norma 5 Estados)' : 'Classificação (4 Níveis UX)';
            }

            renderizarLegendaGrafico();
            if (evolucaoAtualCache) {
                renderizarBannerGradienteAtual(evolucaoAtualCache);
                renderizarGraficoEvolucaoSVG(evolucaoAtualCache);
                renderizarTabelaHistoricoBiomarcador(evolucaoAtualCache);
            }
            renderizarAbasBiomarcadores();
        }

        function obterClassificacaoAtiva(clf) {
            if (!clf) {
                return {
                    nivel: 0,
                    codigo: 'INDETERMINADO',
                    rotulo: 'Sem Faixa',
                    cor_nome: 'Cinza',
                    cor_hex: '#94a3b8',
                    cor_bg: 'rgba(148, 163, 184, 0.12)',
                    cor_borda: 'rgba(148, 163, 184, 0.30)',
                    mensagem_paciente: 'Consulte a referência textual do laudo com seu médico.',
                    equivalencia_clinica: 'Sem Faixa Numérica'
                };
            }
            if (modoNormaAtual === '4' && clf.norma_4_niveis) {
                const n4 = clf.norma_4_niveis;
                const bgMap = {
                    '#10b981': 'rgba(16, 185, 129, 0.14)',
                    '#f59e0b': 'rgba(245, 158, 11, 0.15)',
                    '#f97316': 'rgba(249, 115, 22, 0.15)',
                    '#ef4444': 'rgba(239, 68, 68, 0.16)'
                };
                return {
                    nivel: n4.nivel_4,
                    codigo: n4.codigo_4,
                    rotulo: n4.rotulo_4,
                    cor_nome: n4.cor_nome_4,
                    cor_hex: n4.cor_hex_4,
                    cor_bg: bgMap[n4.cor_hex_4] || 'rgba(148, 163, 184, 0.12)',
                    cor_borda: n4.cor_hex_4,
                    mensagem_paciente: n4.mensagem_4,
                    equivalencia_clinica: 'Mapeamento UX Paciente (4 Níveis Seguros)'
                };
            }
            return clf; // Norma de 5 Classificações por padrão
        }

        function renderizarLegendaGrafico() {
            const container = document.getElementById('legend-items-container');
            if (!container) return;
            const refMin = evolucaoAtualCache ? evolucaoAtualCache.faixa_referencia_min : null;
            const refMax = evolucaoAtualCache ? evolucaoAtualCache.faixa_referencia_max : null;
            const unid = evolucaoAtualCache ? evolucaoAtualCache.unidade : '';
            const refTxt = (refMin !== null && refMax !== null) ? `${refMin} – ${refMax} ${unid}` : '—';

            if (modoNormaAtual === '5') {
                container.innerHTML = `
                    <span class="legend-item">
                        <span style="width:14px; height:10px; background:rgba(16, 185, 129, 0.18); border:1px dashed #10b981; display:inline-block; border-radius:2px;"></span>
                        Faixa de Referência (<span id="legend-ref-range">${refTxt}</span>)
                    </span>
                    <span class="legend-item"><span class="bm-dot" style="background:#10b981;"></span> 1. Normal (10%–90%)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#eab308;"></span> 2. Limítrofe (&lt;10% / &gt;90% int.)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f59e0b;"></span> 3. Alterado Leve (&le;15% ext. / Grau 1)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f97316;"></span> 4. Alterado Moderado (15%–50% / Grau 2)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#ef4444;"></span> 5. Alteração Acentuada (&gt;50% / Grau 3–4)</span>
                `;
            } else {
                container.innerHTML = `
                    <span class="legend-item">
                        <span style="width:14px; height:10px; background:rgba(16, 185, 129, 0.18); border:1px dashed #10b981; display:inline-block; border-radius:2px;"></span>
                        Faixa de Referência (<span id="legend-ref-range">${refTxt}</span>)
                    </span>
                    <span class="legend-item"><span class="bm-dot" style="background:#10b981;"></span> Normal (10%–90%)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f59e0b;"></span> Limítrofe / Atenção (&lt;10% / &gt;90% ou &le;15% ext.)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#f97316;"></span> Alterado Moderado (15%–50%)</span>
                    <span class="legend-item"><span class="bm-dot" style="background:#ef4444;"></span> Alteração Acentuada (&gt;50%)</span>
                `;
            }
        }

        async function carregarBiomarcadoresPaciente(patientId) {
            try {
                const res = await fetch(`/api/paciente/${patientId}/biomarcadores`);
                const lista = await res.json();
                biomarcadoresCache = Array.isArray(lista) ? lista : [];

                const tabsContainer = document.getElementById('biomarker-tabs-bar');
                if (biomarcadoresCache.length === 0) {
                    tabsContainer.innerHTML = `<div style="color:var(--text-muted); font-size:0.84rem;">Nenhum biomarcador numérico registrado para este paciente.</div>`;
                    return;
                }

                // Seleciona Ferritina (2276-4) por padrão se existir, ou o primeiro da lista
                const temAtual = biomarcadoresCache.some(b => b.codigo_loinc === loincSelecionadoAtual);
                if (!temAtual) {
                    const ferritina = biomarcadoresCache.find(b => b.codigo_loinc === '2276-4');
                    loincSelecionadoAtual = ferritina ? '2276-4' : biomarcadoresCache[0].codigo_loinc;
                }

                renderizarAbasBiomarcadores();
                await selecionarBiomarcador(loincSelecionadoAtual);
            } catch (err) {
                console.error("Erro ao carregar biomarcadores:", err);
            }
        }

        function renderizarAbasBiomarcadores() {
            const tabsContainer = document.getElementById('biomarker-tabs-bar');
            tabsContainer.innerHTML = biomarcadoresCache.map(bm => {
                const isActive = bm.codigo_loinc === loincSelecionadoAtual ? 'active' : '';
                const clfAtivo = obterClassificacaoAtiva(bm.classificacao_atual);
                const corDot = clfAtivo.cor_hex || '#10b981';
                const tend = bm.tendencia_atual || {};
                const badgeTend = tend.exibir_badge_tendencia
                    ? `<span class="bm-trend-pill" title="${tend.texto_tendencia}">${tend.seta} ${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}%</span>`
                    : (tend.seta && tend.seta !== '→' ? `<span style="color:#94a3b8; font-size:0.75rem;">${tend.seta}</span>` : '');

                return `
                    <button type="button" class="bm-tab ${isActive}" onclick="selecionarBiomarcador('${bm.codigo_loinc}')">
                        <span class="bm-dot" style="background:${corDot};"></span>
                        <span>${bm.nome_exame}</span>
                        <span class="bm-loinc-tag">${bm.codigo_loinc}</span>
                        ${badgeTend}
                    </button>
                `;
            }).join('');
        }

        async function selecionarBiomarcador(codigoLoinc) {
            loincSelecionadoAtual = codigoLoinc;
            renderizarAbasBiomarcadores();
            const ragCard = document.getElementById('card-rag-resultado');
            if (ragCard) {
                ragCard.classList.remove('open');
                ragCard.innerHTML = '';
            }

            try {
                const res = await fetch(`/api/paciente/${pacienteAtualId}/evolucao/${encodeURIComponent(codigoLoinc)}`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.erro || 'Erro ao buscar evolução do biomarcador');

                evolucaoAtualCache = data;
                renderizarLegendaGrafico();
                renderizarBannerGradienteAtual(data);
                renderizarGraficoEvolucaoSVG(data);
                renderizarTabelaHistoricoBiomarcador(data);
            } catch (err) {
                console.error("Erro na evolução do biomarcador:", err);
            }
        }

        function renderizarBannerGradienteAtual(data) {
            const banner = document.getElementById('banner-status-gradiente');
            const ultimo = data.ultimo_resultado;
            const clfOriginal = ultimo.classificacao;
            const clfAtivo = obterClassificacaoAtiva(clfOriginal);
            const tend = ultimo.tendencia;

            banner.style.background = clfAtivo.cor_bg;
            banner.style.border = `1px solid ${clfAtivo.cor_borda}`;

            const metricPosDesvio = clfOriginal.dentro_faixa
                ? `Posição na faixa: <strong>${clfOriginal.posicao_percentual}%</strong> (Largura: ${clfOriginal.largura_faixa} ${data.unidade})`
                : `Desvio além da borda: <strong>${clfOriginal.desvio_percentual}%</strong> (${clfOriginal.direcao_desvio === 'ABAIXO_DO_MINIMO' ? 'abaixo do mínimo' : 'acima do máximo'})`;

            const badgeTendenciaHtml = tend.exibir_badge_tendencia
                ? `<span class="bm-trend-pill" style="font-size:0.8rem; padding:4px 10px;">⚠️ ${tend.texto_tendencia}</span>`
                : (tend.possui_historico ? `<span style="font-size:0.8rem; color:#cbd5e1;">${tend.seta || '→'} ${tend.texto_tendencia}</span>` : '');

            const rotuloModo = modoNormaAtual === '5'
                ? `● Nível ${clfAtivo.nivel} (Norma 5): ${clfAtivo.rotulo} (${clfAtivo.cor_nome})`
                : `● Nível ${clfAtivo.nivel} (UX 4): ${clfAtivo.rotulo} (${clfAtivo.cor_nome})`;

            banner.innerHTML = `
                <div>
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:6px;">
                        <span style="font-size:1.25rem; font-weight:800; color:#fff;">
                            ${data.nome_exame}: ${ultimo.valor_numerico} ${data.unidade}
                        </span>
                        <span class="grad-badge grad-${clfAtivo.codigo}">
                            ${rotuloModo}
                        </span>
                        ${badgeTendenciaHtml}
                    </div>
                    <div style="font-size:0.88rem; color:#f8fafc; font-weight:500; margin-bottom:4px;">
                        💬 ${clfAtivo.mensagem_paciente}
                    </div>
                    <div style="font-size:0.76rem; color:#94a3b8;">
                        📐 ${metricPosDesvio} • Referência: <strong>${data.faixa_referencia_min} a ${data.faixa_referencia_max} ${data.unidade}</strong> • Base: ${clfAtivo.equivalencia_clinica}
                    </div>
                </div>
                <div style="text-align:right; font-size:0.78rem; color:#cbd5e1;">
                    <div>Última coleta: <strong>${ultimo.data_coleta}</strong></div>
                    <div>Origem: <strong style="color:var(--primary);">${ultimo.laboratorio_origem}</strong></div>
                </div>
            `;
        }

        function renderizarGraficoEvolucaoSVG(data) {
            const container = document.getElementById('svg-chart-container');
            const serie = data.serie_temporal || [];
            const refMin = data.faixa_referencia_min;
            const refMax = data.faixa_referencia_max;

            document.getElementById('chart-title-analito').innerHTML = `
                 Evolução Longitudinal — <span style="color:var(--primary);">${data.nome_exame} (LOINC ${data.codigo_loinc})</span> em ${serie.length} coletas
            `;

            if (serie.length === 0) {
                container.innerHTML = `<div class="empty-state">Sem pontos numéricos para plotar.</div>`;
                return;
            }

            const width = 960;
            const height = 320;
            const padLeft = 64;
            const padRight = 36;
            const padTop = 28;
            const padBottom = 52;
            const plotW = width - padLeft - padRight;
            const plotH = height - padTop - padBottom;

            const valores = serie.map(s => Number(s.valor_numerico));
            let minVal = Math.min(...valores);
            let maxVal = Math.max(...valores);
            if (refMin !== null && refMin !== undefined) minVal = Math.min(minVal, Number(refMin));
            if (refMax !== null && refMax !== undefined) maxVal = Math.max(maxVal, Number(refMax));

            const span = (maxVal - minVal) || (Math.abs(maxVal) * 0.2) || 10;
            const yMin = Math.max(0, minVal - span * 0.18);
            const yMax = maxVal + span * 0.18;

            const toX = (i) => serie.length === 1
                ? padLeft + plotW / 2
                : padLeft + (i / (serie.length - 1)) * plotW;
            const toY = (v) => padTop + plotH - ((v - yMin) / (yMax - yMin)) * plotH;

            // 1. Linhas de grade horizontais (Eixo Y)
            let gridHtml = '';
            const stepsY = 5;
            for (let i = 0; i <= stepsY; i++) {
                const valY = yMin + (i / stepsY) * (yMax - yMin);
                const py = toY(valY);
                gridHtml += `
                    <line x1="${padLeft}" y1="${py}" x2="${width - padRight}" y2="${py}" stroke="rgba(148, 163, 184, 0.12)" stroke-width="1" />
                    <text x="${padLeft - 10}" y="${py + 4}" text-anchor="end" fill="#94a3b8" font-size="11" font-family="JetBrains Mono, monospace">
                        ${valY.toFixed(valY < 10 ? 2 : 1)}
                    </text>
                `;
            }

            // 2. FAIXA SOMBREADA TRANSLÚCIDA OBRIGATÓRIA (faixa_referencia_min a faixa_referencia_max)
            let refBandHtml = '';
            if (refMin !== null && refMax !== null && refMax > refMin) {
                const yTopRef = toY(Number(refMax));
                const yBotRef = toY(Number(refMin));
                const bandH = Math.max(2, yBotRef - yTopRef);

                // Zonas internas de 10% e 90% (fronteira Limítrofe CLSI)
                const largRef = Number(refMax) - Number(refMin);
                const y90 = toY(Number(refMin) + 0.90 * largRef);
                const y10 = toY(Number(refMin) + 0.10 * largRef);

                // Zonas externas de até 15% (CTCAE Grau 1 - Alterado Leve)
                const yExtSup15 = toY(Number(refMax) + 0.15 * largRef);
                const yExtInf15 = toY(Math.max(0, Number(refMin) - 0.15 * largRef));

                refBandHtml = `
                    <!-- Faixa de Referência Normal Sombreada Translúcida (CLSI EP28-A3c) -->
                    <rect x="${padLeft}" y="${yTopRef}" width="${plotW}" height="${bandH}"
                          fill="rgba(16, 185, 129, 0.13)" />
                    <!-- Linha tracejada externa de 15% (Borda Alterado Leve Grau 1) -->
                    <line x1="${padLeft}" y1="${yExtSup15}" x2="${width - padRight}" y2="${yExtSup15}"
                          stroke="rgba(245, 158, 11, 0.35)" stroke-width="1" stroke-dasharray="2,4" />
                    <line x1="${padLeft}" y1="${yExtInf15}" x2="${width - padRight}" y2="${yExtInf15}"
                          stroke="rgba(245, 158, 11, 0.35)" stroke-width="1" stroke-dasharray="2,4" />
                    <!-- Guias sutis de 10% e 90% internos (Zona Limítrofe Interna) -->
                    <line x1="${padLeft}" y1="${y90}" x2="${width - padRight}" y2="${y90}"
                          stroke="rgba(234, 179, 8, 0.40)" stroke-width="1" stroke-dasharray="3,4" />
                    <line x1="${padLeft}" y1="${y10}" x2="${width - padRight}" y2="${y10}"
                          stroke="rgba(234, 179, 8, 0.40)" stroke-width="1" stroke-dasharray="3,4" />
                    <!-- Bordas Superior (Max) e Inferior (Min) -->
                    <line x1="${padLeft}" y1="${yTopRef}" x2="${width - padRight}" y2="${yTopRef}"
                          stroke="rgba(16, 185, 129, 0.70)" stroke-width="1.5" stroke-dasharray="6,4" />
                    <line x1="${padLeft}" y1="${yBotRef}" x2="${width - padRight}" y2="${yBotRef}"
                          stroke="rgba(16, 185, 129, 0.70)" stroke-width="1.5" stroke-dasharray="6,4" />
                    <text x="${width - padRight - 6}" y="${yTopRef - 5}" text-anchor="end" fill="#34d399" font-size="10" font-weight="600">
                        Máx: ${refMax} ${data.unidade}
                    </text>
                    <text x="${width - padRight - 6}" y="${yBotRef + 13}" text-anchor="end" fill="#34d399" font-size="10" font-weight="600">
                        Mín: ${refMin} ${data.unidade}
                    </text>
                `;
            }

            // 3. Linha de conexão temporal dos resultados
            const coords = serie.map((s, idx) => ({ x: toX(idx), y: toY(Number(s.valor_numerico)), item: s, idx }));
            const pathD = coords.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(' ');

            // 4. Pontos interativos coloridos pelo gradiente ativo + rótulos eixo X
            let pointsHtml = '';
            coords.forEach(pt => {
                const clfAtivo = obterClassificacaoAtiva(pt.item.classificacao);
                const cor = clfAtivo.cor_hex || '#38bdf8';
                const setaTend = pt.item.tendencia && pt.item.tendencia.exibir_badge_tendencia
                    ? pt.item.tendencia.seta
                    : '';

                pointsHtml += `
                    <!-- Rótulo Data Coleta Eixo X -->
                    <text x="${pt.x}" y="${height - 18}" text-anchor="middle" fill="#cbd5e1" font-size="11" font-weight="500">
                        ${pt.item.data_coleta}
                    </text>
                    <!-- Valor acima do ponto -->
                    <text x="${pt.x}" y="${pt.y - 12}" text-anchor="middle" fill="${cor}" font-size="11" font-weight="700" font-family="JetBrains Mono, monospace">
                        ${pt.item.valor_numerico}${setaTend ? ' ' + setaTend : ''}
                    </text>
                    <!-- Halo e Círculo Interativo -->
                    <circle cx="${pt.x}" cy="${pt.y}" r="11" fill="${cor}" fill-opacity="0.18"
                            style="cursor:pointer;"
                            onmouseenter="mostrarTooltipPonto(event, ${pt.idx})"
                            onmousemove="moverTooltipPonto(event)"
                            onmouseleave="ocultarTooltipPonto()" />
                    <circle cx="${pt.x}" cy="${pt.y}" r="6" fill="${cor}" stroke="#090d16" stroke-width="2"
                            style="cursor:pointer;"
                            onmouseenter="mostrarTooltipPonto(event, ${pt.idx})"
                            onmousemove="moverTooltipPonto(event)"
                            onmouseleave="ocultarTooltipPonto()" />
                `;
            });

            container.innerHTML = `
                <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:auto; min-width:680px; display:block;">
                    ${gridHtml}
                    ${refBandHtml}
                    <path d="${pathD}" fill="none" stroke="#38bdf8" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
                    ${pointsHtml}
                </svg>
            `;
        }

        function mostrarTooltipPonto(event, idx) {
            if (!evolucaoAtualCache || !evolucaoAtualCache.serie_temporal[idx]) return;
            const pt = evolucaoAtualCache.serie_temporal[idx];
            const clfOrig = pt.classificacao;
            const clfAtivo = obterClassificacaoAtiva(clfOrig);
            const tend = pt.tendencia;
            const tooltip = document.getElementById('chart-tooltip');

            const posOuDesvio = clfOrig.dentro_faixa
                ? `Posição na faixa: ${clfOrig.posicao_percentual}%`
                : `Desvio da borda: ${clfOrig.desvio_percentual}%`;

            tooltip.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; border-bottom:1px solid #24324c; padding-bottom:6px;">
                    <strong style="color:#fff; font-size:0.86rem;">📅 ${pt.data_coleta}</strong>
                    <span class="grad-badge grad-${clfAtivo.codigo}" style="font-size:0.68rem; padding:2px 8px;">
                        ${clfAtivo.rotulo} (${clfAtivo.cor_nome})
                    </span>
                </div>
                <div style="font-size:1.05rem; font-weight:800; color:${clfAtivo.cor_hex}; margin-bottom:4px;">
                    Resultado: ${pt.valor_numerico} ${pt.unidade || evolucaoAtualCache.unidade}
                    ${tend && tend.seta ? `<span style="color:#fbbf24; font-size:0.82rem; margin-left:4px;">${tend.seta} (${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}%)</span>` : ''}
                </div>
                <div style="font-size:0.76rem; color:#cbd5e1; margin-bottom:4px;">
                    🏥 <strong>Laboratório:</strong> <span style="color:#38bdf8; font-weight:700;">${pt.laboratorio_origem}</span>
                </div>
                <div style="font-size:0.73rem; color:#94a3b8; margin-bottom:3px;">
                    🎯 Ref: ${pt.faixa_referencia_min} a ${pt.faixa_referencia_max} ${pt.unidade || evolucaoAtualCache.unidade} • ${posOuDesvio}
                </div>
                <div style="font-size:0.70rem; color:#a5b4fc;">
                    📐 ${clfOrig.equivalencia_clinica}
                </div>
            `;
            tooltip.style.display = 'block';
            moverTooltipPonto(event);
        }

        function moverTooltipPonto(event) {
            const wrapper = document.getElementById('chart-wrapper-evolucao');
            const tooltip = document.getElementById('chart-tooltip');
            const rect = wrapper.getBoundingClientRect();
            let left = event.clientX - rect.left + 14;
            let top = event.clientY - rect.top - 20;
            if (left + 260 > rect.width) left = event.clientX - rect.left - 265;
            if (top < 10) top = 10;
            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        }

        function ocultarTooltipPonto() {
            const tooltip = document.getElementById('chart-tooltip');
            if (tooltip) tooltip.style.display = 'none';
        }

        function renderizarTabelaHistoricoBiomarcador(data) {
            const tbody = document.getElementById('tbody-historico-biomarcador');
            const labsBadge = document.getElementById('badge-labs-unificados');
            const labs = data.laboratorios_unificados || [];
            labsBadge.innerHTML = `🔗 <strong>${labs.length} Laboratórios Unificados:</strong> ${labs.join(' • ')}`;

            // Exibe em ordem cronológica reversa (mais recente no topo) na tabela
            const invertida = [...(data.serie_temporal || [])].reverse();
            tbody.innerHTML = invertida.map(item => {
                const clfOrig = item.classificacao;
                const clfAtivo = obterClassificacaoAtiva(clfOrig);
                const tend = item.tendencia;
                const posTxt = clfOrig.dentro_faixa
                    ? `Posição: <strong>${clfOrig.posicao_percentual}%</strong> (interna)`
                    : `Desvio: <strong>${clfOrig.desvio_percentual}%</strong> (externo)`;

                const tendHtml = !tend.possui_historico
                    ? `<span style="color:#64748b; font-size:0.76rem;">1º Registro</span>`
                    : (tend.exibir_badge_tendencia
                        ? `<span class="bm-trend-pill">${tend.seta} ${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}% (Alerta Borda)</span>`
                        : `<span style="color:#cbd5e1; font-size:0.8rem;">${tend.seta} ${tend.variacao_percentual > 0 ? '+' : ''}${tend.variacao_percentual}%</span>`);

                return `
                    <tr>
                        <td><strong>${item.data_coleta}</strong></td>
                        <td><span style="color:var(--primary); font-weight:600;">🏥 ${item.laboratorio_origem}</span></td>
                        <td style="font-family:'JetBrains Mono', monospace; font-weight:700; font-size:0.92rem; color:#fff;">
                            ${item.valor_numerico} ${item.unidade || data.unidade}
                        </td>
                        <td>${item.faixa_referencia_min} a ${item.faixa_referencia_max} ${item.unidade || data.unidade}</td>
                        <td style="font-size:0.78rem; color:#cbd5e1;">${posTxt}</td>
                        <td>
                            <span class="grad-badge grad-${clfAtivo.codigo}">
                                ● ${clfAtivo.rotulo} (${clfAtivo.cor_nome})
                            </span>
                        </td>
                        <td>${tendHtml}</td>
                    </tr>
                `;
            }).join('');
        }

        async function acionarInterpretacaoRAG() {
            if (!pacienteAtualId || !loincSelecionadoAtual) return;
            const btn = document.getElementById('btn-entender-evolucao');
            const card = document.getElementById('card-rag-resultado');
            const textoOriginal = btn.innerHTML;

            btn.disabled = true;
            btn.innerHTML = `⏳ Carregando Interpretação Determinística...`;

            try {
                const res = await fetch('/exams/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pacienteAtualId,
                        codigo_loinc: loincSelecionadoAtual,
                        usar_llm: false
                    })
                });
                const payload = await res.json();
                if (!res.ok) throw new Error(payload.erro || 'Falha ao interpretar evolução');

                const interp = payload.interpretacao_paciente;
                const meta = payload.rag_metadata || {};
                const clfAtivo = obterClassificacaoAtiva(payload.classificacao_atual);
                const pilares = interp.cinco_pilares_18_25 || {};

                const perguntasHtml = (interp.perguntas_para_o_medico || []).map((q, idx) => `
                    <li class="doctor-question-item">
                        <span style="background:var(--primary); color:#090d16; font-weight:800; border-radius:50%; width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; font-size:0.75rem;">
                            ${idx + 1}
                        </span>
                        <span>"${q}"</span>
                    </li>
                `).join('');

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap; border-bottom:1px solid var(--border); padding-bottom:12px;">
                        <div>
                            <div style="font-size:0.74rem; color:var(--primary); font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">
                                📋 Interpretação Clínica Determinística • Faixa Etária 18 a 25 Anos
                            </div>
                            <h3 style="color:#fff; font-size:1.15rem; margin-top:3px;">
                                ${payload.nome_exame} <span style="font-size:0.85rem; color:var(--text-muted);">(LOINC ${payload.codigo_loinc})</span>
                            </h3>
                        </div>
                        <span class="grad-badge grad-${clfAtivo.codigo}" style="font-size:0.84rem; padding:6px 14px;">
                            Classificação: ${clfAtivo.rotulo} (${clfAtivo.cor_nome})
                        </span>
                    </div>

                    <!-- RESUMO DO EXAME (113 TEXTOS) -->
                    <div class="rag-block" style="margin-top:14px; border-left:4px solid var(--primary); background:rgba(56, 189, 248, 0.05);">
                        <h4 style="color:var(--primary);">🔬 Resumo do Exame e Papel no Organismo</h4>
                        <p style="font-size:0.92rem; color:#f8fafc; line-height:1.6;">${interp.resumo_exame || interp.resumo_acessivel}</p>
                    </div>

                    <!-- TENDÊNCIA NOS ÚLTIMOS EXAMES -->
                    <div class="rag-block" style="margin-top:10px; border-left:4px solid var(--accent); background:rgba(129, 140, 248, 0.05);">
                        <h4 style="color:var(--accent);">📈 Evolução nos Seus Laudos Unificados</h4>
                        <p style="font-size:0.88rem; color:#e2e8f0; line-height:1.55;">${interp.analise_tendencia_numerica}</p>
                    </div>

                    <!-- OS 5 PILARES DETERMINÍSTICOS DO RESULTADO (565 TEXTOS) -->
                    <div style="margin-top:18px;">
                        <h4 style="font-size:0.88rem; text-transform:uppercase; letter-spacing:0.05em; color:#fff; margin-bottom:12px;">
                            🎯 Resumo Estruturado do Resultado (Padrão Open Health):
                        </h4>
                        <div class="rag-grid">
                            <div class="rag-block" style="border-top:3px solid ${clfAtivo.cor_hex};">
                                <h4 style="color:${clfAtivo.cor_hex};">1. Descrição do Resultado</h4>
                                <p>${pilares['1_descricao_resultado'] || interp.o_que_significa_nivel_atual}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #38bdf8;">
                                <h4 style="color:#38bdf8;">2. Pares Etários (18 a 25 Anos)</h4>
                                <p>${pilares['2_estatistica_etaria_18_25'] || 'Prevalência populacional alinhada com as referências do Ministério da Saúde.'}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #fbbf24;">
                                <h4 style="color:#fbbf24;">3. Impactos para o Indivíduo</h4>
                                <p>${pilares['3_impactos_individuo'] || 'Manutenção da rotina saudável e bem-estar físico e mental.'}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #f97316;">
                                <h4 style="color:#f97316;">4. Possíveis Causas do Desvio</h4>
                                <p>${pilares['4_possiveis_causas'] || 'Hábitos alimentares, rotina de sono e variações fisiológicas transitórias.'}</p>
                            </div>

                            <div class="rag-block" style="border-top:3px solid #34d399;">
                                <h4 style="color:#34d399;">5. Correção / Conduta Recomendada</h4>
                                <p>${pilares['5_correcao_desvio'] || 'Manter hábitos preventivos e acompanhamento regular com médico.'}</p>
                            </div>
                        </div>
                    </div>

                    <!-- PERGUNTAS SUGERIDAS PARA A CONSULTA MÉDICA -->
                    <div class="rag-block" style="margin-top:16px; border-color:rgba(56, 189, 248, 0.35); background:rgba(9, 13, 22, 0.75);">
                        <h4>🩺 Perguntas Sugeridas para Levar ao seu Médico na Próxima Consulta</h4>
                        <ul class="doctor-questions-list">
                            ${perguntasHtml}
                        </ul>
                    </div>

                    <div style="margin-top:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-size:0.74rem; color:#94a3b8; border-top:1px solid var(--border); padding-top:10px;">
                        <span>📚 <strong>Diretrizes Clínicas:</strong> SBPC-ML • CLSI EP28-A3c • CTCAE v5.0 • Valores Críticos CAP</span>
                        <span>🛡️ ${interp.aviso_seguranca_etica}</span>
                    </div>
                `;
                card.classList.add('open');
            } catch (err) {
                alert("Erro ao obter interpretação determinística: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = textoOriginal;
            }
        }

        async function alternarConsentimento(consentId) {
            try {
                const res = await fetch(`/api/consent/${consentId}/toggle`, { method: 'POST' });
                if (!res.ok) throw new Error('Falha ao alternar consentimento');
                abrirPaciente(pacienteAtualId);
            } catch (e) {
                alert("Erro: " + e.message);
            }
        }

        function abrirModalNovoConsentimento() {
            document.getElementById('modal-novo-consent').classList.add('open');
        }
        function fecharModalConsent() {
            document.getElementById('modal-novo-consent').classList.remove('open');
        }

        async function salvarNovoConsentimento() {
            if (!pacienteAtualId) return;
            const origem = document.getElementById('input-origem').value;
            const destino = document.getElementById('input-destino').value;
            const escopo = document.getElementById('input-escopo').value;
            const validade = parseInt(document.getElementById('input-validade').value);

            try {
                const res = await fetch('/api/consent/novo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pacienteAtualId,
                        hospital_origem: origem,
                        hospital_destino: destino,
                        escopo: escopo,
                        dias_validade: validade
                    })
                });
                if (!res.ok) throw new Error('Falha ao criar consentimento');
                fecharModalConsent();
                abrirPaciente(pacienteAtualId);
            } catch (e) {
                alert("Erro ao criar consentimento: " + e.message);
            }
        }

        // ==============================================================
        // NÍVEL 3: OBSERVATIONS DO LAUDO EXIBIDAS POR COLUNAS (LOINC)
        // (AQUI É A PARTE CRUCIAL ONDE MOSTRAMOS TODAS AS COLUNAS, INCLUINDO AS VAZIAS!)
        // ==============================================================
        async function abrirLaudoObservacoes(reportId) {
            laudoAtualId = reportId;
            try {
                const res = await fetch(`/api/laudo/${reportId}/colunas`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.erro || 'Falha ao buscar colunas do laudo');

                dadosLaudoColunasCache = data;
                const laudo = data.laudo;

                // Atualiza Breadcrumbs
                document.getElementById('bc-sep-2').style.display = 'inline-block';
                const bcLaudo = document.getElementById('bc-laudo');
                bcLaudo.style.display = 'inline-flex';
                bcLaudo.innerHTML = `🔬 Laudo: <strong>${laudo.laboratorio_origem} (${laudo.data_coleta || 'S/D'})</strong>`;

                // Banner de Informações do Laudo
                document.getElementById('banner-laudo-info').innerHTML = `
                    <div class="info-col"><label>Paciente</label><div>${laudo.nome_paciente}</div></div>
                    <div class="info-col"><label>Laboratório</label><div>${laudo.laboratorio_origem}</div></div>
                    <div class="info-col"><label>Data da Coleta</label><div>${laudo.data_coleta || '—'}</div></div>
                    <div class="info-col"><label>Data da Emissão</label><div>${laudo.data_emissao || '—'}</div></div>
                    <div class="info-col"><label>Versão do Laudo</label><div><span style="color:var(--primary); font-weight:700;">v${laudo.versao}</span></div></div>
                    <div class="info-col"><label>Hash ICP-Brasil</label><div><span class="hash-code" title="${laudo.assinatura_hash}">${laudo.assinatura_hash}</span></div></div>
                `;

                // Badges de Resumo das Colunas
                document.getElementById('stat-col-preenchidas').innerText = `${data.total_preenchidas} Preenchidas`;
                document.getElementById('stat-col-vazias').innerText = `${data.total_vazias} Colunas Vazias`;
                document.getElementById('stat-col-total').innerText = `Total: ${data.total_colunas} Colunas Padronizadas`;

                // Renderiza as visualizações de colunas
                renderizarMatrizColunas(data.colunas);
                renderizarCardsCategorias(data.colunas);

                // Alterna para visualização de Observações
                document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
                document.getElementById('view-laudo-observacoes').classList.add('active');

            } catch (e) {
                alert("Erro ao carregar observações por colunas: " + e.message);
            }
        }

        function alternarModoExibicao(modo) {
            modoExibicaoAtual = modo;
            if (modo === 'matrix') {
                document.getElementById('wrapper-matrix-view').style.display = 'block';
                document.getElementById('wrapper-cards-view').style.display = 'none';
                document.getElementById('btn-view-matrix').style.borderColor = 'var(--primary)';
                document.getElementById('btn-view-cards').style.borderColor = 'var(--border)';
            } else {
                document.getElementById('wrapper-matrix-view').style.display = 'none';
                document.getElementById('wrapper-cards-view').style.display = 'block';
                document.getElementById('btn-view-cards').style.borderColor = 'var(--primary)';
                document.getElementById('btn-view-matrix').style.borderColor = 'var(--border)';
            }
        }

        // 1. RENDERIZAÇÃO DA MATRIZ DE COLUNAS (FORMATO LARGO HORIZONTAL COM SCROLL)
        function renderizarMatrizColunas(colunas) {
            const thead = document.getElementById('thead-matriz');
            const tbody = document.getElementById('tbody-matriz');

            const colunasFiltradas = obterColunasFiltradas(colunas);

            if (colunasFiltradas.length === 0) {
                thead.innerHTML = `<tr><th>Nenhuma coluna encontrada com o filtro atual</th></tr>`;
                tbody.innerHTML = `<tr><td class="empty-state">Tente alterar os filtros de busca acima.</td></tr>`;
                return;
            }

            // Cabeçalho: Cada métrica vira uma coluna com Nome e Código LOINC
            thead.innerHTML = `<tr>` + colunasFiltradas.map(col => `
                <th>
                    <div class="col-name">${col.nome_exibicao}</div>
                    <div class="col-loinc">LOINC: ${col.loinc}</div>
                    <div class="col-cat">${col.categoria.replace(/^\d+\.\s*/, '')}</div>
                </th>
            `).join('') + `</tr>`;

            // Linha com os valores: Exibe os valores preenchidos ou "—" para as colunas vazias
            tbody.innerHTML = `<tr>` + colunasFiltradas.map(col => {
                if (col.preenchida) {
                    const statusClass = col.status_clinico === 'alto' || col.status_clinico === 'baixo' ? 'badge-alterado' : 'badge-normal';
                    return `
                        <td class="matrix-cell-filled">
                            <div class="cell-value">${col.valor}</div>
                            <div class="cell-unit">${col.unidade || '—'}</div>
                            <div class="cell-ref">Ref: ${col.faixa_referencia_formatada}</div>
                            <div style="margin-top:6px;">
                                <span class="badge ${statusClass}">${col.status_clinico.toUpperCase()}</span>
                            </div>
                        </td>
                    `;
                } else {
                    return `
                        <td>
                            <div class="cell-empty">—</div>
                            <div style="font-size:0.68rem; color:#475569; margin-top:4px;">(coluna vazia)</div>
                        </td>
                    `;
                }
            }).join('') + `</tr>`;
        }

        // 2. RENDERIZAÇÃO DOS CARDS DE COLUNAS AGRUPADOS POR CATEGORIA
        function renderizarCardsCategorias(colunas) {
            const container = document.getElementById('container-categorias-cards');
            const colunasFiltradas = obterColunasFiltradas(colunas);

            // Agrupa por categoria
            const grupos = {};
            colunasFiltradas.forEach(col => {
                const cat = col.categoria || 'Geral';
                if (!grupos[cat]) grupos[cat] = [];
                grupos[cat].push(col);
            });

            if (Object.keys(grupos).length === 0) {
                container.innerHTML = `<div class="empty-state">Nenhuma coluna encontrada com o filtro atual.</div>`;
                return;
            }

            container.innerHTML = Object.entries(grupos).map(([cat, lista]) => {
                const preenchidasCat = lista.filter(c => c.preenchida).length;
                const totalCat = lista.length;

                const cardsHtml = lista.map(c => {
                    if (c.preenchida) {
                        return `
                            <div class="col-card filled">
                                <div class="col-card-header">
                                    <div class="col-card-name">${c.nome_exibicao}</div>
                                    <span class="col-card-loinc">${c.loinc}</span>
                                </div>
                                <div class="col-card-value">${c.valor} <span class="col-card-unit">${c.unidade}</span></div>
                                <div class="col-card-ref">Ref: ${c.faixa_referencia_formatada}</div>
                            </div>
                        `;
                    } else {
                        return `
                            <div class="col-card empty">
                                <div class="col-card-header">
                                    <div class="col-card-name" style="color:#64748b;">${c.nome_exibicao}</div>
                                    <span class="col-card-loinc" style="color:#475569;">${c.loinc}</span>
                                </div>
                                <div style="color:#475569; font-size:0.95rem; font-style:italic; margin-top:8px;">— (Coluna Vazia)</div>
                                <div class="col-card-ref" style="color:#334155;">Não coletado neste laudo</div>
                            </div>
                        `;
                    }
                }).join('');

                return `
                    <div class="category-block">
                        <div class="category-title">
                            <span>${cat}</span>
                            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">
                                ${preenchidasCat} preenchidas de ${totalCat} colunas
                            </span>
                        </div>
                        <div class="columns-grid">
                            ${cardsHtml}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Filtros e buscas de colunas
        function obterColunasFiltradas(colunas) {
            if (!colunas) return [];
            let result = [...colunas];

            // Filtro Preenchidas / Vazias / Todas
            if (filtroColunaAtual === 'preenchidas') {
                result = result.filter(c => c.preenchida);
            } else if (filtroColunaAtual === 'vazias') {
                result = result.filter(c => !c.preenchida);
            }

            // Filtro por Categoria do Dropdown
            const catFiltro = document.getElementById('select-categoria').value.toLowerCase();
            if (catFiltro) {
                result = result.filter(c => c.categoria.toLowerCase().includes(catFiltro));
            }

            // Filtro por texto digitado
            const busca = document.getElementById('search-coluna').value.toLowerCase().trim();
            if (busca) {
                result = result.filter(c => 
                    c.nome_exibicao.toLowerCase().includes(busca) || 
                    c.coluna.toLowerCase().includes(busca) ||
                    c.loinc.includes(busca)
                );
            }

            return result;
        }

        function aplicarFiltroColunas(tipo) {
            filtroColunaAtual = tipo;
            document.querySelectorAll('.filters-toolbar .pill-filter').forEach(b => b.classList.remove('active'));
            if (tipo === 'todas') document.getElementById('filter-all').classList.add('active');
            if (tipo === 'preenchidas') document.getElementById('filter-filled').classList.add('active');
            if (tipo === 'vazias') document.getElementById('filter-empty').classList.add('active');

            if (dadosLaudoColunasCache) {
                renderizarMatrizColunas(dadosLaudoColunasCache.colunas);
                renderizarCardsCategorias(dadosLaudoColunasCache.colunas);
            }
        }

        function filtrarPorCategoria() {
            if (dadosLaudoColunasCache) {
                renderizarMatrizColunas(dadosLaudoColunasCache.colunas);
                renderizarCardsCategorias(dadosLaudoColunasCache.colunas);
            }
        }

        function filtrarPorTextoColuna() {
            if (dadosLaudoColunasCache) {
                renderizarMatrizColunas(dadosLaudoColunasCache.colunas);
                renderizarCardsCategorias(dadosLaudoColunasCache.colunas);
            }
        }

        function recarregarVisaoAtual() {
            if (laudoAtualId) {
                abrirLaudoObservacoes(laudoAtualId);
            } else if (pacienteAtualId) {
                abrirPaciente(pacienteAtualId);
            } else {
                carregarListaPacientes();
            }
        }

        async function limparBancoGeral() {
            if (!confirm("Atenção: Deseja realmente zerar todos os pacientes, laudos, observações e consentimentos para reiniciar do zero?")) return;
            try {
                await fetch('/api/limpar_banco', { method: 'POST' });
                navegarParaPacientes();
                alert("Banco de dados zerado com sucesso!");
            } catch (e) {
                alert("Erro ao limpar banco: " + e.message);
            }
        }
    