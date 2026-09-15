EV Charging Station Health Monitoring & Predictive Maintenance
Overview

EV Charging Station Health Monitoring & Predictive Maintenance is a web-based system for monitoring the operational health of electric vehicle (EV) charging stations and supporting predictive maintenance decisions.

The application combines:

Charging-station information
Real-time-style telemetry records
Battery/charging health assessment
Machine-learning-based failure prediction
Maintenance records
Failure history
Operational alerts
Charging-session analytics
Operator management
User feedback
Dashboard-based analytics

The goal is to move from reactive maintenance to condition-based and predictive maintenance by identifying abnormal operating conditions before they result in charging-station failures.

Key Features
1. Dashboard

The main dashboard provides an operational overview of the charging network, including:

Number of charging stations
Telemetry activity
Maintenance information
Alerts
Prediction results
Charging activity
Battery/health indicators
Recent operational information

The dashboard uses a dark monitoring-style interface with health indicators and visual analytics.

2. Charging Station Management

Charging stations can be stored with:

Station name
Charger type
Location

Supported example charger types include:

AC Level 2
DC Fast Charger
CCS
CHAdeMO
Type 2
3. Telemetry Monitoring

The system stores telemetry associated with charging stations:

Temperature
Humidity
Power consumption
Charging-station ID

These measurements form the primary inputs for health assessment and predictive-maintenance analysis.

4. Predictive Maintenance

A Random Forest classification model is included to predict whether a charging station is likely to experience a failure.

The model uses:

Temperature
Humidity
Power Consumption

and produces one of two outcomes:

Charging Station Healthy
Failure Expected

The trained model is stored as:

backend/ml/model.pkl
5. Rule-Based Battery Health Score

In addition to the ML prediction, the dashboard calculates a simplified health score based on temperature and power consumption.

The score is bounded between 20 and 100 and is presented using:

80–100% → Healthy
60–79% → Moderate
Below 60% → Critical

This score is intended as an operational indicator rather than a physical battery-state-of-health measurement.

6. Alerts

The system supports alerts associated with charging stations, including examples such as:

High temperature
High humidity
High power consumption
Voltage issues
Sensor failure

Alerts can be marked as resolved or unresolved.

7. Maintenance Management

Maintenance records contain:

Charging-station ID
Maintenance date
Status

Example statuses:

Completed
Pending
Scheduled
8. Failure History

Historical failures can be recorded with:

Failure type
Description
Failure date
Resolution status
Charging-station ID

This historical information can be used to understand recurring operational problems.

9. Charging Sessions

Charging-session records contain:

Station ID
Vehicle ID
Start time
End time
Energy consumed
Cost

This enables operational and usage-level analysis of the charging network.

10. Operator Management

Operators can be created and updated with:

Name
Email
Phone
Shift

The system includes support for morning, evening, and night shift information.

11. User Authentication

The Flask application includes:

User registration
Login
Logout
Session-based authentication

Passwords created through the registration flow are hashed using bcrypt.

12. Feedback

Users can submit feedback containing:

User name
Comments
Rating
System Architecture

The repository currently contains two related application layers:

                    ┌──────────────────────────────┐
                    │        Web Dashboard         │
                    │          Flask app           │
                    │                              │
                    │ Login / Dashboard / Charts   │
                    │ Stations / Alerts / Reports  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       SQLite Database        │
                    │ predictive_maintenance_      │
                    │ process.db                   │
                    └──────────────┬───────────────┘
                                   ▲
                                   │
                    ┌──────────────┴───────────────┐
                    │       FastAPI Backend        │
                    │                              │
                    │ CRUD APIs + ML prediction    │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      Machine Learning        │
                    │       Random Forest          │
                    │                              │
                    │ Temperature                  │
                    │ Humidity                     │
                    │ Power Consumption            │
                    └──────────────────────────────┘
