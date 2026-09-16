# EV Charging Station Health Monitoring System

## Overview

EV Charging Station Health Monitoring System is a web-based Flask application designed to monitor the health and performance of electric vehicle charging stations.

The system uses telemetry and charging-session data along with machine learning to analyze charging station health, identify potential failures, track maintenance activity, and provide predictive insights through an interactive dashboard.

---

## Features

- User Management
- Charging Station Monitoring
- Telemetry Data Monitoring
- Charging Session Tracking
- Maintenance Management
- Failure History
- Alert Management
- Operator Management
- Feedback Management
- Machine Learning Failure Prediction
- Station Health Analytics
- Battery Health Monitoring
- Interactive Dashboard
- SQLite Database

---

## Technologies Used

- Python
- Flask
- SQLite
- Pandas
- Scikit-learn
- Joblib
- HTML
- CSS
- JavaScript

---

## Project Structure

```text
ev-health-monitoring-system/
│
├── backend/
│   ├── database/
│   ├── ml/
│   │   ├── model.pkl
│   │   ├── predict.py
│   │   └── train_model.py
│   ├── models/
│   ├── schemas/
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

Installation

1. Clone the repository
git clone <repository-url>
cd ev-health-monitoring-system
2. Install dependencies
pip install -r requirements.txt
3. Run the application
python frontend/app.py
4. Open the application

Open the following address in your browser:

http://127.0.0.1:5000

Machine Learning

The system includes a machine learning component for predicting charging station health and potential failures.

The trained model is stored in:

backend/ml/model.pkl

The ML functionality is supported by:

Scikit-learn
Pandas
Joblib
Database

The application uses SQLite for storing project data.

Database file:

predictive_maintenance_process.db

The database contains information related to:

Users
Charging Stations
Telemetry
Charging Sessions
Maintenance
Predictions
Alerts
Failure History
Operators
Feedback
Dashboard

The Flask application provides an interactive dashboard for viewing:

Charging station health
Station performance
Battery health
Predictive maintenance information
Failure history
Alerts
Analytics
Maintenance records

The dashboard also includes a day/night theme option for the interface.

Requirements

The main Python dependencies are listed in:

requirements.txt

Current dependencies:

Flask
pandas
joblib
scikit-learn
Future Enhancements
Real-time IoT sensor integration
Automated failure notifications
Cloud deployment
Advanced predictive maintenance models
Historical performance visualization
Real-time charging station monitoring
#Author

#K.PRASAMHITA
