from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase


def utc_now_naive() -> datetime:
    """Timezone-naive UTC timestamp compatible with SQLite and Postgres TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass

