# Base de conhecimento de exames em CSV — Open Health / HackaLEPoli

Pasta nova e separada do resto do repositório. **Nenhum arquivo existente foi alterado.**

| Arquivo | Linhas de dados | Conteúdo |
|---|---|---|
| `catalogo_exames.csv` | 113 | Um registro por exame da base existente |
| `interpretacoes_exames.csv` | 999 | Seis conteúdos por exame × nível × direção |
| `criterios_classificacao.csv` | 376 | Regras e limites por exame, separados por tipo |
| `pares_etarios.csv` | 72 | Estimativas NHANES 18–25 anos por sexo (36 exames) |
| `pares_etarios_percentis.csv` | 7.272 | Percentis 0–100 ponderados por exame e sexo (72 × 101), base dos gráficos de distribuição |
| `prototipo_leitor_exames.html` | — | Protótipo interativo gerado a partir dos CSVs (`_gerador/montar_prototipo.py`) |
| `mapeamento_niveis.csv` | 12 | Cinco níveis solicitados × códigos atuais × escala visual de 4 |
| `referencias.csv` | 12 | Fontes, versões e status de acesso |
| `pendencias.csv` | 96 | Problemas que impedem uso automático |
| `_gerador/` | — | Scripts que geram e validam os CSVs e o resultado da validação |

> **Status:** os textos clínicos são rascunho técnico. **Nenhuma revisão clínica foi realizada.** Fonte identificada não significa fonte conferida: veja `referencias.status_acesso`.

---

## 1. Estrutura encontrada e destino proposto

**Duas árvores, não equivalentes:**

- **`02_backend/`** — usa `paths_config.py` (só existe nessa árvore). `app.py`, `interpretador_rag.py` e `classificador.py` importam `paths_config` e leem os JSON por caminho centralizado. Tem `planilha_padrao_exames_brcore_loinc.csv`, `banco_exames.csv`, `open_health.db` e `templates/`, ausentes em `backend/`.
- **`backend/`** — versão anterior. `interpretador_rag.py` lê os JSON da própria pasta do módulo (`os.path.join(BASE_DIR, ...)`) sem `paths_config`. 20+ arquivos `.py` diferem de `02_backend/`.

Não foi possível confirmar qual árvore está em produção: nenhum Dockerfile, Procfile ou script de inicialização na raiz aponta para uma delas.

**Caminhos divergentes em `02_backend/paths_config.py`:**

| Constante | Aponta para | Encontrado no ZIP |
|---|---|---|
| `NHANES_DATA_DIR` | `<raiz>/03_bases_de_dados/dados_nhanes` | `<raiz>/dados_nhanes` |
| `NHANES_2012_DIR` | `<raiz>/03_bases_de_dados/dados_nhanes/2012` | `<raiz>/dados_nhanes/2012` |
| `WEARABLES_DATA_DIR` | `<raiz>/03_bases_de_dados/dataset_wearables` | não existe |
| `LAUDOS_DIR` | `<raiz>/04_laudos_clinicos` | `<raiz>/Laudos Hipotéticos`, `<raiz>/Laudos Reais` |
| `FRONTEND_DIR` | `<raiz>/01_frontend` | não existe |

Com esses caminhos, `data_engine.py` não encontra os `.xpt`. Os caminhos de `03_semantica_ontologias` e `04_persistencia_dados` estão corretos.

**Destino proposto:** `02_backend/03_semantica_ontologias/conhecimento_csv/`, ao lado dos JSON que o interpretador já lê pela constante `SEMANTICA_DIR`. Essa escolha depende de confirmar que `02_backend/` é a árvore em uso.

**Base existente reconciliada:**

