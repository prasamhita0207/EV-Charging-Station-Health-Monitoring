from sqlalchemy import Column, Integer, Float, String, DateTime
from backend.database.connection import Base
class ChargingSession(Base):
    __tablename__ = "charging_sessions"
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer)
    vehicle_id = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    energy_consumed = Column(Float)
    cost = Column(Float)
