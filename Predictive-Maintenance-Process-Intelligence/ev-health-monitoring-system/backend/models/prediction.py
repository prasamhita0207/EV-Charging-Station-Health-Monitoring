from sqlalchemy import Column, Integer, Float, String
from backend.database.connection import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    power_consumption = Column(Float)
    prediction = Column(String)