from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 5050
    DEBUG: bool = True
    SERVICE_NAME: str = "wearable-causal-service"

    # Banco de Dados
    DATABASE_PATH: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///../open_health.db")
    # Integrações API
    TERRA_WEBHOOK_SECRET: str = "YOUR_TERRA_WEBHOOK_SECRET"
    TERRA_API_BASE_URL: str = "https://api.tryterra.co/v2"
    TERRA_API_KEY: str = "YOUR_TERRA_API_KEY"
    TERRA_DEV_ID: str = "YOUR_TERRA_DEV_ID"

    # Endpoints de Microserviços Open Health
    FHIR_LAB_SERVICE_URL: str = "http://localhost:5000"
    NHANES_BASELINE_SERVICE_URL: str = "http://localhost:5055"
    HTTP_CLIENT_TIMEOUT_SEC: float = 10.0

    # Polling Schedule
    ENABLE_BACKGROUND_POLLING: bool = True
    POLLING_CRON_HOUR: int = 4
    POLLING_CRON_MINUTE: int = 0

settings = Settings()
