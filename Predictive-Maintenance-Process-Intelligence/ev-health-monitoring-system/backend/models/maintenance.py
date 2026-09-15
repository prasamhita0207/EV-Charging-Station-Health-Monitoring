from sqlalchemy import Column, Integer, String
from backend.database.connection import Base


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    charging_station_id = Column(Integer)
    maintenance_date = Column(String)
    status = Column(String)