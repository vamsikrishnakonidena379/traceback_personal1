#!/bin/bash
# Start Finder Decision Notification Scheduler for TraceBack

echo "Starting TraceBack Finder Decision Notification Scheduler..."
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
echo "TraceBack Finder Decision Scheduler"
echo "========================================"
echo ""
echo "This will check hourly for items where"
echo "the 3-day competition window has ended"
echo "and notify finders to make decisions."
echo ""
echo "Press Ctrl+C to stop the scheduler"
echo ""
echo "========================================"
echo ""

python3 finder_decision_notification_scheduler.py
