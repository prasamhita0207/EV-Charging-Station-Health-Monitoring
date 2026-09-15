import joblib
import pandas as pd

model = joblib.load("backend/ml/model.pkl")

def predict_failure(temperature, humidity, power_consumption):

    sample = pd.DataFrame(
        [[temperature, humidity, power_consumption]],
        columns=[
            "temperature",
            "humidity",
            "power_consumption"
        ]
    )

    prediction = model.predict(sample)

    if prediction[0] == 1:
        return "Failure Expected"

    return "Charging Station Healthy"