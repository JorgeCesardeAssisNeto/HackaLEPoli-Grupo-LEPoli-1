from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent / "04_persistencia_dados" / "open_health.db"


class Settings(BaseSettings):
    """Configurações do microserviço de wearables (porta 5050) integrado à ROOK API."""
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Servidor
    SERVICE_NAME: str = "open-health-wearable-causal-service"
    PORT: int = 5050
    HOST: str = "0.0.0.0"
    DEBUG: bool = False

    # Banco relacional principal (open_health.db)
    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

    # ROOK API (https://docs.tryrook.io)
    ROOK_API_BASE_URL: str = "https://api.rook-connect.com"
    ROOK_CLIENT_UUID: str = ""
    ROOK_CLIENT_SECRET: str = ""
    # Segredo usado para validar o header X-ROOK-HASH (se vazio, usa ROOK_CLIENT_SECRET)
    ROOK_WEBHOOK_SECRET: str = ""

    # Serviços internos (HTTP REST)
    FHIR_LAB_SERVICE_URL: str = "http://localhost:5000"
    NHANES_BASELINE_SERVICE_URL: str = "http://localhost:5055"
    HTTP_CLIENT_TIMEOUT_SEC: float = 8.0

    # Polling diário
    ENABLE_BACKGROUND_POLLING: bool = True
    POLLING_CRON_HOUR: int = 4
    POLLING_CRON_MINUTE: int = 0
    POLLING_LOOKBACK_DAYS: int = 2


settings = Settings()
