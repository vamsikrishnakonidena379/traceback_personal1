@echo off
REM TracBack - Windows Deployment Preparation Script

echo ================================================
echo TracBack Deployment Preparation for Cassini
echo ================================================
echo.

REM Get user input
set /p CASSINI_USER="Enter your Cassini username: "
set /p APP_DIR="Enter your desired directory name (default: traceback): "
if "%APP_DIR%"=="" set APP_DIR=traceback

set CASSINI_HOST=cassini.cs.kent.edu
set FRONTEND_URL=https://%CASSINI_HOST%/~%CASSINI_USER%
set BACKEND_URL=%FRONTEND_URL%/api

echo.
echo Configuration Summary:
echo   Username: %CASSINI_USER%
echo   Server: %CASSINI_HOST%
echo   Frontend URL: %FRONTEND_URL%
echo   Backend API URL: %BACKEND_URL%
echo   App Directory: %APP_DIR%
echo.
set /p CONFIRM="Is this correct? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo Deployment cancelled.
    pause
    exit /b 1
)

REM Create .env.production
echo.
echo Step 1: Creating production environment file...
echo NEXT_PUBLIC_API_URL=%BACKEND_URL%> .env.production
echo Created .env.production

REM Build frontend
echo.
echo Step 2: Building frontend...
set /p BUILD_NOW="Build frontend now? This will take a few minutes (yes/no): "

if "%BUILD_NOW%"=="yes" (
    echo Installing dependencies...
    call npm install
    
    echo Building Next.js application...
    call npm run build
    
    if errorlevel 1 (
        echo Build failed! Please fix errors and try again.
        pause
        exit /b 1
    )
    echo Build successful!
)

REM Create deployment package
echo.
echo Step 3: Creating deployment package...
set TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set DEPLOY_DIR=deploy_%TIMESTAMP%

mkdir %DEPLOY_DIR%
mkdir %DEPLOY_DIR%\frontend
mkdir %DEPLOY_DIR%\backend

echo Copying frontend files...
if exist .next (
    xcopy /E /I /Y .next %DEPLOY_DIR%\frontend\.next > nul
) else (
    echo WARNING: .next folder not found. Please build frontend first.
)
xcopy /E /I /Y public %DEPLOY_DIR%\frontend\public > nul
copy package.json %DEPLOY_DIR%\frontend\ > nul
copy .env.production %DEPLOY_DIR%\frontend\ > nul
if exist package-lock.json copy package-lock.json %DEPLOY_DIR%\frontend\ > nul
if exist pnpm-lock.yaml copy pnpm-lock.yaml %DEPLOY_DIR%\frontend\ > nul

echo Copying backend files...
xcopy /E /I /Y backend\* %DEPLOY_DIR%\backend\ > nul

REM Create upload instructions
echo Creating upload instructions...
(
echo ================================================
echo TracBack - Upload and Deployment Instructions
echo ================================================
echo.
echo Your deployment package is ready: %DEPLOY_DIR%
echo.
echo ================================================
echo STEP 1: UPLOAD FILES TO CASSINI
echo ================================================
echo.
echo Option A: Using WinSCP ^(Recommended for Windows^)
echo   1. Download WinSCP: https://winscp.net/
echo   2. Connect to: %CASSINI_HOST%
echo   3. Username: %CASSINI_USER%
echo   4. Password: Your Cassini password
echo   5. Drag the '%DEPLOY_DIR%' folder to your home directory
echo   6. Rename it to '%APP_DIR%' on the server
echo.
echo Option B: Using SCP command ^(Git Bash/WSL^)
echo   scp -r %DEPLOY_DIR% %CASSINI_USER%@%CASSINI_HOST%:~/%APP_DIR%
echo.
echo ================================================
echo STEP 2: CONNECT TO CASSINI
echo ================================================
echo.
echo ssh %CASSINI_USER%@%CASSINI_HOST%
echo.
echo ================================================
echo STEP 3: SETUP BACKEND
echo ================================================
echo.
echo cd ~/%APP_DIR%/backend
echo python3 -m venv venv
echo source venv/bin/activate
echo pip install --upgrade pip
echo pip install -r requirements.txt
echo.
echo # Start backend
echo nohup python comprehensive_app.py ^> backend.log 2^>^&1 ^&
echo echo $! ^> backend.pid
echo.
echo ================================================
echo STEP 4: SETUP FRONTEND
echo ================================================
echo.
echo cd ~/%APP_DIR%/frontend
echo npm install --production
echo.
echo # Start frontend
echo nohup npm start ^> frontend.log 2^>^&1 ^&
echo echo $! ^> frontend.pid
echo.
echo ================================================
echo STEP 5: CONFIGURE APACHE
echo ================================================
echo.
echo Create/edit ~/.htaccess file:
echo.
echo RewriteEngine On
echo RewriteBase /~%CASSINI_USER%/
echo.
echo # Proxy API requests to Flask backend
echo RewriteRule ^^api/^(.*^)$ http://localhost:5000/api/$1 [P,L]
echo.
echo # Proxy frontend requests to Next.js
echo RewriteCond %%{REQUEST_FILENAME} !-f
echo RewriteCond %%{REQUEST_FILENAME} !-d
echo RewriteRule ^^^(.*^)$ http://localhost:3000/$1 [P,L]
echo.
echo ================================================
echo STEP 6: VERIFY DEPLOYMENT
echo ================================================
echo.
echo Visit: %FRONTEND_URL%
echo.
echo Test:
echo - Login/Signup
echo - Report lost/found items
echo - Search and matching
echo - Messaging system
echo.
echo ================================================
echo TROUBLESHOOTING
echo ================================================
echo.
echo Check if services are running:
echo   ps aux ^| grep python
echo   ps aux ^| grep node
echo.
echo View logs:
echo   tail -f ~/%APP_DIR%/backend/backend.log
echo   tail -f ~/%APP_DIR%/frontend/frontend.log
echo.
echo Stop services:
echo   kill $^(cat ~/%APP_DIR%/backend/backend.pid^)
echo   kill $^(cat ~/%APP_DIR%/frontend/frontend.pid^)
echo.
echo ================================================
echo GRANT MODERATOR ACCESS
echo ================================================
echo.
echo cd ~/%APP_DIR%/backend
echo source venv/bin/activate
echo python grant_moderator_access.py grant email@kent.edu
echo.
) > %DEPLOY_DIR%\DEPLOYMENT_INSTRUCTIONS.txt

echo.
echo ================================================
echo Deployment Package Ready!
echo ================================================
echo.
echo Package: %DEPLOY_DIR%
echo.
echo Next steps:
echo 1. Read: %DEPLOY_DIR%\DEPLOYMENT_INSTRUCTIONS.txt
echo 2. Upload the '%DEPLOY_DIR%' folder to Cassini
echo 3. Follow the instructions in the file
echo.
echo Opening instructions file...
start notepad %DEPLOY_DIR%\DEPLOYMENT_INSTRUCTIONS.txt
echo.
pause