- `base_conhecimento_exames_565.json`: 113 exames × 5 faixas = 565 registros. Confirmado.
- Os mesmos 113 identificadores `coluna` aparecem em `catalogo_colunas_completo.json` e `mapa_colunas_loinc.json`.
- Faixas: `NORMAL`, `LIMITROFE`, `ALTERADO_LEVE`, `ALTERADO_MODERADO`, `ALTERACAO_ACENTUADA`.
- **Inconsistências registradas, não corrigidas:**
  - **`vdrl_sifilis`:** LOINC corrompido na base e no catálogo (`5292-88081.0150.7702 / CIP 6164788886`). O mapa traz `5292-8`.
  - **Categorias trocadas:** PCR, VHS e coagulação estão em "9. Marcadores tumorais". Marcadores tumorais e sorologias estão em "10. Marcadores cardíacos". Ferro e vitaminas estão em "8. Inflamação".
  - **Numeração:** não existe categoria 7.
  - **Nomes gerados do identificador:** 15 nomes carregam a unidade no fim (ex.: "Proteinas Totais G Dl").
  - **Textos da base:** são o mesmo modelo repetido entre exames, até para sorologias (o texto de HIV fala em "atividade metabólica"). Trazem percentuais sem fonte (86%, 8%…), prescrições (ex.: "ferro quelato") e expressões de julgamento. **Não foram reaproveitados**; só identificadores, nomes e categorias foram preservados.

**Faixas de referência:** não ficam nos JSON. O classificador usa o intervalo extraído de cada laudo. Quando o laudo não traz intervalo, usa `FAIXAS_PADRAO_LOINC` em `04_persistencia_dados/database.py`, que cobre 32 dos 113 exames, sem população, método nem laboratório. Hemoglobina, hematócrito e hemácias usam limites femininos para todos. A faixa de PCR está em mg/dL, mas a coluna é em mg/L.

---

## 2. Dicionário de dados e relações

**Convenções:** UTF-8 sem BOM; vírgula como delimitador; todos os campos entre aspas (`QUOTE_ALL`), com aspas internas duplicadas; uma linha de cabeçalho; ponto decimal; datas ISO 8601 (`AAAA-MM-DD`). LOINC e identificadores são texto. **Ausência = campo vazio** (`""`), nunca zero.

**Estados de informação** (não são níveis de gravidade): `conteudo_disponivel`, `nao_aplicavel`, `evidencia_insuficiente`, `pendente_validacao`. A base não produziu nenhuma linha `evidencia_insuficiente`, porque todo exame tem texto redigido para as direções relevantes; o estado continua permitido.

### Relações

```
catalogo_exames (exame_id) 1──N interpretacoes_exames (exame_id)
                           1──N criterios_classificacao (exame_id)
                           1──N pares_etarios (exame_id)
                           1──N pendencias (exame_id; vazio = pendência geral)
interpretacoes_exames.par_ids ──N→ pares_etarios.par_id   (lista separada por ';' — ver nota)
interpretacoes_exames.nivel_id ──→ mapeamento_niveis.nivel_id
*.ref_id / ref_id_texto / ref_id_resumo ──→ referencias.ref_id
```

Nota: `par_ids` usa no máximo dois valores (um por sexo), ambos com o prefixo `PAR_<exame_id>_`. Também dá para obter o mesmo vínculo por junção direta em `pares_etarios.exame_id`, sem ler a lista.

### `catalogo_exames.csv` — PK `exame_id`

| Campo | Descrição / valores |
|---|---|
| `exame_id`, `coluna` | Identificador `coluna` da base existente (idênticos) |
| `codigo_loinc` | Exatamente como na base 565, inclusive se inconsistente |
| `codigo_loinc_mapa` | Valor em `mapa_colunas_loinc.json` |
| `nome_exame`, `categoria` | Exatamente como na base 565 |
| `tipo_resultado` | `quantitativo` · `qualitativo` · `qualitativo_com_titulo` · `pendente_validacao` |
| `unidade` | Derivada apenas do sufixo do identificador; vazia quando não há sufixo |
| `unidade_origem` | `sufixo_do_identificador_coluna` · `ausente` |
| `sexo_dependente` | `sim` · `nao_avaliado` |
| `direcoes_relevantes` | `ambas` · `alto` · `baixo` · `qualitativo` · `contexto` (depende de sexo/ciclo/gestação) |
| `resumo_exame` | **Conteúdo 1**: o que o exame mede e para que serve |
| `status_catalogo` | `conferido_com_catalogo` · `inconsistencia_registrada` |

### `interpretacoes_exames.csv` — PK `interp_id`; chave natural única `exame_id + nivel_id + direcao`

