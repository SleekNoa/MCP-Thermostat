"""
hardware.py

Hardware Abstraction Layer for the MCP Thermostat System.

This module is responsible ONLY for interacting with physical hardware:
- AHT20 temperature & humidity sensor (I2C)
- 16x2 HD44780 LCD display
- PWM LEDs (red/blue)
- GPIO buttons
- Environmental safety evaluation

It contains NO thermostat logic.
"""

import logging
from threading import Lock

import board
import busio
import digitalio

import adafruit_ahtx0
import adafruit_character_lcd.character_lcd as characterlcd

from gpiozero import PWMLED, Button

from config import (
    RED_LED_PIN, BLUE_LED_PIN,
    GREEN_BUTTON_PIN, RED_BUTTON_PIN, BLUE_BUTTON_PIN,
    LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7,
    LCD_COLUMNS, LCD_ROWS,
    SAFE_MODE_WINDOW_F,
    ENV_SAFE, ENV_UNSAFE, ENV_SENSOR_FAIL
)

logger = logging.getLogger(__name__)


# ============================================================
# TEMPERATURE SENSOR (AHT20)
# ============================================================

class TemperatureSensor:
    """
    Handles AHT20 temperature + humidity sensor over I2C.
    """

    def __init__(self):
        self.sensor = None
        self.ok = False

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_ahtx0.AHTx0(i2c)
            self.ok = True
            logger.info("AHT20 sensor initialized successfully.")
        except Exception as e:
            logger.error(f"AHT20 initialization failed: {e}")
            self.sensor = None
            self.ok = False

    def read_temp_f(self):
        """Return temperature in Fahrenheit or None if failed."""
        if not self.ok or self.sensor is None:
            return None

        try:
            temp_c = self.sensor.temperature
            return (temp_c * 9.0 / 5.0) + 32.0
        except Exception as e:
            logger.error(f"Temperature read failed: {e}")
            return None

    def read_humidity(self):
        """Return humidity % or None if failed."""
        if not self.ok or self.sensor is None:
            return None

        try:
            return float(self.sensor.relative_humidity)
        except Exception as e:
            logger.error(f"Humidity read failed: {e}")
            return None


# ============================================================
# LCD DISPLAY (THREAD SAFE)
# ============================================================

class ManagedDisplay:
    """
    Thread-safe wrapper for 16x2 HD44780 LCD.
    """

    def __init__(self):
        self.lock = Lock()
        self.lcd = None

        try:
            self.lcd_rs = digitalio.DigitalInOut(getattr(board, LCD_RS))
            self.lcd_en = digitalio.DigitalInOut(getattr(board, LCD_E))
            self.lcd_d4 = digitalio.DigitalInOut(getattr(board, LCD_D4))
            self.lcd_d5 = digitalio.DigitalInOut(getattr(board, LCD_D5))
            self.lcd_d6 = digitalio.DigitalInOut(getattr(board, LCD_D6))
            self.lcd_d7 = digitalio.DigitalInOut(getattr(board, LCD_D7))

            self.lcd = characterlcd.Character_LCD_Mono(
                self.lcd_rs, self.lcd_en,
                self.lcd_d4, self.lcd_d5,
                self.lcd_d6, self.lcd_d7,
                LCD_COLUMNS, LCD_ROWS
            )

            self.lcd.clear()
            logger.info("LCD display initialized.")

        except Exception as e:
            logger.error(f"LCD initialization failed: {e}")
            self.lcd = None

    def update(self, text: str):
        """
        Safe LCD update (2 lines max, 16 chars each).
        """
        if not self.lcd:
            return

        with self.lock:
            try:
                lines = text.split("\n")[:2]
                safe = "\n".join(line[:16] for line in lines)
                self.lcd.clear()
                self.lcd.message = safe
            except Exception as e:
                logger.warning(f"LCD update failed: {e}")

    def clear(self):
        """Clear LCD safely."""
        if not self.lcd:
            return

        with self.lock:
            try:
                self.lcd.clear()
            except Exception:
                pass


# ============================================================
# LED CONTROLLER (PWM)
# ============================================================

class LEDController:
    """
    Controls red/blue PWM LEDs.
    """

    def __init__(self):
        self.red = PWMLED(RED_LED_PIN)
        self.blue = PWMLED(BLUE_LED_PIN)
        logger.info("PWM LEDs initialized.")

    def off(self):
        self.red.off()
        self.blue.off()

    def red_solid(self):
        self.blue.off()
        self.red.value = 1.0

    def blue_solid(self):
        self.red.off()
        self.blue.value = 1.0

    def red_fade(self):
        self.blue.off()
        self.red.pulse()

    def blue_fade(self):
        self.red.off()
        self.blue.pulse()


# ============================================================
# BUTTON PANEL
# ============================================================

class ButtonPanel:
    """
    Physical GPIO buttons (active LOW).
    """

    def __init__(self):
        self.green = Button(GREEN_BUTTON_PIN, pull_up=True) # bounce_time=0.2
        self.red   = Button(RED_BUTTON_PIN,   pull_up=True) # bounce_time=0.2
        self.blue  = Button(BLUE_BUTTON_PIN,  pull_up=True) # bounce_time=0.2

        logger.info("Buttons initialized.")


# ============================================================
# ENVIRONMENT SAFETY
# ============================================================

def evaluate_environment_safety(temp_f, setpoint_f):
    """
    Determines if environment is SAFE or UNSAFE.

    SAFE range = ±SAFE_MODE_WINDOW_F around setpoint.
    """

    if temp_f is None:
        return ENV_SENSOR_FAIL

    low = setpoint_f - SAFE_MODE_WINDOW_F
    high = setpoint_f + SAFE_MODE_WINDOW_F

    return ENV_SAFE if low <= temp_f <= high else ENV_UNSAFE