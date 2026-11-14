# Sessão 04: Persistência & Longitude Relacional (SQL / SQLite)

Camada de acesso a dados (DAO), scripts DDL e integridade referencial relacional.

## Arquivos nesta Sessão:

### `database.py`
- **Origem no projeto:** `Etapa Exames de Sangue/database.py`
- **Descrição:** Camada DAO (Data Access Object) SQLite. Controla migrações de esquema, inserções de pacientes, laudos, observações, consentimentos e consultas históricas longitudinais.

### `schema_open_health.sql`
- **Origem no projeto:** `Etapa Exames de Sangue/schema_open_health.sql`
- **Descrição:** Script SQL DDL de criação do banco de dados relacional (pacientes, consentimentos, laudos, observations, wearable_metrics e views analíticas).

### `check_views.py`
- **Origem no projeto:** `check_views.py`
- **Descrição:** Script de validação e integridade de views SQL analíticas e consistência de índices temporais.