| Campo | Descrição / valores |
|---|---|
| `nivel_id`, `nivel_nome` | 1 Normal · 2 Levemente alterado · 3 Nível de atenção · 4 Alterado de maneira moderada · 5 Alterado grave. Vazio = resultado fora da escala (reagente de sorologia) |
| `direcao` | `dentro_referencia` · `abaixo` · `acima` · `nao_reagente` · `reagente` · `abaixo_limiar` · `nao_aplicavel` |
| `descricao_resultado` | **Conteúdo 2** |
| `informacoes_pares_etarios` | **Conteúdo 3**: a comparação é exibida em gráfico. O texto só aponta para `pares_etarios.csv` e `pares_etarios_percentis.csv`, ou traz a frase padrão de ausência |
| `impactos_individuo` | **Conteúdo 4** |
| `possiveis_causas` | **Conteúdo 5**, incluindo interferências pré-analíticas |
| `mitigacao` | **Conteúdo 6** |
| `status_informacao` | Estado de informação (acima) |
| `status_criterio` | Se o nível tem critério numérico definido: `fonte_do_projeto_sem_validacao` · `pendente_validacao` · `nao_aplicavel` |
| `resultado_critico` | `nao_definido` em todas as linhas (ver seção 5) |
| `urgencia` | `nao_deduzida_do_nivel` |
| `revisao_clinica` | `nao_realizada` |

### `criterios_classificacao.csv` — PK `criterio_id`

| Campo | Descrição / valores |
|---|---|
| `tipo_criterio` | `intervalo_referencia` · `regra_algoritmica_projeto` · `limite_decisao_clinica` · `grau_evento_adverso_ctcae` · (`valor_critico`: reservado, sem linhas) |
| `nivel_id_produto` | Preenchido só quando o critério define um nível do produto (hoje, apenas o nível 1 = dentro do intervalo) |
| `codigo_destino_atual` | Código do classificador atual, para as regras do projeto |
| `operador_inferior/superior` | `>=`, `>`, `<`, `<=` ou vazio (sem limite) |
| `limite_inferior/superior` | Números com ponto decimal |
| `limite_relativo` | Limites expressos em LLN/ULN (CTCAE) |
| `e_valor_critico` | `nao` |
| `status_validacao` | `fonte_do_projeto_sem_validacao` · `regra_do_projeto_nao_validada_clinicamente` · `transcrito_sem_conferencia_documento` |

### `pares_etarios.csv` — PK `par_id`

Campos: população, faixa etária, sexo, critérios de inclusão, ciclo, arquivo, variável NHANES, peso usado, unidade, `n_amostra`, `n_sem_valor`, `p2_5`, `p50`, `p97_5`, `pct_abaixo_ref_projeto`, `pct_acima_ref_projeto`, método de cálculo, referência, limitações e `status_informacao` (`estimativa_disponivel` · `evidencia_insuficiente`).

### `mapeamento_niveis.csv`, `referencias.csv` e `pendencias.csv`

Ver seção 4 para `mapeamento_niveis.csv`. `referencias.status_acesso`: `lido_localmente` · `arquivos_xpt_lidos_localmente` · `nao_acessado_nesta_sessao` · `nao_aplicavel`.

### Como recuperar os seis conteúdos para um exame e nível

```sql
SELECT c.resumo_exame,                       -- 1
       i.descricao_resultado,                -- 2
       i.informacoes_pares_etarios,          -- 3 (texto)
       i.impactos_individuo,                 -- 4
       i.possiveis_causas,                   -- 5
       i.mitigacao                           -- 6
FROM interpretacoes_exames i
JOIN catalogo_exames c ON c.exame_id = i.exame_id
WHERE i.exame_id = 'ferritina_ng_mL' AND i.nivel_id = '4' AND i.direcao = 'abaixo';
-- números dos pares: JOIN pares_etarios p ON p.exame_id = i.exame_id
```

---

## 3. Correspondência com o JSON consumido pelo interpretador

