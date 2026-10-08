from flask import Flask, render_template, request, jsonify, send_file
import joblib
import mysql.connector
import numpy as np
import os
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

import pandas as pd

# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# ============================================================
# MODEL AND SCALER
# Trained strictly on:
# 1. Energy_Consumption (kWh)
# 2. Production_Output (Units)
# 3. Working_Hour (0-23)
# 4. Weekend (0 or 1)
# (Temperature and Humidity completely removed)
# ============================================================

MODEL_PATH = "model/random_forest.pkl"
SCALER_PATH = "model/scaler.pkl"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
FEATURE_NAMES = ["Energy_Consumption", "Production_Output", "Working_Hour", "Weekend"]

def predict_ml_model(energy, production, hour, weekend):
    """Predict CO2 emission using Random Forest with proper feature names."""
    df_feat = pd.DataFrame(
        [[float(energy), float(production), int(hour), int(weekend)]],
        columns=FEATURE_NAMES
    )
    scaled = scaler.transform(df_feat)
    return float(model.predict(scaled)[0])

# Electricity emission factor (CEA Scope 2 standard: 1 kWh = 0.82 kg CO2)
EMISSION_FACTOR = 0.82

# Model training energy range for interpolation
MODEL_ENERGY_MIN = 0.22
MODEL_ENERGY_MAX = 19.79

# Configurable Machine Operating Thresholds (Derived from PZEM-004T)
# When Active Power >= POWER_THRESHOLD_WATTS (or Current >= CURRENT_THRESHOLD_AMPS),
# the machine is classified as RUNNING / ON. Otherwise IDLE / OFF.
MACHINE_POWER_THRESHOLD_WATTS = float(os.getenv("MACHINE_POWER_THRESHOLD_WATTS", "20.0"))
MACHINE_CURRENT_THRESHOLD_AMPS = float(os.getenv("MACHINE_CURRENT_THRESHOLD_AMPS", "0.15"))

# In-memory session tracker for working hours derivation
RUNTIME_TRACKER = {
    "device_id": "ESP32_FACTORY_01",
    "is_running": False,
    "session_start_time": None,
    "total_operating_seconds": 0.0,
    "last_status_change": datetime.now(),
    "last_telemetry_time": None,
    "production_offset": 0
}

# ============================================================
# DATABASE CONNECTION HELPER
# ============================================================

