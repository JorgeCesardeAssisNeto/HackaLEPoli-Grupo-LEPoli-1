# Open Health — Wearable Ingestion & Causal Inference (porta 5050)

Ingestão de wearables via **ROOK API** (webhook + polling diário), persistência em `open_health.db`
e DAG causal em 3 camadas com limiares estáticos para 4 alvos clínicos.

## Estrutura
```
main.py  config.py  database.py  pytest.ini  .env.example  Dockerfile
models/    base, mappings (RookUserMapping), wearable_metrics, causal_results
schemas/   rook, metrics, causal, interservice
clients/   rook_client (REST ROOK), fhir_client (:5000), nhanes_client (:5055)
services/  rook_normalizer, ingestion_service, causal_engine, alert_service
routers/   webhook, ingestion, causal, health
tasks/     polling (APScheduler)
tests/
```

## Endpoints
| Método | Rota | Função |
|---|---|---|
| POST | `/wearables/webhook` | Webhook da ROOK (valida `x-rook-signature` / `rook-signature` / `x-rook-hash` quando configurado) |
| POST | `/wearables/link-user` | Vincula `user_id` ROOK ↔ paciente (padrão: `user_id = patient_id`) |
| GET | `/wearables/authorizer/{user_id}/{data_source}` | URL de autorização OAuth (Garmin, Oura...) |
| POST | `/wearables/metrics/manual` | Insere métricas e confundidores (tela, cafeína, álcool) |
| POST | `/wearables/sync` | Polling imediato |
| POST | `/causal/evaluate/{patient_id}` | Avaliação causal |
| GET/PATCH | `/causal/alerts/...` | Consulta/atualiza alertas |
| GET | `/health`, `/health/ready`, `/metrics` | Saúde |

## Executar
```powershell
python -m pip install -r requirements.txt
copy .env.example .env     # preencha ROOK_CLIENT_UUID / ROOK_SECRET_KEY
python -m pytest
python main.py             # http://localhost:5050/docs
```

## Configuração na ROOK
- **URL do webhook:** `https://<URL-PUBLICA>/wearables/webhook` (POST; responde 200).
- **Assinatura (opcional):** headers `x-rook-signature` / `rook-signature` / `x-rook-hash`. Só é validada se o header vier **e** `ROOK_WEBHOOK_SECRET` estiver preenchido (não vazio/placeholder) e `DEBUG=false`; caso contrário a entrega é aceita.
- **Variáveis (Render):** `ROOK_CLIENT_UUID`, `ROOK_SECRET_KEY`, `ROOK_WEBHOOK_SECRET`, `ROOK_API_BASE_URL`, `DATABASE_URL` (`postgres://` é convertido para asyncpg).
  Em desenvolvimento: `ngrok http 5050` e use a URL `https://xxxx.ngrok-free.app/wearables/webhook`.
- Cadastre-a no ROOK Portal → Webhooks (Sandbox e Production separados).
- Credenciais (`client_uuid` e `secret_key`) vão no `.env`; REST usa HTTP Basic.
- O `user_id` na ROOK deve ser o `patient_id` (1–50 caracteres) — assim nenhum vínculo extra é necessário.

> A ROOK não fornece tempo de tela, cafeína nem álcool: envie-os por `/wearables/metrics/manual`.
