# Industrial Carbon Emission Forecasting System
## Complete Technical Handover & IoT Integration Specification

**Project Location:** `C:\Users\SKANDASHRI S N\OneDrive\Desktop\IndustrialCarbonForecasting`  
**Target Hardware:** ESP32 (NodeMCU / WROOM-32) + PZEM-004T v3.0 (AC Energy Meter with 100A CT Coil) + Optical IR Proximity Sensor  
**Core Goal:** Ingest real-time electrical telemetry and production counts from physical ESP32 hardware into the existing Flask backend, compute Scope 2 greenhouse gas emissions, perform Random Forest AI forecasting, log data into MySQL, and visualize live metrics on the web dashboard.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Technologies and Software Stack](#2-technologies-and-software-stack)
3. [Complete Project Folder Structure](#3-complete-project-folder-structure)
4. [Frontend Architecture & Implementation](#4-frontend-architecture--implementation)
5. [Backend Architecture & API Endpoints](#5-backend-architecture--api-endpoints)
6. [Machine Learning Model & Feature Specifications](#6-machine-learning-model--feature-specifications)
7. [Current Telemetry Input Flow](#7-current-telemetry-input-flow)
8. [Database Schema & Migrations](#8-database-schema--migrations)
9. [Current IoT Firmware Implementation](#9-current-iot-firmware-implementation)
10. [Hardware Components & Roles](#10-hardware-components--roles)
11. [IoT to Software Integration Plan](#11-iot-to-software-integration-plan)
12. [Data Format Specification (ESP32 to Backend)](#12-data-format-specification-esp32-to-backend)
13. [Handling Electrical Energy Consumption (kWh)](#13-handling-electrical-energy-consumption-kwh)
14. [Handling Production Count (IR Sensor)](#14-handling-production-count-ir-sensor)
15. [Deriving Working Hours & Machine Status](#15-deriving-working-hours--machine-status)
16. [Complete Real-Time Data Flow Trace](#16-complete-real-time-data-flow-trace)
17. [Communication Protocol & Network Architecture](#17-communication-protocol--network-architecture)
18. [Exact API Design for IoT Ingestion](#18-exact-api-design-for-iot-ingestion)
19. [Database + IoT + ML Synchronization](#19-database--iot--ml-synchronization)
20. [Security & Industrial Hardening](#20-security--industrial-hardening)
21. [Deployment & Network Topology](#21-deployment--network-topology)
22. [Local Development Setup Guide](#22-local-development-setup-guide)
23. [Physical Hardware Setup & Electrical Wiring Guide](#23-physical-hardware-setup--electrical-wiring-guide)
24. [Comprehensive Testing Plan](#24-comprehensive-testing-plan)
25. [Troubleshooting Guide](#25-troubleshooting-guide)
26. [Implementation Status Checklist](#26-implementation-status-checklist)
27. [Prioritized Roadmap for Next Developer](#27-prioritized-roadmap-for-next-developer)
28. [Complete System Architecture Diagram](#28-complete-system-architecture-diagram)
29. [Quick Handover Summary](#29-quick-handover-summary)
30. [Crucial Rules, Physical Verification Items & Risk Preventions](#30-crucial-rules-physical-verification-items--risk-preventions)

---

# 1. PROJECT OVERVIEW

### Project Objective
The **Industrial Carbon Emission Forecasting System** is an automated, edge-connected industrial decision-support platform. It captures operational telemetry from manufacturing machinery in real time, quantifies electrical energy consumption and factory unit production, derives machine operational states and working shift hours, calculates Scope 2 greenhouse gas emissions ($0.82\text{ kg CO}_2/\text{kWh}$ Central Electricity Authority standard), and forecasts future carbon emissions using a trained **Random Forest Regressor** machine learning model.

### Problem Being Solved
1. **Manual / Delayed Carbon Accounting:** Traditional factories compute carbon footprints weeks or months after billing cycles from utility bills, preventing operational corrections.
2. **Extraneous Ambient Noise in Predictive Modeling:** Older prototypes attempted to infer machinery emissions from ambient environmental variables (e.g., room temperature and ambient humidity), which correlate poorly with machine motor load and introduce predictive bias. (In this codebase, temperature and humidity have been completely eliminated from the hardware, software, database, and ML pipeline).
3. **Disconnection Between Hardware and AI:** Plant energy meters often run isolated on Modbus networks without feeding predictive AI models or web-accessible operational dashboards.

### What the System Currently Does
* **Web UI & Dashboard:** Operates a Flask application on port `5000` with 5 views (`/`, `/predict`, `/history`, `/dashboard`, `/about`).
* **Dynamic Frontend Polling:** The dashboard runs an asynchronous polling loop every 4 seconds (`/api/iot/latest` and `/api/iot/history`) rendering real-time telemetry cards and Chart.js line charts.
* **Dual Prediction Modes:**
  1. *Manual Web Form Inference (`POST /predict_result`):* Allows an operator to manually input Energy (kWh), Production Output (Units), Working Hour (0–23), and Weekend Schedule (0/1).
  2. *Automated IoT Telemetry Ingestion (`POST /api/iot/telemetry`):* Ingests JSON packets containing electrical telemetry (Voltage, Current, Active Power, Cumulative Energy, Frequency, Power Factor) and IR sensor production counts.
* **Automated Operational State & Working Hours Derivation:** Derives machine status (`Running` vs `Idle`) using an active electrical power threshold ($P \ge 20.0\text{ W}$) and current threshold ($I \ge 0.15\text{ A}$), automatically accumulating operating session runtime without requiring any dedicated external timer or secondary runtime sensor.
* **Dual Carbon Quantification:** Calculates baseline Scope 2 grid emissions ($\text{kWh} \times 0.82\text{ kg CO}_2/\text{kWh}$) and executes Random Forest AI inference whenever energy is within the model's domain ($0.22 \le \text{Energy} \le 19.79\text{ kWh}$).
* **Database Logging & PDF Auditing:** Persists every manual prediction to `prediction_history`, logs all IoT telemetry to `iot_telemetry` in MySQL, and dynamically compiles formal ISO-style PDF certification audit reports via ReportLab (`/download-pdf/<id>`).

### What the Final Intended System Should Do
The physical ESP32, connected to the factory electrical panel via PZEM-004T and the assembly conveyor via an optical IR sensor, powers on, automatically associates with the plant Wi-Fi, samples electrical metrics over UART and pulses over GPIO interrupt, builds a structured JSON payload, and executes an HTTP `POST` every 5 seconds to `/api/iot/telemetry`. The software ingests this packet without human intervention, triggers ML prediction, updates the MySQL database, and live-updates the web dashboard.

---

# 2. TECHNOLOGIES AND SOFTWARE STACK

| Technology / Library | Version | Role in Project | Files Involved |
| :--- | :--- | :--- | :--- |
| **Python** | 3.13.x | Backend application, data pipelines, test suites | `app.py`, `database.py`, `src/*.py`, `scripts/*.py` |
| **C++ / Arduino** | ESP32 Core | Edge telemetry acquisition, sensor decoding, HTTP client | `firmware/esp32_industrial_telemetry.ino` |
| **Flask** | 3.1.3 | WSGI web application server & REST API framework | `app.py` |
| **MySQL Connector Python** | 26.7.0 | Official Oracle MySQL database driver | `database.py`, `app.py` |
| **Scikit-Learn** | 1.9.0 | Machine learning pipeline, RandomForestRegressor, StandardScaler | `src/train_model.py`, `src/evaluate.py`, `app.py`, `src/predict.py` |
| **Joblib** | 1.5.3 | Serializer / Deserializer for `.pkl` model binaries | `app.py`, `src/train_model.py`, `src/predict.py` |
| **Pandas** | 3.0.5 | Tabular data manipulation and feature engineering | `src/*.py`, `app.py` |
| **NumPy** | 2.4.6 | Numerical math, synthetic data noise generation | `src/*.py`, `app.py` |
| **ReportLab** | 5.0.0 | Programmatic PDF report generation engine | `app.py` (`download_pdf` route) |
| **Matplotlib** | 3.11.1 | Scientific plotting of model evaluation graphs | `src/evaluate.py`, `src/visualize.py` |
| **Seaborn** | 0.13.2 | Statistical correlation heatmap plotting | `src/evaluate.py` |
| **Requests** | 2.34.2 | HTTP client library for simulation test scripts | `scripts/test_esp32_iot.py` |
| **HTML5 & Vanilla CSS3** | Custom | Responsive dashboard UI, KPI cards, modal lightbox | `templates/*.html`, `static/style.css` |
| **Chart.js** | CDN | Real-time dual-axis time-series canvas chart | `templates/dashboard.html`, `static/script.js` |
| **ArduinoJson** | v6 / v7 | Embedded JSON serialization on ESP32 | `firmware/esp32_industrial_telemetry.ino` |
| **PZEM004Tv30** | v3.0 | Modbus-RTU UART driver for PZEM-004T | `firmware/esp32_industrial_telemetry.ino` |
| **WiFi & HTTPClient** | ESP32 Core | 2.4 GHz Wi-Fi association & HTTP POST handling | `firmware/esp32_industrial_telemetry.ino` |
| **Docker** | **None** | *NOT CONFIRMED FROM CODE* — No Dockerfile or compose files present | N/A |
| **Cloud Hosting** | **Localhost**| *NOT CONFIRMED FROM CODE* — Configured for LAN binding (`0.0.0.0:5000`) | `app.py` |

---

# 3. COMPLETE PROJECT FOLDER STRUCTURE

```
IndustrialCarbonForecasting/
│
├── dataset/                                   # Data storage directory
│   ├── hybrid_dataset.csv                     # Final 1,800-row expanded dataset used to train Random Forest
│   ├── industrial_energy.csv                  # Raw historical manufacturing equipment dataset
│   ├── industrial_energy_cleaned.csv          # Intermediate cleaned dataset (missing values handled)
│   ├── industrial_energy_expanded_low_energy.csv # Expanded dataset with low-energy samples (0.22 - 19.79 kWh)
│   ├── industrial_energy_features.csv         # Engineered features dataset (specific energy, hour, weekend)
│   └── iot_carbon.csv                         # Reference benchmark dataset used for domain validation
│
├── firmware/                                  # Embedded Microcontroller Firmware
│   └── esp32_industrial_telemetry.ino        # Complete Arduino C++ sketch for ESP32 + PZEM-004T + IR sensor
│
├── model/                                     # Trained Machine Learning Artifacts
│   ├── random_forest.pkl                      # Serialized Scikit-Learn RandomForestRegressor binary
│   └── scaler.pkl                             # Serialized Scikit-Learn StandardScaler binary
│
├── notebooks/                                 # Research Notebooks
│   └── preprocessing.ipynb                    # 0-byte placeholder notebook file
│
├── reports/                                   # Evaluation Artifacts & PDF Storage
│   ├── graphs/                                # High-resolution PNG evaluation figures
│   │   ├── correlation_heatmap.png            # Multivariate Pearson correlation heatmap
│   │   ├── feature_importance.png             # Bar chart of Random Forest Gini feature importances
│   │   ├── prediction_vs_actual.png           # Actual vs Predicted parity scatter plot (R² = 0.9869)
│   │   └── residual_plot.png                  # Residual error distribution plot (MAE = 0.3344 kg)
│   ├── predictions/                           # Generated PDF certificates (stored by record ID)
│   │   └── CO2_Prediction_*.pdf               # Individual certification report files
│   └── results.txt                            # Verified text metrics (MAE, MSE, RMSE, R², MAPE, CV)
│
├── scripts/                                   # Automation, Testing & Emulation
│   ├── test_esp32_iot.py                      # Hardware emulation & simulation streaming script
│   └── verify_system.py                       # 14-point automated test suite covering DB, ML, APIs, PDF
│
├── src/                                       # Core Python Source Code & Pipelines
│   ├── check_dataset.py                       # Diagnostic script to check statistical ranges of dataset
│   ├── create_hybrid_dataset.py               # Generates hybrid_dataset.csv with Scope 2 & process logic
│   ├── evaluate.py                            # Computes evaluation metrics and generates graphs
│   ├── feature_engineering.py                 # Extracts hour, day of week, weekend, and specific energy
│   ├── predict.py                             # Standalone inference helper function and bounds checker
│   ├── preprocess.py                          # Data cleaning, column standardization, missing value handling
│   ├── test_model.py                          # Quick sanity check testing model inference on 5 sample vectors
│   ├── train_model.py                         # Complete training pipeline: holdout split, scaler, RF fitting
│   ├── utils.py                               # Threshold helpers, emission classifications, Scope 2 formula
│   ├── validate_dataset.py                    # Compares hybrid dataset distribution with iot_carbon.csv
│   └── visualize.py                           # Dedicated plotting script generating reports/graphs/
│
├── static/                                    # Frontend Static Web Assets
│   ├── graphs/                                # Static copies of ML evaluation graphs for Dashboard UI
│   │   ├── actual_vs_predicted_fixed.png
│   │   ├── correlation_heatmap_fixed.png
│   │   ├── feature_importance_fixed.png
│   │   └── residual_analysis_fixed.png
│   ├── script.js                              # Frontend UI logic, form validation, 4s polling, Chart.js
│   └── style.css                              # Design system, CSS variables, grid, responsive layout
│
├── templates/                                 # Jinja2 HTML5 Templates
│   ├── about.html                             # Project architecture, methodology, and tech stack view
│   ├── dashboard.html                         # Real-time IoT monitoring dashboard with live polling
│   ├── history.html                           # Tabular view of prediction_history with PDF download links
│   ├── index.html                             # Home landing page with hero banner and system cards
│   └── predict.html                           # Manual telemetry input form and emission results card
│
├── app.py                                     # Primary Flask application, routes, APIs, and in-memory state
├── database.py                                # MySQL connection factory and schema migration runner
├── README.md                                  # Markdown documentation and hardware setup guide
└── requirements.txt                           # Python package dependencies manifest
```

---

# 4. FRONTEND ARCHITECTURE & IMPLEMENTATION

### Pages & Navigation
* **Framework:** Server-rendered HTML5 via Flask Jinja2 with custom CSS (`static/style.css`) and client JavaScript (`static/script.js`).
* **Pages:**
  1. `Home` (`/` -> `index.html`): High-level overview, architecture highlights, CTA buttons.
  2. `Predict` (`/predict` -> `predict.html`): Manual telemetry entry form (Energy, Production, Hour, Weekend) and emission results card.
  3. `Dashboard` (`/dashboard` -> `dashboard.html`): Real-time IoT operations center with hardware status card, KPI metrics, live electrical sub-cards, Chart.js trend graph, and ML diagnostic plots with modal lightbox.
  4. `History` (`/history` -> `history.html`): Audit table of manual predictions with links to download ReportLab PDF certificates.
  5. `About` (`/about` -> `about.html`): Theoretical foundations, Scope 2 formulations, and tech stack details.

### Real-Time Polling Engine (`static/script.js`)
On `dashboard.html`, the browser runs an asynchronous polling loop every 4 seconds:
```javascript
function updateDashboardTelemetry() {
    // 1. Fetch latest IoT status
    fetch("/api/iot/latest")
        .then(res => res.json())
        .then(data => {
            // Updates DOM textContent for Energy, Production, Hours, CO2,
            // Voltage, Current, Power, Power Factor, Machine Status, and Connection Badge
        });

    // 2. Fetch history for Chart.js trend chart
    fetch("/api/iot/history")
        .then(res => res.json())
        .then(data => {
            iotChart.data.labels = data.labels;
            iotChart.data.datasets[0].data = data.energies;
            iotChart.data.datasets[1].data = data.co2_emissions;
            iotChart.update("none");
        });
}
setInterval(updateDashboardTelemetry, 4000);
```

---

# 5. BACKEND ARCHITECTURE & API ENDPOINTS

* **Main Entry File:** `app.py` (965 lines). Executed directly via `python app.py`.
* **Database Connection Factory:** `get_db()` connects to MySQL database `IndustrialCarbonForecasting` (user `root`, password `root`).

### API Endpoint Catalog

#### 1. Ingest IoT Telemetry (Primary Hardware Ingestion)
* **Method & URL:** `POST /api/iot/telemetry`
* **Purpose:** Receives electrical telemetry from PZEM-004T and item counts from IR sensor.
* **Input Format:** `application/json`
* **Input Payload:**
  ```json
  {
    "device_id": "ESP32_FACTORY_01",
    "voltage": 231.4,
    "current": 2.45,
    "power": 540.2,
    "energy_kwh": 12.85,
    "frequency": 50.0,
    "power_factor": 0.95,
    "production_count": 105,
    "operating_hours": 3.5,
    "is_mock": false
  }
  ```
* **Processing:**
  1. Validates JSON payload and field types.
  2. Evaluates machine operational status: `machine_is_on = (power >= 20.0)` (or `current >= 0.15`).
  3. Updates in-memory `RUNTIME_TRACKER` to accumulate operating seconds when running.
  4. Calculates Scope 2 baseline: `calculated_co2 = energy_kwh * 0.82`.
  5. Determines current hour (`datetime.now().hour`) and weekend flag (`1` if weekend, else `0`).
  6. Executes ML model: `predict_ml_model(energy_kwh, production_count, hour, weekend)`.
  7. Inserts record into MySQL table `iot_telemetry`.
* **Output:** HTTP 201 Created with JSON object including `record_id`, `machine_status`, `calculated_co2`, `forecast_co2`.

#### 2. Query Latest Telemetry
* **Method & URL:** `GET /api/iot/latest`
* **Purpose:** Provides latest reading, online indicator (fresh if $\le 90\text{ s}$), and connection state string.
* **Output:** JSON object containing all electrical fields and hardware status badges.

#### 3. Query Telemetry Trend History
* **Method & URL:** `GET /api/iot/history`
* **Purpose:** Supplies the last 25 readings in chronological order for Chart.js.
* **Output:** JSON object containing `labels`, `voltages`, `powers`, `energies`, `productions`, and `co2_emissions`.

#### 4. Simulation / Mock Ingestion
* **Method & URL:** `POST /api/iot/mock`
* **Purpose:** Ingests simulated telemetry with `is_mock=1` for testing before hardware is deployed.

#### 5. Reset Batch Counter
* **Method & URL:** `POST /api/iot/reset_production`
* **Purpose:** Resets `production_offset` in `RUNTIME_TRACKER` for new production batches.

#### 6. Download PDF Certification
* **Method & URL:** `GET /download-pdf/<int:prediction_id>`
* **Purpose:** Generates and returns an ISO-style A4 PDF certificate via ReportLab.

---

# 6. MACHINE LEARNING MODEL & FEATURE SPECIFICATIONS

### Algorithm & Pipeline
* **Algorithm:** `sklearn.ensemble.RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)`
* **Scaler:** `sklearn.preprocessing.StandardScaler`
* **Model Artifact:** `model/random_forest.pkl`
* **Scaler Artifact:** `model/scaler.pkl`
* **Training Dataset:** `dataset/hybrid_dataset.csv` (1,800 rows, 20% holdout test)

### EXACT Feature Names and EXACT Feature Order
The model expects **strictly 4 features in this exact order**:
```python
FEATURE_NAMES = [
    "Energy_Consumption",  # Feature 1: Float (kWh)
    "Production_Output",   # Feature 2: Float (Units)
    "Working_Hour",        # Feature 3: Integer (0 to 23)
    "Weekend"              # Feature 4: Binary Integer (0 for Weekday, 1 for Weekend)
]
```
* **Target Variable:** `CO2_Emission` (kg CO2).

### Verified Evaluation Metrics (`reports/results.txt`)
* **Holdout Test Set:** 360 samples (20.0%)
* **Coefficient of Determination ($R^2$):** **`0.9869`**
* **5-Fold Cross-Validation Mean $R^2$:** **`0.9816`** ($\pm 0.0021$)
* **Mean Absolute Error (MAE):** **`0.3344 kg CO2`**
* **Root Mean Squared Error (RMSE):** **`0.4204 kg CO2`**
* **Mean Absolute Percentage Error (MAPE):** **`8.05%`**

### Feature Importance Breakdown
1. `Energy_Consumption`: **91.36%** ($0.913553$)
2. `Production_Output`: **3.63%** ($0.036280$)
3. `Working_Hour`: **2.72%** ($0.027245$)
4. `Weekend`: **2.29%** ($0.022922$)

### Out-of-Domain Fallback Logic
* The model's training range is `MODEL_ENERGY_MIN = 0.22 kWh` to `MODEL_ENERGY_MAX = 19.79 kWh`.
* When input energy is within `[0.22, 19.79]`, the system uses `predict_ml_model()`.
* Outside this range, the system avoids extrapolation bias and falls back to the CEA Scope 2 formula:
  $$\text{CO}_2\ (\text{kg}) = \text{Energy (kWh)} \times 0.82\ \text{kg CO}_2/\text{kWh}$$

---

# 7. CURRENT TELEMETRY INPUT FLOW

```
                          INPUT SOURCES
               ┌─────────────────────────────────┐
               │  A. Web Form: /predict          │
               │  B. ESP32 / Mock: /api/iot/...  │
               └───────────────┬─────────────────┘
                               │
                               ▼
                        BACKEND VALIDATION
               - Non-negative numbers
               - Hour: 0 - 23 | Weekend: 0 or 1
                               │
                               ▼
                     DOMAIN RANGE EVALUATION
                   /─────────────────────────\
                  <  0.22 <= Energy <= 19.79  >
                   \─────────────────────────/
                         /             \
                   YES  /               \  NO
                       v                 v
            ┌───────────────────┐ ┌───────────────────┐
            │   ML FORECAST     │ │  SCOPE 2 FACTOR   │
            │ StandardScaler    │ │ Energy * 0.82     │
            │ RandomForest.pkl  │ │                   │
            └─────────┬─────────┘ └─────────┬─────────┘
                      │                     │
                      └──────────┬──────────┘
                                 │
                                 ▼
                     MYSQL DATABASE PERSISTENCE
                     - prediction_history OR
                     - iot_telemetry
                                 │
                                 ▼
                    OPERATOR PRESENTATION & UI
                    - Result card / PDF download
                    - Live Dashboard DOM / Chart.js
```

---

# 8. DATABASE SCHEMA & MIGRATIONS

* **Database Engine:** MySQL Server (Port `3306`)
* **Database Name:** `IndustrialCarbonForecasting`
* **Credentials:** User `root` | Password `root`
* **Schema Runner:** [database.py](file:///C:/Users/SKANDASHRI%20S%20N/OneDrive/Desktop/IndustrialCarbonForecasting/database.py)

### 1. Table: `prediction_history`
| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INT` | No | Auto Increment | Primary Key |
| `energy_consumption` | `FLOAT` | No | None | Energy in kWh |
| `production_output` | `FLOAT` | No | None | Units produced |
| `working_hour` | `INT` | No | None | Shift hour (0–23) |
| `weekend` | `INT` | No | None | 0 = Weekday, 1 = Weekend |
| `predicted_co2` | `FLOAT` | No | None | Calculated/forecasted CO2 (kg) |
| `prediction_time` | `TIMESTAMP` | Yes | CURRENT_TIMESTAMP | Record timestamp |

### 2. Table: `iot_telemetry`
| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INT` | No | Auto Increment | Primary Key |
| `device_id` | `VARCHAR(50)`| No | `'ESP32_FACTORY_01'` | Microcontroller ID |
| `voltage` | `FLOAT` | No | `0.0` | RMS AC Line Voltage (V) |
| `current` | `FLOAT` | No | `0.0` | AC Load Current (A) |
| `power` | `FLOAT` | No | `0.0` | Active Electrical Power (W) |
| `energy_kwh` | `FLOAT` | No | `0.0` | Cumulative Energy (kWh) |
| `frequency` | `FLOAT` | No | `50.0` | AC Frequency (Hz) |
| `power_factor` | `FLOAT` | No | `1.0` | Power Factor |
| `production_count`| `INT` | No | `0` | Debounced Item Count |
| `operating_hours` | `FLOAT` | No | `0.0` | Machine Running Hours |
| `machine_status` | `VARCHAR(20)`| Yes | `'Running'` | "Running" or "Idle" |
| `co2_emission` | `FLOAT` | No | None | Scope 2 Calculated CO2 |
| `forecast_co2` | `FLOAT` | Yes | `NULL` | Random Forest Forecast |
| `is_mock` | `TINYINT(1)` | Yes | `0` | 0 = Physical, 1 = Mock |
| `recorded_at` | `TIMESTAMP` | Yes | CURRENT_TIMESTAMP | Server receipt timestamp |

---

# 9. CURRENT IOT FIRMWARE IMPLEMENTATION

The firmware is located at [firmware/esp32_industrial_telemetry.ino](file:///C:/Users/SKANDASHRI%20S%20N/OneDrive/Desktop/IndustrialCarbonForecasting/firmware/esp32_industrial_telemetry.ino).

### Key Code Characteristics
* **Libraries:** `<WiFi.h>`, `<HTTPClient.h>`, `<ArduinoJson.h>`, `<PZEM004Tv30.h>`.
* **Hardware UART Configuration:**
  ```cpp
  #define PZEM_RX_PIN 16 // ESP32 RX2 connects to PZEM TX
  #define PZEM_TX_PIN 17 // ESP32 TX2 connects to PZEM RX
  PZEM004Tv30 pzem(Serial2, PZEM_RX_PIN, PZEM_TX_PIN);
  ```
* **IR Sensor Interrupt Configuration:**
  ```cpp
  #define PIN_IR_SENSOR 18
  pinMode(PIN_IR_SENSOR, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_IR_SENSOR), onProductDetected, FALLING);
  ```
* **150ms Interrupt Debounce Routine:**
  ```cpp
  void IRAM_ATTR onProductDetected() {
      unsigned long currentMs = millis();
      if ((currentMs - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
          productionCounter++;
          lastDebounceTime = currentMs;
      }
  }
  ```
* **Working Hours Tracking:**
  Accumulates active milliseconds when `power >= 20.0W`, converting to hours via `(float)activeMs / 3600000.0`.
* **Transmit Cadence:** Every `5000 ms` (5 seconds) via HTTP POST.

---

# 10. HARDWARE COMPONENTS & ROLES

1. **ESP32 Microcontroller Node:** Runs the firmware loop, interrogates the PZEM Modbus registers over UART, counts pulses from the IR sensor, performs runtime accumulation, and handles HTTP transmission.
2. **PZEM-004T v3.0 Multi-Meter:** Samples high-voltage AC mains to provide Voltage (V), Current (A), Active Power (W), Cumulative Energy (kWh), Frequency (Hz), and Power Factor.
3. **100A Split-Core Current Transformer (CT):** Clamps non-invasively around **EXACTLY ONE LIVE (PHASE) CONDUCTOR** to sense load current.
4. **Optical IR Proximity Sensor:** Positioned at the production conveyor/chute to count finished goods.

---

# 11. IOT TO SOFTWARE INTEGRATION PLAN

To integrate the physical hardware, follow these exact steps:

### Task 1: Update Firmware Configuration
* **File to modify:** `firmware/esp32_industrial_telemetry.ino` (Lines 42–46).
* **Action:** Replace placeholder strings with actual 2.4 GHz Wi-Fi credentials and the local LAN IPv4 address of the host machine running Flask:
  ```cpp
  const char* WIFI_SSID     = "Factory_WiFi_2.4G";
  const char* WIFI_PASSWORD = "FactorySecurePassword";
  const char* BACKEND_URL   = "http://192.168.1.45:5000/api/iot/telemetry";
  ```

### Task 2: Configure Host Firewall
* **Action:** Create an inbound rule in Windows Defender Firewall allowing TCP traffic on port `5000`.

### Task 3: Bench Test & Verify Ingestion
* **Action:** Power the ESP32 via USB and open the Arduino Serial Monitor (115200 baud). Confirm HTTP 201 responses from the Flask server. Open `http://localhost:5000/dashboard` and verify the status badge switches to **`🟢 LIVE IoT MODE (ESP32 Connected)`**.

---

# 12. DATA FORMAT SPECIFICATION (ESP32 TO BACKEND)

```json
{
  "device_id": "ESP32_FACTORY_01",
  "voltage": 230.4,
  "current": 2.45,
  "power": 540.2,
  "energy_kwh": 12.85,
  "frequency": 50.0,
  "power_factor": 0.95,
  "production_count": 105,
  "operating_hours": 3.50,
  "machine_status": "Running",
  "is_mock": false
}
```

* `voltage`: Float (Volts RMS).
* `current`: Float (Amperes RMS).
* `power`: Float (Active Watts).
* `energy_kwh`: Float (Cumulative kilowatt-hours) — maps directly to ML feature `Energy_Consumption`.
* `frequency`: Float (Hertz).
* `power_factor`: Float (0.00 – 1.00).
* `production_count`: Integer (Units produced) — maps directly to ML feature `Production_Output`.
* `operating_hours`: Float (Cumulative machine runtime).
* `machine_status`: String (`"Running"` vs `"Idle"`).
* `is_mock`: Boolean (Must be `false` for real hardware).

---

# 13. HANDLING ELECTRICAL ENERGY CONSUMPTION (kWh)

* **Measurement:** The PZEM-004T measures cumulative electrical work internally via its dedicated metering ASIC and non-volatile EEPROM.
* **Unit Alignment:** The firmware method `pzem.energy()` returns cumulative energy directly in **kilowatt-hours (kWh)**.
* **ML Feature Mapping:** The value is placed directly into the `Energy_Consumption` input feature of the Random Forest model without requiring manual unit conversions.

---

# 14. HANDLING PRODUCTION COUNT (IR SENSOR)

* **Physical Sensing:** Each finished product passing the optical beam pulls the digital input LOW (`FALLING` edge).
* **Debouncing:** The firmware enforces a 150 ms lockout in the interrupt routine to eliminate false double-counts caused by optical reflection or conveyor vibration.
* **Batch Counter Reset:** Clicking **"🔄 Reset Batch"** on the dashboard triggers `POST /api/iot/reset_production` to reset the batch offset.

---

# 15. DERIVING WORKING HOURS & MACHINE STATUS

No external vibration sensor or mechanical runtime counter is needed:
* **Running Condition:** Active Power $P \ge 20.0\text{ W}$ (or Current $I \ge 0.15\text{ A}$).
* **Idle Condition:** Active Power $P < 20.0\text{ W}$.
* **Accumulation:** Both the ESP32 and Flask backend track elapsed running seconds and convert them to fractional hours:
  $$\text{Operating Hours} = \frac{\sum \text{Running Seconds}}{3600}$$

---

# 16. COMPLETE REAL-TIME DATA FLOW TRACE

1. **Physical Operation:** Motor draws $540\text{ W}$ ($2.45\text{ A}$ at $230\text{ V}$).
2. **Product Detect:** IR sensor detects part; counter increments from $104$ to $105$.
3. **ESP32 Sampling:** Reads PZEM registers; identifies $P \ge 20.0\text{ W}$; updates runtime to $3.50\text{ h}$.
4. **HTTP Post:** Sends JSON payload to `http://<HOST_IP>:5000/api/iot/telemetry`.
5. **Backend Processing:** Computes Scope 2 emission ($12.85 \times 0.82 = 10.54\text{ kg CO}_2$), assembles feature vector `[12.85, 105, 15, 0]`, transforms via `scaler.pkl`, and predicts via `random_forest.pkl` ($11.23\text{ kg CO}_2$).
6. **Database Persistence:** Inserts record into MySQL `iot_telemetry`.
7. **Frontend Update:** Browser polls `/api/iot/latest`, updating KPI cards and advancing the Chart.js line chart.

---

# 17. COMMUNICATION PROTOCOL & NETWORK ARCHITECTURE

* **Protocol:** HTTP/1.1 REST API via standard POST requests.
* **Why REST:** Native to Flask, robust against network drops, supported directly by the ESP32 `HTTPClient` library, and simple to debug with standard tools.
* **Cadence:** Telemetry transmitted every 5 seconds.
* **Network Requirements:** Host workstation and ESP32 must reside on the same 2.4 GHz Wi-Fi subnet.

---

# 18. EXACT API DESIGN FOR IOT INGESTION

### Endpoint Specification
```http
POST /api/iot/telemetry HTTP/1.1
Host: <HOST_IP>:5000
Content-Type: application/json

{
  "device_id": "ESP32_FACTORY_01",
  "voltage": 230.4,
  "current": 2.45,
  "power": 540.2,
  "energy_kwh": 12.85,
  "frequency": 50.0,
  "power_factor": 0.95,
  "production_count": 105,
  "operating_hours": 3.50,
  "machine_status": "Running",
  "is_mock": false
}
```

### Successful Response (HTTP 201 Created)
```json
{
  "status": "success",
  "record_id": 142,
  "device_id": "ESP32_FACTORY_01",
  "voltage": 230.4,
  "current": 2.45,
  "power": 540.2,
  "energy_kwh": 12.85,
  "frequency": 50.0,
  "power_factor": 0.95,
  "production_count": 105,
  "operating_hours": 3.5,
  "session_duration_minutes": 45.2,
  "machine_status": "Running",
  "energy_per_unit": 0.1224,
  "calculated_co2": 10.54,
  "forecast_co2": 11.23,
  "pollution_level": "Low",
  "is_mock": false,
  "timestamp": "2026-10-04 22:45:00"
}
```

---

# 19. DATABASE + IOT + ML SYNCHRONIZATION

* **Prediction Timing:** Executes immediately upon receiving each telemetry packet.
* **Execution Time:** Random Forest inference takes under 2 milliseconds of CPU time.
* **Synchronization:** Synchronous inference guarantees that every row in `iot_telemetry` contains both the calculated Scope 2 emission and the ML forecast for that exact moment.

---

# 20. SECURITY & INDUSTRIAL HARDENING

1. **Subnet Isolation:** Deploy the ESP32 and host PC on an isolated industrial IoT VLAN.
2. **Device Authentication (Recommended):** Add an `X-API-Key` header check in `app.py` and the ESP32 firmware to restrict ingestion to authorized devices.
3. **SQL Injection Defense:** All queries in `app.py` and `database.py` use parameterized statements (`%s` placeholders).
4. **Credential Management:** Keep MySQL passwords configurable via environment variables (`os.getenv("DB_PASSWORD")`).

---

# 21. DEPLOYMENT & NETWORK TOPOLOGY

* **Binding:** Flask is bound to `0.0.0.0:5000` to accept external LAN connections.
* **ESP32 Addressing:** The ESP32 must target the host workstation's actual LAN IPv4 address (e.g. `http://192.168.1.45:5000`), never `127.0.0.1` or `localhost`.
* **Firewall Rule:** Windows Defender Firewall must have an inbound rule allowing TCP traffic on port `5000`.

---

# 22. LOCAL DEVELOPMENT SETUP GUIDE

```powershell
# 1. Navigate to project root
cd "C:\Users\SKANDASHRI S N\OneDrive\Desktop\IndustrialCarbonForecasting"

# 2. Create and activate Python virtual environment
python -m venv env
.\env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify/initialize MySQL tables
python database.py

# 5. Run verification test suite (Confirms 14/14 tests pass)
python scripts/verify_system.py

# 6. Start the Flask application
python app.py

# 7. Test simulation stream (in separate terminal)
python scripts/test_esp32_iot.py 5
```

---

# 23. PHYSICAL HARDWARE SETUP & ELECTRICAL WIRING GUIDE

> [!CAUTION]
> ### HIGH-VOLTAGE ELECTRICAL SAFETY WARNING
> * The PZEM-004T connects directly to **220V–240V AC mains electricity**.
> * Always de-energize and lock out the main power breaker before working with high-voltage screw terminals.
> * House the PZEM-004T and ESP32 inside an insulated, flame-retardant enclosure.
> * The CT clamp must go around **ONLY ONE LIVE (PHASE) CONDUCTOR**. Never clamp around Phase + Neutral together.

### Pinout Connections

| Sensor / Module | Sensor Pin | ESP32 Pin | Function / Description |
| :--- | :--- | :--- | :--- |
| **PZEM-004T** | `5V` (VCC) | **`VIN` (5V)** | Powers PZEM optocouplers (Must have 5V) |
| **PZEM-004T** | `GND` | **`GND`** | Ground reference |
| **PZEM-004T** | `TX` | **`GPIO 16` (RX2)** | Serial transmit from PZEM to ESP32 |
| **PZEM-004T** | `RX` | **`GPIO 17` (TX2)** | Serial receive from ESP32 to PZEM |
| **PZEM-004T AC** | `L` (Screw) | **AC Live / Phase** | Measures line voltage |
| **PZEM-004T AC** | `N` (Screw) | **AC Neutral** | Neutral voltage reference |
| **PZEM-004T CT** | `CT1`, `CT2` | **CT Coil Leads** | 2 leads from 100A CT clamp |
| **IR Sensor** | `VCC` | **`3.3V` or `VIN`** | Sensor supply voltage |
| **IR Sensor** | `GND` | **`GND`** | Ground reference |
| **IR Sensor** | `OUT` | **`GPIO 18`** | Digital pulse output (Interrupt FALLING) |

---

# 24. COMPREHENSIVE TESTING PLAN

| Test ID | Subsystem | Action / Input | Expected Result | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | Database | Run `python database.py` | Schema initialized; tables reported | Terminal logs |
| **T-02** | Test Suite | Run `python scripts/verify_system.py` | 14/14 tests pass | Terminal logs |
| **T-03** | Simulation | Run `python scripts/test_esp32_iot.py 5`| HTTP 201 for all 5 packets | Terminal logs |
| **T-04** | Dashboard UI | Load `http://localhost:5000/dashboard` | Cards show live values; chart updates | Browser view |
| **T-05** | IR Sensor | Wave object across IR beam | Counter increments on Serial Monitor | Serial Monitor (115200) |
| **T-06** | PZEM UART | Connect PZEM to test load | Voltage $\approx 230\text{V}$, Power $> 0\text{W}$ | Serial Monitor (115200) |
| **T-07** | Wi-Fi Link | ESP32 boot sequence | Assigned IP printed; Wi-Fi connected | Serial Monitor (115200) |
| **T-08** | End-to-End | Power on ESP32 with sensors | Dashboard pill turns green; live values appear | Dashboard view |

---

# 25. TROUBLESHOOTING GUIDE

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **ESP32 Wi-Fi fails to connect** | Network is 5 GHz-only or requires web login | Use a dedicated 2.4 GHz SSID with WPA2-PSK security. |
| **PZEM values are NaN or 0** | PZEM VCC connected to 3.3V instead of 5V, or RX/TX inverted | Connect PZEM VCC to `VIN` (5V); connect PZEM TX to GPIO 16 and RX to GPIO 17. |
| **PZEM Voltage works, Current is 0**| CT coil clamped around both Live and Neutral conductors | Separate conductors and clamp around **ONLY ONE LIVE WIRE**. |
| **ESP32 reports HTTP -1 error** | Target URL uses `localhost`, or Windows Firewall blocks port 5000 | Use host PC's actual LAN IP in `BACKEND_URL`; add firewall inbound rule for port 5000. |
| **IR counts multiple times per part**| Optical bounce or conveyor vibration | Increase `DEBOUNCE_DELAY_MS` in firmware to `250` ms; adjust sensor potentiometer. |
| **ML model feature mismatch error** | Input features do not match expected 4-feature DataFrame | Ensure inputs are passed as DataFrame with columns `Energy_Consumption`, `Production_Output`, `Working_Hour`, `Weekend`. |

---

# 26. IMPLEMENTATION STATUS CHECKLIST

- [x] **Frontend Web Architecture:** Complete with HTML5 templates, CSS design system, and responsive layout.
- [x] **Backend Server:** Flask 3.1.3 operational on port 5000 with 9 endpoints.
- [x] **MySQL Database:** Schemas and migrations operational in `database.py`.
- [x] **ML Model & Scaler:** Random Forest ($R^2 = 0.9821$) and StandardScaler saved in `model/`.
- [x] **Scope 2 Carbon Math:** CEA grid factor standard ($0.82\text{ kg CO}_2/\text{kWh}$) implemented.
- [x] **PDF Certification Engine:** ReportLab pipeline operational at `/download-pdf/<id>`.
- [x] **IoT REST API:** `/api/iot/telemetry`, `/api/iot/latest`, `/api/iot/history` operational.
- [x] **Real-Time Polling:** Asynchronous 4-second JavaScript loop operational on dashboard.
- [x] **Working Hours Derivation:** Operational status derived from active power ($P \ge 20.0\text{ W}$).
- [x] **Firmware Code:** Complete Arduino sketch in `firmware/esp32_industrial_telemetry.ino`.
- [x] **Automated Test Suite:** `scripts/verify_system.py` passes 14/14 tests.
- [ ] **Firmware Flashing:** Physical ESP32 must be configured with local Wi-Fi and host IP, then flashed.
- [ ] **Physical Sensor Wiring:** PZEM and IR sensor must be wired to ESP32 on the bench.
- [ ] **Factory Panel Deployment:** Physical installation of hardware in machine electrical panel.

---

# 27. PRIORITIZED ROADMAP FOR NEXT DEVELOPER

### Phase 1: Software & Database Verification (Day 1)
1. Start MySQL and run `python database.py`.
2. Run `python scripts/verify_system.py` to confirm all 14 tests pass.
3. Start `python app.py` and run `python scripts/test_esp32_iot.py 5` to verify dashboard polling.

### Phase 2: Firmware Setup & Flashing (Day 1 – Day 2)
1. Install Arduino IDE 2.x with ESP32 board support, `PZEM004Tv30`, and `ArduinoJson`.
2. Find host PC LAN IPv4 address via `ipconfig`.
3. Open `firmware/esp32_industrial_telemetry.ino`, update `WIFI_SSID`, `WIFI_PASSWORD`, and `BACKEND_URL`.
4. Upload sketch to ESP32 over USB and verify Wi-Fi connection in Serial Monitor (115200 baud).

### Phase 3: Bench Testing Sensors (Day 2)
1. Wire IR sensor to GPIO 18 (5V, GND, Signal). Verify counts on Serial Monitor.
2. Wire PZEM UART to GPIO 16/17 (VIN, GND, TX, RX). Connect test AC load through CT coil.
3. Verify voltage, current, and power on Serial Monitor and confirm incoming HTTP 201 responses in Flask.
4. Confirm dashboard status card turns **`🟢 LIVE IoT MODE (ESP32 Connected)`**.

### Phase 4: Factory Panel Installation (Day 3)
1. De-energize machine main breaker.
2. Mount hardware inside an insulated enclosure.
3. Clamp CT coil around the single Phase conductor; connect AC voltage references to PZEM L and N.
4. Position IR sensor at the parts chute.
5. Energize breaker and verify continuous real-time operation.

---

# 28. COMPLETE SYSTEM ARCHITECTURE DIAGRAM

```
═══════════════════════════════════════════════════════════════════════════════════════
                    PHYSICAL INDUSTRIAL EDGE LAYER
═══════════════════════════════════════════════════════════════════════════════════════
  ┌──────────────────────────────────┐          ┌──────────────────────────────────┐
  │   PZEM-004T v3.0 Multi-Meter    │          │  Optical IR Proximity Sensor     │
  │   - RMS Voltage (80-260V AC)     │          │  - Active item detection beam    │
  │   - Active Power (Watts)         │          │  - High-to-Low transition logic  │
  │   - AC Current via 100A CT Coil  │          └────────────────┬─────────────────┘
  │   - Cumulative Energy (kWh)      │                           │
  │   - Frequency & Power Factor     │                           │ GPIO 18 (Interrupt)
  └────────────────┬─────────────────┘                           │ FALLING Edge
                   │ UART Modbus-RTU                             ▼
                   │ GPIO 16 (RX2) / GPIO 17 (TX2) ┌───────────────────────────────┐
                   └──────────────────────────────►│ 150ms Debounced ISR Counter   │
                                                   └─────────────┬─────────────────┘
                                                                 │
                                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             ESP32 MICROCONTROLLER                                │
│  - Edge thresholding: Active Power >= 20.0W -> Status = "Running"                │
│  - Millisecond session runtime tracking: operating_hours = activeMs / 3600000.0  │
│  - Dynamic JSON serializer: StaticJsonDocument<384>                              │
│  - Transmit scheduler: Fixed 5000 ms (5s) interval                               │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         │ Wi-Fi 802.11 b/g/n (Local Subnet)
                                         │ HTTP POST (application/json)
                                         ▼
═══════════════════════════════════════════════════════════════════════════════════════
                    FLASK APPLICATION BACKEND SERVER (Port 5000)
═══════════════════════════════════════════════════════════════════════════════════════
┌──────────────────────────────────────────────────────────────────────────────────┐
│  REST Ingestion Endpoint: POST /api/iot/telemetry                                │
│  - Validates numeric parameters & prevents negative values                       │
│  - Updates in-memory RUNTIME_TRACKER session state                               │
│  - Computes Scope 2 Grid Baseline: CO2 = Energy_kWh * 0.82 kg/kWh               │
└───────────────────┬──────────────────────────────────────────────┬───────────────┘
                    │                                              │
                    ▼                                              ▼
┌──────────────────────────────────────┐       ┌───────────────────────────────────┐
│     MYSQL RELATIONAL DATABASE        │       │  SCIKIT-LEARN ML INFERENCE PIPELINE│
│     Database: IndustrialCarbon...    │       │                                   │
│                                      │       │  Feature Assembly (Exact Order):  │
│  Table: iot_telemetry                │       │  [Energy, Prod, Hour, Weekend]    │
│  - id, device_id, V, I, P, kWh       │       │                 │                 │
│  - frequency, power_factor           │       │                 ▼                 │
│  - production_count, operating_hours │       │  model/scaler.pkl                 │
│  - machine_status, co2_emission      │       │  StandardScaler.transform()       │
│  - forecast_co2, is_mock, recorded_at│       │                 │                 │
│                                      │       │                 ▼                 │
│  Table: prediction_history           │       │  model/random_forest.pkl          │
│  - Stores manual web predictions     │       │  RandomForestRegressor.predict()  │
└───────────────────▲──────────────────┘       └─────────────────┬─────────────────┘
                    │                                            │
                    │ Query (Every 4s)                           │ Store Forecast
                    └──────────────────────┬─────────────────────┘
                                           │
                                           ▼
═══════════════════════════════════════════════════════════════════════════════════════
                    CLIENT PRESENTATION & OPERATOR DASHBOARD
═══════════════════════════════════════════════════════════════════════════════════════
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Browser Client: templates/dashboard.html  |  static/script.js                   │
│  - Recurring 4s polling: GET /api/iot/latest  &  GET /api/iot/history            │
│  - Hardware Status Card: "LIVE IoT MODE (ESP32 Connected)" (Green Pulse)         │
│  - Primary KPI Cards: Energy (kWh) • Production • Operating Hours • CO2          │
│  - Electrical Strip: Active Power (W) • Voltage (V) • Current (A) • Power Factor │
│  - Chart.js Dynamic Trend Chart: Dual Y-axis (Energy vs Scope 2 CO2)             │
│  - ML Diagnostic Visualizations: Residuals, Parity, Feature Importance, Heatmap   │
│  - ISO-Style Audit Report: Programmatic ReportLab PDF generation                 │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

# 29. QUICK HANDOVER SUMMARY

```
========================================================================================
                      TECHNICAL HANDOVER SUMMARY SPECIFICATION
========================================================================================

PROJECT:
  Industrial Carbon Emission Forecasting System
  Repository: C:\Users\SKANDASHRI S N\OneDrive\Desktop\IndustrialCarbonForecasting

CURRENT STATUS:
  Software, database, machine learning model, REST APIs, and frontend are 100% complete
  and verified (14/14 automated tests passing). Firmware source code is complete.
  Physical hardware bench wiring, Wi-Fi credential configuration, and factory panel
  installation remain to be performed by the incoming developer.

TECH STACK:
  Python 3.13, Flask 3.1.3, MySQL (mysql-connector-python 26.7.0), Scikit-Learn 1.9.0,
  Pandas 3.0.5, NumPy 2.4.6, ReportLab 5.0.0, Chart.js, HTML5/CSS3, ESP32 C++ (Arduino).

FRONTEND:
  Flask Jinja2 MPA with 5 templates: index.html, predict.html, history.html,
  dashboard.html, about.html. Custom responsive CSS design system. Script.js executes
  asynchronous 4-second polling to /api/iot/latest and /api/iot/history, driving
  real-time DOM updates and a dual-axis Chart.js line graph.

BACKEND:
  app.py (965 lines). Implements /predict_result, /download-pdf/<id>, /history, /dashboard,
  and IoT endpoints: POST /api/iot/telemetry, GET /api/iot/latest, GET /api/iot/history,
  POST /api/iot/mock, POST /api/iot/reset_production.

DATABASE:
  MySQL database "IndustrialCarbonForecasting" on localhost:3306 (user: root, pass: root).
  Two tables:
  1. prediction_history (Manual web form predictions).
  2. iot_telemetry (Real-time ESP32 electrical & production telemetry).
  All migrations automated in database.py. Zero temperature/humidity fields exist.

ML MODEL:
  Supervised RandomForestRegressor (n_estimators=100, max_depth=10, random_state=42).
  StandardScaler normalization. Metrics: R² = 0.9869, MAE = 0.3344 kg CO2.
  Domain boundaries: 0.22 to 19.79 kWh. (Falls back to 0.82 kg/kWh outside domain).

CURRENT INPUTS:
  Feature 1: Energy_Consumption (kWh)
  Feature 2: Production_Output (Units)
  Feature 3: Working_Hour (Integer, 0 to 23)
  Feature 4: Weekend (Binary flag: 0 for Weekday, 1 for Weekend)

IOT HARDWARE:
  1. Controller: ESP32 DevKit v1 (NodeMCU-32S).
  2. Energy Meter: PZEM-004T v3.0 + 100A Current Transformer (CT) clamp.
  3. Production Counter: Optical IR Proximity Sensor (Digital, falling-edge interrupt).
  4. Working Hours: Derived from PZEM Active Power (P >= 20.0W threshold). No extra sensor.

CURRENT IOT STATUS:
  Firmware written in firmware/esp32_industrial_telemetry.ino.
  Pin definitions: GPIO 16 (RX2), GPIO 17 (TX2), GPIO 18 (IR interrupt).
  Backend REST API /api/iot/telemetry is fully functional and tested via simulation.
  Physical ESP32 has not yet been flashed with local credentials or wired to sensors.

API:
  Primary Ingestion: POST /api/iot/telemetry
  Primary Polling:   GET  /api/iot/latest
  Trend History:     GET  /api/iot/history
  Simulation Mode:   POST /api/iot/mock

DATA FORMAT:
  JSON over HTTP POST. Payload fields: device_id (string), voltage (float), current (float),
  power (float), energy_kwh (float), frequency (float), power_factor (float),
  production_count (int), operating_hours (float), machine_status (string), is_mock (bool).

DATABASE FLOW:
  ESP32 POST -> Flask /api/iot/telemetry -> Threshold & Scope 2 Math -> ML Inference ->
  INSERT INTO iot_telemetry -> Browser polls /api/iot/latest every 4s -> DOM & Charts update.

ML FLOW:
  Payload energy_kwh and production_count extracted -> Server obtains current hour (0-23)
  and weekend flag (0/1) -> Assembles DataFrame [Energy_Consumption, Production_Output,
  Working_Hour, Weekend] -> scaler.transform() -> model.predict() -> Output stored as forecast_co2.

DEPLOYMENT:
  Localhost binding (0.0.0.0:5000). ESP32 must target the host PC's local LAN IPv4
  address (e.g. http://192.168.1.45:5000/api/iot/telemetry) over shared 2.4 GHz Wi-Fi.

REMAINING WORK:
  1. Flash firmware with actual factory 2.4 GHz Wi-Fi SSID, password, and host LAN IP.
  2. Wire hardware: PZEM UART to GPIO 16/17, IR sensor to GPIO 18.
  3. Clamp CT coil around Phase conductor and connect AC reference leads to PZEM L & N.
  4. Perform bench validation, then install inside factory panel enclosure.

KNOWN ISSUES / CAUTIONS:
  1. PZEM screw terminals connect to 220V AC mains. Observe strict electrical safety!
  2. PZEM optocouplers require 5V (connect to VIN, NOT 3.3V).
  3. CT coil must clamp around Phase ONLY (clamping Phase + Neutral yields zero reading).
  4. ESP32 requires 2.4 GHz Wi-Fi (incompatible with 5 GHz-only SSIDs).
  5. Windows Defender Firewall may block inbound port 5000 from LAN until an inbound rule is added.

IMPORTANT FILES:
  - app.py (Main web server & REST endpoints)
  - database.py (MySQL initialization & schema)
  - firmware/esp32_industrial_telemetry.ino (ESP32 C++ firmware sketch)
  - scripts/verify_system.py (Automated test suite)
  - scripts/test_esp32_iot.py (Hardware emulation streaming script)
  - model/random_forest.pkl (Trained Random Forest model)
  - model/scaler.pkl (Trained StandardScaler)
  - templates/dashboard.html (Live monitoring dashboard view)
  - static/script.js (Client polling logic & Chart.js integration)

FIRST STEPS FOR NEW DEVELOPER:
  1. Run 'python database.py' to verify MySQL tables.
  2. Run 'python scripts/verify_system.py' to confirm 14/14 tests pass.
  3. Run 'python app.py' to launch server.
  4. Find your PC's LAN IP using 'ipconfig'.
  5. Open 'firmware/esp32_industrial_telemetry.ino' in Arduino IDE, set Wi-Fi and IP,
     and upload to ESP32.
========================================================================================
```

---

# 30. CRUCIAL RULES, PHYSICAL VERIFICATION ITEMS & RISK PREVENTIONS

1. **Host Workstation IP Resolution:** The ESP32 cannot resolve `127.0.0.1` or `localhost`. The developer must determine the host PC's IPv4 address via `ipconfig` and set `BACKEND_URL = "http://<PC_LAN_IP>:5000/api/iot/telemetry"`.
2. **Network Band Compatibility:** The ESP32 supports only **2.4 GHz Wi-Fi**. It cannot associate with 5 GHz-only networks.
3. **PZEM Power Supply:** The PZEM-004T low-voltage header requires **5V DC** on VCC (connect to ESP32 `VIN`, not `3.3V`).
4. **Current Transformer (CT) Clamping:** Clamp the CT coil around **EXACTLY ONE LIVE CONDUCTOR (Phase)**. Clamping both Phase and Neutral causes magnetic fields to cancel out, resulting in zero current and power readings.
5. **Debouncing Verification:** Verify that conveyor vibrations do not trigger false product counts. If duplicate pulses occur, increase `DEBOUNCE_DELAY_MS` to 250–300 ms in the firmware.
6. **High-Voltage Isolation:** Always de-energize the factory circuit breaker before connecting high-voltage wires to the PZEM-004T screw terminals. House all electronics inside an insulated enclosure.













