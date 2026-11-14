# Organização do repositório

Este documento orienta a navegação e uma organização segura dos arquivos. Os nomes e caminhos existentes foram preservados nesta etapa: mover pastas sem uma alteração local abrangente e testes poderia quebrar imports Python, caminhos de dados, builds do Lovable e referências a documentos.

## Estrutura atual (resumo)

```text
.
├── components/                 # componentes React e UI
├── routes/                     # rotas TanStack
├── public/                     # arquivos públicos do frontend
├── backend/                    # backend Python e serviço wearables/causal
├── 02_backend/                 # módulos Python adicionais/versão paralela
├── dados_nhanes/               # dados NHANES
├── conhecimento_exames_completo/ # bases e ferramentas de conhecimento
├── Laudos Hipotéticos/         # documentos de demonstração
├── Laudos Reais/               # documentos potencialmente sensíveis
├── Documentos do Hackathon/    # material do desafio
├── PDF's Projeto/              # PDFs de referência/regulamentação
├── assets/                     # imagens
├── drizzle/                    # schema e migrações
└── supabase/                   # configuração Supabase
```

## Regras para futuras mudanças

1. **Frontend:** mantenha componentes, rotas, configurações e arquivos gerados na raiz enquanto o projeto Lovable/TanStack depender dessa estrutura. Não mova o app para `frontend/` sem atualizar configurações e validar o build.
2. **Backends:** `backend/` e `02_backend/` não são cópias idênticas. O serviço `backend/wearable_causal_service/` e as pastas numeradas têm conteúdo específico. Compare cada arquivo e atualize imports, configuração de execução e documentação antes de consolidar em uma só árvore.
3. **Dados e documentos:** só mova datasets e documentos depois de atualizar `paths_config.py`, scripts e referências nos READMEs. Preserve a distinção entre dados sintéticos e reais.
4. **Banco:** não mova nem edite `drizzle/` ou migrações `supabase/` sem seguir `AGENTS.md` e o fluxo de gestão do projeto.
5. **Histórico Git:** uma remoção de arquivo sensível no commit atual não o apaga de commits anteriores. Se um segredo foi publicado, revogue/rotacione-o; para documentos pessoais, avalie a remoção do histórico e as obrigações de privacidade antes de republicar.

## Segurança e limpeza

- `backend/wearable_causal_service/.env` aparece no repositório. Verifique localmente se contém credenciais; se houver, revogue-as/rotacione-as e remova o arquivo do controle de versão. `.gitignore` não deixa de rastrear um arquivo que já foi commitado.
- Revise `Laudos Reais/` antes de manter o repositório público. Não copie documentos clínicos identificáveis para novas pastas.
- Remova `__pycache__/`, `*.py[cod]` e outros artefatos gerados do versionamento quando estiver trabalhando em uma cópia local. Esta branch adiciona regras de ignore para evitar novos arquivos desse tipo.
- Os arquivos `.xpt` de NHANES e dados de demonstração devem permanecer identificados e separados de quaisquer registros reais.

## Estrutura-alvo sugerida (para migração futura)

```text
docs/             # documentação do projeto, desafio e relatórios
assets/           # imagens e recursos visuais
backend/          # backend consolidado, somente após validar a duplicidade
  01_core_api/
  02_ingestao_ocr/
  03_semantica_ontologias/
  04_persistencia_dados/
  05_inteligencia_rag/
  06_populacional_nhanes/
  07_sensores_wearables/
  08_machine_learning_causal/
  09_geradores_sinteticos/
  10_relatorios_cientificos/
data/              # datasets não sensíveis, separados por origem
clinical_docs/     # somente materiais fictícios/desidentificados
```

A estrutura-alvo é uma proposta, não um registro de arquivos já movidos. A aplicação web e os arquivos gerenciados pelo Lovable permanecem na raiz até que exista uma migração validada.
