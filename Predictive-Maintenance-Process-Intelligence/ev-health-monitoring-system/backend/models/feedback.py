from sqlalchemy import Column, Integer, String
from backend.database.connection import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String)
    comments = Column(String)
    rating = Column(Integer)