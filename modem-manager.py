#!/usr/bin/env python3
"""
EC200G Modem Internet Connection Manager - Simplified
- Enables internet on modem startup
- Monitors usb0 for IP address
- Re-sends AT command when IP is lost
- Tracks reconnection statistics permanently
"""

import serial
import time
import os
import glob
import subprocess
import sys
import logging
import json
from datetime import datetime

# Configuration
CHECK_INTERVAL = 60  # Check every 60 seconds
RETRY_INTERVAL = 60  # Retry failed commands after 60 seconds
STARTUP_DELAY = 10   # Wait 10 seconds on startup
AT_TIMEOUT = 5       # AT command timeout
LOG_FILE = '/var/log/modem-manager.log'
STATS_FILE = '/var/log/modem-reconnect-stats.json'
RECONNECT_LOG = '/var/log/modem-reconnections.log'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_stats():
    """Load reconnection statistics from file"""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load stats: {e}")
    
    # Return default stats
    return {
        'total_reconnections': 0,
        'last_reconnection': None,
        'first_reconnection': None,
        'startup_time': datetime.now().isoformat()
    }

def save_stats(stats):
    """Save reconnection statistics to file"""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save stats: {e}")

def log_reconnection(reason='no_ip'):
    """Log a successful reconnection event"""
    timestamp = datetime.now().isoformat()
    
    # Load current stats
    stats = load_stats()
    
    # Update stats
    stats['total_reconnections'] += 1
    stats['last_reconnection'] = timestamp
    if stats['first_reconnection'] is None:
        stats['first_reconnection'] = timestamp
    
    # Save updated stats
    save_stats(stats)
    
    # Append to permanent reconnection log
    try:
        with open(RECONNECT_LOG, 'a') as f:
            f.write(f"{timestamp} - Reconnection #{stats['total_reconnections']} - Reason: {reason}\n")
    except Exception as e:
        logger.error(f"Could not write to reconnection log: {e}")
    
    logger.info(f"📊 Reconnection logged - Total count: {stats['total_reconnections']}")
    
    return stats['total_reconnections']

def get_rs485_port():
    """Get the actual ttyUSB device that rs485 symlink points to"""
    try:
        if os.path.exists('/dev/rs485'):
            return os.path.basename(os.path.realpath('/dev/rs485'))
    except Exception as e:
        logger.debug(f"Error getting RS485 port: {e}")
    return None

def find_modem_port():
    """Find the modem AT command port (excludes RS485)"""
    rs485_port = get_rs485_port()
    usb_ports = sorted(glob.glob('/dev/ttyUSB*'))
    
    if not usb_ports:
        logger.warning("No ttyUSB ports found")
        return None
    
    logger.info(f"Scanning {len(usb_ports)} USB serial ports for modem...")
    
    for port in usb_ports:
        port_name = os.path.basename(port)
        
        # Skip RS485 port
        if rs485_port and port_name == rs485_port:
            logger.debug(f"Skipping {port} (RS485)")
            continue
        
        logger.debug(f"Testing {port}...")
        
        # Test if this is a modem port
        if test_at_command(port, 'AT'):
            logger.info(f"Modem found on {port}")
            return port
    
    logger.warning("No modem port found")
    return None

def send_at_command(port, command, timeout=AT_TIMEOUT):
    """Send AT command and return response"""
    try:
        ser = serial.Serial(port, 115200, timeout=timeout)
        time.sleep(0.1)
        
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Send command
        logger.debug(f"Sending: {command}")
        ser.write((command + '\r\n').encode())
        time.sleep(0.5)
        
        # Read response
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        ser.close()
        
        logger.debug(f"Response: {response.strip()}")
        return response
        
    except Exception as e:
        logger.error(f"Error sending AT command to {port}: {e}")
        return None

def test_at_command(port, command):
    """Test if port responds to AT command"""
    response = send_at_command(port, command, timeout=2)
    return response and 'OK' in response

def enable_modem_internet(port, is_recovery=False):
    """Enable internet on modem using AT command"""
    if is_recovery:
        logger.info(f"Re-enabling internet on modem ({port})...")
    else:
        logger.info(f"Enabling internet on modem ({port})...")
    
    response = send_at_command(port, 'AT+QNETDEVCTL=1,1,1', timeout=10)
    
    if response:
        if 'OK' in response:
            if is_recovery:
                logger.info("✓ Modem internet re-enabled successfully")
            else:
                logger.info("✓ Modem internet enabled successfully")
            return True
        elif 'ERROR' in response:
            logger.error(f"✗ Modem returned error: {response.strip()}")
            return False
        else:
            logger.warning(f"⚠ Unexpected response: {response.strip()}")
            return False
    else:
        logger.error("✗ No response from modem")
        return False

