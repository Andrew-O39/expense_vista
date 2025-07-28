from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.base import Base
from app.core.config import settings

from app.db.base_class import *  # Import all models

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)  # sync engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to provide a database session
def get_db() -> Session:
    """
    Provides a transactional scope around a series of operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables locally for testing or initial setup
if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")