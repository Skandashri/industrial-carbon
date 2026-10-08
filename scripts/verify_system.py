"""
Comprehensive Verification Suite
Industrial Carbon Emission Forecasting System
Tests all backend routes, database operations, ML inference, IoT endpoints, and PDF generation.
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, get_db, model, scaler, EMISSION_FACTOR, MODEL_ENERGY_MIN, MODEL_ENERGY_MAX, MACHINE_POWER_THRESHOLD_WATTS
import numpy as np

def run_tests():
    print("=" * 70)
    print("RUNNING INDUSTRIAL CARBON FORECASTING SYSTEM VERIFICATION")
    print("=" * 70)

    client = app.test_client()
    passed_tests = 0
    total_tests = 0

    def assert_test(condition, test_name):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f" [PASS] {test_name}")
        else:
            print(f" [FAIL] {test_name}")

    # 1. Database Connectivity & Schema Verification
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]

        cursor.execute("DESCRIBE prediction_history")
        pred_cols = [c[0].lower() for c in cursor.fetchall()]

        cursor.execute("DESCRIBE iot_telemetry")
        iot_cols = [c[0].lower() for c in cursor.fetchall()]

        cursor.close()
        conn.close()

        schema_ok = (
            "prediction_history" in tables and
            "iot_telemetry" in tables and
            "temperature" not in pred_cols and
            "humidity" not in pred_cols and
            "temperature" not in iot_cols and
            "humidity" not in iot_cols and
            "voltage" in iot_cols and
            "current" in iot_cols and
            "power" in iot_cols
        )
        assert_test(schema_ok, "Database tables & schema (Zero temp/humidity, full PZEM electrical columns)")
    except Exception as e:
        assert_test(False, f"Database connection error: {e}")

    # 2. ML Model & Scaler Loading & Shape
    try:
        import pandas as pd
        feat_df = pd.DataFrame([[12.5, 100.0, 14, 0]], columns=["Energy_Consumption", "Production_Output", "Working_Hour", "Weekend"])
        scaled = scaler.transform(feat_df)
        pred = model.predict(scaled)[0]
        assert_test(pred > 0 and isinstance(pred, (float, np.floating)), f"ML Model inference (4 features: Energy, Production, Hour, Weekend) -> {pred:.2f} kg CO2")
    except Exception as e:
        assert_test(False, f"ML inference error: {e}")

    # 3. Static Pages
    res = client.get("/")
    assert_test(res.status_code == 200 and b"Industrial Carbon" in res.data, "GET / (Home page)")

    res = client.get("/about")
    assert_test(res.status_code == 200 and b"About the System" in res.data, "GET /about (About page)")

    res = client.get("/predict")
    assert_test(res.status_code == 200 and b"Operating Telemetry Input" in res.data, "GET /predict (Predict page)")

    # 4. Form Prediction Route without Temperature and Humidity
    pred_payload = {
        "energy": "14.20",
        "production": "115",
        "hour": "15",
        "weekend": "0"
    }
    res = client.post("/predict_result", data=pred_payload, follow_redirects=True)
    assert_test(res.status_code == 200 and b"Emission Analysis Result" in res.data, "POST /predict_result (Core parameters: Energy=14.20 kWh)")

    # 4b. Low Energy Prediction (1.0 kWh, within new 0.22 - 19.79 kWh AI domain)
    low_pred_payload = {
        "energy": "1.00",
        "production": "15",
        "hour": "11",
        "weekend": "0"
    }
    res_low = client.post("/predict_result", data=low_pred_payload, follow_redirects=True)
    assert_test(res_low.status_code == 200 and b"Random Forest Machine Learning Model" in res_low.data, "POST /predict_result (Low energy: 1.00 kWh processed via AI model)")

    # 4c. Out of Range Protection Warning (0.10 kWh < 0.22 kWh minimum)
    oor_payload = {
        "energy": "0.10",
        "production": "0",
        "hour": "8",
        "weekend": "0"
    }
    res_oor = client.post("/predict_result", data=oor_payload, follow_redirects=True)
    assert_test(res_oor.status_code == 200 and b"validated training range" in res_oor.data, "POST /predict_result (Out-of-range protection: 0.10 kWh triggers warning notice)")

    # 5. History Route
    res = client.get("/history")
    assert_test(res.status_code == 200 and b"Historical Prediction Log" in res.data, "GET /history (Historical records)")

    # 6. Live IoT Telemetry API (Ingestion with PZEM metrics)
    iot_payload = {
        "device_id": "TEST_ESP32_PZEM_NODE",
        "voltage": 232.4,
        "current": 2.50,
        "power": 550.0,
        "energy_kwh": 13.50,
        "frequency": 50.0,
        "power_factor": 0.95,
        "production_count": 110,
        "is_mock": False
    }
    res = client.post("/api/iot/telemetry", json=iot_payload)
    data = res.get_json()
    expected_co2 = round(13.50 * EMISSION_FACTOR, 2)
    assert_test(
        res.status_code == 201 and
        data.get("status") == "success" and
        data.get("calculated_co2") == expected_co2 and
        data.get("machine_status") == "Running" and
        data.get("power") == 550.0,
        f"POST /api/iot/telemetry (Live PZEM-004T payload: P=550W, Status=Running, calculated_co2={expected_co2} kg CO2)"
    )

    record_id = data.get("record_id")

    # 7. Machine Idle Detection via Threshold
    idle_payload = {
        "device_id": "TEST_ESP32_PZEM_NODE",
        "voltage": 230.0,
        "current": 0.04,
        "power": 5.0,  # Below threshold (20W)
        "energy_kwh": 13.51,
        "production_count": 110,
        "is_mock": False
    }
    res = client.post("/api/iot/telemetry", json=idle_payload)
    idle_data = res.get_json()
    assert_test(
        res.status_code == 201 and idle_data.get("machine_status") == "Idle",
        f"POST /api/iot/telemetry (PZEM P=5W < {MACHINE_POWER_THRESHOLD_WATTS}W threshold -> Status=Idle)"
    )

    # 8. Live IoT Latest Endpoint
    res = client.get("/api/iot/latest")
    latest_data = res.get_json()
    assert_test(
        res.status_code == 200 and
        latest_data.get("device_id") == "TEST_ESP32_PZEM_NODE" and
        latest_data.get("is_online") is True and
        "voltage" in latest_data and
        "power" in latest_data,
        "GET /api/iot/latest (Real-time telemetry, PZEM electrical values & freshness status)"
    )

    # 9. Live IoT History Endpoint
    res = client.get("/api/iot/history")
    hist_data = res.get_json()
    assert_test(
        res.status_code == 200 and
        len(hist_data.get("energies", [])) > 0 and
        len(hist_data.get("powers", [])) > 0,
        "GET /api/iot/history (Trend chart data including energy, power, CO2)"
    )

    # 10. Mock IoT Ingestion Endpoint
    res = client.post("/api/iot/mock", json={"energy_kwh": 15.0, "production_count": 120, "operating_hours": 8.0})
    mock_data = res.get_json()
    assert_test(res.status_code == 200 and mock_data.get("mode") == "mock_testing", "POST /api/iot/mock (Simulation mode)")

    # 11. Dashboard Route
    res = client.get("/dashboard")
    assert_test(
        res.status_code == 200 and
        b"Current Energy Consumption" in res.data and
        b"Machine Operating Hours" in res.data,
        "GET /dashboard (IoT Dashboard with core telemetry cards and charts)"
    )

    # 12. PDF Generation
    if record_id:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM prediction_history ORDER BY id DESC LIMIT 1")
        latest_pred_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        res = client.get(f"/download-pdf/{latest_pred_id}")
        assert_test(res.status_code == 200 and res.content_type == "application/pdf", f"GET /download-pdf/{latest_pred_id} (Generated PDF certification)")

    print("=" * 70)
    print(f"VERIFICATION SUMMARY: {passed_tests}/{total_tests} tests PASSED ({passed_tests/total_tests*100:.1f}%)")
    print("=" * 70)
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
