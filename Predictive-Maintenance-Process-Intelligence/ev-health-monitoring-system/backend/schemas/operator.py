# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class OperatorCreate(BaseModel):
    name: str
    email: str
    phone: str
    shift: str


class OperatorResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    shift: str

    class Config:
        from_attributes = True
