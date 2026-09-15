import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

data = []

for i in range(1000):

    temperature = 20 + (i % 40)       # 20–59
    humidity = 30 + (i % 60)          # 30–89
    power_consumption = 5 + (i % 30)  # 5–34

    # Healthy by default
    failure = 0

    # Failure only when two or more conditions are severe
    score = 0

    if temperature > 45:
        score += 1

    if humidity > 75:
        score += 1

    if power_consumption > 25:
        score += 1

    if score >= 2:
        failure = 1

    data.append([
        temperature,
        humidity,
        power_consumption,
        failure
    ])

dataset = pd.DataFrame(
    data,
    columns=[
    "temperature",
    "humidity",
    "power_consumption",
    "failure"
]
)

X = dataset[[
    "temperature",
    "humidity",
    "power_consumption"
]]

y = dataset["failure"]

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

print(dataset["failure"].value_counts())
print(model.score(X, y))

joblib.dump(model, "backend/ml/model.pkl")

print("Model trained successfully.")