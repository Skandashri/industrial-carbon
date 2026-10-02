# Industrial Carbon Emission Forecasting System
### Real-Time IoT Telemetry & Machine Learning Architecture

An end-to-end industrial sustainability and predictive decision-support system that ingests real-time operating telemetry from manufacturing equipment using an **ESP32 microcontroller**, computes accurate Scope 2 greenhouse gas emissions ($0.82\text{ kg CO}_2/\text{kWh}$ grid baseline), and forecasts future carbon emissions using a trained **Random Forest Regressor**.

---

## 1. Physical IoT Hardware Setup (Budget: ₹1,325 – ₹2,750)

| Requirement | Hardware Component | Estimated Cost | Interface | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **IoT Controller** | ESP32 (NodeMCU / WROOM-32) | ₹400 – ₹700 | Wi-Fi / REST | Edge computing node, data collection & transmission |
| **Energy Consumption** | PZEM-004T v3.0 + CT Coil (100A) | ₹600 – ₹1,300 | UART (Serial2) | Voltage, Current, Active Power, Frequency, PF, Energy (kWh) |
| **Production Count** | IR Proximity Sensor (E18-D80NK / TCRT5000) | ₹25 – ₹100 | GPIO 18 (Interrupt) | Counts finished goods/batches with 150ms debouncing |
| **Working Hours** | Derived from PZEM power readings | ₹0 (No sensor!) | Software threshold | Active runtime accumulated when Power &ge; 20.0 W |
| **Wiring & Power** | Jumper wires, USB cable, connectors | ₹300 – ₹650 | 5V DC power | Prototype power & signal interconnects |
| **Temperature & Humidity** | **REMOVED COMPLETELY** | ₹0 | None | Eliminated from all ML, DB, API, and UI layers |

---

## 2. System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │       PHYSICAL INDUSTRIAL HARDWARE       │
                               │                                         │
                               │  [PZEM-004T + CT]     [IR Sensor]       │
                               │  (V, I, P, kWh, PF)    (Item Detect)    │
                               └────────────┬────────────────┬───────────┘
                                            │ UART           │ GPIO 18
                                            ▼                ▼
                               ┌─────────────────────────────────────────┐
                               │           ESP32 CONTROLLER              │
                               │  - PZEM Modbus-RTU Reader               │
                               │  - 150ms Debounced Production Counter   │
                               │  - Runtime Accumulator (P >= 20W)       │
                               └────────────────────┬────────────────────┘
                                                    │ Wi-Fi HTTP POST (JSON)
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │          FLASK BACKEND & APIS           │
                               │  /api/iot/telemetry  |  /api/iot/latest │
                               │  - Status & Runtime Derivation Engine   │
                               │  - Scope 2 CO2: kWh × 0.82 kg CO2/kWh   │
                               │  - Random Forest ML Forecasting         │
                               └────────────┬────────────────┬───────────┘
                                            │                │
                        ┌───────────────────┴──┐          ┌──┴───────────────────┐
                        ▼                      ▼          ▼                      ▼
               ┌─────────────────┐   ┌─────────────────┐ ┌─────────────────┐   ┌─────────────────┐
               │  MySQL Database │   │ Live Dashboard  │ │ ML Diagnostics  │   │ Certified PDF   │
               │  iot_telemetry  │   │ Dynamic Polling │ │ R² = 0.982       │   │ Emission Audit  │
               │  pred_history   │   │ Mode Badges     │ │ MAE = 0.34 kg    │   │ Reports         │
               └─────────────────┘   └─────────────────┘ └─────────────────┘   └─────────────────┘
