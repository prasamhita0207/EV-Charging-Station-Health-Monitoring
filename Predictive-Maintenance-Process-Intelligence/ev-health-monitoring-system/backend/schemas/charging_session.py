from pydantic import BaseModel
from datetime import datetime
class ChargingSessionCreate(BaseModel):
    station_id: int
    vehicle_id: str
    start_time: datetime
    end_time: datetime
    energy_consumed: float
    cost: float
class ChargingSessionResponse(BaseModel):
    id: int
    station_id: int
    vehicle_id: str
    start_time: datetime
    end_time: datetime
    energy_consumed: float
    cost: float
    class Config:
        from_attributes = True