from pydantic import BaseModel


class MaintenanceCreate(BaseModel):
    charging_station_id: int
    maintenance_date: str
    status: str


class MaintenanceResponse(BaseModel):
    id: int
    charging_station_id: int
    maintenance_date: str
    status: str

    class Config:
        from_attributes = True