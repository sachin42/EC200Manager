#!/bin/bash
# Modem Manager Status Monitor
# Shows current status of modem connection

echo "=== EC200G Modem Manager Status ==="
echo ""

# Check if service is running
echo "Service Status:"
if systemctl is-active --quiet modem-manager; then
    echo "  ✓ Service is running"
    UPTIME=$(systemctl show modem-manager --property=ActiveEnterTimestamp --value)
    echo "  Started: $UPTIME"
else
    echo "  ✗ Service is not running"
    echo ""
    echo "Start with: sudo systemctl start modem-manager"
    exit 1
fi
echo ""

# Check modem ports
echo "USB Serial Ports:"
if ls /dev/ttyUSB* &>/dev/null; then
    ls -l /dev/ttyUSB* | awk '{print "  " $NF}'
else
    echo "  ✗ No ttyUSB ports found"
fi
echo ""

# Check network interface
echo "Network Interface (usb0):"
if ip link show usb0 &>/dev/null; then
    echo "  ✓ Interface exists"
    
    # Check if UP
    if ip link show usb0 | grep -q "state UP"; then
        echo "  ✓ Interface is UP"
    else
        echo "  ✗ Interface is DOWN"
    fi
    
    # Check carrier
    if [ -f /sys/class/net/usb0/carrier ]; then
        CARRIER=$(cat /sys/class/net/usb0/carrier 2>/dev/null)
        if [ "$CARRIER" = "1" ]; then
            echo "  ✓ Carrier detected"
        else
            echo "  ✗ No carrier"
        fi
    fi
    
    # Check IP address
    IP=$(ip -4 addr show usb0 2>/dev/null | grep inet | awk '{print $2}')
    if [ -n "$IP" ]; then
        echo "  ✓ IP Address: $IP"
    else
        echo "  ✗ No IP address"
    fi
    
    # Show link details
    echo ""
    echo "  Interface details:"
    ip -br addr show usb0 | sed 's/^/    /'
else
    echo "  ✗ Interface usb0 not found"
fi
echo ""

# Show recent log entries
echo "Recent Activity (last 10 lines):"
if [ -f /var/log/modem-manager.log ]; then
    tail -n 10 /var/log/modem-manager.log | sed 's/^/  /'
else
    # Try journalctl if log file doesn't exist
    journalctl -u modem-manager -n 10 --no-pager | sed 's/^/  /'
fi
echo ""

# Connection test
echo "Quick Connection Test:"
if ip link show usb0 &>/dev/null && [ -n "$IP" ]; then
    # Try to ping gateway
    GATEWAY=$(ip route | grep "default.*usb0" | awk '{print $3}')
    if [ -n "$GATEWAY" ]; then
        echo "  Testing connectivity to gateway $GATEWAY..."
        if ping -c 1 -W 2 -I usb0 $GATEWAY &>/dev/null; then
            echo "  ✓ Gateway reachable"
        else
            echo "  ✗ Gateway unreachable"
        fi
    else
        echo "  ⚠ No default route via usb0"
    fi
else
    echo "  ⚠ Cannot test - interface not ready"
fi
echo ""

echo "==================================="
echo "Commands:"
echo "  View live logs: sudo journalctl -u modem-manager -f"
echo "  Restart service: sudo systemctl restart modem-manager"
echo "  Stop service: sudo systemctl stop modem-manager"
echo "  Full log: tail -f /var/log/modem-manager.log"
