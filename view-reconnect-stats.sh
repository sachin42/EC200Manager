#!/bin/bash
# View Modem Reconnection Statistics

STATS_FILE="/var/log/modem-reconnect-stats.json"
RECONNECT_LOG="/var/log/modem-reconnections.log"

echo "=== EC200G Modem Reconnection Statistics ==="
echo ""

# Check if stats file exists
if [ -f "$STATS_FILE" ]; then
    echo "Statistics Summary:"
    echo "-------------------"
    
    # Parse JSON and display
    if command -v jq &>/dev/null; then
        # Use jq if available for pretty printing
        TOTAL=$(jq -r '.total_reconnections' "$STATS_FILE" 2>/dev/null)
        LAST=$(jq -r '.last_reconnection' "$STATS_FILE" 2>/dev/null)
        FIRST=$(jq -r '.first_reconnection' "$STATS_FILE" 2>/dev/null)
        STARTUP=$(jq -r '.startup_time' "$STATS_FILE" 2>/dev/null)
        
        echo "  Total Reconnections: $TOTAL"
        [ "$FIRST" != "null" ] && echo "  First Reconnection:  $FIRST"
        [ "$LAST" != "null" ] && echo "  Last Reconnection:   $LAST"
        [ "$STARTUP" != "null" ] && echo "  Service Started:     $STARTUP"
    else
        # Fallback if jq not available
        cat "$STATS_FILE"
    fi
    
    echo ""
    echo "Stats file: $STATS_FILE"
else
    echo "⚠ No statistics file found yet."
    echo "The file will be created after the first reconnection event."
    echo ""
    echo "Expected location: $STATS_FILE"
fi

echo ""

# Show reconnection log
if [ -f "$RECONNECT_LOG" ]; then
    LINE_COUNT=$(wc -l < "$RECONNECT_LOG")
    echo "Reconnection History ($LINE_COUNT events):"
    echo "-------------------"
    
    if [ $LINE_COUNT -gt 0 ]; then
        if [ $LINE_COUNT -le 20 ]; then
            # Show all if 20 or fewer
            cat "$RECONNECT_LOG"
        else
            # Show first 5 and last 10
            echo "First 5 reconnections:"
            head -n 5 "$RECONNECT_LOG" | sed 's/^/  /'
            echo ""
            echo "... (skipping $((LINE_COUNT - 15)) entries) ..."
            echo ""
            echo "Last 10 reconnections:"
            tail -n 10 "$RECONNECT_LOG" | sed 's/^/  /'
        fi
    fi
    
    echo ""
    echo "Full log: $RECONNECT_LOG"
else
    echo "⚠ No reconnection log found yet."
    echo "The log will be created after the first reconnection event."
    echo ""
    echo "Expected location: $RECONNECT_LOG"
fi

echo ""
echo "==================================="

# Show commands
echo "Commands:"
echo "  View full log:       cat $RECONNECT_LOG"
echo "  Clear statistics:    sudo rm $STATS_FILE $RECONNECT_LOG"
echo "  Service status:      systemctl status modem-manager"
echo "  Live monitoring:     sudo journalctl -u modem-manager -f"