def get_db():
    """Create and return a MySQL connection."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="IndustrialCarbonForecasting"
    )

# ============================================================
# POLLUTION STATUS + PREVENTION MEASURES
# ============================================================

def get_emission_status_and_measures(prediction):
    prediction = float(prediction)

    if prediction < 100:
        pollution_level = "Low"
        prevention_measures = [
            "Continue monitoring industrial energy consumption.",
            "Maintain machines regularly for energy-efficient operation.",
            "Continue using high-efficiency motors and variable frequency drives.",
            "Monitor carbon emissions periodically against baseline."
        ]
    elif prediction < 300:
        pollution_level = "Medium"
        prevention_measures = [
            "Investigate sub-optimal machine operating loads.",
            "Optimize machine operating hours and idle intervals.",
            "Perform preventive maintenance on high-draw equipment.",
            "Improve production throughput per kilowatt-hour.",
            "Review power factor and harmonic distortion levels.",
            "Schedule heavy processing during off-peak tariff periods."
        ]
    else:
        pollution_level = "High"
        prevention_measures = [
            "Immediately investigate excessive electrical energy spikes.",
            "Audit machine operating schedules and eliminate prolonged idling.",
            "Perform urgent overhaul of mechanical friction points and cooling.",
            "Consider renewable energy offset (e.g. onsite rooftop solar PV).",
            "Optimize industrial batch scheduling to maximize production efficiency.",
            "Implement automated cutoff for idle machinery."
        ]

    return pollution_level, prevention_measures

# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")

# ============================================================
# PREDICTION PAGE
# ============================================================

@app.route("/predict")
def predict():
    return render_template("predict.html")

# ============================================================
# PREDICTION PROCESSING (Core parameters only: Energy, Prod, Hour, Weekend)
# ============================================================

@app.route("/predict_result", methods=["POST"])
def predict_result():
    try:
        energy = float(request.form["energy"])
        production = float(request.form["production"])
        hour = int(request.form["hour"])
        weekend = int(request.form["weekend"])

        # Input validation
        if energy <= 0:
            return render_template(
                "predict.html",
                error="Energy consumption must be greater than 0 kWh."
            )

        if production < 0:
            return render_template(
                "predict.html",
                error="Production output cannot be negative."
            )

        if hour < 0 or hour > 23:
            return render_template(
                "predict.html",
                error="Working hour must be between 0 and 23."
            )

        if weekend not in [0, 1]:
            return render_template(
                "predict.html",
                error="Invalid weekend value. Use 0 for No or 1 for Yes."
            )

        # Input vector: [Energy, Production, Working_Hour, Weekend]
        data = np.array([[energy, production, hour, weekend]], dtype=float)

        # Prediction logic
        is_in_range = (MODEL_ENERGY_MIN <= energy <= MODEL_ENERGY_MAX)
        range_warning = None
        if not is_in_range:
            range_warning = f"Energy value is outside the model's validated training range ({MODEL_ENERGY_MIN:.2f} – {MODEL_ENERGY_MAX:.2f} kWh). Prediction may be less reliable."

        if is_in_range:
            prediction = predict_ml_model(energy, production, hour, weekend)
            prediction_method = "Random Forest Machine Learning Model"
            is_ai_prediction = True
        else:
            prediction = float(energy * EMISSION_FACTOR)
            prediction_method = f"Electricity Emission Factor ({EMISSION_FACTOR} kg CO2/kWh)"
            is_ai_prediction = False

        prediction = max(0.0, prediction)
        pollution_level, prevention_measures = get_emission_status_and_measures(prediction)

        # Save to MySQL (temperature & humidity completely removed)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO prediction_history
            (energy_consumption, production_output, working_hour, weekend, predicted_co2)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (energy, production, hour, weekend, prediction)
        )
        conn.commit()
        prediction_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return render_template(
            "predict.html",
            prediction=round(prediction, 2),
            prediction_method=prediction_method,
            pollution_level=pollution_level,
            prevention_measures=prevention_measures,
            prediction_id=prediction_id,
            is_ai_prediction=is_ai_prediction,
            range_warning=range_warning,
            model_energy_min=MODEL_ENERGY_MIN,
            model_energy_max=MODEL_ENERGY_MAX,
            energy=energy,
            production=production,
            hour=hour,
            weekend=weekend
        )

    except ValueError:
        return render_template(
            "predict.html",
            error="Please enter valid numeric values for all fields."
        )
    except Exception as e:
        print("Prediction Error:", e)
        return render_template(
            "predict.html",
            error=f"Prediction Error: {str(e)}"
        )

# ============================================================
# PREDICT AGAIN
# ============================================================

@app.route("/predict-again")
def predict_again():
    return render_template("predict.html")

# ============================================================
# DOWNLOAD PDF CERTIFICATION
# ============================================================

@app.route("/download-pdf/<int:prediction_id>")
def download_pdf(prediction_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                energy_consumption,
                production_output,
                working_hour,
                weekend,
                predicted_co2,
                prediction_time
            FROM prediction_history
            WHERE id = %s
            """,
            (prediction_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result is None:
            return """
            <h2>Prediction Not Found</h2>
            <p>The requested prediction record does not exist.</p>
            <a href="/predict">Back to Prediction</a>
            """

        (
            prediction_id,
            energy,
            production,
            hour,
            weekend,
            predicted_co2,
            prediction_time
        ) = result

        energy_value = float(energy)
        production_value = float(production)
        predicted_co2 = float(predicted_co2)

        pollution_level, prevention_measures = get_emission_status_and_measures(predicted_co2)

        if MODEL_ENERGY_MIN <= energy_value <= MODEL_ENERGY_MAX:
            prediction_method = "Random Forest Machine Learning Model"
        else:
            prediction_method = f"Electricity Emission Factor ({EMISSION_FACTOR} kg CO2/kWh)"

        os.makedirs("reports/predictions", exist_ok=True)
        filename = f"reports/predictions/CO2_Prediction_{prediction_id}.pdf"

        document = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        title_style.alignment = TA_CENTER
        normal_style = styles["Normal"]
        heading_style = styles["Heading2"]

        elements = []
        elements.append(Paragraph("Industrial CO2 Emission Prediction Report", title_style))
        elements.append(Spacer(1, 20))

        record_time = (
            prediction_time.strftime("%d-%m-%Y %H:%M:%S")
            if prediction_time else datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        )

        elements.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", normal_style))
        elements.append(Paragraph(f"<b>Record Timestamp:</b> {record_time}", normal_style))
        elements.append(Paragraph(f"<b>Prediction Record ID:</b> #{prediction_id}", normal_style))
        elements.append(Spacer(1, 15))

        # Core Telemetry Parameters Table
        input_data = [
            ["Parameter", "Observed Value"],
            ["Energy Consumption", f"{energy_value:.2f} kWh"],
            ["Production Count", f"{production_value:.2f} Units"],
            ["Working / Shift Hour", f"{hour:02d}:00 hrs"],
            ["Manufacturing Schedule", "Weekend Operation" if weekend == 1 else "Standard Weekday"]
        ]

        input_table = Table(input_data, colWidths=[240, 210])
        input_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))

        elements.append(Paragraph("Core Telemetry Parameters", heading_style))
        elements.append(Spacer(1, 8))
        elements.append(input_table)
        elements.append(Spacer(1, 20))

        # Result Table
        result_data = [
            ["Forecasted CO2 Emission", f"{predicted_co2:.2f} kg CO2"],
            ["Pollution Classification", pollution_level],
            ["Inference Methodology", prediction_method],
            ["Grid Emission Constant", f"{EMISSION_FACTOR} kg CO2/kWh"]
        ]

        result_table = Table(result_data, colWidths=[240, 210])
        result_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfdf5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#065f46"))
        ]))

        elements.append(Paragraph("Emission Forecast & Analysis", heading_style))
        elements.append(Spacer(1, 8))
        elements.append(result_table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Recommended Mitigation Measures", heading_style))
        elements.append(Spacer(1, 8))
        for measure in prevention_measures:
            elements.append(Paragraph(f"• {measure}", normal_style))
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            "This certification report was generated by the Industrial Carbon Emission Forecasting System. "
            "Telemetry input is evaluated using Scikit-Learn Machine Learning models and Scope 2 emission standards.",
            normal_style
        ))

        document.build(elements)
        return send_file(filename, as_attachment=True)

    except Exception as e:
        print("PDF Error:", e)
        return f"""
        <h2>PDF Generation Error</h2>
        <p>{str(e)}</p>
        <a href="/predict">Back to Prediction</a>
        """

