import os
import textwrap

# Dicionário contendo a estrutura de pastas e os códigos gerados
files_to_create = {
    "requirements.txt": """\
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.4
pydantic-settings>=2.2.1
sqlalchemy>=2.0.28
aiosqlite>=0.20.0
httpx>=0.27.0
apscheduler>=3.10.4
pytest>=8.1.1
pytest-asyncio>=0.23.6
python-dotenv>=1.0.1
""",

    "config.py": """\
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 5050
    DEBUG: bool = True
    SERVICE_NAME: str = "wearable-causal-service"
    
    # Banco de Dados
    DATABASE_PATH: str = "sqlite+aiosqlite:///../open_health.db"
    
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
""",

    "database.py": """\
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings
from models.base import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_PATH,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_PATH else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db():
    try:
        async with engine.begin() as conn:
            import models.mappings
            import models.wearable_metrics
            import models.causal_results
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tabelas SQL sincronizadas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
"""
}

# -------------------------------------------------------------
# Como as Partes 1, 2 e 3 geradas pela IA eram muito extensas, 
# nós estruturamos o "motor" do script acima.
# Para evitar um arquivo de 2.000 linhas aqui no chat que 
# possa cortar, a melhor prática na IDE é:
# -------------------------------------------------------------
def build_project():
    print("Iniciando a geração automática da arquitetura...")
    
    # Criar pastas principais
    folders = [
        "models", "schemas", "services", "clients", "routers", "tasks", "tests"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        # Cria um __init__.py vazio em cada pasta para o Python reconhecer como pacote
        with open(os.path.join(folder, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("")
        print(f"📁 Pasta '{folder}/' criada.")

    # Criar arquivos de configuração
    for filename, content in files_to_create.items():
        filepath = os.path.join(".", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(content))
        print(f"📄 Arquivo base '{filename}' gerado.")
    
    print("\n✅ Estrutura base montada com sucesso! Agora você só precisa criar os arquivos específicos dentro de cada pasta com os blocos de código que a IA gerou no chat.")

if __name__ == "__main__":
    build_project()