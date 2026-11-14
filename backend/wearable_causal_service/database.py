from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from models.base import Base


def _prepare_engine_config(database_url: str) -> Tuple[str, Dict[str, Any]]:
    """Normalizes SQLite path creation and asyncpg SSL query params safely."""
    if database_url.startswith("sqlite"):
        sqlite_path = database_url.split("///", 1)[-1] if "///" in database_url else settings.DATABASE_PATH
        if sqlite_path and sqlite_path != ":memory:":
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        return database_url, {"check_same_thread": False}

    # asyncpg rejects ?sslmode=... in DSN kwargs; convert sslmode -> connect_args["ssl"]
    parsed = urlsplit(database_url)
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    connect_args: Dict[str, Any] = {}
    filtered_pairs = []
    for k, v in query_pairs:
        kl = k.lower()
        if kl == "sslmode":
            vl = v.lower()
            connect_args["ssl"] = False if vl == "disable" else vl
        elif kl == "channel_binding":
            continue
        else:
            filtered_pairs.append((k, v))
    clean_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(filtered_pairs), parsed.fragment))
    return clean_url, connect_args


ENGINE_URL, connect_args = _prepare_engine_config(settings.DATABASE_URL)

engine = create_async_engine(
    ENGINE_URL,
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

