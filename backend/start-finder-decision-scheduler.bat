@echo off
REM Start Finder Decision Notification Scheduler for TraceBack

echo Starting TraceBack Finder Decision Notification Scheduler...
echo.

REM Get the directory where the script is located
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if database exists
if not exist "traceback_100k.db" (
    echo ERROR: Database file traceback_100k.db not found
    echo Please make sure you're running this from the backend directory
    pause
    exit /b 1
)

echo.
echo ========================================
echo TraceBack Finder Decision Scheduler
echo ========================================
echo.
echo This will check hourly for items where
echo the 3-day competition window has ended
echo and notify finders to make decisions.
echo.
echo Press Ctrl+C to stop the scheduler
echo.
echo ========================================
echo.

python finder_decision_notification_scheduler.py

pause
