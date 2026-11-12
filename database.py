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
