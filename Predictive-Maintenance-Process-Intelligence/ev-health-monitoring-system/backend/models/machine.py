from sqlalchemy import Column, Integer, String
from backend.database.connection import Base


class Machine(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_name = Column(String)
    charger_type = Column(String)
    location = Column(String)
    