from database.connection import engine
from database.models import Base

from data_governance.governance_model import GovernancePolicy

from database.models import ChatSession
from database.models import ChatMessage

Base.metadata.create_all(bind=engine)

print("TABLES CREATED SUCCESSFULLY")