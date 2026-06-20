"""SQLAlchemy engine, session factory, and declaritive base."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    def get_db():
        """Yield a database session and quarantee it is closed aftewards"""

        db = SessionLocal()
        try:
            yield db
        finally:
            db.close