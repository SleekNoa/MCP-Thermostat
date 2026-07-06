"""
prompts.py

MCP Prompts / Instructions for the Thermostat System.

These guide the client AI on safe and correct interaction patterns.
"""

from config import MCP_INSTRUCTIONS


def thermostat_review():
    """
    Main guidance prompt provided to MCP clients.
    """
    return f"""
THERMOSTAT CONTROL GUIDANCE (v1.0.1)

You are controlling a physical Raspberry Pi thermostat with real hardware.

AVAILABLE MODES:
  • OFF   - All LEDs off, no heating/cooling
  • HEAT  - Red LED: fade when temp < setpoint, solid when satisfied
  • COOL  - Blue LED: fade when temp > setpoint, solid when satisfied
  • SAFE  - Blue fade inside ±5°F window, Red fade outside window

BUTTON BEHAVIOR (physical + MCP):
  GREEN = cycle mode (OFF → HEAT → COOL → SAFE → OFF)
  RED   = +1°F setpoint
  BLUE  = -1°F setpoint

ENVIRONMENTAL SAFETY RULES:
  - SAFE WINDOW = ±5°F around current setpoint
  - If environment == UNSAFE or SENSOR_FAILURE:
       → Actuator tools (set_state, lcd_*, increment_*, decrement_*) are BLOCKED
       → Diagnostic tools (temperature, humidity, self_test) remain allowed
  - The thermostat continues running autonomously regardless of MCP safety state.

RECOMMENDED SAFE WORKFLOW:
  1. Always start by reading:
       - thermostat://temperature_f
       - thermostat://environment_safety
       - thermostat://state

  2. If environment == "SAFE":
       → You may use actuator tools
  3. If environment == "UNSAFE":
       → Only read diagnostics
       → Do NOT call LCD, state change, or setpoint tools
       → Wait or inform user

  4. Use self_test() to verify hardware health.

ADDITIONAL SYSTEM INSTRUCTIONS:
{MCP_INSTRUCTIONS}

Be conservative. When in doubt, read environment first.
"""