`interpretador_rag.py` carrega `base_conhecimento_exames_565.json` em `BASE_565_POR_COLUNA` e `BASE_565_POR_LOINC`. A estrutura é `{coluna: {coluna, codigo_loinc, nome_exame, categoria, resumo_exame, faixas: {CODIGO: {...}}}}`. **Um CSV novo não é usado automaticamente.**

| JSON existente | Origem nos CSVs | Conversão |
|---|---|---|
| chave do dicionário, `coluna` | `catalogo.exame_id` | direta |
| `codigo_loinc`, `nome_exame`, `categoria` | `catalogo` | direta (preservados) |
| `resumo_exame` | `catalogo.resumo_exame` | direta |
| `faixas.<CODIGO>` | `interpretacoes` filtrado pelo nível | só para códigos com correspondência validada em `mapeamento_niveis` (hoje nenhum além de condicionais) |
| `faixa_codigo`, `nivel` | `mapeamento_niveis.codigo_atual` / `nivel_atual` | **não pela posição numérica** |
| `descricao_resultado` | `interpretacoes.descricao_resultado` | uma por direção; o JSON tem uma por faixa → precisa de chave por direção |
| `estatistica_etaria_18_25` | `interpretacoes.informacoes_pares_etarios` | texto direto; vazio → frase padrão de ausência |
| `impactos_individuo`, `possiveis_causas` | mesmos nomes | uma por direção (o JSON atual mistura baixo e alto) |
| `correcao_desvio` | `interpretacoes.mitigacao` | mesmo papel conceitual: próximos passos. Renomear na conversão |
| `cor_hex`, `cor_nome`, `faixa_nome` | não existem nos CSVs | manter os do classificador |

**Diferença estrutural:** o JSON tem um texto por faixa; os CSVs têm um texto por faixa **e** direção. A conversão precisa de um dos formatos abaixo:

- **(a) Estender o JSON:** `faixas.<CODIGO>.por_direcao.{abaixo|acima}` com os mesmos campos. O consumidor escolhe pela `direcao_desvio` que o classificador já devolve.
- **(b) Achatar:** concatenar as duas direções em um texto. **Não recomendado**: reproduz o problema atual de causas de valores baixos e altos misturadas.

Esboço da conversão (a), **não executado**:

```python
import csv, json
cat = {r["exame_id"]: r for r in csv.DictReader(open("catalogo_exames.csv", encoding="utf-8"))}
mapa = {r["nivel_id"]: r["codigo_atual"] for r in csv.DictReader(open("mapeamento_niveis.csv", encoding="utf-8"))
        if r["escala_origem"] == "produto_5_niveis" and r["status_correspondencia"] in ("equivalencia_parcial",)}  # ampliar só após validação
saida = {}
for r in csv.DictReader(open("interpretacoes_exames.csv", encoding="utf-8")):
    cod = mapa.get(r["nivel_id"])
    if not cod or r["status_informacao"] == "nao_aplicavel":
        continue
    e = saida.setdefault(r["exame_id"], {k: cat[r["exame_id"]][k] for k in ("coluna", "codigo_loinc", "nome_exame", "categoria", "resumo_exame")} | {"faixas": {}})
    f = e["faixas"].setdefault(cod, {"faixa_codigo": cod, "por_direcao": {}})
    f["por_direcao"][r["direcao"]] = {
        "descricao_resultado": r["descricao_resultado"],
        "estatistica_etaria_18_25": r["informacoes_pares_etarios"] or "Não há estimativa validada disponível nesta base para este exame e recorte etário.",
        "impactos_individuo": r["impactos_individuo"],
        "possiveis_causas": r["possiveis_causas"],
        "correcao_desvio": r["mitigacao"],          # mitigacao -> correcao_desvio
        "status_informacao": r["status_informacao"],
    }
json.dump(saida, open("base_conhecimento_exames_csv.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
```

---

## 4. Adaptações mínimas necessárias (não aplicadas)

**Carregamento (`interpretador_rag.py`):**
1. Adicionar `KB_CSV_DIR` em `paths_config.py` e ler os CSVs com `csv.DictReader`, ou ler o JSON gerado pela conversão acima num caminho novo, sem sobrescrever o JSON atual.
2. Na consulta, escolher o texto por `codigo` **e** `direcao_desvio` (`abaixo`/`acima`), que `classificar_resultado_gradiente` já retorna.
3. Quando `status_informacao` for `nao_aplicavel` ou `pendente_validacao`, mostrar o estado e não um texto de outro nível.
4. Em `backend/`, que não tem `paths_config`, seria preciso apontar o caminho à mão. Recomenda-se unificar numa árvore antes.

