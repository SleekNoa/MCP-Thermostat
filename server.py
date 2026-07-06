#!/usr/bin/env python3
"""
server.py - Modern MCP Thermostat Server (June 2026 compatible)
Uses fastmcp 3.4.2 with Streamable HTTP
"""

import logging
import atexit
import signal
import sys

import anyio
from fastmcp import FastMCP

# Local imports
from config import SERVER_NAME, MCP_INSTRUCTIONS
from thermostat import Thermostat

import resources
import tools
import prompts


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# THERMOSTAT INITIALIZATION
# ------------------------------------------------------------

thermo = Thermostat()
resources.thermostat = thermo


# ------------------------------------------------------------
# MCP SERVER SETUP
# ------------------------------------------------------------

mcp = FastMCP(
    name=SERVER_NAME,
    instructions=MCP_INSTRUCTIONS
)

logger.info(f"{SERVER_NAME} MCP server initialized (fastmcp 3.4.2).")


# ------------------------------------------------------------
# REGISTER RESOURCES
# ------------------------------------------------------------

mcp.resource("thermostat://state")(resources.thermostat_state)
mcp.resource("thermostat://setpoint")(resources.thermostat_setpoint)
mcp.resource("thermostat://temperature_f")(resources.thermostat_temperature_f)
mcp.resource("thermostat://humidity")(resources.thermostat_humidity)
mcp.resource("thermostat://environment_safety")(resources.thermostat_environment_safety)

mcp.resource("leds://status")(resources.leds_status)
mcp.resource("buttons://status")(resources.buttons_status)
mcp.resource("lcd://status")(resources.lcd_status)
mcp.resource("system://info")(resources.system_info)


# ------------------------------------------------------------
# REGISTER TOOLS
# ------------------------------------------------------------

mcp.tool()(tools.lcd_print)
mcp.tool()(tools.lcd_clear)
mcp.tool()(tools.set_state)
mcp.tool()(tools.increment_setpoint)
mcp.tool()(tools.decrement_setpoint)

mcp.tool()(tools.read_temperature)
mcp.tool()(tools.read_humidity)
mcp.tool()(tools.self_test)


# ------------------------------------------------------------
# REGISTER PROMPTS
# ------------------------------------------------------------

mcp.prompt("thermostat_review")(prompts.thermostat_review)


# ------------------------------------------------------------
# CLEAN SHUTDOWN
# ------------------------------------------------------------

def shutdown_handler(*args):
    logger.info("Shutdown signal received...")
    try:
        thermo.shutdown()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    sys.exit(0)

atexit.register(thermo.shutdown)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

if __name__ == "__main__":
    logger.info(f"Starting {SERVER_NAME} on http://0.0.0.0:8000")

    try:
        mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/mcp",
    )
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.exception("Server crashed")
    finally:
        thermo.shutdown()