import os
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from models.base import Base

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

# Garante que o diretório do arquivo exista (apenas SQLite)
if IS_SQLITE:
    Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Build async engine
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables defined in the metadata."""
    import models  # noqa: F401  (registra todas as tabelas no metadata)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