Main Components
Component	Technology
Web dashboard	Flask
REST API	FastAPI
API server	Uvicorn
ORM	SQLAlchemy
Database	SQLite
ML model	Scikit-learn Random Forest
ML serialization	Joblib
Data processing	Pandas
Front-end	HTML / CSS / JavaScript embedded in Flask templates
Authentication	Flask sessions + bcrypt
Project Structure
Predictive-Maintenance-Process-Intelligence/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── .gitignore
│
├── predictive_maintenance_process.db
│
├── database/
│   └── init.sql
│
└── ev-health-monitoring-system/
    │
    ├── README.md
    ├── requirements.txt
    ├── seed_data.py
    ├── predictive_maintenance_process.db
    │
    └── backend/
        │
        ├── main.py
        │
        ├── database/
        │   └── connection.py
        │
        ├── models/
        │   ├── user.py
        │   ├── machine.py
        │   ├── telemetry.py
        │   ├── maintenance.py
        │   ├── prediction.py
        │   ├── failure_history.py
        │   ├── alert.py
        │   ├── charging_session.py
        │   ├── operator.py
        │   └── feedback.py
        │
        ├── schemas/
        │   ├── user.py
        │   ├── machine.py
        │   ├── telemetry.py
        │   ├── maintenance.py
        │   ├── predict.py
        │   ├── prediction.py
        │   ├── failure_history.py
        │   ├── alert.py
        │   ├── charging_session.py
        │   └── operator.py
        │
        └── ml/
            ├── train_model.py
            ├── predict.py
            └── model.pkl

__pycache__, .git, macOS metadata files, and other generated files are omitted from the logical project structure above.

Machine Learning Workflow

The predictive-maintenance component uses a Random Forest Classifier.

Input Features
X = [
    temperature,
    humidity,
    power_consumption
]
Target
failure

where:

0 = Healthy
1 = Failure Expected
Training Logic

The included training script generates a synthetic dataset of 1,000 records.

A record is considered a failure condition when at least two of the following conditions are severe:

Temperature > 45
Humidity > 75
Power consumption > 25

The Random Forest model is then trained using:

RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

The resulting model is saved to:

backend/ml/model.pkl
Prediction Flow
Telemetry
    │
    ├── Temperature
    ├── Humidity
    └── Power Consumption
             │
             ▼
       Random Forest
             │
             ▼
    ┌───────────────────┐
    │ Prediction Result │
    └───────────────────┘
       │             │
       ▼             ▼
    Healthy    Failure Expected
Database

The project uses SQLite for local development.

The main database file is:

predictive_maintenance_process.db

The database contains tables for the main operational entities, including:

users
charging_stations
telemetry
maintenance
predictions
failure_history
alerts
charging_sessions
operators
feedback

SQLAlchemy models are located under:

ev-health-monitoring-system/backend/models/
Installation
Prerequisites

Install:

Python 3.10+
pip
Git (optional)
1. Clone the repository
git clone <repository-url>
cd Predictive-Maintenance-Process-Intelligence
2. Create a virtual environment

Windows:

python -m venv venv
venv\Scripts\activate

macOS/Linux:

python3 -m venv venv
source venv/bin/activate
3. Install dependencies

For the Flask dashboard and ML functionality, install the required packages:

pip install flask pandas scikit-learn joblib bcrypt

For the FastAPI backend:

pip install -r ev-health-monitoring-system/requirements.txt

The repository's dependency files cover the FastAPI/SQLAlchemy portion; the Flask dashboard also requires the Flask/ML packages shown above.

Running the Web Dashboard

The main user-facing application is:

app.py

From the project root:

python app.py

The application runs on:

http://localhost:5000

Open the address in a browser.

Running the FastAPI Backend

Move into the backend project:

cd ev-health-monitoring-system

Start the API using Uvicorn:

uvicorn backend.main:app --reload

The API will normally be available at:

http://127.0.0.1:8000

FastAPI automatically provides interactive API documentation at:

http://127.0.0.1:8000/docs
Training the ML Model

From:

ev-health-monitoring-system/

run:

python backend/ml/train_model.py

The script:

Generates the training dataset.
Creates the failure labels.
Trains the Random Forest classifier.
Prints the class distribution and training score.
Saves the trained model as:
backend/ml/model.pkl
Generating Sample Data

The project includes a seed script for populating the database with demonstration data.

From:

ev-health-monitoring-system/

run:

python seed_data.py

The script creates sample records including approximately:

50 charging stations
500 telemetry records
100 maintenance records
20 prediction records
10 feedback records
5 operators
200 charging sessions
Failure-history records
50 alerts
Sample users

This is useful for demonstrating the dashboard without manually entering records.

API Endpoints

The FastAPI backend exposes endpoints for the major entities.

Authentication / Users
POST   /login
POST   /register
POST   /users
GET    /users
GET    /users/all
Charging Stations
POST   /charging-stations
GET    /charging-stations
GET    /charging-stations/all
Telemetry
POST   /telemetry
GET    /telemetry
GET    /telemetry/all
Maintenance
POST   /maintenance
GET    /maintenance/all
Predictions
POST   /predict
POST   /prediction
GET    /prediction/all
Operators
POST   /operators
GET    /operators
GET    /operators/all
PUT    /operators/{operator_id}
Feedback
POST   /feedback
GET    /feedback/all
Failure History
POST   /failure-history
GET    /failure-history
GET    /failure-history/all
Alerts
POST   /alerts
GET    /alerts
GET    /alerts/all
Charging Sessions
POST   /charging-session
GET    /charging-session
GET    /charging-session/all
Prediction API Example