# ============================================================
# HISTORY
# ============================================================

@app.route("/history")
def history():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                energy_consumption,
                production_output,
                working_hour,
                weekend,
                predicted_co2,
                prediction_time
            FROM prediction_history
            ORDER BY id DESC
            """
        )
        predictions = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template(
            "history.html",
            predictions=predictions
        )

    except Exception as e:
        print("History Error:", e)
        return f"""
        <h2>History Retrieval Notice</h2>
        <p>{str(e)}</p>
        <a href="/">Back to Home</a>
        """

# ============================================================
# LIVE IOT REST API (ESP32 + PZEM-004T + IR SENSOR)
# ============================================================

@app.route("/api/iot/telemetry", methods=["POST"])
def receive_iot_telemetry():
    """
    Primary ingestion endpoint for physical ESP32 IoT node.
    Receives PZEM-004T electrical readings and IR production sensor counts.
    Derives machine working hours and operational status from PZEM power/current readings.
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400

        device_id = str(data.get("device_id", "ESP32_FACTORY_01"))

        # PZEM-004T Electrical measurements
        voltage = float(data.get("voltage", 230.0))
        current = float(data.get("current", 0.0))
        power = float(data.get("power", 0.0))
        energy_kwh = float(data.get("energy_kwh", 0.0))
        frequency = float(data.get("frequency", 50.0))
        power_factor = float(data.get("power_factor", 1.0))

        # IR Sensor Production Count
        production_count = int(data.get("production_count", 0))
        is_mock = int(bool(data.get("is_mock", False)))

        now = datetime.now()

        # ----------------------------------------------------
        # Derive Machine Operating Status & Working Hours
        # ----------------------------------------------------
        # Machine is RUNNING if active power >= threshold (or current >= threshold)
        if power > 0:
            machine_is_on = (power >= MACHINE_POWER_THRESHOLD_WATTS)
        elif current > 0:
            machine_is_on = (current >= MACHINE_CURRENT_THRESHOLD_AMPS)
        else:
            # Fallback if reported directly
            machine_is_on = (data.get("machine_status", "Idle").lower() in ["running", "on", "active"])

        machine_status = "Running" if machine_is_on else "Idle"

        # Update in-memory tracker
        global RUNTIME_TRACKER
        if RUNTIME_TRACKER["last_telemetry_time"] is not None:
            elapsed_sec = (now - RUNTIME_TRACKER["last_telemetry_time"]).total_seconds()
            # If interval is realistic (< 120s) and machine was running, accumulate seconds
            if 0 < elapsed_sec < 120 and RUNTIME_TRACKER["is_running"]:
                RUNTIME_TRACKER["total_operating_seconds"] += elapsed_sec

        # State transition tracking
        if machine_is_on != RUNTIME_TRACKER["is_running"]:
            RUNTIME_TRACKER["last_status_change"] = now
            RUNTIME_TRACKER["is_running"] = machine_is_on
            if machine_is_on:
                RUNTIME_TRACKER["session_start_time"] = now
            else:
                RUNTIME_TRACKER["session_start_time"] = None
        elif machine_is_on and RUNTIME_TRACKER["session_start_time"] is None:
            RUNTIME_TRACKER["session_start_time"] = now

        RUNTIME_TRACKER["last_telemetry_time"] = now

        # Use reported operating hours from ESP32 if provided and greater, otherwise use derived
        reported_hours = float(data.get("operating_hours", 0.0))
        derived_hours = round(RUNTIME_TRACKER["total_operating_seconds"] / 3600.0, 3)
        operating_hours = max(reported_hours, derived_hours)

        # ----------------------------------------------------
        # Scope 2 Calculated CO2 (Standard Grid Emission)
        # ----------------------------------------------------
        calculated_co2 = round(energy_kwh * EMISSION_FACTOR, 2)

        # ----------------------------------------------------
        # ML Model Forecast for this industrial state
        # ----------------------------------------------------
        current_hour = now.hour
        current_weekend = 1 if now.weekday() >= 5 else 0

        try:
            forecast_co2 = round(predict_ml_model(energy_kwh, production_count, current_hour, current_weekend), 2)
        except Exception:
            forecast_co2 = calculated_co2

        # ----------------------------------------------------
        # Save to MySQL iot_telemetry table
        # ----------------------------------------------------
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO iot_telemetry
            (device_id, voltage, current, power, energy_kwh, frequency, power_factor,
             production_count, operating_hours, machine_status, co2_emission, forecast_co2, is_mock)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                device_id, voltage, current, power, energy_kwh, frequency, power_factor,
                production_count, operating_hours, machine_status, calculated_co2, forecast_co2, is_mock
            )
        )
        conn.commit()
        record_id = cursor.lastrowid
        cursor.close()
        conn.close()

        pollution_level, _ = get_emission_status_and_measures(calculated_co2)

        # Current session duration in minutes
        session_duration_min = 0.0
        if machine_is_on and RUNTIME_TRACKER["session_start_time"]:
            session_duration_min = round((now - RUNTIME_TRACKER["session_start_time"]).total_seconds() / 60.0, 1)

        energy_per_unit = round(energy_kwh / max(1, production_count), 4)

        return jsonify({
            "status": "success",
            "record_id": record_id,
            "device_id": device_id,
            "voltage": round(voltage, 1),
            "current": round(current, 2),
            "power": round(power, 1),
            "energy_kwh": round(energy_kwh, 2),
            "frequency": round(frequency, 1),
            "power_factor": round(power_factor, 2),
            "production_count": production_count,
            "operating_hours": operating_hours,
            "session_duration_minutes": session_duration_min,
            "machine_status": machine_status,
            "energy_per_unit": energy_per_unit,
            "calculated_co2": calculated_co2,
            "forecast_co2": forecast_co2,
            "pollution_level": pollution_level,
            "is_mock": bool(is_mock),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }), 201

    except Exception as e:
        print("IoT Telemetry Ingestion Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/iot/latest", methods=["GET"])
