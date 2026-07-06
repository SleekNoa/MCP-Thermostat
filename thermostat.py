"""
thermostat.py

Core thermostat logic using python-statemachine.
Implements 4 states: OFF, HEAT, COOL, SAFE.

Features:
- Temperature sampling thread
- LCD update thread (alternating display)
- Automatic LED control based on mode + temperature
- Button handling
- Environmental safety integration (does NOT block local operation)
"""

import logging
from config import DEBUG
from threading import Thread
from time import sleep
from datetime import datetime
from math import floor




from statemachine import StateMachine, State

from config import (
    DEFAULT_SETPOINT_F,
    TEMP_SAMPLE_INTERVAL,
    LCD_UPDATE_INTERVAL,
    ENV_SAFE, ENV_UNSAFE, ENV_SENSOR_FAIL
)

from hardware import (
    TemperatureSensor,
    ManagedDisplay,
    LEDController,
    ButtonPanel,
    evaluate_environment_safety
)

logger = logging.getLogger(__name__)


# ============================================================
# THERMOSTAT STATE MACHINE
# ============================================================

class Thermostat(StateMachine):
    """
    4-state thermostat:
    - off   : everything off
    - heat  : red LED (fade when heating needed)
    - cool  : blue LED (fade when cooling needed)
    - safe  : blue/red fade based on ±5°F window
    """

    off = State(initial=True)
    heat = State()
    cool = State()
    safe = State()

    # Cycle through modes
    cycle = (
        off.to(heat) |
        heat.to(cool) |
        cool.to(safe) |
        safe.to(off)
    )

    def __init__(self):
        super().__init__()

        # Hardware
        self.sensor = TemperatureSensor()
        self.display = ManagedDisplay()
        self.leds = LEDController()
        self.buttons = ButtonPanel()

        # State variables
        self.setpoint = DEFAULT_SETPOINT_F
        self.current_temp_f = None
        self.environment_state = ENV_SAFE

        self.stop_threads = False

        # Bind physical buttons
        self._bind_buttons()

        # Start background threads
        self._start_threads()

        logger.info("Thermostat state machine initialized.")

    # ============================================================
    # BUTTON HANDLERS
    # ============================================================

    def _bind_buttons(self):
        """Attach callbacks to physical buttons."""
        self.buttons.green.when_pressed = self.process_cycle
        self.buttons.red.when_pressed   = self.increase_setpoint
        self.buttons.blue.when_pressed  = self.decrease_setpoint

    def process_cycle(self):
        """Cycle through thermostat modes."""
        logger.info("Button: Cycling mode")
        self.cycle()
        self.update_leds()

    def increase_setpoint(self):
        self.setpoint += 1
        logger.info(f"Button: Setpoint increased to {self.setpoint}°F")
        self.update_leds()

    def decrease_setpoint(self):
        self.setpoint -= 1
        logger.info(f"Button: Setpoint decreased to {self.setpoint}°F")
        self.update_leds()

    # ============================================================
    # TEMPERATURE & SAFETY
    # ============================================================

    def update_temperature(self):
        """Read sensor and evaluate environmental safety."""
        self.current_temp_f = self.sensor.read_temp_f()

        if self.current_temp_f is None:
            self.environment_state = ENV_SENSOR_FAIL
        else:
            self.environment_state = evaluate_environment_safety(
                self.current_temp_f, self.setpoint
            )

    # ============================================================
    # LED LOGIC
    # ============================================================

    def update_leds(self):
        """Matches original updateLights() behavior."""

        if self.current_state == self.off:
            self.leds.off()
            return

        if self.current_temp_f is None:
            return

        temp = floor(self.current_temp_f)

        if self.current_state == self.heat:
            if temp < self.setpoint:
                self.leds.red_fade()
            else:
                self.leds.red_solid()

        elif self.current_state == self.cool:
            if temp > self.setpoint:
                self.leds.blue_fade()
            else:
                self.leds.blue_solid()

        elif self.current_state == self.safe:
            low = self.setpoint - 5
            high = self.setpoint + 5

            if low <= temp <= high:
                self.leds.blue_fade()
            else:
                self.leds.red_fade()

    # ============================================================
    # BACKGROUND THREADS
    # ============================================================

    def _lcd_thread(self):
        """LCD thread matching original manageMyDisplay behavior."""

        counter = 1
        alt_counter = 1

        while not self.stop_threads:

            # -----------------------------
            # DEBUG OUTPUT (SAFE)
            # -----------------------------
            if DEBUG:
                print("Processing Display Info...")
                print(f"State: {self.current_state.id}")
                print(f"SetPoint: {self.setpoint}")

                if self.current_temp_f is None:
                    print("Temp: ERR")
                else:
                    print(f"Temp: {floor(self.current_temp_f)}")

            # -----------------------------
            # Line 1: timestamp
            # -----------------------------
            now = datetime.now()
            line1 = now.strftime("%m/%d/%Y %H:%M") + "\n"

            # -----------------------------
            # Line 2: alternating display
            # -----------------------------
            if alt_counter < 6:

                if self.current_temp_f is None:
                    line2 = "Temp: ERR"
                else:
                    temp = floor(self.current_temp_f)
                    line2 = f"Temp: {temp}F"

                alt_counter += 1
                alt_counter += 1  # preserve original quirk

            else:

                state = self.current_state.id.upper()
                line2 = f"{state}, Set: {self.setpoint}F"

                alt_counter += 1

                if alt_counter >= 11:
                    self.update_leds()
                    alt_counter = 1

                alt_counter += 1

                if alt_counter >= 11:
                    self.update_leds()
                    alt_counter = 1

            # -----------------------------
            # Update LCD
            # -----------------------------
            self.display.update(f"{line1}{line2}")

            # -----------------------------
            # periodic refresh logic
            # -----------------------------
            if counter % 30 == 0:
                self.update_leds()
                counter = 1
            else:
                counter += 1

            sleep(LCD_UPDATE_INTERVAL)

    def _temp_thread(self):
        """Temperature sampling + LED update thread."""
        while not self.stop_threads:
            self.update_temperature()
            self.update_leds()
            sleep(TEMP_SAMPLE_INTERVAL)

    def _start_threads(self):
        Thread(target=self._temp_thread, daemon=True).start()
        Thread(target=self._lcd_thread, daemon=True).start()

    # ============================================================
    # CLEANUP
    # ============================================================

    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down thermostat...")
        self.stop_threads = True
        sleep(0.3)  # Give threads time to exit
        self.leds.off()
        self.display.clear()
        logger.info("Thermostat shutdown complete.")