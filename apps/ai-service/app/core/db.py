from collections.abc import Generator

from shared_db import create_engine, create_session_factory

from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = create_session_factory(engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

