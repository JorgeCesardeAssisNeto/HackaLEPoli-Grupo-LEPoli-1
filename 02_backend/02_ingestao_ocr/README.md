# Sessão 02: Pipeline de Ingestão & OCR de Laudos

Módulos de ingestão documental para conversão de laudos em PDF para dados estruturados.

## Arquivos nesta Sessão:

### `extrator.py`
- **Origem no projeto:** `Etapa Exames de Sangue/extrator.py`
- **Descrição:** Extrator inteligente via LLM multimodal (Gemini). Processa páginas de laudos em PDF e extrai JSON estrito com valores, unidades e referências.

### `extrator_local.py`
- **Origem no projeto:** `Etapa Exames de Sangue/extrator_local.py`
- **Descrição:** Extrator offline determinístico baseado em expressões regulares e heurísticas laboratoriais para execução sem dependência de nuvem.

