# 🏛️ Arquitetura do Backend — Open Health Brasil (Hackathon LEPoli)

Esta pasta consolida e categoriza **todos os componentes de backend** da plataforma Open Health Brasil, organizados modularmente por responsabilidades.

## 📂 Estrutura de Pastas por Sessões

- [**`01_core_api/`**](./01_core_api): Sessão 01: Core Web & APIs de Serviços (Flask / Microserviços)
- [**`02_ingestao_ocr/`**](./02_ingestao_ocr): Sessão 02: Pipeline de Ingestão & OCR de Laudos
- [**`03_semantica_ontologias/`**](./03_semantica_ontologias): Sessão 03: Padronização Semântica & Ontologias (LOINC / FHIR)
- [**`04_persistencia_dados/`**](./04_persistencia_dados): Sessão 04: Persistência & Longitude Relacional (SQL / SQLite)
- [**`05_inteligencia_rag/`**](./05_inteligencia_rag): Sessão 05: Inteligência Médica & RAG (Retrieval-Augmented Generation)
- [**`06_populacional_nhanes/`**](./06_populacional_nhanes): Sessão 06: Big Data Populacional & Bridge Wearables (CDC NHANES)
- [**`07_sensores_wearables/`**](./07_sensores_wearables): Sessão 07: Sensores Wearables & Séries Biométricas
- [**`08_machine_learning_causal/`**](./08_machine_learning_causal): Sessão 08: Modelos Preditivos & Inferência Causal
- [**`09_geradores_sinteticos/`**](./09_geradores_sinteticos): Sessão 09: Geradores de Dados Sintéticos & Ferramentas Auxiliares
- [**`10_relatorios_cientificos/`**](./10_relatorios_cientificos): Sessão 10: Motores de Relatórios Científicos & Gráficos Automatizados

---

## 🔄 Fluxograma Arquitetural Geral

```mermaid
flowchart TD
    subgraph S_ENTRADAS ["📥 Fontes de Dados"]
        PDF_LAUDO["Laudos Médicos (PDF)"]
        WEARABLE_CSV["Séries Temporais Wearables"]
        CDC_NHANES["Repositório CDC NHANES"]
    end

    subgraph S02 ["02_ingestao_ocr"]
        EXT_CLOUD["extrator.py (Gemini LLM)"]
        EXT_LOCAL["extrator_local.py (Regex)"]
    end

    subgraph S03 ["03_semantica_ontologias"]
        MAPPER["mapeador_planilha.py"]
        CLASSIF["classificador.py"]
        ONTOLOGY[("Bases LOINC & FHIR")]
    end

    subgraph S04 ["04_persistencia_dados"]
        DB_MOD["database.py"]
        DB_SQL[("open_health.db (SQLite)")]
    end

    subgraph S05 ["05_inteligencia_rag"]
        RAG_MOD["interpretador_rag.py"]
        GEN_KNOW["gerador_conhecimento.py"]
    end

    subgraph S01 ["01_core_api"]
        APP_CLINICO["app.py (API Clínica)"]
        APP_NHANES["app_nhanes.py (Pop.)"]
        APP_WEAR["app_wearables.py (Sensores)"]
    end

    subgraph S06_08 ["06_populacional & 08_machine_learning"]
        ENGINE["data_engine.py"]
        BRIDGE["wearable_bridge.py"]
        MODELS["train_models & test_models"]
    end

    subgraph S10 ["10_relatorios_cientificos"]
        REPORTS["Compiladores PDF & Gráficos"]
    end

    PDF_LAUDO --> EXT_CLOUD & EXT_LOCAL
    EXT_CLOUD & EXT_LOCAL --> MAPPER
    ONTOLOGY --> MAPPER & CLASSIF
    MAPPER --> CLASSIF --> DB_MOD --> DB_SQL
    DB_SQL --> RAG_MOD & APP_CLINICO
    RAG_MOD --> APP_CLINICO
    WEARABLE_CSV --> APP_WEAR & BRIDGE
    CDC_NHANES --> ENGINE
    MODELS --> ENGINE --> BRIDGE
    DB_SQL <--> BRIDGE
    DB_SQL & ENGINE --> REPORTS
```
