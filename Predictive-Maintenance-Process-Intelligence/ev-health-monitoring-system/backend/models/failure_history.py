from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class FailureHistory(Base):
    __tablename__ = "failure_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    charging_station_id = Column(
        Integer, ForeignKey("charging_stations.id", ondelete="CASCADE"), nullable=False
    )
    failure_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    failure_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved = Column(String(10), default="No", nullable=False)  # "Yes" or "No"
