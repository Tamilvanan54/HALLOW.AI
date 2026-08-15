from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database.connection import Base


class GovernancePolicy(Base):

    __tablename__ = "governance_policies"

    id = Column(Integer, primary_key=True)

    policy_name = Column(String(100))

    description = Column(String(500))

    status = Column(String(50), default="Active")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )