from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:Dpi%401234@localhost:5432/college_ai"

try:
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    print("DATABASE CONNECTED")
    conn.close()
except Exception as e:
    print("ERROR:", e)