Send telemetry values to:

POST /predict

Example request:

{
  "temperature": 50,
  "humidity": 80,
  "power_consumption": 30
}

Example response:

{
  "prediction": "Failure Expected"
}

A normal operating condition may return:

{
  "prediction": "Charging Station Healthy"
}
Dashboard Pages

The Flask application includes routes for:

/                   → Login
/register           → Registration
/dashboard          → Main monitoring dashboard
/stations           → Charging stations
/alerts             → Alerts
/telemetry          → Telemetry
/maintenance        → Maintenance
/predictions        → ML predictions
/failure-history    → Failure history
/charging-sessions  → Charging sessions
/operators          → Operator management
/feedback           → User feedback
/analytics          → Analytics
/battery-health     → Battery health
/logout              → Logout
Example Workflow

A typical monitoring workflow is:

1. Register / Login
        │
        ▼
2. View Charging Network
        │
        ▼
3. Collect / Enter Telemetry
        │
        ├── Temperature
        ├── Humidity
        └── Power Consumption
        │
        ▼
4. Calculate Health Indicators
        │
        ▼
5. Run ML Failure Prediction
        │
        ├── Healthy
        └── Failure Expected
        │
        ▼
6. Generate / Review Alerts
        │
        ▼
7. Schedule Maintenance
        │
        ▼
8. Record Failure / Maintenance History
        │
        ▼
9. Analyze Charging Operations
Sample Login Data

The seed script includes demonstration users.

Admin
Email: admin@ev-health.com
Password: admin123
Operator
Email: operator@ev-health.com
Password: stationPass2026!

Important: These credentials are for demonstration/development data only. They should be changed or removed before deploying the application to a real environment.

Security Notes

This project is intended primarily for academic/prototype use.

Before production deployment, the following should be improved:

Store the Flask secret key in an environment variable.
Never commit real credentials to source control.
Use environment variables for database configuration.
Use HTTPS.
Restrict CORS origins instead of allowing all origins.
Add proper authorization/role-based access control.
Validate and sanitize all API inputs.
Use secure password handling consistently across all user-creation paths.
Disable Flask debug mode in production.
Add authentication/authorization to protected FastAPI endpoints.
Use a production database for large deployments.
Limitations

The current ML implementation is a prototype predictive-maintenance model trained on synthetically generated data. Its predictions should not be interpreted as validated real-world failure probabilities.

The current system would need real historical charging-station telemetry and verified failure labels to become suitable for operational predictive maintenance.

Other areas that can be improved include:

Real-time IoT telemetry ingestion
Time-series feature engineering
More charging-station sensor variables
Model validation using unseen test data
Precision/recall/F1 evaluation
Model versioning
Probability-based risk scores
Automated alert generation from predictions
Maintenance recommendation logic
Role-based access control
Production database deployment
Monitoring of model performance over time
Future Enhancements

Possible extensions include:

IoT Integration

Connect actual charging stations and IoT sensors to stream:

Temperature
Voltage
Current
Power
Humidity
Connector status
Error codes
Advanced Predictive Maintenance

Introduce:

XGBoost / LightGBM
LSTM time-series models
Anomaly detection
Remaining Useful Life (RUL) estimation
Failure probability scoring
Intelligent Maintenance Scheduling

Automatically prioritize stations based on:

Risk Score
+
Failure History
+
Current Telemetry
+
Station Usage
+
Maintenance History
Real-Time Monitoring

Add:

WebSockets
Live telemetry updates
Real-time alerts
Notification services
Production Deployment

Deploy the system using:

Docker
PostgreSQL
Nginx
Cloud infrastructure
CI/CD
Technology Stack
Backend
├── Flask
├── FastAPI
├── Uvicorn
└── SQLAlchemy

Database
└── SQLite

Machine Learning
├── Scikit-learn
├── Random Forest
├── Pandas
└── Joblib

Frontend
├── HTML
├── CSS
└── JavaScript

Development
├── Python
└── Git
Project Objective

The primary objective of this project is to demonstrate how machine learning, telemetry monitoring, operational data, and predictive maintenance concepts can be combined into a single EV charging-station health monitoring platform.

Instead of waiting for a charging station to fail, the system uses available operational indicators to identify potentially abnormal conditions and provide an early warning for maintenance teams.

MIT License

This project is intended for educational, academic, and prototype purposes.
