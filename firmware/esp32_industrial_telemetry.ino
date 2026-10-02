/*
 * =====================================================================================
 * ESP32 Industrial Telemetry Firmware - Industrial Carbon Emission Forecasting
 * =====================================================================================
 *
 * Microcontroller: ESP32 (NodeMCU / ESP32-WROOM-32 / DevKit v1)
 *
 * Final IoT Hardware Setup:
 * 1. Energy Meter: PZEM-004T v3.0 + CT Clamp
 *    - UART Interface: HardwareSerial2 (ESP32 GPIO 16 RX2 <-> PZEM TX, GPIO 17 TX2 <-> PZEM RX)
 *    - Measures: Voltage (V), Current (A), Active Power (W), Energy (kWh), Frequency (Hz), Power Factor
 * 2. Production Counter: IR Proximity Sensor (E18-D80NK / TCRT5000 / Active IR Module)
 *    - Digital Interface: GPIO 18 (Interrupt-driven with 150ms debouncing)
 * 3. Working Hours: Derived entirely from PZEM-004T electrical readings
 *    - When Active Power >= POWER_THRESHOLD_WATTS (default: 20.0W), machine is RUNNING
 *    - When Active Power < POWER_THRESHOLD_WATTS, machine is IDLE / OFF
 *    - NO separate current or working-hours sensor needed!
 * 4. Temperature & Humidity: COMPLETELY REMOVED from hardware and software.
 *
 * Transmission:
 *    - Wi-Fi HTTP POST (JSON) to Flask backend endpoint: /api/iot/telemetry
 *
 * SAFETY NOTICE:
 *    - PZEM-004T connects to high-voltage mains AC (80-260V AC).
 *    - Mains wiring MUST be done with proper isolation, insulated enclosure, and rated terminals.
 *    - The CT coil must clamp around ONLY ONE live conductor (Phase), NOT Phase + Neutral together.
 *    - The low-voltage side of PZEM (VCC, RX, TX, GND) is optically isolated from AC mains.
 *    - Never touch the PZEM high-voltage screw terminals while connected to AC power!
 * =====================================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>      // Requires ArduinoJson v6 or v7 (by Benoit Blanchon)
#include <PZEM004Tv30.h>      // Requires PZEM-004T v3.0 library (by Jakub Mandula / Mandar Joshi)

// =====================================================================================
// 1. CONFIGURATION PARAMETERS (EASY TO MODIFY)
// =====================================================================================

// Wi-Fi Credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";         // <-- Replace with your Wi-Fi SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";     // <-- Replace with your Wi-Fi Password

// Flask Backend Ingestion URL (Use your computer's local LAN IP address, e.g. 192.168.1.100)
const char* BACKEND_URL   = "http://192.168.1.100:5000/api/iot/telemetry";
const char* DEVICE_ID     = "ESP32_FACTORY_01";

// Telemetry Transmit Interval in Milliseconds (5000 ms = 5 seconds)
const unsigned long TRANSMIT_INTERVAL_MS = 5000;

// Hardware Pin Definitions
#define PZEM_RX_PIN           16    // ESP32 RX2 connects to PZEM TX
#define PZEM_TX_PIN           17    // ESP32 TX2 connects to PZEM RX
#define PIN_IR_SENSOR         18    // Digital pin for IR sensor output (interrupt)

// Operational Thresholds
// Active power threshold (Watts) to classify machine as RUNNING vs IDLE
const float POWER_THRESHOLD_WATTS = 20.0;

// Debounce delay (ms) for IR sensor to prevent multi-triggering per single unit
const unsigned long DEBOUNCE_DELAY_MS = 150;

// =====================================================================================
// 2. HARDWARE OBJECTS & STATE VARIABLES
// =====================================================================================

// Initialize PZEM-004T on ESP32 Hardware Serial 2 (Serial2)
PZEM004Tv30 pzem(Serial2, PZEM_RX_PIN, PZEM_TX_PIN);

// Production Counter Variables (volatile for interrupt safety)
volatile unsigned long productionCounter = 0;
volatile unsigned long lastDebounceTime  = 0;

// Machine Working Hours Tracking
unsigned long machineRunStartMs = 0;
unsigned long totalOperatingMs   = 0;
bool isMachineRunning            = false;
unsigned long lastTransmitTime   = 0;

// =====================================================================================
// 3. INTERRUPT SERVICE ROUTINE (ISR) - IR PRODUCTION SENSOR
// =====================================================================================

void IRAM_ATTR onProductDetected() {
    unsigned long currentMs = millis();
    if ((currentMs - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
        productionCounter++;
        lastDebounceTime = currentMs;
    }
}

// =====================================================================================
// 4. SETUP
// =====================================================================================

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n=======================================================");
    Serial.println(" ESP32 Industrial Telemetry Node Starting");
    Serial.println(" Energy (PZEM-004T) | Production (IR) | Working Hours");
    Serial.println("=======================================================");

    // Initialize IR sensor pin with internal pull-up resistor
    pinMode(PIN_IR_SENSOR, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_IR_SENSOR), onProductDetected, FALLING);
    Serial.println("[OK] IR Production Sensor attached on GPIO 18 (Interrupt FALLING)");

    // PZEM serial initialized by library constructor
    Serial.println("[OK] PZEM-004T HardwareSerial2 initialized on GPIO 16 (RX), 17 (TX)");

    // Connect to Wi-Fi
    connectWiFi();

    Serial.println("[OK] Telemetry Node is Ready. Entering main loop...\n");
}

// =====================================================================================
// 5. MAIN LOOP
// =====================================================================================

void loop() {
    // Keep Wi-Fi connection alive
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    // 1. Read PZEM-004T Electrical Telemetry
    float voltage     = pzem.voltage();
    float current     = pzem.current();
    float power       = pzem.power();
    float energyKWh   = pzem.energy();
    float frequency   = pzem.frequency();
    float powerFactor = pzem.pf();

    // Check for reading anomalies or disconnected PZEM sensor
    bool pzemValid = !isnan(voltage) && !isnan(power) && !isnan(energyKWh);

    if (!pzemValid) {
        voltage     = 0.0;
        current     = 0.0;
        power       = 0.0;
        frequency   = 50.0;
        powerFactor = 1.0;
        // Keep last known energy if any
    }

    // 2. Derive Machine Operating Status from PZEM Active Power
    // Machine is RUNNING when power is above threshold; otherwise IDLE
    if (power >= POWER_THRESHOLD_WATTS) {
        if (!isMachineRunning) {
            isMachineRunning = true;
            machineRunStartMs = millis();
            Serial.printf("[STATE CHANGE] Machine turned ON (Power: %.1f W >= %.1f W)\n", power, POWER_THRESHOLD_WATTS);
        }
    } else {
        if (isMachineRunning) {
            totalOperatingMs += (millis() - machineRunStartMs);
            isMachineRunning = false;
            Serial.printf("[STATE CHANGE] Machine turned OFF (Power: %.1f W < %.1f W)\n", power, POWER_THRESHOLD_WATTS);
        }
    }

    // 3. Compute Cumulative Operating Hours
    unsigned long activeMs = totalOperatingMs;
    if (isMachineRunning) {
        activeMs += (millis() - machineRunStartMs);
    }
    float operatingHours = (float)activeMs / 3600000.0;

    // 4. Transmit Telemetry Packet to Flask Backend at Configured Interval
    if (millis() - lastTransmitTime >= TRANSMIT_INTERVAL_MS) {
        lastTransmitTime = millis();

        sendTelemetry(
            voltage,
            current,
            power,
            energyKWh,
            frequency,
            powerFactor,
            productionCounter,
            operatingHours,
            isMachineRunning ? "Running" : "Idle"
        );
    }

    delay(20);
}

// =====================================================================================
// 6. WI-FI CONNECTION HELPER
// =====================================================================================

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.print("[WIFI] Connecting to SSID: ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 25) {
        delay(400);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[OK] Wi-Fi Connected!");
        Serial.print("[WIFI] Assigned ESP32 IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[!] Wi-Fi Connection Timeout. Will retry on next cycle...");
    }
}

// =====================================================================================
// 7. SEND TELEMETRY TO FLASK REST API
// =====================================================================================

void sendTelemetry(float v, float i, float p, float e, float freq, float pf,
                   unsigned long count, float hours, const char* status) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[!] Cannot send telemetry: Wi-Fi offline");
        return;
    }

    HTTPClient http;
    http.begin(BACKEND_URL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(4000);

    // Build JSON Payload
    StaticJsonDocument<384> doc;
    doc["device_id"]        = DEVICE_ID;
    doc["voltage"]          = round(v * 10.0) / 10.0;
    doc["current"]          = round(i * 100.0) / 100.0;
    doc["power"]            = round(p * 10.0) / 10.0;
    doc["energy_kwh"]       = round(e * 100.0) / 100.0;
    doc["frequency"]        = round(freq * 10.0) / 10.0;
    doc["power_factor"]     = round(pf * 100.0) / 100.0;
    doc["production_count"] = count;
    doc["operating_hours"]  = round(hours * 100.0) / 100.0;
    doc["machine_status"]   = status;
    doc["is_mock"]          = false; // Live physical hardware reading

    String jsonString;
    serializeJson(doc, jsonString);

    Serial.print("[TX -> Flask] ");
    Serial.println(jsonString);

    int httpCode = http.POST(jsonString);

    if (httpCode > 0) {
        String resp = http.getString();
        Serial.printf("[RX <- Flask] HTTP %d: %s\n", httpCode, resp.c_str());
    } else {
        Serial.printf("[!] HTTP POST Failed: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
}
