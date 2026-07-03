# MCP Thermostat

A physical Raspberry Pi thermostat exposed as a modern MCP (Model Context Protocol) server.

Built with FastMCP 3.4.2 and Streamable HTTP transport (July 2026 standard).

## Features

- 4 thermostat modes: **OFF**, **HEAT**, **COOL**, **SAFE**
- Real hardware control (AHT20 sensor, PWM LEDs, 16x2 LCD, physical buttons)
- Environmental safety window (±5°F) with actuator protection
- Full MCP compliance (Tools, Resources, Prompts)
- Works with AnythingLLM, Claude, Cursor, GitHub Copilot, LM Studio, etc.

## Hardware

- Raspberry Pi (tested on Pi 4/5)
- AHT20 Temperature & Humidity Sensor
- PWM Red + Blue LEDs
- 16x2 HD44780 LCD
- 3 buttons (Green, Red, Blue)

## Quick Start

```bash
cd pi-thermostat-mcp
sudo ../.venv/bin/python server.py

Server will listen on http://0.0.0.0:8000
MCP Endpoint

URL: http://your-pi-ip:8000
Transport: streamable-http

```
## Available Tools

```
lcd_print(line1, line2)
lcd_clear()
set_state("off" | "heat" | "cool" | "safe")
increment_setpoint()
decrement_setpoint()
read_temperature()
read_humidity()
self_test()
```


## Resources

```
thermostat://state
thermostat://setpoint
thermostat://temperature_f
thermostat://humidity
thermostat://environment_safety
leds://status
buttons://status
lcd://status
```

## Project Structure

```
textpi-thermostat-mcp/
├── config.py
├── hardware.py
├── thermostat.py
├── resources.py
├── tools.py
├── prompts.py
├── server.py
└── requirements.txt
```

## License
MIT License
Made with <3 for the MCP community.

