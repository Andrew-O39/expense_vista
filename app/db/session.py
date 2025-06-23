from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connected:", result.fetchone())
    except Exception as e:
        print("❌ Connection failed:", e)