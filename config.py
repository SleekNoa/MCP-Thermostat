"""
config.py

Configuration constants for the MCP Thermostat System.
Centralized, well-documented settings for hardware pins, safety parameters, timing,
and MCP server metadata.
"""

# ============================================================
# GPIO PIN ASSIGNMENTS
# ============================================================

# Buttons (active-low with internal pull-up enabled in gpiozero)
GREEN_BUTTON_PIN = 24   # Cycle thermostat mode: OFF → HEAT → COOL → SAFE → OFF
RED_BUTTON_PIN   = 25   # Increase setpoint by +1°F
BLUE_BUTTON_PIN  = 12   # Decrease setpoint by -1°F

# LEDs (PWM capable pins for fading)
RED_LED_PIN  = 18
BLUE_LED_PIN = 23

# LCD Pins (HD44780 16x2 in 4-bit mode)
# Using string format compatible with adafruit_blinka / board module
LCD_RS = "D17"
LCD_E  = "D27"
LCD_D4 = "D5"
LCD_D5 = "D6"
LCD_D6 = "D13"
LCD_D7 = "D26"

LCD_COLUMNS = 16
LCD_ROWS    = 2

# ============================================================
# THERMOSTAT CONFIG
# ============================================================

DEFAULT_SETPOINT_F = 72
SAFE_MODE_WINDOW_F = 5       # ±5°F window used in SAFE mode for environmental safety

DEBUG = False

# Thread timing (seconds)
TEMP_SAMPLE_INTERVAL = 2.0   # How often to read temperature and update LEDs
LCD_UPDATE_INTERVAL  = 1.0   # LCD refresh rate (alternates info)
LED_FADE_FREQUENCY   = 1.0   # Not directly used (PWMLED.pulse() handles timing)

# ============================================================
# MCP SERVER CONFIG
# ============================================================

SERVER_NAME    = "mcp-thermostat"
SERVER_VERSION = "1.0.1"     # Bumped for this cleaned version

MCP_INSTRUCTIONS = """
You are interacting with a Raspberry Pi hardware thermostat.
The system has 4 modes: OFF, HEAT, COOL, SAFE.

SAFE mode:
- LED fades BLUE when temperature is within ±5°F of setpoint.
- LED fades RED when outside the window.

Environmental UNSAFE only blocks actuator MCP tools.
The thermostat itself continues normal autonomous operation.
"""

# Environmental safety state names
ENV_SAFE         = "SAFE"
ENV_UNSAFE       = "UNSAFE"
ENV_SENSOR_FAIL  = "SENSOR_FAILURE"

# ============================================================
# THREAD CONTROL
# ============================================================

THREAD_STOP_FLAG = False  # Legacy flag - prefer instance flag in Thermostat class