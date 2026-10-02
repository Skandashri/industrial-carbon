import mysql.connector

def get_db_connection():
    """Establish and return a MySQL database connection."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="IndustrialCarbonForecasting"
    )

def init_database():
    """Verify, initialize and migrate database tables for IoT & ML forecasting."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify connection
    cursor.execute("SELECT DATABASE();")
    db_name = cursor.fetchone()[0]
    print(f"[OK] Connected Database: {db_name}")

    # 1. Ensure prediction_history table exists (strictly without temperature & humidity)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        energy_consumption FLOAT NOT NULL,
        production_output FLOAT NOT NULL,
        working_hour INT NOT NULL,
        weekend INT NOT NULL,
        predicted_co2 FLOAT NOT NULL,
        prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Check and drop obsolete temperature and humidity columns if they exist from older schema
    cursor.execute("DESCRIBE prediction_history")
    existing_pred_cols = [col[0] for col in cursor.fetchall()]

    if "temperature" in existing_pred_cols:
        print("[MIGRATE] Dropping obsolete 'temperature' column from prediction_history...")
        cursor.execute("ALTER TABLE prediction_history DROP COLUMN temperature")
    if "humidity" in existing_pred_cols:
        print("[MIGRATE] Dropping obsolete 'humidity' column from prediction_history...")
        cursor.execute("ALTER TABLE prediction_history DROP COLUMN humidity")

    # 2. Ensure iot_telemetry table exists for real-time ESP32 PZEM & IR sensor telemetry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS iot_telemetry (
        id INT AUTO_INCREMENT PRIMARY KEY,
        device_id VARCHAR(50) NOT NULL DEFAULT 'ESP32_FACTORY_01',
        voltage FLOAT NOT NULL DEFAULT 0.0,
        current FLOAT NOT NULL DEFAULT 0.0,
        power FLOAT NOT NULL DEFAULT 0.0,
        energy_kwh FLOAT NOT NULL DEFAULT 0.0,
        frequency FLOAT NOT NULL DEFAULT 50.0,
        power_factor FLOAT NOT NULL DEFAULT 1.0,
        production_count INT NOT NULL DEFAULT 0,
        operating_hours FLOAT NOT NULL DEFAULT 0.0,
        machine_status VARCHAR(20) DEFAULT 'Running',
        co2_emission FLOAT NOT NULL,
        forecast_co2 FLOAT NULL DEFAULT NULL,
        is_mock TINYINT(1) DEFAULT 0,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migrate existing iot_telemetry table to add new electrical & ML fields if missing
    cursor.execute("DESCRIBE iot_telemetry")
    existing_iot_cols = [col[0] for col in cursor.fetchall()]

    migrations = [
        ("voltage", "FLOAT NOT NULL DEFAULT 0.0 AFTER device_id"),
        ("current", "FLOAT NOT NULL DEFAULT 0.0 AFTER voltage"),
        ("power", "FLOAT NOT NULL DEFAULT 0.0 AFTER current"),
        ("frequency", "FLOAT NOT NULL DEFAULT 50.0 AFTER energy_kwh"),
        ("power_factor", "FLOAT NOT NULL DEFAULT 1.0 AFTER frequency"),
        ("forecast_co2", "FLOAT NULL DEFAULT NULL AFTER co2_emission"),
    ]

    for col_name, col_def in migrations:
        if col_name not in existing_iot_cols:
            print(f"[MIGRATE] Adding missing column '{col_name}' to iot_telemetry...")
            cursor.execute(f"ALTER TABLE iot_telemetry ADD COLUMN {col_name} {col_def}")

    conn.commit()

    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    print("\nTables in database:")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f" - {t}: {cnt} records")

    cursor.close()
    conn.close()
    print("\n[OK] Database schema initialized and migrated successfully.")

if __name__ == "__main__":
    init_database()