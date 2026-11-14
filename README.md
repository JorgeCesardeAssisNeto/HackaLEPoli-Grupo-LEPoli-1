# Open Health Brasil — Hackathon LEPoli

Repositório do Grupo LEPoli 1 com o protótipo web, serviços de backend, dados de apoio e materiais do hackathon.

> **Aviso:** este repositório é público. Não publique credenciais, arquivos `.env` com valores, nem documentos clínicos identificáveis. Os laudos reais atualmente presentes no histórico devem ser revisados e removidos com cuidado; apagar um arquivo da versão atual não o apaga do histórico Git.

## Mapa do repositório

- `components/`, `routes/`, `public/` e arquivos de configuração na raiz: aplicação web Lovable/TanStack. Permanecem na raiz para preservar a configuração atual de build e geração de rotas.
- `backend/`: serviços e módulos Python, incluindo `wearable_causal_service/`.
- `02_backend/`: outra cópia/versão dos módulos do backend e ferramentas associadas. Consulte [`docs/ORGANIZACAO.md`](docs/ORGANIZACAO.md) antes de alterar ou remover; há diferenças entre as duas árvores.
- `dados_nhanes/`: arquivos de dados NHANES.
- `conhecimento_exames_completo/`: bases e ferramentas relacionadas ao conhecimento de exames.
- `Laudos Hipotéticos/`, `Laudos Reais/`, `Documentos do Hackathon/` e `PDF's Projeto/`: documentos e materiais de referência. Os nomes originais foram mantidos para não quebrar referências existentes.
- `assets/`: imagens usadas pelo projeto.
- `drizzle/` e `supabase/`: arquivos de banco e configuração gerenciados pelo projeto. Não altere migrações sem seguir as instruções de `AGENTS.md`.

## Executar a aplicação web

Requer Node.js e npm:

```sh
npm install
npm run dev
```

## Backend

Os serviços Python têm dependências e instruções próprias. Consulte os `README.md` dentro de `backend/` e `backend/wearable_causal_service/` antes de executar. Configure segredos apenas no ambiente local ou no provedor de deploy; use `.env.example` como modelo, nunca publique valores secretos.

## Organização e contribuições

Veja [`docs/ORGANIZACAO.md`](docs/ORGANIZACAO.md) para o inventário, a convenção de pastas e os cuidados necessários antes de mover arquivos. Esta organização documental não altera os caminhos do código ou migra dados clínicos.
