from random import randint, uniform, choice

from backend.database.connection import SessionLocal
from backend.models.machine import Machine
from backend.models.telemetry import Telemetry
from backend.models.maintenance import Maintenance

# pyrefly: ignore [missing-import]
from backend.models.prediction import Prediction

# pyrefly: ignore [missing-import]
from backend.models.feedback import Feedback

# pyrefly: ignore [missing-import]
from backend.models.operator import Operator

from backend.models.alert import Alert

from datetime import datetime, timedelta
from backend.models.charging_session import ChargingSession

db = SessionLocal()

# -----------------------
# Create Charging Stations
# -----------------------

charger_types = ["AC Level 2", "DC Fast Charger", "CCS", "CHAdeMO", "Type 2"]

locations = ["Hyderabad", "Visakhapatnam", "Vijayawada", "Bengaluru", "Chennai"]

print("Creating charging stations...")

for i in range(1, 51):
    charging_station = Machine(
        station_name=f"Charging Station {i}",
        charger_type=choice(charger_types),
        location=choice(locations),
    )

    db.add(charging_station)

db.commit()

print("50 charging stations created.")

# -----------------------
# Create 500 Telemetry Records
# -----------------------

print("Creating telemetry data...")

for _ in range(500):

    telemetry = Telemetry(
        charging_station_id=randint(1, 50),
        temperature=round(uniform(25, 45), 2),
        humidity=round(uniform(30, 60), 2),
        power_consumption=round(uniform(10, 30), 2),
    )

    db.add(telemetry)

db.commit()

print("500 telemetry records created.")

# -----------------------
# Create 100 Maintenance Records
# -----------------------

statuses = ["Completed", "Pending", "Scheduled"]

print("Creating maintenance records...")

for i in range(100):

    maintenance = Maintenance(
        charging_station_id=randint(1, 50),
        maintenance_date=f"2026-07-{(i % 30) + 1:02d}",
        status=choice(statuses),
    )

    db.add(maintenance)

db.commit()

print("100 maintenance records created.")

db.close()

print("\nDatabase populated successfully.")

for _ in range(20):

    prediction = Prediction(
        temperature=30,
        humidity=45,
        power_consumption=12,
        prediction="Charging Station Healthy",
    )

    db.add(prediction)

for i in range(10):

    feedback = Feedback(user_name=f"User {i}", comments="Excellent Service", rating=5)

    db.add(feedback)

operators = [
    Operator(
        name="Rahul Sharma",
        email="rahul@example.com",
        phone="9876543210",
        shift="Morning",
    ),
    Operator(
        name="Priya Nair",
        email="priya@example.com",
        phone="9876543211",
        shift="Evening",
    ),
    Operator(
        name="Arjun Kumar", email="arjun@example.com", phone="9876543212", shift="Night"
    ),
    Operator(
        name="Sneha Reddy",
        email="sneha@example.com",
        phone="9876543213",
        shift="Morning",
    ),
    Operator(
        name="Kiran Patel",
        email="kiran@example.com",
        phone="9876543214",
        shift="Evening",
    ),
]

db.add_all(operators)

# Existing code
db.commit()
db.close()

print("20 predictions, 10 feedback and 5 operators added.")

# -----------------------
# Create 200 Charging Session Records
# -----------------------

print("Creating charging session records...")

base_time = datetime(2026, 8, 1, 8, 0)

for i in range(200):

    start = base_time + timedelta(minutes=i * 45)
    duration = randint(20, 90)
    end = start + timedelta(minutes=duration)

    session = ChargingSession(
        station_id=randint(1, 50),
        vehicle_id=f"TN{randint(10,99)}EV{1000+i}",
        start_time=start,
        end_time=end,
        energy_consumed=round(uniform(10, 60), 2),
        cost=round(uniform(150, 900), 2)
    )

    db.add(session)

db.commit()

print("200 charging session records created.")

from backend.database.connection import SessionLocal
from backend.models.failure_history import FailureHistory

db = SessionLocal()

records = [
    FailureHistory(
        charging_station_id=1,
        failure_type="Power Failure",
        description="Station lost power during charging.",
        failure_date="2026-07-05",
        resolved="Yes",
    ),
    FailureHistory(
        charging_station_id=2,
        failure_type="Connector Fault",
        description="Charging connector damaged.",
        failure_date="2026-07-15",
        resolved="No",
    ),
    FailureHistory(
        charging_station_id=3,
        failure_type="Communication Error",
        description="Unable to connect to server.",
        failure_date="2026-07-22",
        resolved="Yes",
    ),
    FailureHistory(
        charging_station_id=4,
        failure_type="Overheating",
        description="Charging station overheated.",
        failure_date="2026-08-01",
        resolved="No",
    ),
]

db.add_all(records)
db.commit()

print("Failure History Seeded Successfully")

# -----------------------
# Create 50 Alert Records
# -----------------------

alert_types = [
    "High Temperature",
    "High Humidity",
    "High Power Consumption",
    "Voltage Issue",
    "Sensor Failure",
]

descriptions = [
    "Temperature exceeded safe limit.",
    "Humidity level is abnormal.",
    "Power consumption is too high.",
    "Voltage fluctuation detected.",
    "Sensor is not responding.",
]

print("Creating alert records...")

for _ in range(50):

    alert = Alert(
        charging_station_id=randint(1, 50),
        alert_type=choice(alert_types),
        description=choice(descriptions),
        is_resolved=choice([True, False]),
    )

    db.add(alert)

db.commit()

print("50 alert records created.")

# -----------------------
# Create Sample Users
# -----------------------
from backend.models.user import User

print("Creating sample users...")

demo_users = [
    User(
        name="Admin Operator",
        email="admin@ev-health.com",
        password="admin123"
    ),
    User(
        name="Rahul Sharma",
        email="operator@ev-health.com",
        password="stationPass2026!"
    )
]

for user in demo_users:
    existing = db.query(User).filter(User.email == user.email).first()
    if not existing:
        db.add(user)

db.commit()
print("Sample users seeded successfully.")

db.close()

