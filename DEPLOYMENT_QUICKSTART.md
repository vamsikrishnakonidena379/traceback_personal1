# 🚀 TracBack - Cassini Deployment Quick Start

## For Windows Users (EASIEST METHOD)

### Step 1: Run the Deployment Script

Double-click: `deploy_to_cassini.bat`

This will:
1. Ask for your Cassini username
2. Create production configuration
3. Build your frontend
4. Package everything for upload

### Step 2: Upload to Cassini

**Use WinSCP (Easiest):**
1. Download WinSCP: https://winscp.net/eng/download.php
2. Install and open WinSCP
3. Create new connection:
   - File protocol: SFTP
   - Host name: `cassini.cs.kent.edu`
   - Port: 22
   - Username: Your Cassini username
   - Password: Your Cassini password
4. Click "Login"
5. Drag the `deploy_YYYYMMDD_HHMMSS` folder to your home directory (right panel)
6. Rename it to `traceback` on the server

### Step 3: Setup on Server

Open PuTTY or Windows Terminal and connect:

```bash
ssh your-username@cassini.cs.kent.edu
```

Then run these commands:

```bash
# Setup backend
cd ~/traceback/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Start backend (Flask API on port 5000)
nohup python comprehensive_app.py > backend.log 2>&1 &
echo $! > backend.pid

# Setup frontend
cd ~/traceback/frontend
npm install --production

# Start frontend (Next.js on port 3000)
nohup npm start > frontend.log 2>&1 &
echo $! > frontend.pid
```

### Step 4: Configure Apache

Create `.htaccess` file in your home directory:

```bash
cd ~
nano .htaccess
```

Paste this (replace `your-username` with your actual username):

```apache
RewriteEngine On
RewriteBase /~your-username/

# Proxy API requests to Flask backend
RewriteRule ^api/(.*)$ http://localhost:5000/api/$1 [P,L]

# Proxy frontend requests to Next.js
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ http://localhost:3000/$1 [P,L]
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

### Step 5: Access Your App

Visit: `https://cassini.cs.kent.edu/~your-username`

---

## Alternative: Using Git Bash (For Git Users)

If you have Git for Windows installed:

```bash
# Run deployment script
bash deploy_to_cassini.sh

# Upload files
scp -r deploy_YYYYMMDD_HHMMSS your-username@cassini.cs.kent.edu:~/traceback

# Then follow Step 3 and 4 above
```

---

## Verify Your Deployment

### Check if services are running:

```bash
ps aux | grep python | grep comprehensive_app
ps aux | grep node | grep npm
```

You should see both processes running.

### Check logs:

```bash
# Backend logs
tail -f ~/traceback/backend/backend.log

# Frontend logs
tail -f ~/traceback/frontend/frontend.log
```

### Test the application:

Visit your URL and test:
- ✅ Homepage loads
- ✅ Login/Signup works
- ✅ Report lost item
- ✅ Report found item
- ✅ Search functionality
- ✅ Messaging system
- ✅ View matches

---

## Managing Your Deployment

### Stop Services:

```bash
# Stop backend
kill $(cat ~/traceback/backend/backend.pid)

# Stop frontend
kill $(cat ~/traceback/frontend/frontend.pid)
```

### Restart Services:

```bash
# Restart backend
cd ~/traceback/backend
source venv/bin/activate
nohup python comprehensive_app.py > backend.log 2>&1 &
echo $! > backend.pid

# Restart frontend
cd ~/traceback/frontend
nohup npm start > frontend.log 2>&1 &
echo $! > frontend.pid
```

### View Logs in Real-Time:

```bash
# Watch backend logs
tail -f ~/traceback/backend/backend.log

# Watch frontend logs
tail -f ~/traceback/frontend/frontend.log
```

---

## Grant Moderator Access to Team Members

```bash
cd ~/traceback/backend
source venv/bin/activate

# Grant moderator access
python grant_moderator_access.py grant achapala@kent.edu
python grant_moderator_access.py grant bdharav1@kent.edu
python grant_moderator_access.py grant lperam10@kent.edu
python grant_moderator_access.py grant rviswesr@kent.edu
```

---

## Common Issues & Solutions

### Issue: Port already in use

```bash
# Find and kill process using port 5000
lsof -i :5000
kill -9 PID

# Or kill all Python processes
pkill -f comprehensive_app.py
```

### Issue: Frontend not loading

```bash
# Check if Node.js is installed
node --version

# If not, install Node.js on Cassini
# Contact CS IT support for help
```

### Issue: Database errors

```bash
# Check database permissions
cd ~/traceback/backend
ls -la traceback_100k.db

# Set correct permissions
chmod 644 traceback_100k.db
```

### Issue: Cannot connect to server

```bash
# Check SSH connection
ssh your-username@cassini.cs.kent.edu

# If connection fails, check VPN or network
```

---

## Backup Your Database

```bash
# Create backup
cd ~/traceback/backend
cp traceback_100k.db traceback_backup_$(date +%Y%m%d).db

# Download backup to local machine (from your PC)
scp your-username@cassini.cs.kent.edu:~/traceback/backend/traceback_backup_*.db ./
```

---

## Update Your Deployment

### Update Backend Only:

```bash
# On local machine: package backend
# Upload via WinSCP

# On server:
cd ~/traceback/backend
kill $(cat backend.pid)
# Replace files
source venv/bin/activate
nohup python comprehensive_app.py > backend.log 2>&1 &
echo $! > backend.pid
```

### Update Frontend Only:

```bash
# On local machine: build
npm run build

# Upload .next folder via WinSCP

# On server:
cd ~/traceback/frontend
kill $(cat frontend.pid)
nohup npm start > frontend.log 2>&1 &
echo $! > frontend.pid
```

---

## Important Notes

1. **Database Location**: The database (`traceback_100k.db`) stays in `backend/` folder
2. **Logs Location**: Logs are in respective folders (backend.log, frontend.log)
3. **Ports Used**: 
   - Backend: 5000 (Flask)
   - Frontend: 3000 (Next.js)
4. **Public URL**: Apache proxies both to your public URL
5. **Email Configuration**: Already set up with traceback24@gmail.com

---

## Need Help?

1. **Check logs first**: `tail -f ~/traceback/backend/backend.log`
2. **Verify services are running**: `ps aux | grep "python\|node"`
3. **Test backend directly**: `curl http://localhost:5000/api/test`
4. **Contact CS IT**: For Cassini-specific issues

---

## Team Access

Once deployed, share the URL with your team:

**Production URL**: `https://cassini.cs.kent.edu/~your-username`

Team members can:
- Register accounts
- Report lost/found items
- Search and match items
- Message each other
- Review successful returns

**Moderators** (with special access):
- Achyutha Chapala (achapala@kent.edu)
- Bharath Dharavath (bdharav1@kent.edu)
- Lahari Perumalla (lperam10@kent.edu)
- Roopa Vishweshwaraiah (rviswesr@kent.edu)

---

Good luck with your deployment! 🎉
