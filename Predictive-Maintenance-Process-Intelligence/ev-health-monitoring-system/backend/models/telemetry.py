from sqlalchemy import Column, Integer, Float
from backend.database.connection import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    charging_station_id = Column(Integer)
    temperature = Column(Integer)
    humidity = Column(Float)
    power_consumption = Column(Float)