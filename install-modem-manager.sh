#!/bin/bash
# Install Modem Manager Service

echo "=== EC200G Modem Manager Installation ==="
echo ""

# Copy the Python script to system location
echo "Step 1: Installing modem manager script..."
sudo cp modem-manager.py /usr/local/sbin/modem-manager.py
sudo chmod +x /usr/local/sbin/modem-manager.py
echo "✓ Script installed to /usr/local/sbin/modem-manager.py"

# Copy the stats viewer script
if [ -f "view-reconnect-stats.sh" ]; then
    sudo cp view-reconnect-stats.sh /usr/local/bin/view-reconnect-stats
    sudo chmod +x /usr/local/bin/view-reconnect-stats
    echo "✓ Stats viewer installed to /usr/local/bin/view-reconnect-stats"
fi
echo ""

# Install dependencies
echo "Step 2: Checking dependencies..."
if ! python3 -c "import serial" 2>/dev/null; then
    echo "Installing python3-serial..."
    sudo apt-get update
    sudo apt-get install -y python3-serial
fi

# Optional: Install jq for better stats display
if ! command -v jq &>/dev/null; then
    echo "Installing jq (for stats display)..."
    sudo apt-get install -y jq
fi

echo "✓ Dependencies installed"
echo ""

# Create systemd service
echo "Step 3: Creating systemd service..."
sudo tee /etc/systemd/system/modem-manager.service > /dev/null << 'EOF'
[Unit]
Description=EC200G Modem Internet Connection Manager
After=network.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/sbin/modem-manager.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Run as root (needed for network configuration)
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file created"
echo ""

# Create log rotation config
echo "Step 4: Setting up log rotation..."
sudo tee /etc/logrotate.d/modem-manager > /dev/null << 'EOF'
/var/log/modem-manager.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

echo "✓ Log rotation configured"
echo ""

# Reload systemd and enable service
echo "Step 5: Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable modem-manager.service
echo "✓ Service enabled"
echo ""

echo "==================================="
echo "Installation complete!"
echo ""
echo "Service management commands:"
echo "  Start:   sudo systemctl start modem-manager"
echo "  Stop:    sudo systemctl stop modem-manager"
echo "  Status:  sudo systemctl status modem-manager"
echo "  Logs:    sudo journalctl -u modem-manager -f"
echo "  Log file: tail -f /var/log/modem-manager.log"
echo ""
echo "Reconnection statistics:"
echo "  View stats:  view-reconnect-stats"
echo "  Stats file:  /var/log/modem-reconnect-stats.json"
echo "  Event log:   /var/log/modem-reconnections.log"
echo ""
read -p "Start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start modem-manager
    sleep 2
    echo ""
    echo "Service status:"
    sudo systemctl status modem-manager --no-pager
    echo ""
    echo "Recent logs:"
    sudo journalctl -u modem-manager -n 20 --no-pager
else
    echo "Start manually with: sudo systemctl start modem-manager"
fi