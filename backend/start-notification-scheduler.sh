#!/bin/bash
# Start Public Item Notification Scheduler for TraceBack

echo "Starting TraceBack Public Item Notification Scheduler..."
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if database exists
if [ ! -f "traceback_100k.db" ]; then
    echo "ERROR: Database file traceback_100k.db not found"
    echo "Please make sure you're running this from the backend directory"
    exit 1
fi

echo ""
echo "========================================"
echo "TraceBack Notification Scheduler"
echo "========================================"
echo ""
echo "This will check for newly public items every hour"
echo "and send email notifications to all users."
echo ""
echo "Press Ctrl+C to stop the scheduler"
echo ""
echo "========================================"
echo ""

python3 public_item_notification_scheduler.py
