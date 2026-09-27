from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)


def get_db() -> Generator[Session, None, None]:
    """Una sesión por request; se hace rollback si algo falla a mitad de la operación."""
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
