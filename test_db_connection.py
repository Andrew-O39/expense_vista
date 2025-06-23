from sqlalchemy import create_engine
from app.core.config import settings

def test_connection():
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connected:", result.fetchone())
    except Exception as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    test_connection()