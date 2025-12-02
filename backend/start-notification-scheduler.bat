@echo off
REM Start Public Item Notification Scheduler for TraceBack
echo Starting TraceBack Public Item Notification Scheduler...
echo.

cd /d "%~dp0"

REM Check if Python is available
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
echo TraceBack Notification Scheduler
echo ========================================
echo.
echo This will check for newly public items every hour
echo and send email notifications to all users.
echo.
echo Press Ctrl+C to stop the scheduler
echo.
echo ========================================
echo.

python public_item_notification_scheduler.py

pause
