# ⚡ EV Charging Station Health Monitoring System


<p align="center">

  <strong>AI-Powered Predictive Maintenance and Health Monitoring for EV Charging Stations</strong>

</p>


<p align="center">

  A web-based system for monitoring electric vehicle charging stations, analyzing telemetry data, predicting potential failures, managing maintenance activities, and visualizing station health through an interactive dashboard.

</p>


---


## 📌 Table of Contents


- [About the Project](#-about-the-project)

- [Problem Statement](#-problem-statement)

- [Project Objectives](#-project-objectives)

- [Key Features](#-key-features)

- [System Architecture](#-system-architecture)

- [Technology Stack](#-technology-stack)

- [Project Structure](#-project-structure)

- [Application Modules](#-application-modules)

- [Machine Learning](#-machine-learning)

- [Prediction Logic](#-prediction-logic)

- [Database](#-database)

- [Backend API](#-backend-api)

- [Frontend Dashboard](#-frontend-dashboard)

- [Installation](#-installation)

- [Running the Backend](#-running-the-backend)

- [Running the Frontend](#-running-the-frontend)

- [Training the ML Model](#-training-the-ml-model)

- [API Documentation](#-api-documentation)

- [Sample API Workflow](#-sample-api-workflow)

- [Seed Data](#-seed-data)

- [Configuration](#-configuration)

- [Project Workflow](#-project-workflow)

- [Security](#-security)

- [Troubleshooting](#-troubleshooting)

- [Future Enhancements](#-future-enhancements)

- [Project Status](#-project-status)

- [Contributors](#-contributors)

- [License](#-license)


---


# 📖 About the Project


The **EV Charging Station Health Monitoring System** is a web-based application developed to monitor and analyze the operational health of Electric Vehicle (EV) charging stations.


The system combines:


- Charging station information

- Telemetry data

- Charging-session information

- Maintenance records

- Failure history

- Alerts

- Operator information

- Machine learning

- Prediction history

- User feedback

- Interactive analytics


The primary purpose of the system is to provide a centralized platform where charging-station health can be monitored and potential failures can be identified using machine-learning-based prediction.


The project consists of a **FastAPI backend**, a **Flask frontend dashboard**, and a **SQLite database**.


---


# 🎯 Problem Statement


EV charging stations are critical infrastructure for electric vehicles. Continuous operation of these stations requires monitoring of parameters such as temperature, humidity, and power consumption.


Abnormal operating conditions may indicate a potential failure.


Traditional maintenance approaches can depend heavily on manual monitoring and scheduled maintenance. A predictive maintenance approach can instead use operational data to identify potentially unhealthy conditions.


This project provides a software platform for:


- Monitoring charging stations

- Collecting telemetry information

- Tracking charging activity

- Managing maintenance records

- Recording failures

- Generating alerts

- Predicting potential failures

- Visualizing station health


---


# 🎯 Project Objectives


The major objectives of the system are:


1. Monitor EV charging stations.

2. Store charging-station information.

3. Record telemetry data.

4. Monitor charging sessions.

5. Maintain maintenance records.

6. Maintain historical failure information.

7. Generate and manage alerts.

8. Manage charging-station operators.

9. Predict potential charging-station failures.

10. Store prediction results.

11. Collect feedback on predictions.

12. Provide an interactive monitoring dashboard.

13. Provide analytics related to station health and performance.

14. Support predictive maintenance workflows.


---


# 🚀 Key Features


## ⚡ Charging Station Monitoring


- Charging station management

- Station information

- Charger type and location

- Station health information

- Station-related telemetry


## 📡 Telemetry Monitoring


Telemetry records include:


- Temperature

- Humidity

- Power consumption

- Charging station ID


## 🔮 Failure Prediction


Prediction inputs:


- Temperature

- Humidity

- Power Consumption


Possible results:


- `Failure Expected`

- `Charging Station Healthy`


## 🔧 Maintenance Management


- Maintenance records

- Maintenance dates

- Maintenance status

- Maintenance history


## 🚨 Alert Management


Supported alert categories include:


- High Temperature

- High Humidity

- High Power Consumption

- Voltage Issue

- Sensor Failure


## 📜 Failure History


Failure records contain:


- Charging station

- Failure type

- Description

- Failure date

- Resolution status


## 🔌 Charging Sessions


Charging-session records include:


- Charging station

- Vehicle ID

- Start time

- End time

- Energy consumed

- Cost


## 👷 Operator Management


Operator information includes:


- Name

- Email

- Phone

- Shift


## 💬 Feedback Management


Feedback includes:


- User name

- Comments

- Rating


## 📊 Analytics


The dashboard provides analytics for:


- Charging stations

- Telemetry

- Maintenance

- Predictions

- Failures

- Alerts

- Charging sessions


## 🔋 Battery Health


The frontend includes battery-health monitoring based on charging-station telemetry values.


---


# 🏗️ System Architecture


```text

                    ┌─────────────────────────┐

                    │       User / Operator   │

                    └────────────┬────────────┘

                                 │

                                 ▼

                    ┌─────────────────────────┐

                    │    Flask Web Dashboard  │

                    │        Frontend         │

                    └────────────┬────────────┘

                                 │

                                 ▼

                    ┌─────────────────────────┐

                    │      FastAPI Backend    │

                    │       REST APIs         │

                    └────────────┬────────────┘

                                 │

             ┌───────────────────┼───────────────────┐

             │                   │                   │

             ▼                   ▼                   ▼

     ┌───────────────┐   ┌───────────────┐   ┌───────────────┐

     │    SQLite     │   │ Machine       │   │   Business    │

     │    Database   │   │ Learning      │   │    Logic      │

     └───────────────┘   └───────────────┘   └───────────────┘

                              │

                              ▼

                     ┌─────────────────┐

                     │ Failure         │

                     │ Prediction      │

                     └─────────────────┘

```


---


# 🛠️ Technology Stack


| Category | Technology |

|---|---|

| Programming Language | Python |

| Frontend Framework | Flask |

| Backend Framework | FastAPI |

| Database | SQLite |

| ORM | SQLAlchemy |

| Machine Learning | Scikit-learn |

| Data Processing | Pandas |

| Model Serialization | Joblib |

| Authentication | bcrypt |

| API Server | Uvicorn |

| Web Technologies | HTML, CSS, JavaScript |


---


# 📂 Project Structure


```text

EV-Charging-Station-Health-Monitoring/

│

├── README.md

│

└── Predictive-Maintenance-Process-Intelligence/

    │

    └── ev-health-monitoring-system/

        │

        ├── backend/

        │   ├── __init__.py

        │   ├── database/

        │   │   ├── __init__.py

        │   │   └── connection.py

        │   ├── ml/

        │   │   ├── model.pkl

        │   │   ├── predict.py

        │   │   └── train_model.py

        │   ├── models/

        │   │   ├── __init__.py

        │   │   ├── alert.py

        │   │   ├── charging_session.py

        │   │   ├── failure_history.py

        │   │   ├── feedback.py

        │   │   ├── machine.py

        │   │   ├── maintenance.py

        │   │   ├── operator.py

        │   │   ├── prediction.py

        │   │   ├── telemetry.py

        │   │   └── user.py

        │   ├── schemas/

        │   │   ├── __init__.py

        │   │   ├── alert.py

        │   │   ├── charging_session.py

        │   │   ├── failure_history.py

        │   │   ├── feedback.py

        │   │   ├── maintenance.py

        │   │   ├── machine.py

        │   │   ├── operator.py

        │   │   ├── predict.py

        │   │   ├── prediction.py

        │   │   ├── telemetry.py

        │   │   └── user.py

        │   └── main.py

        │

        ├── frontend/

        │   └── app.py

        │

        ├── predictive_maintenance_process.db

        ├── seed_data.py

        ├── requirements.txt

        ├── README.md

        └── .gitignore

```


---


# 🧩 Application Modules


## 1. User Management


- User registration

- User login

- User records

- Password hashing


## 2. Charging Station Management


- Add charging stations

- Retrieve charging stations

- Charger type

- Location

- Station information


## 3. Telemetry Management


- Temperature

- Humidity

- Power consumption

- Historical telemetry


## 4. Maintenance Management


- Create maintenance records

- Retrieve maintenance records

- Track maintenance status


## 5. Prediction Management


- Real-time failure prediction

- Prediction history

- Prediction storage

- Prediction retrieval


## 6. Feedback Management


- Prediction feedback

- User comments

- Ratings


## 7. Failure History


- Failure type

- Description

- Date

- Resolution status


## 8. Alert Management


- Alert type

- Description

- Resolution status

- Charging-station association


## 9. Charging Sessions


- Vehicle ID

- Start time

- End time

- Energy consumed

- Cost


## 10. Operator Management


- Operator name

- Email

- Phone

- Shift

- Operator updates


---


# 🤖 Machine Learning


The machine-learning components are located in:


```text

backend/ml/

```


Files:


```text

backend/ml/

├── model.pkl

├── predict.py

└── train_model.py

```


The project uses a:


```text

RandomForestClassifier

```


with:


```text

n_estimators = 100

random_state = 42

```


Input features:


```text

temperature

humidity

power_consumption

```


---


# 🧠 Prediction Logic


The training logic identifies severe operating conditions using:


```text

Temperature > 45

Humidity > 75

Power Consumption > 25

```


A failure condition is generated when **two or more** of these severe conditions are present.


```text

                    Telemetry

                       │

        ┌──────────────┼──────────────┐

        ▼              ▼              ▼

   Temperature     Humidity      Power Consumption

        │              │              │

        ▼              ▼              ▼

     > 45?           > 75?           > 25?

        │              │              │

        └──────────────┼──────────────┘

                       │

                       ▼

              Two or more severe

                 conditions?

                  /       \

                YES       NO

                 │         │

                 ▼         ▼

             FAILURE    HEALTHY

```


Possible results:


```text

Failure Expected

```


or:


```text

Charging Station Healthy

```


---


# 🧪 Model Training


The model-training script is:


```text

backend/ml/train_model.py

```


The training workflow generates synthetic telemetry data containing:


```text

temperature

humidity

power_consumption

failure

```


The trained model is saved as:


```text

backend/ml/model.pkl

```


---


# 🗄️ Database


The project uses:


```text

SQLite

```


Database file:


```text

predictive_maintenance_process.db

```


The database supports:


- Users

- Charging stations

- Telemetry

- Maintenance

- Predictions

- Feedback

- Operators

- Failure history

- Alerts

- Charging sessions


---


# 🔌 Backend API


The FastAPI backend is located at:


```text

backend/main.py

```


The API provides functionality for:


- Users

- Charging stations

- Telemetry

- Maintenance

- Operators

- Predictions

- Feedback

- Alerts

- Charging sessions

- Failure history


---


# 📡 API Endpoints


## Health / Root


```http

GET /

```


## Users


```http

POST /login

POST /register

POST /users

GET  /users/all

GET  /users

```


## Charging Stations


```http

POST /charging-stations

GET  /charging-stations/all

GET  /charging-stations

```


## Telemetry


```http

POST /telemetry

GET  /telemetry/all

GET  /telemetry

```


## Maintenance


```http

POST /maintenance

GET  /maintenance/all

```


## Predictions


```http

POST /predict

POST /prediction

GET  /prediction/all

```


## Operators


```http

POST /operators

GET  /operators/all

GET  /operators

PUT  /operators/{operator_id}

```


## Feedback


```http

POST /feedback

GET  /feedback/all

```


## Failure History


```http

POST /failure-history

GET  /failure-history/all

GET  /failure-history

```


## Alerts


```http

POST /alerts

GET  /alerts/all

GET  /alerts

```


## Charging Sessions


```http

POST /charging-session

GET  /charging-session/all

GET  /charging-session

```


---


# 🖥️ Frontend Dashboard


The frontend is implemented using Flask.


Main file:


```text

frontend/app.py

```


Available dashboard sections include:


- Login

- Registration

- Dashboard

- Stations

- Station Details

- Telemetry

- Maintenance

- Predictions

- Failure History

- Alerts

- Charging Sessions

- Operators

- Feedback

- Analytics

- Battery Health

- Logout


---


# ⚙️ Installation


## Step 1 — Clone the Repository


```bash

git clone https://github.com/prasamhita0207/EV-Charging-Station-Health-Monitoring.git

cd EV-Charging-Station-Health-Monitoring

cd Predictive-Maintenance-Process-Intelligence/ev-health-monitoring-system

```


## Step 2 — Create Virtual Environment


### Windows


```powershell

python -m venv venv

venv\Scripts\activate

```


### macOS / Linux


```bash

python3 -m venv venv

source venv/bin/activate

```


## Step 3 — Install Dependencies


```bash

pip install -r requirements.txt

```


If required backend packages are missing:


```bash

pip install fastapi uvicorn sqlalchemy bcrypt

```


---


# ▶️ Running the Frontend


From:


```text

Predictive-Maintenance-Process-Intelligence/ev-health-monitoring-system

```


run:


```bash

python frontend/app.py

```


Open:


```text

http://127.0.0.1:5000

```


---


# 🚀 Running the Backend


Run:


```bash

uvicorn backend.main:app --reload

```


Open:


```text

http://127.0.0.1:8000

```


---


# 📚 API Documentation


FastAPI Swagger:


```text

http://127.0.0.1:8000/docs

```


FastAPI ReDoc:


```text

http://127.0.0.1:8000/redoc

```


---


# 🧪 Sample Prediction Request


Endpoint:


```http

POST /predict

```


Request:


```json

{

  "temperature": 40,

  "humidity": 60,

  "power_consumption": 20

}

```


Example response:


```json

{

  "prediction": "Charging Station Healthy"

}

```


Potential failure response:


```json

{

  "prediction": "Failure Expected"

}

```


---


# 📡 Sample Telemetry Request


```http

POST /telemetry

```


Example:


```json

{

  "charging_station_id": 1,

  "temperature": 38.5,

  "humidity": 55,

  "power_consumption": 24.5

}

```


---


# ⚡ Sample Charging Station Request


```http

POST /charging-stations

```


Example:


```json

{

  "station_name": "Charging Station 51",

  "charger_type": "DC Fast Charger",

  "location": "Hyderabad"

}

```


---


# 🔧 Sample Maintenance Request


```http

POST /maintenance

```


Example:


```json

{

  "charging_station_id": 1,

  "maintenance_date": "2026-08-15",

  "status": "Scheduled"

}

```


---


# 💬 Sample Feedback Request


```http

POST /feedback

```


Example:


```json

{

  "user_name": "User 1",

  "comments": "Excellent Service",

  "rating": 5

}

```


---


# 🚨 Sample Alert Request


```http

POST /alerts

```


Example:


```json

{

  "charging_station_id": 1,

  "alert_type": "High Temperature",

  "description": "Temperature exceeded safe limit.",

  "is_resolved": false

}

```


---


# 🔌 Sample Charging Session


```http

POST /charging-session

```


Example:


```json

{

  "station_id": 1,

  "vehicle_id": "TN25EV1001",

  "start_time": "2026-08-01T08:00:00",

  "end_time": "2026-08-01T09:00:00",

  "energy_consumed": 35.5,

  "cost": 450

}

```


---


# 🌱 Seed Data


The project includes:


```text

seed_data.py

```


The seed script is used to prepare sample project data for development and demonstration.


Run:


```bash

python seed_data.py

```


Sample data categories include:


- Charging stations

- Telemetry

- Maintenance

- Predictions

- Feedback

- Operators

- Charging sessions

- Failure history

- Alerts

- Users


---


# 🔐 Authentication


The application provides:


```text

/register

/login

```


New user passwords are hashed using bcrypt before storage.


The Flask frontend uses session-based authentication.


---


# 🔄 Complete System Workflow


```text

EV Charging Station

        ↓

Telemetry Collection

        ↓

Temperature / Humidity / Power Consumption

        ↓

FastAPI Backend

        ↓

SQLite Database

        ↓

Machine Learning Model

        ↓

Failure Prediction

        ↓

Healthy / Failure Expected

        ↓

Alerts & Maintenance

        ↓

Flask Dashboard

        ↓

Analytics & Feedback

```


---


# 🧠 Predictive Maintenance Workflow


```text

1. Collect telemetry

        ↓

2. Store telemetry

        ↓

3. Analyze operating parameters

        ↓

4. Send parameters to ML model

        ↓

5. Generate health prediction

        ↓

6. Store prediction

        ↓

7. Display prediction

        ↓

8. Monitor failures and alerts

        ↓

9. Perform maintenance

        ↓

10. Collect feedback

```


---


# 🛠️ Troubleshooting


## FastAPI Error


If:


```text

ModuleNotFoundError: No module named 'fastapi'

```


run:


```bash

pip install fastapi

```


## Flask Error


```bash

pip install Flask

```


## Scikit-learn Error


```bash

pip install scikit-learn

```


## Pandas Error


```bash

pip install pandas

```


## Joblib Error


```bash

pip install joblib

```


## SQLAlchemy Error


```bash

pip install sqlalchemy

```


## Uvicorn Error


```bash

pip install uvicorn

```


## Model Not Found


If:


```text

backend/ml/model.pkl

```


is missing, train the model:


```bash

python backend/ml/train_model.py

```


---


# 🔮 Future Enhancements


Possible future improvements include:


- Real-time IoT sensor integration

- Automated failure notifications

- Cloud deployment

- Advanced predictive-maintenance algorithms

- Real-time charging-station monitoring

- Advanced historical performance visualization

- Automated maintenance scheduling

- Map-based station visualization

- Real-time charging-session integration


---


# 📌 Project Status


The project includes:


- ✅ Flask frontend

- ✅ FastAPI backend

- ✅ SQLite database

- ✅ SQLAlchemy models

- ✅ User registration

- ✅ User login

- ✅ Charging station management

- ✅ Telemetry management

- ✅ Maintenance management

- ✅ Machine-learning failure prediction

- ✅ Prediction storage

- ✅ Prediction feedback

- ✅ Failure history

- ✅ Alert management

- ✅ Charging-session management

- ✅ Operator management

- ✅ Analytics dashboard

- ✅ Battery health monitoring

- ✅ Seed-data functionality

- ✅ Trained ML model


---


# 📦 Main Project Files


| File | Purpose |

|---|---|

| `backend/main.py` | FastAPI application and REST APIs |

| `backend/database/connection.py` | Database connection |

| `backend/ml/model.pkl` | Trained ML model |

| `backend/ml/train_model.py` | ML training script |

| `backend/ml/predict.py` | Prediction logic |

| `frontend/app.py` | Flask dashboard |

| `seed_data.py` | Sample data generation |

| `predictive_maintenance_process.db` | SQLite database |

| `requirements.txt` | Python dependencies |

| `.gitignore` | Git ignore rules |

| `README.md` | Project documentation |


---


# 🔗 Important URLs


Frontend:


```text

http://127.0.0.1:5000

```


Backend:


```text

http://127.0.0.1:8000

```


Swagger:


```text

http://127.0.0.1:8000/docs

```


ReDoc:


```text

http://127.0.0.1:8000/redoc

```


---


# 👥 Contributors


This is a team project developed as part of the **Infosys Springboard internship/project work**.


### Project Team


- Team Leader

- Backend Development Team

- Frontend Development Team

- Machine Learning Team

- Database & Integration Team


> Add the actual team member names and individual responsibilities before final submission.


---


# 🎓 Academic / Internship Project


This project demonstrates the integration of:


- Web development

- REST API development

- Database management

- Machine learning

- Predictive maintenance

- Data visualization

- EV charging infrastructure monitoring


---


# 📄 License


This project is developed for academic and internship purposes.


If your team has been assigned a specific open-source license, replace this section with the corresponding license information.


---


**# ⭐ GitHub Repository**

https://github.com/prasamhita0207/EV-Charging-Station-Health-Monitoring

---

**## ⚡ EV Charging Station Health Monitoring System**

**Monitor → Analyze → Predict → Maintain**

---

**# AUTHOR**

**## KADALI PRASAMHITA**
