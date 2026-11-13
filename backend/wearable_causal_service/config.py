import re
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent / "04_persistencia_dados" / "open_health.db"


def is_placeholder(value: str) -> bool:
    """True para segredo vazio ou valor de exemplo (YOUR_..., changeme, xxx...)."""
    v = (value or "").strip().lower()
    return not v or v.startswith("your_") or v.startswith("seu-") or v in {"changeme", "change-me", "xxx", "placeholder"}


class Settings(BaseSettings):
    """Configurações do microserviço (porta 5050). Variáveis desconhecidas são ignoradas."""
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

    # Banco relacional (SQLite local ou PostgreSQL no Render)
    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

    # ROOK API
    ROOK_API_BASE_URL: str = "https://api.rook-connect.com"
    ROOK_CLIENT_UUID: str = ""
    ROOK_SECRET_KEY: str = ""
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

    @field_validator("DATABASE_URL")
    @classmethod
    def _async_driver(cls, url: str) -> str:
        """Render fornece postgres:// ou postgresql://; o SQLAlchemy assíncrono exige +asyncpg."""
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return re.sub(r"^(postgres|postgresql)://", "postgresql+asyncpg://", url)


settings = Settings()
