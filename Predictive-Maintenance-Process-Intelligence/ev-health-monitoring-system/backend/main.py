import bcrypt
from backend.models import machine

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.database.connection import engine, Base, get_db
from backend.models.user import User
from backend.schemas.user import UserCreate, UserLogin, UserResponse
from backend.models.machine import Machine
from backend.schemas.machine import MachineCreate
from backend.models.telemetry import Telemetry
from backend.schemas.telemetry import TelemetryCreate
from backend.models.maintenance import Maintenance
from backend.schemas.maintenance import MaintenanceCreate
from backend.ml.predict import predict_failure
from backend.schemas.predict import PredictionInput

from backend.models.operator import Operator
from backend.schemas.operator import OperatorCreate

from backend.models.prediction import Prediction
from backend.schemas.prediction import PredictionCreate

from backend.models.feedback import Feedback
from backend.schemas.feedback import FeedbackCreate

from backend.models.failure_history import FailureHistory
from backend.schemas.failure_history import FailureHistoryCreate

from backend.models.alert import Alert
from backend.schemas.alert import AlertCreate, AlertResponse

from backend.models.charging_session import ChargingSession
from backend.schemas.charging_session import (
    ChargingSessionCreate,
    ChargingSessionResponse,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EV Charging Station Health Monitoring API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_password(plain_password: str, stored_password: str) -> bool:
    if stored_password.startswith(("$2b$", "$2a$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), stored_password.encode("utf-8"))
        except Exception:
            return False
    return stored_password == plain_password


@app.get("/")
def home():
    return {"message": "EV Charging Station Health Monitoring Backend Running"}


@app.post("/login")
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.email == credentials.email, User.name == credentials.email)
    ).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password"
        )

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    clean_email = user.email.strip().lower()
    clean_name = user.name.strip()

    existing_user = db.query(User).filter(User.email.ilike(clean_email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )

    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    new_user = User(
        name=clean_name,
        email=clean_email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    new_user = User(name=user.name, email=user.email, password=user.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User added successfully", "id": new_user.id}


@app.get("/users/all")
def get_all_users(db: Session = Depends(get_db)):

    users = db.query(User).all()

    return users


@app.get("/users")
def get_users():
    return {"message": "User API is working"}


@app.post("/charging-stations")
def create_charging_station(machine_data: MachineCreate, db: Session = Depends(get_db)):

    charging_station = Machine(
        station_name=machine_data.station_name,
        charger_type=machine_data.charger_type,
        location=machine_data.location,
    )

    db.add(charging_station)
    db.commit()
    db.refresh(charging_station)

    return {"message": "Charging station added successfully", "id": charging_station.id}


@app.get("/charging-stations/all")
def get_all_charging_stations(db: Session = Depends(get_db)):

    charging_stations = db.query(Machine).all()

    return charging_stations


@app.get("/charging-stations")
def get_charging_stations():
    return {"message": "Charging station API is working"}


@app.post("/telemetry")
def create_telemetry(telemetry_data: TelemetryCreate, db: Session = Depends(get_db)):

    telemetry = Telemetry(
        charging_station_id=telemetry_data.charging_station_id,
        temperature=telemetry_data.temperature,
        humidity=telemetry_data.humidity,
        power_consumption=telemetry_data.power_consumption,
    )

    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)

    return {"message": "Telemetry added successfully", "id": telemetry.id}


@app.get("/telemetry/all")
def get_all_telemetry(db: Session = Depends(get_db)):

    telemetry = db.query(Telemetry).all()

    return telemetry


@app.get("/telemetry")
def get_telemetry():
    return {"message": "Telemetry API is working"}


@app.post("/maintenance")
def create_maintenance(data: MaintenanceCreate, db: Session = Depends(get_db)):

    maintenance = Maintenance(
        charging_station_id=data.charging_station_id,
        maintenance_date=data.maintenance_date,
        status=data.status,
    )

    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    return {"message": "Maintenance record added successfully", "id": maintenance.id}


@app.get("/maintenance/all")
def get_all_maintenance(db: Session = Depends(get_db)):

    maintenance = db.query(Maintenance).all()

    return maintenance


@app.post("/predict")
def predict_charging_station(data: PredictionInput):

    result = predict_failure(data.temperature, data.humidity, data.power_consumption)

    return {"prediction": result}


@app.post("/operators")
def create_operator(operator: OperatorCreate, db: Session = Depends(get_db)):

    new_operator = Operator(
        name=operator.name,
        email=operator.email,
        phone=operator.phone,
        shift=operator.shift,
    )

    db.add(new_operator)
    db.commit()
    db.refresh(new_operator)

    return {"message": "Operator added successfully", "id": new_operator.id}


@app.get("/operators/all")
def get_all_operators(db: Session = Depends(get_db)):

    operators = db.query(Operator).all()

    return operators


@app.get("/operators")
def get_operators():

    return {"message": "Operator API is working"}


@app.put("/operators/{operator_id}")
def update_operator(
    operator_id: int, operator: OperatorCreate, db: Session = Depends(get_db)
):

    existing_operator = db.query(Operator).filter(Operator.id == operator_id).first()

    if not existing_operator:
        return {"message": "Operator not found"}

    existing_operator.name = operator.name
    existing_operator.email = operator.email
    existing_operator.phone = operator.phone
    existing_operator.shift = operator.shift

    db.commit()
    db.refresh(existing_operator)

    return {"message": "Operator updated successfully", "operator": existing_operator}


@app.post("/prediction")
def create_prediction(data: PredictionCreate, db: Session = Depends(get_db)):

    prediction = Prediction(
        temperature=data.temperature,
        humidity=data.humidity,
        power_consumption=data.power_consumption,
        prediction=data.prediction,
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return {"message": "Prediction saved successfully", "id": prediction.id}


@app.get("/prediction/all")
def get_predictions(db: Session = Depends(get_db)):

    return db.query(Prediction).all()


@app.post("/feedback")
def create_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):

    feedback = Feedback(
        user_name=data.user_name, comments=data.comments, rating=data.rating
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {"message": "Feedback added successfully", "id": feedback.id}


@app.get("/feedback/all")
def get_feedback(db: Session = Depends(get_db)):

    return db.query(Feedback).all()


@app.post("/failure-history")
def create_failure_history(data: FailureHistoryCreate, db: Session = Depends(get_db)):

    failure = FailureHistory(
        charging_station_id=data.charging_station_id,
        failure_type=data.failure_type,
        description=data.description,
        failure_date=data.failure_date,
        resolved=data.resolved,
    )

    db.add(failure)
    db.commit()
    db.refresh(failure)

    return {"message": "Failure History added successfully", "id": failure.id}


@app.get("/failure-history/all")
def get_all_failure_history(db: Session = Depends(get_db)):

    failures = db.query(FailureHistory).all()

    return failures


@app.get("/failure-history")
def get_failure_history():
    return {"message": "Failure History API is working"}


@app.post("/alerts", response_model=dict)
def create_alert(alert_data: AlertCreate, db: Session = Depends(get_db)):
    new_alert = Alert(
        charging_station_id=alert_data.charging_station_id,
        alert_type=alert_data.alert_type,
        description=alert_data.description,
        is_resolved=alert_data.is_resolved,
    )

    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return {"message": "Alert added successfully", "id": new_alert.id}


@app.get("/alerts/all", response_model=list[AlertResponse])
def get_all_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    return alerts


@app.get("/alerts", response_model=dict)
def get_alerts():
    return {"message": "Alert API is working"}

# -----------------------
# Charging Session APIs
# -----------------------

@app.post("/charging-session", response_model=ChargingSessionResponse)
def create_charging_session(
    session: ChargingSessionCreate,
    db: Session = Depends(get_db)
):

    new_session = ChargingSession(
        station_id=session.station_id,
        vehicle_id=session.vehicle_id,
        start_time=session.start_time,
        end_time=session.end_time,
        energy_consumed=session.energy_consumed,
        cost=session.cost
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


@app.get("/charging-session/all", response_model=list[ChargingSessionResponse])
def get_all_charging_sessions(db: Session = Depends(get_db)):

    sessions = db.query(ChargingSession).all()

    return sessions


@app.get("/charging-session")
def get_charging_session():
    return {
        "message": "Charging Session API is working"
    }
