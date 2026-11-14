# Sessão 03: Padronização Semântica & Ontologias (LOINC / FHIR)

Padronização semântica, dicionários biomédicos e motores de regras determinísticas de referência.

## Arquivos nesta Sessão:

### `mapeador_planilha.py`
- **Origem no projeto:** `Etapa Exames de Sangue/mapeador_planilha.py`
- **Descrição:** Algoritmo de mapeamento semântico que correlaciona nomes laboratoriais livres a códigos oficiais LOINC e padrões BR Core / HL7 FHIR.

### `classificador.py`
- **Origem no projeto:** `Etapa Exames de Sangue/classificador.py`
- **Descrição:** Motor de classificação clínica determinística. Compara valores com intervalos biológicos de referência e gera alertas e criticidades clínicas.

### `base_conhecimento_exames_565.json`
- **Origem no projeto:** `Etapa Exames de Sangue/base_conhecimento_exames_565.json`
- **Descrição:** Base estruturada contendo o catálogo de 565 biomarcadores clínicos, suas unidades e significados fisiológicos.

### `base_conhecimento_loinc.json`
- **Origem no projeto:** `Etapa Exames de Sangue/base_conhecimento_loinc.json`
- **Descrição:** Ontologia internacional LOINC com descrições, termos canônicos, sistemas corporais e métodos analíticos.

### `mapa_colunas_loinc.json`
- **Origem no projeto:** `Etapa Exames de Sangue/mapa_colunas_loinc.json`
- **Descrição:** Mapeamento De-Para entre nomes comerciais de exames laboratoriais e suas colunas padronizadas LOINC.

### `catalogo_colunas_completo.json`
- **Origem no projeto:** `Etapa Exames de Sangue/catalogo_colunas_completo.json`
- **Descrição:** Catálogo unificado de metadados, tipos de dados e especificações de colunas laboratoriais.

