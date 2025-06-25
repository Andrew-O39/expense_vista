from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from expense_tracker.app.db.base import Base
from expense_tracker.app.core.config import settings

from expense_tracker.app.db.base_class import *  # Import all models

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)  # sync engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for local testing
if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")