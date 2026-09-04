from sqlalchemy import Column, Integer, String
from database.connection import Base


class MonitoringStats(Base):

    __tablename__ = "monitoring_stats"

    id = Column(Integer, primary_key=True)

    metric_name = Column(String(100))

    metric_value = Column(String(100))