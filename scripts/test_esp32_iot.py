"""
ESP32 Telemetry Simulation & Testing Script
Industrial Carbon Forecasting System

This script sends realistic IoT sensor payloads representing:
- PZEM-004T: Voltage (V), Current (A), Active Power (W), Energy (kWh), Frequency (Hz), Power Factor
- IR Sensor: Production Count (units)
- Derived Working Hours: Automatically determined from power/current threshold

Can be run in:
- Simulation Mode: is_mock = True
- Hardware Emulation Mode: is_mock = False
"""

import time
import random
import requests
import sys

API_URL = "http://127.0.0.1:5000/api/iot/telemetry"
DEVICE_ID = "ESP32_FACTORY_01"

def send_telemetry_packet(voltage, current, power, energy_kwh, production_count, frequency=50.0, power_factor=0.95, is_mock=True):
    payload = {
        "device_id": DEVICE_ID,
        "voltage": round(voltage, 1),
        "current": round(current, 2),
        "power": round(power, 1),
        "energy_kwh": round(energy_kwh, 2),
        "frequency": round(frequency, 1),
        "power_factor": round(power_factor, 2),
        "production_count": int(production_count),
        "is_mock": is_mock
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Telemetry accepted! Record #{data.get('record_id')}: "
                  f"V={payload['voltage']}V, I={payload['current']}A, P={payload['power']}W, "
                  f"E={payload['energy_kwh']} kWh, Count={payload['production_count']} -> "
                  f"Status={data.get('machine_status')} | "
                  f"Hours={data.get('operating_hours')}h | "
                  f"CO2={data.get('calculated_co2')} kg (Forecast={data.get('forecast_co2')} kg)")
            return True
        else:
            print(f"[ERR] HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Could not connect to {API_URL}: {e}")
        return False

def run_test_stream(num_packets=5, interval_sec=2, live_mode=False):
    mode_str = "LIVE IoT EMULATION" if live_mode else "SIMULATION / TEST MODE"
    print("=" * 70)
    print(f"Industrial Carbon Forecasting - ESP32 Telemetry Test ({mode_str})")
    print(f"Target Endpoint: {API_URL}")
    print(f"Packets: {num_packets}, Interval: {interval_sec}s, Device: {DEVICE_ID}")
    print("=" * 70)

    base_v = 230.0
    base_i = 2.45
    base_pf = 0.96
    base_energy = 12.10
    base_prod = 100

    successes = 0
    for i in range(1, num_packets + 1):
        v = base_v + random.uniform(-2.5, 2.5)
        # Alternate high load vs idle to test machine status detection
        if i % 4 == 0:
            i_amp = 0.05  # Idle / Standby draw
        else:
            i_amp = base_i + random.uniform(-0.3, 0.5)

        power = v * i_amp * base_pf
        base_energy += (power * (interval_sec / 3600.0) / 1000.0) + 0.01
        base_prod += random.choice([0, 1, 2])

        print(f"\n[Packet {i}/{num_packets}] Transmitting...")
        if send_telemetry_packet(v, i_amp, power, base_energy, base_prod, frequency=50.0, power_factor=base_pf, is_mock=(not live_mode)):
            successes += 1

        if i < num_packets:
            time.sleep(interval_sec)

    print("\n" + "=" * 70)
    print(f"Transmission finished: {successes}/{num_packets} packets successfully ingested.")
    print("=" * 70)
    return successes == num_packets

if __name__ == "__main__":
    count = 3
    is_live = "--live" in sys.argv
    for arg in sys.argv[1:]:
        if arg.isdigit():
            count = int(arg)
    run_test_stream(num_packets=count, interval_sec=1, live_mode=is_live)
