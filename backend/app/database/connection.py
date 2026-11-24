from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

if settings.db_null_pool:
    # Serverless (Vercel): do not keep connections, Neon's pooler handles pooling
    engine = create_engine(
        settings.database_url, poolclass=NullPool, pool_pre_ping=True
    )
else:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()