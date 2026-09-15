from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertCreate(BaseModel):
    charging_station_id: int
    alert_type: str
    description: str
    is_resolved: Optional[bool] = False


class AlertResponse(BaseModel):
    id: int
    charging_station_id: int
    alert_type: str
    description: str
    is_resolved: bool
    timestamp: datetime

    class Config:
        from_attributes = True
