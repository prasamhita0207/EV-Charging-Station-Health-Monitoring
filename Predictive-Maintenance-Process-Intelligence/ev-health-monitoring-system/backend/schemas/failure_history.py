# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class FailureHistoryCreate(BaseModel):
    charging_station_id: int
    failure_type: str
    description: str
    failure_date: str
    resolved: str


class FailureHistoryResponse(BaseModel):
    id: int
    charging_station_id: int
    failure_type: str
    description: str
    failure_date: str
    resolved: str

    class Config:
        from_attributes = True
