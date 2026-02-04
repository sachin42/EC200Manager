#!/usr/bin/env python3
"""
Modem Manager Configuration
Edit this file to customize behavior
"""

# Timing Configuration
CHECK_INTERVAL = 60      # How often to check connection (seconds)
RETRY_INTERVAL = 60      # Time between retry attempts (seconds)
STARTUP_DELAY = 10       # Wait before starting operations (seconds)
AT_TIMEOUT = 5          # AT command timeout (seconds)

# Network Interface
NETWORK_INTERFACE = 'usb0'  # Interface to monitor

# AT Commands
ENABLE_INTERNET_CMD = 'AT+QNETDEVCTL=1,1,1'  # Command to enable internet
TEST_CMD = 'AT'                               # Command to test modem

# Serial Port Configuration
BAUD_RATE = 115200
SERIAL_TIMEOUT = 5

# Recovery Configuration
MAX_CONSECUTIVE_FAILURES = 3  # Re-scan for modem after this many failures
MAX_INITIAL_RETRIES = 5       # Maximum retries during startup

# DHCP Configuration
DHCP_TIMEOUT = 30       # DHCP request timeout (seconds)
DHCP_RETRY_DELAY = 2    # Delay before checking for IP after DHCP

# Logging
LOG_FILE = '/var/log/modem-manager.log'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR

# Excluded Ports
# Add ports to exclude from modem scanning
EXCLUDED_PORTS = [
    '/dev/rs485',  # RS485 adapter (symlink)
]

# Optional: Specific port to use (leave empty for auto-detection)
MODEM_PORT = ''  # e.g., '/dev/ttyUSB2' or empty for auto-detect
