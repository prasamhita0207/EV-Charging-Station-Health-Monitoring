# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String

from backend.database.connection import Base


class Operator(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(100), unique=True, nullable=False)

    phone = Column(String(15), nullable=False)

    shift = Column(String(20), nullable=False)
