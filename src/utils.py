"""
Industrial Carbon Forecasting - Common Utilities
Helpers for emission classifications, unit conversions, and threshold checks.
"""

EMISSION_FACTOR = 0.82  # CEA Scope 2 standard (kg CO2 / kWh)
DEFAULT_MACHINE_POWER_THRESHOLD_WATTS = 20.0  # Threshold in Watts to consider machine RUNNING

def get_emission_classification(co2_kg):
    """Classify emission into Low, Medium, or High with actionable directives."""
    val = float(co2_kg)
    if val < 100.0:
        level = "Low"
        measures = [
            "Continue monitoring industrial energy consumption.",
            "Maintain machinery regularly for energy-efficient operation.",
            "Continue using high-efficiency motors and variable frequency drives.",
            "Monitor carbon emissions periodically against baseline."
        ]
    elif val < 300.0:
        level = "Medium"
        measures = [
            "Investigate sub-optimal machine operating loads.",
            "Optimize machine operating hours and idle intervals.",
            "Perform preventive maintenance on high-draw equipment.",
            "Improve production throughput per kilowatt-hour.",
            "Review power factor and harmonic distortion levels.",
            "Schedule heavy processing during off-peak tariff periods."
        ]
    else:
        level = "High"
        measures = [
            "Immediately investigate excessive electrical energy spikes.",
            "Audit machine operating schedules and eliminate prolonged idling.",
            "Perform urgent overhaul of mechanical friction points and cooling.",
            "Consider renewable energy offset (e.g. onsite rooftop solar PV).",
            "Optimize industrial batch scheduling to maximize production efficiency.",
            "Implement automated cutoff for idle machinery."
        ]
    return level, measures

def calculate_co2(energy_kwh):
    """Calculates Scope 2 CO2 in kg from electrical energy in kWh."""
    return round(float(energy_kwh) * EMISSION_FACTOR, 2)

def is_machine_running(power_watts=0.0, current_amps=0.0, threshold_watts=DEFAULT_MACHINE_POWER_THRESHOLD_WATTS):
    """Determines machine ON/OFF status based on PZEM active power or current."""
    if power_watts > 0:
        return power_watts >= threshold_watts
    return current_amps >= 0.15
