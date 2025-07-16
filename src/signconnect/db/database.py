# src/signconnect/db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from signconnect.core.config import get_settings

# get the database URL from the settings
SQLALCHEMY_DATABASE_URL = get_settings().DATABASE_URL

# create the SQLALCHEMY engine. The engine is the entry point to the db
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# create a SessionLocal class. Each instance of SessionLocal will be a new bs session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create a Base class. Our ORM models will inherit from this class.
Base = declarative_base()

# dependency for getting a db session
def get_db():
    """
    FastAPI dependency that provides a database session for a single request.
    It ensures the session is always closed after the request is finished.
    :return: Database session.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def enable_pgvector_extension():
    """
    Enables the pgvector extension in the database.
    This must be run before creating tables with Vector columns.
    """
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()