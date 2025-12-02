#!/bin/bash
# TracBack - Cassini Deployment Script
# This script helps deploy the frontend and backend to Kent State's Cassini server

echo "================================================"
echo "TracBack Deployment Helper for Cassini Server"
echo "================================================"
echo ""

# Step 1: Get user information
echo "Step 1: Cassini Server Information"
echo "-----------------------------------"
read -p "Enter your Cassini username: " CASSINI_USER
read -p "Enter your desired subdirectory (e.g., traceback): " APP_DIR

CASSINI_HOST="cassini.cs.kent.edu"
REMOTE_PATH="/home/$CASSINI_USER/$APP_DIR"
FRONTEND_URL="https://$CASSINI_HOST/~$CASSINI_USER"
BACKEND_URL="$FRONTEND_URL/api"

echo ""
echo "Configuration Summary:"
echo "  Username: $CASSINI_USER"
echo "  Server: $CASSINI_HOST"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Backend API URL: $BACKEND_URL"
echo "  Remote Path: $REMOTE_PATH"
echo ""
read -p "Is this correct? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled. Please run the script again."
    exit 1
fi

# Step 2: Update environment file
echo ""
echo "Step 2: Updating environment configuration..."
echo "---------------------------------------------"
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=$BACKEND_URL
EOF
echo "✓ Created .env.production with API URL: $BACKEND_URL"

# Step 3: Build frontend
echo ""
echo "Step 3: Building frontend for production..."
echo "-------------------------------------------"
read -p "Build frontend now? (yes/no): " BUILD_FRONTEND

if [ "$BUILD_FRONTEND" = "yes" ]; then
    echo "Installing dependencies..."
    npm install
    
    echo "Building Next.js application..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✓ Frontend build successful!"
    else
        echo "✗ Frontend build failed. Please fix errors and try again."
        exit 1
    fi
fi

# Step 4: Create deployment package
echo ""
echo "Step 4: Creating deployment package..."
echo "---------------------------------------"
DEPLOY_DIR="deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p $DEPLOY_DIR

echo "Packaging frontend..."
mkdir -p $DEPLOY_DIR/frontend
cp -r .next $DEPLOY_DIR/frontend/ 2>/dev/null || echo "Warning: .next not found, build frontend first"
cp -r public $DEPLOY_DIR/frontend/ 2>/dev/null
cp package.json $DEPLOY_DIR/frontend/
cp package-lock.json $DEPLOY_DIR/frontend/ 2>/dev/null
cp .env.production $DEPLOY_DIR/frontend/

