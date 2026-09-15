from pydantic import BaseModel


class MachineCreate(BaseModel):
    station_name: str
    charger_type: str
    location: str


class MachineResponse(BaseModel):
    id: int
    station_name: str
    charger_type: str
    location: str

    class Config:
        from_attributes = True