**Classificação (`classificador.py` e `database.py`):**
1. Corrigir os caminhos NHANES em `paths_config.py` (seção 1) ou mover `dados_nhanes/` para o caminho esperado.
2. **Níveis:** não converter código atual em nível do produto pela posição. Correspondências (`mapeamento_niveis.csv`):

| Nível solicitado | Código atual | Status |
|---|---|---|
| 1 Normal | `NORMAL` (+ `LIMITROFE`, que está dentro do intervalo) | equivalência parcial |
| 2 Levemente alterado | — | **pendente** (`LIMITROFE` não é alteração; `ALTERADO_LEVE` é só candidato) |
| 3 Nível de atenção | — | **pendente** (sem definição operacional) |
| 4 Alterado de maneira moderada | `ALTERADO_MODERADO` | candidato condicional |
| 5 Alterado grave | `ALTERACAO_ACENTUADA` | candidato condicional; ≠ CTCAE grau 5 (morte) ≠ valor crítico |
| — | `INDETERMINADO` | estado técnico; **nunca converter em NORMAL** |

3. **Escala visual de 4 níveis** (`NIVEIS_4_VISUAIS_PACIENTE`): `NORMAL`; `LIMITROFE` (inclui `ALTERADO_LEVE` do classificador); `ALTERADO_MODERADO`; `ALTERACAO_ACENTUADA`; mais `INDETERMINADO`. Ela junta valores dentro e fora do intervalo na mesma cor. A nova base mantém os cinco níveis e não depende dessa escala.
4. Substituir as regras 10%/90%, 15% e 50% por critérios por exame quando houver fonte. As regras atuais estão em `criterios_classificacao.csv` como `regra_algoritmica_projeto`, convertidas em limites numéricos para os 32 exames com faixa no projeto. Em 13 casos a regra gera limite inferior negativo.
5. Corrigir as unidades da faixa de PCR e separar as faixas por sexo antes de usar `FAIXAS_PADRAO_LOINC`.
6. Criar a lógica de valor crítico a partir da política do laboratório, separada do nível.
7. Remover dos comentários e rótulos do classificador as equivalências "CLSI EP28 zona central", "CTCAE Grau 1/2" e "Graus 3–4 / CAP": essas normas não definem essas zonas.

---

## 5. Critérios e versões das fontes

| Fonte | Versão | Uso nesta base | Acesso |
|---|---|---|---|
| CLSI EP28-A3c | A3c | Só como escopo do conceito de intervalo de referência. **Não** justifica cinco níveis, zona ideal nem percentuais | não acessado (documento pago) |
| NCI CTCAE | **5.0** (2017) | 52 linhas `grau_evento_adverso_ctcae` para 12 analitos (13 termos), em LLN/ULN. Escolhida por ser a citada no código; a 6.0 não foi usada nem misturada | não acessado; limites transcritos sem conferência — `transcrito_sem_conferencia_documento` |
| CAP | 2019 | Só escopo: valores críticos dependem da política do laboratório. **Nenhum limite crítico foi criado** | não acessado |
| ADA Standards of Care | 2025, Seção 2 | Limites de decisão para glicose de jejum (100–125; ≥ 126 mg/dL) e HbA1c (5,7–6,4; ≥ 6,5%), com exigência de confirmação | não acessado; transcrito sem conferência |
| NHANES 2017–mar/2020 e 2011–2012 | arquivos do repo | Pares etários (seção 6) | arquivos `.xpt` lidos localmente |
| Código do projeto | ZIP fornecido | Faixas (`database.py`) e regras (`classificador.py`), marcadas como não validadas | lido localmente |
| Textos (`REF_RASCUNHO_AUTORAL`) | 1.0 | Resumo, causas, impactos, mitigação | redigidos a partir de conhecimento geral; **sem fonte primária por item** |

