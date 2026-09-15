from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from backend.database.connection import Base
import datetime


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    charging_station_id = Column(
        Integer, ForeignKey("charging_stations.id"), index=True
    )

    alert_type = Column(String, index=True)
    description = Column(String)
    is_resolved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