def get_latest_iot_telemetry():
    """Returns the most recent physical or simulation IoT telemetry reading."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                device_id,
                voltage,
                current,
                power,
                energy_kwh,
                frequency,
                power_factor,
                production_count,
                operating_hours,
                machine_status,
                co2_emission,
                forecast_co2,
                is_mock,
                recorded_at
            FROM iot_telemetry
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({
                "status": "no_data",
                "message": "No IoT telemetry recorded yet.",
                "is_online": False,
                "connection_state": "Standby / Waiting for ESP32",
                "connection_badge": "offline",
                "power_threshold_watts": MACHINE_POWER_THRESHOLD_WATTS
            })

        (
            device_id,
            voltage,
            current,
            power,
            energy_kwh,
            frequency,
            power_factor,
            production_count,
            operating_hours,
            machine_status,
            co2_emission,
            forecast_co2,
            is_mock,
            recorded_at
        ) = row

        now = datetime.now()
        time_diff = (now - recorded_at).total_seconds()
        is_fresh = time_diff <= 90

        if is_fresh:
            if is_mock:
                connection_state = "TEST / SIMULATION MODE"
                connection_badge = "testing"
            else:
                connection_state = "LIVE IoT MODE (ESP32 Connected)"
                connection_badge = "online"
        else:
            connection_state = f"Offline / Last Heard {recorded_at.strftime('%H:%M:%S')}"
            connection_badge = "idle"

        # Session duration
        session_duration_min = 0.0
        if machine_status == "Running" and RUNTIME_TRACKER["session_start_time"]:
            session_duration_min = round((now - RUNTIME_TRACKER["session_start_time"]).total_seconds() / 60.0, 1)

        energy_val = float(energy_kwh or 0.0)
        prod_val = int(production_count or 0)
        energy_per_unit = round(energy_val / max(1, prod_val), 4)

        calculated_co2 = round(float(co2_emission or (energy_val * EMISSION_FACTOR)), 2)
        if forecast_co2 is None:
            try:
                forecast_co2 = round(predict_ml_model(energy_val, prod_val, now.hour, 1 if now.weekday() >= 5 else 0), 2)
            except Exception:
                forecast_co2 = calculated_co2
        else:
            forecast_co2 = round(float(forecast_co2), 2)

        return jsonify({
            "status": "success",
            "device_id": device_id,
            "voltage": round(float(voltage or 0.0), 1),
            "current": round(float(current or 0.0), 2),
            "power": round(float(power or 0.0), 1),
            "energy_kwh": round(energy_val, 2),
            "frequency": round(float(frequency or 50.0), 1),
            "power_factor": round(float(power_factor or 1.0), 2),
            "production_count": prod_val,
            "operating_hours": round(float(operating_hours or 0.0), 2),
            "session_duration_minutes": session_duration_min,
            "machine_status": machine_status or "Idle",
            "energy_per_unit": energy_per_unit,
            "co2_emission": calculated_co2,
            "forecast_co2": forecast_co2,
            "is_mock": bool(is_mock),
            "is_online": is_fresh,
            "connection_state": connection_state,
            "connection_badge": connection_badge,
            "last_received": recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "power_threshold_watts": MACHINE_POWER_THRESHOLD_WATTS,
            "current_threshold_amps": MACHINE_CURRENT_THRESHOLD_AMPS
        })

    except Exception as e:
        print("Latest IoT Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/iot/history", methods=["GET"])
def get_iot_history():
    """Returns recent IoT readings for dashboard charting."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                voltage,
                current,
                power,
                energy_kwh,
                production_count,
                operating_hours,
                co2_emission,
                forecast_co2,
                is_mock,
                recorded_at
            FROM iot_telemetry
            ORDER BY id DESC
            LIMIT 25
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Reverse to chronological order
        rows.reverse()

        labels = [r[10].strftime("%H:%M:%S") for r in rows]
        voltages = [round(float(r[1] or 0.0), 1) for r in rows]
        currents = [round(float(r[2] or 0.0), 2) for r in rows]
        powers = [round(float(r[3] or 0.0), 1) for r in rows]
        energies = [round(float(r[4] or 0.0), 2) for r in rows]
        productions = [int(r[5] or 0) for r in rows]
        operating_hours = [round(float(r[6] or 0.0), 2) for r in rows]
        co2_emissions = [round(float(r[7] or 0.0), 2) for r in rows]
        forecasts = [round(float(r[8] if r[8] is not None else r[7]), 2) for r in rows]

        return jsonify({
            "status": "success",
            "labels": labels,
            "voltages": voltages,
            "currents": currents,
            "powers": powers,
            "energies": energies,
            "productions": productions,
            "operating_hours": operating_hours,
            "co2_emissions": co2_emissions,
            "forecasts": forecasts
        })

    except Exception as e:
        print("IoT History Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/iot/mock", methods=["POST"])
