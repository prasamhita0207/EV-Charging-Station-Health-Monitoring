from pydantic import BaseModel


class TelemetryCreate(BaseModel):
    charging_station_id: int
    temperature: float
    humidity: float
    power_consumption: float


class TelemetryResponse(BaseModel):
    charging_station_id: int
    temperature: float
    humidity: float
    power_consumption: float

    class Config:
        from_attributes = True