```

---

## 3. Electrical Wiring & Connection Guide

### A. PZEM-004T v3.0 to ESP32 (Low-Voltage Side)
The low-voltage header of the PZEM-004T is optically isolated from high-voltage AC mains.

| PZEM-004T Pin | ESP32 Pin | Wire Function |
| :--- | :--- | :--- |
| **5V (VCC)** | **VIN / 5V** | Powers PZEM optocouplers (requires 5V) |
| **TX** | **GPIO 16 (RX2)** | Modbus-RTU Serial transmit from PZEM |
| **RX** | **GPIO 17 (TX2)** | Modbus-RTU Serial receive to PZEM |
| **GND** | **GND** | Ground reference |

### B. PZEM-004T High-Voltage Mains Connection & Safety
> [!CAUTION]
> **ELECTRICAL SAFETY WARNING:**
> The AC side of PZEM-004T connects directly to 220V–240V AC mains electricity.
> - High-voltage wiring MUST be installed inside an insulated, flame-retardant enclosure.
> - Work on mains wiring ONLY when the breaker/isolator switch is completely OFF.
> - Never touch screw terminals while energized.
> - The Current Transformer (CT) coil must clamp around **ONLY ONE LIVE (PHASE) WIRE**, NEVER around Phase and Neutral together (which would cancel out magnetic flux and read zero).

* **Screw Terminals `L` & `N`**: Connect to 220V AC Live and Neutral for voltage measurement.
* **Screw Terminals `CT`**: Connect to the two leads of the CT clamp coil.

### C. IR Production Sensor to ESP32
| IR Sensor Pin | ESP32 Pin | Function |
| :--- | :--- | :--- |
| **VCC** | **3.3V or VIN** | Power supply (matches sensor rating) |
| **GND** | **GND** | Ground reference |
| **OUT / Signal** | **GPIO 18** | Digital signal (Interrupt FALLING with 150ms debounce) |

---

## 4. How Working Hours Are Derived (No Extra Sensor)

Operating hours are derived dynamically from PZEM-004T active power readings:
* **Operating Threshold:** Default `MACHINE_POWER_THRESHOLD_WATTS = 20.0 W` (or `MACHINE_CURRENT_THRESHOLD_AMPS = 0.15 A`). Configurable in backend environment.
* **Running State:** When measured Active Power $\ge 20.0\text{ W}$, the machine is classified as **`Running`** and runtime begins accumulating.
* **Idle State:** When measured Active Power $< 20.0\text{ W}$, the machine is classified as **`Idle / Off`** and runtime accumulation pauses.
* Both the ESP32 firmware and Flask backend track:
  - Machine state (`Running` vs `Idle`)
  - Current operating session duration (minutes)
  - Total cumulative operating hours

---

## 5. Scope 2 CO2 Calculation & ML Forecasting

1. **Measured IoT Values:**
   - Active Power ($P$), Current ($I$), Voltage ($V$), and cumulative electrical Energy ($\text{kWh}$) measured directly by PZEM-004T.
   - Production throughput ($Units$) counted directly by IR proximity sensor.
2. **Scientifically Calculated CO2:**
   Categorized as **Scope 2 Indirect Greenhouse Gas Emissions** under the GHG Protocol:
   $$\text{CO}_2\ (\text{kg}) = \text{Energy Consumption (kWh)} \times 0.82\ \text{kg CO}_2/\text{kWh}$$
   *(Grid baseline factor established by the Central Electricity Authority / CEA standard).*
3. **Machine Learning Forecast:**
   A supervised **Random Forest Regressor** trained on historical industrial operational data forecasts future carbon emissions using the feature vector:
   $$X = [\text{Energy Consumption (kWh)},\ \text{Production Count},\ \text{Working Hour (0-23)},\ \text{Weekend (0/1)}]$$

---

## 6. IoT REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/iot/telemetry` | `POST` | Primary ingestion endpoint for ESP32 readings (V, I, P, kWh, Count, Hours, Status). |
| `/api/iot/latest` | `GET` | Returns most recent telemetry packet, freshness indicator, and hardware online state. |
| `/api/iot/history` | `GET` | Returns recent 25 records for dynamic Chart.js live trends (Energy, Power, CO2). |
| `/api/iot/mock` | `POST` | Dedicated simulation endpoint for demonstration without physical hardware (`is_mock=1`). |
| `/api/iot/reset_production` | `POST` | Resets active batch production counter to zero. |

---

## 7. How to Run the Completed Project

### Step 1: Initialize Database & Migrations
Ensure MySQL is running on `localhost:3306` with database `IndustrialCarbonForecasting` (root/root):
```bash
python database.py
```

### Step 2: (Optional) Retrain or Evaluate the ML Model
```bash
python src/preprocess.py
python src/feature_engineering.py
python src/create_hybrid_dataset.py
python src/train_model.py
python src/evaluate.py
```

### Step 3: Launch the Flask Application
```bash
python app.py
```
Application will be accessible at `http://127.0.0.1:5000` (or `http://<YOUR_LOCAL_IP>:5000` on your LAN).

### Step 4: Verification Suite
Run the automated test suite to verify all endpoints, database queries, and ML models:
```bash
python scripts/verify_system.py
```

---

## 8. Switching Between Test Mode and Live IoT Mode

### Mode 1: Test / Simulation Mode (Before Hardware Arrives)
1. Open the Dashboard at `http://127.0.0.1:5000/dashboard`.
2. Click the **"⚡ Inject Test Reading"** button on the top-right status card, or run:
   ```bash
   python scripts/test_esp32_iot.py 5
   ```
3. The dashboard status pill will display **`TEST / SIMULATION MODE`** with an amber indicator, clearly separating simulated testing from real telemetry.

### Mode 2: Live IoT Mode (Physical Hardware Deployed)
1. Open `firmware/esp32_industrial_telemetry.ino` in Arduino IDE.
2. Set your Wi-Fi credentials (`WIFI_SSID`, `WIFI_PASSWORD`) and backend LAN IP (`BACKEND_URL`).
3. Connect ESP32 via USB and upload the sketch.
4. Once ESP32 starts transmitting, the dashboard status pill automatically switches to:
   **`🟢 LIVE IoT MODE (ESP32 Connected)`**.