def check_interface_exists(interface='usb0'):
    """Check if network interface exists"""
    try:
        result = subprocess.run(
            ['ip', 'link', 'show', interface],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        logger.debug(f"Interface {interface} check failed: {e}")
        return False

def get_interface_ip(interface='usb0'):
    """Get IP address of interface"""
    try:
        result = subprocess.run(
            ['ip', '-4', 'addr', 'show', interface],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse IP address
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('inet '):
                    ip = line.split()[1].split('/')[0]
                    return ip
    except Exception as e:
        logger.debug(f"IP check failed: {e}")
    return None

def main():
    logger.info("="*60)
    logger.info("EC200G Modem Internet Manager Starting...")
    logger.info("="*60)
    
    # Load and display current stats
    stats = load_stats()
    logger.info(f"Reconnection Statistics:")
    logger.info(f"   Total reconnections: {stats['total_reconnections']}")
    if stats['last_reconnection']:
        logger.info(f"   Last reconnection: {stats['last_reconnection']}")
    logger.info(f"   Stats file: {STATS_FILE}")
    logger.info(f"   Reconnection log: {RECONNECT_LOG}")
    
    # Startup delay
    if STARTUP_DELAY > 0:
        logger.info(f"Waiting {STARTUP_DELAY} seconds for modem to initialize...")
        time.sleep(STARTUP_DELAY)
    
    # Find modem port
    modem_port = find_modem_port()
    if not modem_port:
        logger.error("Fatal: Cannot find modem port. Exiting.")
        sys.exit(1)
    
    # Initial setup - enable internet
    logger.info("Initial modem internet setup...")
    success = False
    retry_count = 0
    max_retries = 5
    
    while not success and retry_count < max_retries:
        if retry_count > 0:
            logger.info(f"Retry {retry_count}/{max_retries} after {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)
        
        success = enable_modem_internet(modem_port, is_recovery=False)
        retry_count += 1
    
    if not success:
        logger.error("Fatal: Failed to enable modem internet after retries. Exiting.")
        sys.exit(1)
    
    # Wait for interface to get IP
    logger.info("Waiting 30 seconds for interface to get IP...")
    time.sleep(30)
    
    # Main monitoring loop
    logger.info("Starting connection monitoring loop...")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    
    consecutive_failures = 0
    last_ip = None
    
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            
            logger.info("-" * 40)
            
            # Check if interface exists
            if not check_interface_exists('usb0'):
                logger.warning("✗ Interface usb0 does not exist")
                consecutive_failures += 1
                
                # Try to re-enable modem internet
                logger.info("Attempting to re-enable modem internet...")
                if enable_modem_internet(modem_port, is_recovery=True):
                    logger.info("Waiting 30 seconds for interface...")
                    time.sleep(30)
                    
                    # Check if interface appeared
                    if check_interface_exists('usb0'):
                        # Log successful reconnection
                        count = log_reconnection(reason='interface_missing')
                        logger.info(f"Interface restored (Total reconnections: {count})")
                        consecutive_failures = 0
                    else:
                        logger.warning("Interface still missing after re-enable")
                else:
                    logger.error("Failed to re-enable modem internet")
                    if consecutive_failures >= 3:
                        logger.warning("Multiple failures - re-scanning for modem port...")
                        new_port = find_modem_port()
                        if new_port:
                            modem_port = new_port
                            consecutive_failures = 0
                continue
            
            # Check for IP address
            ip = get_interface_ip('usb0')
            
            if ip:
                if ip != last_ip:
                    logger.info(f"✓ Interface usb0 has IP: {ip}")
                    last_ip = ip
                else:
                    logger.info(f"✓ Connection healthy - IP: {ip}")
                consecutive_failures = 0
            else:
                logger.warning("✗ Interface usb0 has no IP address")
                consecutive_failures += 1
                
                # Re-enable modem internet to get IP
                logger.info("Re-enabling modem internet to restore IP...")
                if enable_modem_internet(modem_port, is_recovery=True):
                    logger.info("Waiting 30 seconds for IP assignment...")
                    time.sleep(30)
                    
                    # Check if we got IP
                    new_ip = get_interface_ip('usb0')
                    if new_ip:
                        # Log successful reconnection
                        count = log_reconnection(reason='no_ip')
                        logger.info(f"✓ IP restored: {new_ip} (Total reconnections: {count})")
                        last_ip = new_ip
                        consecutive_failures = 0
                    else:
                        logger.warning("⚠ Still no IP after re-enabling")
                else:
                    logger.error("Failed to re-enable modem internet")
                    
                    # After 3 failures, try re-scanning for port
                    if consecutive_failures >= 3:
                        logger.warning("Multiple failures - re-scanning for modem port...")
                        new_port = find_modem_port()
                        if new_port:
                            modem_port = new_port
                            consecutive_failures = 0
    
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()