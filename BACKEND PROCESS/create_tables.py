from sqlalchemy import text
from database.connection import engine, Base
from database.models import User, AuditLog, Feedback, ChatSession, ChatMessage, PDFDocument
from data_governance.governance_model import GovernancePolicy

def run_migrations():
    print("⏳ Running database schema migrations...")
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS college VARCHAR(150);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS year VARCHAR(50);"))
            conn.execute(text("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS modified_answer VARCHAR(10000);"))
            conn.execute(text("ALTER TABLE pdf_documents ADD COLUMN IF NOT EXISTS department VARCHAR(100) DEFAULT 'ALL';"))
            conn.execute(text("ALTER TABLE pdf_documents ADD COLUMN IF NOT EXISTS year VARCHAR(50) DEFAULT 'ALL';"))
            conn.execute(text("ALTER TABLE pdf_documents ADD COLUMN IF NOT EXISTS uploaded_by VARCHAR(150);"))
        print("✅ DATABASE TABLES AND COLUMNS MIGRATED SUCCESSFULLY!")
    except Exception as e:
        print(f"⚠️ DB Migration warning: {e}")

if __name__ == "__main__":
    run_migrations()