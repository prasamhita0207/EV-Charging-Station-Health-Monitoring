from pydantic import BaseModel


class PredictionInput(BaseModel):
    temperature: float
    humidity: float
    power_consumption: float