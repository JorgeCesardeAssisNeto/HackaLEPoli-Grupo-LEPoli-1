# Sessão 01: Core Web & APIs de Serviços (Flask / Microserviços)

Servidores HTTP, orquestradores de endpoints REST e interfaces interativas da plataforma.

## Arquivos nesta Sessão:

### `app.py`
- **Origem no projeto:** `Etapa Exames de Sangue/app.py`
- **Descrição:** Servidor Web principal (Flask) do módulo clínico. Gerencia upload de laudos PDF, orquestração de OCR, consultas longitudinais (3 anos), painel de consentimento LGPD e integração com RAG.

### `app_nhanes.py`
- **Origem no projeto:** `nhanes_explorer/app.py`
- **Descrição:** Servidor Web analítico do explorador populacional NHANES. Provê endpoints para consultas analíticas multivariadas, gráficos epidemiológicos e calibração estatística.

### `app_wearables.py`
- **Origem no projeto:** `Dataset Wearables/app_wearables.py`
- **Descrição:** Microserviço dedicado ao processamento analítico e exploração de séries temporais de wearables (frequência cardíaca, HRV, sono, passos e estresse).