Páginas e trechos não foram registrados porque os documentos não foram abertos nesta sessão. Nenhum critério CTCAE ou ADA define, sozinho, um nível do produto.

---

## 6. Contagens de cobertura e validações executadas

**Cobertura (113 exames × 5 níveis):** 113/113 exames têm linha para todos os cinco níveis.

| `status_informacao` | Linhas |
|---|---|
| `conteudo_disponivel` (nível 1 com texto) | 112 |
| `pendente_validacao` (texto redigido, critério do nível não definido) | 651 |
| `nao_aplicavel` (direção sem significado; níveis 2–5 de sorologias) | 236 |
| **Total** | **999** |

Por nível: nível 1 = 113 · níveis 2 a 5 = 220 cada (abaixo + acima) · fora da escala (sorologias reagentes/abaixo do limiar) = 6. Os 113 exames incluem 5 qualitativos (HIV, HBsAg, anti-HCV, VDRL e FAN) e anti-HBs, com tipo pendente. A conta passa de 565 porque direção e contexto viram linhas próprias.

**Critérios:** 32 intervalos do projeto · 288 regras algorítmicas do projeto · 52 graus CTCAE · 4 limites ADA · 0 valores críticos. 81 exames não têm intervalo no projeto.

**Pares etários:** 72 linhas (36 exames × 2 sexos), todas com n ≥ 100 (entre 137 e 552). Método:
- exclui gestantes;
- usa o peso MEC, de jejum ou de subamostra, conforme o arquivo;
- calcula percentis ponderados;
- **não calcula** o erro-padrão pelo desenho amostral.

O % fora da faixa do projeto não foi calculado para PCR (unidades diferentes) nem para TSH e T4 livre (dependem do método).

**Validações executadas com o parser `csv` do Python** (`_gerador/validar_csvs.py`; saída em `_gerador/resultado_validacao.txt`) — **35 verificações OK, 0 falhas**:
- **Arquivos e chaves:** 7 arquivos com chave primária única e não vazia, cabeçalho único e UTF-8 sem BOM.
- **Catálogo:** cobre os 113 exames, com LOINC e nomes idênticos à base 565.
- **Integridade:** toda referência cruzada é válida (`exame_id`, `ref_id`, `par_ids`).
- **Cobertura:** os 5 níveis estão presentes para todos os exames, sem duplicidade exame + nível + direção.
- **Textos:** nenhuma expressão proibida; nenhum percentual da base antiga copiado; causas de valores baixos e altos sempre em textos distintos.
- **Dados ausentes:** pares sem amostra suficiente ficariam vazios, nunca zero.
- **Limites:** numéricos com ponto decimal; as regras do projeto não têm lacuna nem sobreposição nos 32 exames.

Reproduzir:

```bash
python conhecimento_exames_csv/_gerador/gerar_csvs.py
python conhecimento_exames_csv/_gerador/validar_csvs.py
```

---

## 7. Pendências que impedem uso automático

Lista completa em `pendencias.csv` (96 linhas). As que bloqueiam:

1. **Revisão clínica de todos os textos** (`REF_RASCUNHO_AUTORAL`); nenhuma foi feita.
2. **Critérios por exame para os níveis 2 a 5:** sem eles, todas essas linhas ficam `pendente_validacao`, e "Nível de atenção" não tem definição.
3. **Intervalos de referência** para 81 exames, e faixas por sexo para hemoglobina, hematócrito e hemácias.
4. **Valores críticos:** política do laboratório parceiro, com limites, população e comunicação.
5. **Conferência CTCAE v5.0 e ADA 2025** contra os documentos oficiais, com registro de página.
6. **LOINC do VDRL**, categorias trocadas e nomes com unidade na base 565.
7. **Unidade da faixa de PCR** (mg/dL × mg/L).
8. **Árvore em uso** (`02_backend/` × `backend/`) e caminhos de `paths_config.py`.
9. **Estatísticas brasileiras:** os pares são dos EUA. Não há base populacional brasileira no repositório.
10. **Imagem de requisitos:** não veio no material recebido. Os cinco níveis e os seis conteúdos foram seguidos conforme o texto da solicitação.
