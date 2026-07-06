"""
tools.py

MCP Tools (Actions) for the Thermostat.

Actuator tools are blocked when environment is UNSAFE.
Diagnostic tools are always allowed.
"""

import logging
from time import sleep

from config import ENV_SAFE, ENV_UNSAFE, ENV_SENSOR_FAIL
import resources

logger = logging.getLogger(__name__)


# ============================================================
# SAFETY DECISION LOGGING
# ============================================================

def log_decision(step: str, input_data, rule: str, action: str, result):
    logger.info(
        f"[SAFETY TRACE] step={step} | input={input_data} | "
        f"rule='{rule}' | action={action} | result={result}"
    )


# ============================================================
# RULE ENFORCEMENT
# ============================================================

def allow_actuator(action_name: str):
    """
    Hybrid safety model:
    - Diagnostics + self_test always allowed
    - Actuator tools blocked only on UNSAFE environment
    """
    if resources.thermostat is None:
        return False, "THERMOSTAT NOT INITIALIZED"

    env = resources.thermostat.environment_state

    # Always-allowed actions
    if action_name in ["read_temperature", "read_humidity", "self_test", "emergency_stop"]:
        log_decision("RULE_CHECK", env, "diagnostic or emergency", action_name, "ALLOWED")
        return True, "ALLOWED"

    # Block actuators in unsafe conditions
    if env in (ENV_UNSAFE, ENV_SENSOR_FAIL):
        log_decision(
            step="RULE_CHECK",
            input_data=env,
            rule="environment safety window violation",
            action=action_name,
            result="DENIED"
        )
        return False, f"DENIED: ENVIRONMENT {env}"

    log_decision("RULE_CHECK", env, "safe environment", action_name, "ALLOWED")
    return True, "ALLOWED"


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

def lcd_print(line1: str, line2: str):
    """Print text to LCD (requires SAFE environment)."""
    allowed, msg = allow_actuator("lcd_print")
    if not allowed:
        return msg

    text = f"{line1[:16]}\n{line2[:16]}"
    resources.thermostat.display.update(text)

    log_decision("LCD_PRINT", (line1, line2), "requires SAFE", "lcd_write", "OK")
    return "LCD UPDATED"


def lcd_clear():
    """Clear the LCD (requires SAFE environment)."""
    allowed, msg = allow_actuator("lcd_clear")
    if not allowed:
        return msg

    resources.thermostat.display.clear()
    log_decision("LCD_CLEAR", None, "requires SAFE", "lcd_clear", "OK")
    return "LCD CLEARED"


def set_state(state: str):
    """Change thermostat mode (requires SAFE environment)."""
    allowed, msg = allow_actuator("set_state")
    if not allowed:
        return msg

    state = state.lower().strip()
    valid_states = ["off", "heat", "cool", "safe"]

    if state not in valid_states:
        return f"Invalid state '{state}'. Must be one of: {valid_states}"

    # Use state machine transition
    getattr(resources.thermostat, state).enter()
    resources.thermostat.update_leds()

    log_decision("SET_STATE", state, "valid + SAFE", "state_change", "OK")
    return f"STATE SET TO {state.upper()}"


def increment_setpoint():
    """Increase setpoint by 1°F (requires SAFE)."""
    allowed, msg = allow_actuator("increment_setpoint")
    if not allowed:
        return msg

    resources.thermostat.setpoint += 1
    resources.thermostat.update_leds()

    log_decision("SETPOINT_INC", resources.thermostat.setpoint, "requires SAFE", "increase", "OK")
    return f"SETPOINT = {resources.thermostat.setpoint}°F"


def decrement_setpoint():
    """Decrease setpoint by 1°F (requires SAFE)."""
    allowed, msg = allow_actuator("decrement_setpoint")
    if not allowed:
        return msg

    resources.thermostat.setpoint -= 1
    resources.thermostat.update_leds()

    log_decision("SETPOINT_DEC", resources.thermostat.setpoint, "requires SAFE", "decrease", "OK")
    return f"SETPOINT = {resources.thermostat.setpoint}°F"


def read_temperature():
    """Diagnostic: always allowed."""
    temp = resources.thermostat.current_temp_f if resources.thermostat else None
    result = None if temp is None else round(temp, 2)
    log_decision("READ_TEMP", None, "diagnostic", "read_temperature", result)
    return result


def read_humidity():
    """Diagnostic: always allowed."""
    if resources.thermostat and resources.thermostat.sensor:
        h = resources.thermostat.sensor.read_humidity()
        result = None if h is None else round(h, 2)
    else:
        result = None
    log_decision("READ_HUMIDITY", None, "diagnostic", "read_humidity", result)
    return result


def self_test():
    """Hardware self-test (always allowed)."""
    try:
        t = read_temperature()
        h = read_humidity()

        resources.thermostat.leds.red_solid()
        sleep(0.3)
        resources.thermostat.leds.off()

        resources.thermostat.leds.blue_solid()
        sleep(0.3)
        resources.thermostat.leds.off()

        resources.thermostat.display.update("SELF TEST\nRUNNING...")
        sleep(1.2)

        resources.thermostat.display.update(f"Temp: {t}F\nHum: {h}%")
        sleep(1.5)

        resources.thermostat.display.update("SELF TEST\nCOMPLETE ✓")
        sleep(1.2)
        resources.thermostat.display.clear()

        log_decision("SELF_TEST", None, "always allowed", "full_hardware_test", "PASS")
        return {"temperature_f": t, "humidity": h, "result": "PASS"}

    except Exception as e:
        logger.exception("Self test failed")
        log_decision("SELF_TEST", None, "error", "full_hardware_test", str(e))
        return {"result": f"FAIL: {e}"}