echo "Packaging backend..."
mkdir -p $DEPLOY_DIR/backend
cp -r backend/* $DEPLOY_DIR/backend/
# Create requirements.txt if not exists
if [ ! -f backend/requirements.txt ]; then
    cat > $DEPLOY_DIR/backend/requirements.txt << 'EOF'
Flask==2.3.3
Flask-CORS==4.0.0
SQLAlchemy==3.0.5
torch==2.0.1
torchvision==0.15.2
sentence-transformers==2.2.2
Pillow==10.0.0
opencv-python==4.8.0.76
pytz==2024.1
schedule==1.2.0
EOF
fi

echo "✓ Deployment package created: $DEPLOY_DIR"

# Step 5: Create server setup script
echo ""
echo "Step 5: Creating server setup script..."
echo "----------------------------------------"
cat > $DEPLOY_DIR/setup_server.sh << 'SETUPSCRIPT'
#!/bin/bash
# Run this script on Cassini server after uploading files

echo "Setting up TracBack on Cassini..."

# Setup backend
cd backend
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setting up database permissions..."
chmod 644 traceback_100k.db 2>/dev/null || echo "Database not found, will be created on first run"
chmod 755 .

# Create startup scripts
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd ~/APPDIR/backend
source venv/bin/activate
nohup python comprehensive_app.py > logs/backend.log 2>&1 &
echo $! > backend.pid
echo "Backend started with PID: $(cat backend.pid)"
EOF

cat > stop_backend.sh << 'EOF'
#!/bin/bash
if [ -f backend.pid ]; then
    kill $(cat backend.pid)
    rm backend.pid
    echo "Backend stopped"
else
    echo "No backend.pid file found"
fi
EOF

chmod +x start_backend.sh stop_backend.sh

# Setup frontend
cd ../frontend
echo "Installing Node.js dependencies..."
npm install --production

# Create frontend startup script
cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd ~/APPDIR/frontend
nohup npm start > logs/frontend.log 2>&1 &
echo $! > frontend.pid
echo "Frontend started with PID: $(cat frontend.pid)"
EOF

cat > stop_frontend.sh << 'EOF'
#!/bin/bash
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid)
    rm frontend.pid
    echo "Frontend stopped"
else
    echo "No frontend.pid file found"
fi
EOF

chmod +x start_frontend.sh stop_frontend.sh

# Create logs directory
mkdir -p logs

echo ""
echo "Setup complete! Next steps:"
echo "1. Start backend: cd backend && ./start_backend.sh"
echo "2. Start frontend: cd frontend && ./start_frontend.sh"
echo "3. Access your app at: https://cassini.cs.kent.edu/~YOURUSERNAME"
echo ""
echo "To stop services:"
echo "  Backend: cd backend && ./stop_backend.sh"
echo "  Frontend: cd frontend && ./stop_frontend.sh"
SETUPSCRIPT

# Replace placeholder
sed -i "s|APPDIR|$APP_DIR|g" $DEPLOY_DIR/setup_server.sh
sed -i "s|YOURUSERNAME|$CASSINI_USER|g" $DEPLOY_DIR/setup_server.sh
chmod +x $DEPLOY_DIR/setup_server.sh

echo "✓ Server setup script created"

# Step 6: Create upload instructions
cat > $DEPLOY_DIR/UPLOAD_INSTRUCTIONS.txt << EOF
================================================
TracBack - Deployment Instructions for Cassini
================================================

1. UPLOAD FILES TO CASSINI
--------------------------
From your local machine, run:

scp -r $DEPLOY_DIR $CASSINI_USER@$CASSINI_HOST:~/$APP_DIR

Or use an SFTP client like FileZilla:
  Host: $CASSINI_HOST
  Username: $CASSINI_USER
  Port: 22
  Upload the entire '$DEPLOY_DIR' folder to your home directory


2. CONNECT TO CASSINI
----------------------
ssh $CASSINI_USER@$CASSINI_HOST


3. RUN SETUP SCRIPT
-------------------
cd ~/$APP_DIR
chmod +x setup_server.sh
./setup_server.sh


4. START SERVICES
-----------------
# Start backend
cd backend
./start_backend.sh

# Start frontend (in a new terminal or after backend)
cd ../frontend
./start_frontend.sh


5. VERIFY DEPLOYMENT
--------------------
Visit: $FRONTEND_URL

Test the following:
- Login/Signup
- Report lost/found items
- Search functionality
- Messaging system


6. CONFIGURE APACHE (if needed)
-------------------------------
Create/edit ~/.htaccess:

RewriteEngine On
RewriteBase /~$CASSINI_USER/

# Proxy API requests to Flask backend
RewriteRule ^api/(.*)$ http://localhost:5000/api/\$1 [P,L]

# Proxy frontend requests to Next.js
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ http://localhost:3000/\$1 [P,L]


7. TROUBLESHOOTING
------------------
View logs:
  Backend: tail -f ~/traceback/backend/logs/backend.log
  Frontend: tail -f ~/traceback/frontend/logs/frontend.log

Check if services are running:
  ps aux | grep python
  ps aux | grep node

Restart services:
  cd backend && ./stop_backend.sh && ./start_backend.sh
  cd frontend && ./stop_frontend.sh && ./start_frontend.sh


8. GRANT MODERATOR ACCESS
--------------------------
cd backend
source venv/bin/activate
python grant_moderator_access.py grant email@kent.edu


For support, contact the development team.
EOF

echo ""
echo "================================================"
echo "Deployment package ready!"
echo "================================================"
echo ""
echo "Package location: $DEPLOY_DIR/"
echo ""
echo "Next steps:"
echo "1. Review: $DEPLOY_DIR/UPLOAD_INSTRUCTIONS.txt"
echo "2. Upload files to Cassini server"
echo "3. SSH to Cassini and run setup_server.sh"
echo ""
echo "Quick upload command:"
echo "  scp -r $DEPLOY_DIR $CASSINI_USER@$CASSINI_HOST:~/"
echo ""
read -p "Press Enter to continue..."