def inject_mock_iot():
    """
    Dedicated test/simulation mode endpoint to test system before physical hardware is attached.
    Sets is_mock=1 explicitly and routes through the standard telemetry processor.
    """
    try:
        data = request.get_json(silent=True) or {}

        # Default realistic simulated industrial readings
        voltage = float(data.get("voltage", 230.5 + (np.random.rand() - 0.5) * 4.0))
        current = float(data.get("current", 2.45 + (np.random.rand() - 0.5) * 0.4))
        power = float(data.get("power", voltage * current * 0.95))
        energy_kwh = float(data.get("energy_kwh", 12.45 + (np.random.rand() - 0.5) * 1.5))
        frequency = float(data.get("frequency", 50.0 + (np.random.rand() - 0.5) * 0.2))
        power_factor = float(data.get("power_factor", 0.95))
        production_count = int(data.get("production_count", 95 + int(np.random.rand() * 10)))
        operating_hours = float(data.get("operating_hours", 4.5))

        # Check threshold
        machine_is_on = (power >= MACHINE_POWER_THRESHOLD_WATTS)
        machine_status = "Running" if machine_is_on else "Idle"

        calculated_co2 = round(energy_kwh * EMISSION_FACTOR, 2)

        now = datetime.now()
        try:
            forecast_co2 = round(predict_ml_model(energy_kwh, production_count, now.hour, 1 if now.weekday() >= 5 else 0), 2)
        except Exception:
            forecast_co2 = calculated_co2

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO iot_telemetry
            (device_id, voltage, current, power, energy_kwh, frequency, power_factor,
             production_count, operating_hours, machine_status, co2_emission, forecast_co2, is_mock)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (
                "MOCK_ESP32_TEST", voltage, current, power, energy_kwh, frequency, power_factor,
                production_count, operating_hours, machine_status, calculated_co2, forecast_co2
            )
        )
        conn.commit()
        record_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "mode": "mock_testing",
            "message": "Simulation telemetry packet logged successfully",
            "record_id": record_id,
            "voltage": round(voltage, 1),
            "current": round(current, 2),
            "power": round(power, 1),
            "energy_kwh": round(energy_kwh, 2),
            "production_count": production_count,
            "operating_hours": round(operating_hours, 2),
            "machine_status": machine_status,
            "calculated_co2": calculated_co2,
            "forecast_co2": forecast_co2
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/iot/reset_production", methods=["POST"])
def reset_production_count():
    """Resets or offsets production count for a new shift or manufacturing batch."""
    try:
        global RUNTIME_TRACKER
        RUNTIME_TRACKER["production_offset"] = 0
        return jsonify({"status": "success", "message": "Production counter reset successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    total_predictions = 0
    avg_co2 = 0.0
    latest_iot = None

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Summary of historical predictions
        cursor.execute("SELECT COUNT(*), COALESCE(AVG(predicted_co2), 0) FROM prediction_history")
        row = cursor.fetchone()
        if row:
            total_predictions = row[0]
            avg_co2 = float(row[1]) if row[1] is not None else 0.0

        # Latest IoT reading
        cursor.execute(
            """
            SELECT
                device_id,
                voltage,
                current,
                power,
                energy_kwh,
                frequency,
                power_factor,
                production_count,
                operating_hours,
                machine_status,
                co2_emission,
                forecast_co2,
                is_mock,
                recorded_at
            FROM iot_telemetry
            ORDER BY id DESC
            LIMIT 1
            """
        )
        iot_row = cursor.fetchone()

        if iot_row:
            time_diff = (datetime.now() - iot_row[13]).total_seconds()
            is_fresh = time_diff <= 90

            energy_val = float(iot_row[4] or 0.0)
            prod_val = int(iot_row[7] or 0)
            energy_per_unit = round(energy_val / max(1, prod_val), 4)

            latest_iot = {
                "device_id": iot_row[0],
                "voltage": round(float(iot_row[1] or 0.0), 1),
                "current": round(float(iot_row[2] or 0.0), 2),
                "power": round(float(iot_row[3] or 0.0), 1),
                "energy_kwh": round(energy_val, 2),
                "frequency": round(float(iot_row[5] or 50.0), 1),
                "power_factor": round(float(iot_row[6] or 1.0), 2),
                "production_count": prod_val,
                "operating_hours": round(float(iot_row[8] or 0.0), 2),
                "machine_status": iot_row[9] or "Idle",
                "energy_per_unit": energy_per_unit,
                "co2_emission": round(float(iot_row[10] or (energy_val * EMISSION_FACTOR)), 2),
                "forecast_co2": round(float(iot_row[11] if iot_row[11] is not None else iot_row[10]), 2),
                "is_mock": bool(iot_row[12]),
                "is_online": is_fresh,
                "recorded_at": iot_row[13].strftime("%Y-%m-%d %H:%M:%S")
            }

        cursor.close()
        conn.close()

    except Exception as e:
        print("Dashboard Query Notice:", e)

    return render_template(
        "dashboard.html",
        total_predictions=total_predictions,
        avg_co2=round(avg_co2, 2),
        latest_iot=latest_iot,
        model_energy_min=MODEL_ENERGY_MIN,
        model_energy_max=MODEL_ENERGY_MAX,
        emission_factor=EMISSION_FACTOR,
        power_threshold_watts=MACHINE_POWER_THRESHOLD_WATTS,
        current_threshold_amps=MACHINE_CURRENT_THRESHOLD_AMPS
    )

# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():
    return render_template("about.html")

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )