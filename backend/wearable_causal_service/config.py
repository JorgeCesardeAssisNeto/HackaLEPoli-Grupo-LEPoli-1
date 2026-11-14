import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOK_PRODUCTION_BASE_URL = "https://api.rook-connect.com"
ROOK_SANDBOX_BASE_URL = "https://api.rook-connect.review"
DEFAULT_ROOK_CLIENT_UUID = "9bc48033-9d8e-45b4-8c6a-1ef162951442"

BASE_DIR = Path(__file__).resolve().parent


def _resolve_default_db_path() -> Path:
    """Prefers the active FHIR database in 02_backend when present in the monorepo."""
    monorepo_db = BASE_DIR.parent.parent / "02_backend" / "04_persistencia_dados" / "open_health.db"
    if monorepo_db.exists():
        return monorepo_db
    legacy_dir = BASE_DIR.parent / "04_persistencia_dados"
    if legacy_dir.exists():
        return legacy_dir / "open_health.db"
    return BASE_DIR / "open_health.db"


DEFAULT_DB_PATH = _resolve_default_db_path()


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
    SERVICE_API_KEY: str = ""

    # Banco relacional (SQLite local ou PostgreSQL no Render)
    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

    # ROOK API
    ROOK_API_BASE_URL: str = ROOK_PRODUCTION_BASE_URL
    ROOK_CLIENT_UUID: str = DEFAULT_ROOK_CLIENT_UUID
    ROOK_SECRET_KEY: str = ""
    ROOK_CLIENT_SECRET: str = ""
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

    @model_validator(mode="after")
    def _normalize_rook_settings(self):
        """Aceita ROOK_CLIENT_SECRET como alias, garante UUID padrão e usa URL Sandbox quando DEBUG=True."""
        if is_placeholder(self.ROOK_CLIENT_UUID):
            self.ROOK_CLIENT_UUID = DEFAULT_ROOK_CLIENT_UUID
        if is_placeholder(self.ROOK_SECRET_KEY) and not is_placeholder(self.ROOK_CLIENT_SECRET):
            self.ROOK_SECRET_KEY = self.ROOK_CLIENT_SECRET
        if self.DEBUG and not os.getenv("ROOK_API_BASE_URL"):
            if self.ROOK_API_BASE_URL == ROOK_PRODUCTION_BASE_URL:
                self.ROOK_API_BASE_URL = ROOK_SANDBOX_BASE_URL
        return self

    @property
    def database_display(self) -> str:
        """Safe database identifier for logs and /health without leaking credentials."""
        if self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL.split("///", 1)[-1] if "///" in self.DATABASE_URL else self.DATABASE_PATH
        parsed = urlsplit(self.DATABASE_URL)
        host = parsed.hostname or "unknown-host"
        port = f":{parsed.port}" if parsed.port else ""
        return f"{parsed.scheme}://{host}{port}{parsed.path}"


settings = Settings()
