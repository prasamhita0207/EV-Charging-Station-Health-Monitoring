from pydantic import BaseModel

class PredictionCreate(BaseModel):
    temperature: float
    humidity: float
    power_consumption: float
    prediction: str