# TracBack - Simple Cassini Deployment Guide

## Quick Start (3 Easy Steps)

### Step 1: Prepare Files Locally

```bash
# Navigate to your project
cd c:\Capstone_Dec1_12PM\traceback

# Run deployment script (Git Bash on Windows)
bash deploy_to_cassini.sh
```

The script will:
- Ask for your Cassini username
- Create production configuration
- Build your frontend
- Package everything into a deployment folder

### Step 2: Upload to Cassini

**Option A: Using SCP (Recommended)**
```bash
scp -r deploy_YYYYMMDD_HHMMSS your-username@cassini.cs.kent.edu:~/
```

**Option B: Using FileZilla**
1. Open FileZilla
2. Connect to: `cassini.cs.kent.edu`
3. Username: Your Cassini username
4. Password: Your Cassini password
5. Drag the `deploy_YYYYMMDD_HHMMSS` folder to your home directory

### Step 3: Setup on Cassini

```bash
# SSH to Cassini
ssh your-username@cassini.cs.kent.edu

# Go to deployment folder
cd deploy_YYYYMMDD_HHMMSS

# Run setup (takes 5-10 minutes)
chmod +x setup_server.sh
./setup_server.sh

# Start backend
cd backend
./start_backend.sh

# Start frontend
cd ../frontend
./start_frontend.sh
```

Your app is now live at: `https://cassini.cs.kent.edu/~your-username`

---

## Manual Deployment (If Script Doesn't Work)

### 1. Update Environment Configuration

Create `.env.production`:
```env
NEXT_PUBLIC_API_URL=https://cassini.cs.kent.edu/~your-username/api
```

### 2. Build Frontend

```bash
npm install
npm run build
```

### 3. Create Deployment Package

```bash
# Create folder
mkdir cassini_deploy
cd cassini_deploy

# Copy frontend
mkdir frontend
cp -r ../.next frontend/
cp -r ../public frontend/
cp ../package.json frontend/
cp ../.env.production frontend/

# Copy backend
mkdir backend
cp -r ../backend/* backend/
```

### 4. Upload to Cassini

```bash
scp -r cassini_deploy your-username@cassini.cs.kent.edu:~/traceback
```

### 5. Setup Backend on Cassini

```bash
ssh your-username@cassini.cs.kent.edu
cd traceback/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install Flask Flask-CORS SQLAlchemy torch torchvision sentence-transformers Pillow opencv-python pytz schedule

# Start backend
nohup python comprehensive_app.py > backend.log 2>&1 &
echo $! > backend.pid
```

### 6. Setup Frontend on Cassini

```bash
cd ../frontend

# Install dependencies
npm install --production

# Start frontend
nohup npm start > frontend.log 2>&1 &
echo $! > frontend.pid
```

---

## Configuration Files Needed on Cassini

### 1. ~/.htaccess (Apache Configuration)

Create `~/.htaccess` in your home directory:

```apache
RewriteEngine On
RewriteBase /~your-username/

# Proxy API requests to Flask backend (port 5000)
RewriteRule ^api/(.*)$ http://localhost:5000/api/$1 [P,L]

# Proxy frontend requests to Next.js (port 3000)
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ http://localhost:3000/$1 [P,L]
```

Replace `your-username` with your actual Cassini username.

### 2. Backend Environment (if needed)

Create `backend/.env`:
```env
FLASK_ENV=production
DATABASE_PATH=./traceback_100k.db
```

---

## Managing Your Deployment

### Check if Services are Running

```bash
# Check backend
ps aux | grep python | grep comprehensive_app

# Check frontend
ps aux | grep node | grep npm
```

### View Logs

```bash
# Backend logs
tail -f ~/traceback/backend/backend.log

# Frontend logs
tail -f ~/traceback/frontend/frontend.log
```

### Stop Services

```bash
# Stop backend
cd ~/traceback/backend
kill $(cat backend.pid)

# Stop frontend
cd ~/traceback/frontend
kill $(cat frontend.pid)
```

### Restart Services

```bash
# Restart backend
cd ~/traceback/backend
kill $(cat backend.pid)
source venv/bin/activate
nohup python comprehensive_app.py > backend.log 2>&1 &
echo $! > backend.pid

# Restart frontend
cd ~/traceback/frontend
kill $(cat frontend.pid)
nohup npm start > frontend.log 2>&1 &
echo $! > frontend.pid
```

---

## Port Configuration

Your application uses:
- **Backend (Flask)**: Port 5000
- **Frontend (Next.js)**: Port 3000

Apache proxies these through your public URL.

---

## Database Management

### Backup Database

```bash
cd ~/traceback/backend
cp traceback_100k.db traceback_100k_backup_$(date +%Y%m%d).db
```

### Check Database

```bash
cd ~/traceback/backend
sqlite3 traceback_100k.db "SELECT COUNT(*) FROM users;"
```

---

## Granting Moderator Access

```bash
cd ~/traceback/backend
source venv/bin/activate
python grant_moderator_access.py grant email@kent.edu
```

---

## Troubleshooting

### Problem: Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000
# Or
netstat -tulpn | grep 5000

# Kill the process
kill -9 PID
```

### Problem: Cannot Access Website

1. Check if services are running: `ps aux | grep python`
2. Check logs for errors: `tail -f backend.log`
3. Verify Apache configuration: `cat ~/.htaccess`
4. Test backend directly: `curl http://localhost:5000/api/test`

### Problem: Database Locked

```bash
# Check WAL mode
cd ~/traceback/backend
sqlite3 traceback_100k.db "PRAGMA journal_mode;"

# Should return: wal
# If not, set it:
sqlite3 traceback_100k.db "PRAGMA journal_mode=WAL;"
```

### Problem: Python Dependencies Missing

```bash
cd ~/traceback/backend
source venv/bin/activate
pip install -r requirements.txt
```

---

## Security Checklist

- [ ] Change default passwords in database
- [ ] Set proper file permissions: `chmod 644 traceback_100k.db`
- [ ] Keep email credentials secure (don't commit to git)
- [ ] Regularly backup database
- [ ] Monitor logs for suspicious activity
- [ ] Update dependencies periodically

---

## Updating Your Deployment

### Update Backend Code

```bash
# On local machine, build new package
# Upload and replace files
ssh your-username@cassini.cs.kent.edu
cd ~/traceback/backend
./stop_backend.sh
# Replace files
./start_backend.sh
```

### Update Frontend

```bash
# On local machine
npm run build

# Upload .next folder
scp -r .next your-username@cassini.cs.kent.edu:~/traceback/frontend/

# Restart frontend
ssh your-username@cassini.cs.kent.edu
cd ~/traceback/frontend
./stop_frontend.sh
./start_frontend.sh
```

---

## Support

If you encounter issues:

1. Check the logs first
2. Verify all services are running
3. Test components individually (backend, frontend, database)
4. Check Apache/proxy configuration

For Kent State specific issues, contact CS department IT support.

---

## Quick Reference Commands

```bash
# SSH to server
ssh your-username@cassini.cs.kent.edu

# Start everything
cd ~/traceback/backend && ./start_backend.sh
cd ~/traceback/frontend && ./start_frontend.sh

# Stop everything
cd ~/traceback/backend && ./stop_backend.sh
cd ~/traceback/frontend && ./stop_frontend.sh

# View logs
tail -f ~/traceback/backend/backend.log
tail -f ~/traceback/frontend/frontend.log

# Check status
ps aux | grep "python\|node"

# Backup database
cp ~/traceback/backend/traceback_100k.db ~/traceback_backup_$(date +%Y%m%d).db
```
