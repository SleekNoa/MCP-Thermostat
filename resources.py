"""
resources.py

MCP Read-Only Resources for the Thermostat.

Provides safe, observable state to MCP clients without side effects.
All resources are registered in server.py.
"""

from datetime import datetime
import logging

from config import (
    SERVER_NAME,
    SERVER_VERSION,
)

from hardware import evaluate_environment_safety

logger = logging.getLogger(__name__)

# Global reference injected by server.py
thermostat = None


# ============================================================
# THERMOSTAT RESOURCES
# ============================================================

def thermostat_state():
    """Current thermostat mode (OFF/HEAT/COOL/SAFE)."""
    if thermostat is None:
        return "UNKNOWN"
    return thermostat.current_state.id.upper()


def thermostat_setpoint():
    """Current temperature setpoint in °F."""
    if thermostat is None:
        return None
    return thermostat.setpoint


def thermostat_temperature_f():
    """Latest temperature reading (rounded)."""
    if thermostat is None or thermostat.current_temp_f is None:
        return None
    return round(float(thermostat.current_temp_f), 2)


def thermostat_humidity():
    """Latest humidity reading (rounded)."""
    if thermostat is None or thermostat.sensor is None:
        return None
    h = thermostat.sensor.read_humidity()
    return None if h is None else round(float(h), 2)


def thermostat_environment_safety():
    """Current environmental safety status."""
    if thermostat is None:
        return "UNKNOWN"
    return thermostat.environment_state


# ============================================================
# LED STATUS
# ============================================================

def leds_status():
    """Return current PWM values of LEDs (0.0 - 1.0)."""
    if thermostat is None or thermostat.leds is None:
        return {"red": 0.0, "blue": 0.0}
    return {
        "red":  float(thermostat.leds.red.value),
        "blue": float(thermostat.leds.blue.value)
    }


# ============================================================
# BUTTON STATUS
# ============================================================

def buttons_status():
    """Current pressed state of physical buttons."""
    if thermostat is None or thermostat.buttons is None:
        return {"green": False, "red": False, "blue": False}
    b = thermostat.buttons
    return {
        "green": b.green.is_pressed,
        "red":   b.red.is_pressed,
        "blue":  b.blue.is_pressed
    }


# ============================================================
# LCD STATUS
# ============================================================

def lcd_status():
    """Return last text shown on LCD (shadow copy fallback)."""
    if thermostat is None or thermostat.display is None or thermostat.display.lcd is None:
        return "LCD UNAVAILABLE"

    try:
        # Try to read current message
        return getattr(thermostat.display.lcd, 'message', "NO BUFFER")
    except Exception as e:
        logger.debug(f"Could not read LCD buffer: {e}")
        # Fallback to last known text if you add a shadow variable later
        return "LCD READ ERROR"


# ============================================================
# SYSTEM INFO
# ============================================================

def system_info():
    """General server metadata."""
    return {
        "server_name": SERVER_NAME,
        "version": SERVER_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_statemachine": "active"
    }