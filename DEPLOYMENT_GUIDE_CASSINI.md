# TracBack Deployment Guide for Cassini Server

## Prerequisites
- Access to Kent State Cassini server
- SSH access configured
- Node.js 18+ and Python 3.8+ installed on server

## Step 1: Configure Environment Variables

### Update Production API URL
Edit `.env.production` and replace with your actual Cassini URL:
```bash
NEXT_PUBLIC_API_URL=https://cassini.cs.kent.edu/~yourusername/api
```

## Step 2: Build Frontend for Production

```bash
# Install dependencies
npm install

# Build optimized production bundle
npm run build

# Test production build locally (optional)
npm start
```

## Step 3: Deploy Backend to Cassini

### Upload Backend Files
```bash
# From your local machine
scp -r backend/ yourusername@cassini.cs.kent.edu:~/traceback/

# SSH into Cassini
ssh yourusername@cassini.cs.kent.edu
cd ~/traceback/backend
```

### Setup Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Backend for Production
Create `backend/config_production.py`:
```python
import os

# Database
DB_PATH = '/home/yourusername/traceback/backend/traceback_100k.db'

# Server Configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000
DEBUG = False

# CORS - Update with your frontend URL
CORS_ORIGINS = [
    'https://cassini.cs.kent.edu/~yourusername',
    'https://your-domain.kent.edu'
]

# Email Configuration (update with production SMTP)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'traceback24@gmail.com',
    'password': os.getenv('EMAIL_PASSWORD'),  # Set via environment variable
    'use_tls': True
}
```

### Setup Systemd Service (Recommended)
Create `/etc/systemd/system/traceback-backend.service`:
```ini
[Unit]
Description=TracBack Backend API
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/traceback/backend
Environment="PATH=/home/yourusername/traceback/backend/venv/bin"
Environment="EMAIL_PASSWORD=your_app_password"
ExecStart=/home/yourusername/traceback/backend/venv/bin/python comprehensive_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable traceback-backend
sudo systemctl start traceback-backend
sudo systemctl status traceback-backend
```

### Alternative: Use Screen Session
```bash
# Start backend in screen
screen -S traceback-backend
cd ~/traceback/backend
source venv/bin/activate
python comprehensive_app.py

# Detach: Ctrl+A, then D
# Reattach: screen -r traceback-backend
```

## Step 4: Setup Notification Schedulers

### Create scheduler services
```bash
# Public item notification scheduler
sudo systemctl enable traceback-public-scheduler
sudo systemctl start traceback-public-scheduler

# Finder decision notification scheduler
sudo systemctl enable traceback-finder-scheduler
sudo systemctl start traceback-finder-scheduler
```

Or use cron:
```bash
crontab -e
# Add these lines:
0 * * * * cd ~/traceback/backend && venv/bin/python public_item_notification_scheduler.py
0 * * * * cd ~/traceback/backend && venv/bin/python finder_decision_notification_scheduler.py
```

## Step 5: Deploy Frontend to Cassini

### Upload Built Files
```bash
# Copy the production build
scp -r .next/ static/ public/ package.json yourusername@cassini.cs.kent.edu:~/traceback/frontend/
```

### Configure Apache/Nginx Reverse Proxy

#### Apache Configuration (`.htaccess`):
```apache
RewriteEngine On
RewriteBase /~yourusername/

# Proxy API requests to backend
RewriteCond %{REQUEST_URI} ^/~yourusername/api/
RewriteRule ^api/(.*)$ http://localhost:5000/api/$1 [P,L]

# Serve Next.js app
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ http://localhost:3000/$1 [P,L]
```

### Start Next.js Production Server
```bash
cd ~/traceback/frontend
npm install --production
PORT=3000 npm start

# Or with PM2 (recommended):
npm install -g pm2
pm2 start npm --name "traceback-frontend" -- start
pm2 save
pm2 startup
```

## Step 6: Configure Database Permissions

```bash
cd ~/traceback/backend
chmod 644 traceback_100k.db
chmod 755 .
```

## Step 7: Setup Moderator Access

```bash
cd ~/traceback/backend
source venv/bin/activate
python grant_moderator_access.py grant email@kent.edu
```

## Step 8: Test Deployment

1. Visit your frontend URL: `https://cassini.cs.kent.edu/~yourusername`
2. Test login/signup
3. Test report lost/found items
4. Test claim attempts
5. Test messaging system
6. Verify email notifications work

## Troubleshooting

### Backend not accessible
```bash
# Check if backend is running
sudo systemctl status traceback-backend
# Or: ps aux | grep comprehensive_app.py

# Check logs
sudo journalctl -u traceback-backend -f
```

### Frontend shows API errors
```bash
# Verify API_URL is correct
cat .env.production

# Check CORS configuration in backend
# Make sure your frontend URL is in CORS_ORIGINS
```

### Database locked errors
```bash
# Check database permissions
ls -la traceback_100k.db

# Enable WAL mode (already done in code)
sqlite3 traceback_100k.db "PRAGMA journal_mode=WAL;"
```

### Email notifications not working
```bash
# Check email configuration
# Verify EMAIL_PASSWORD environment variable is set
echo $EMAIL_PASSWORD

# Check scheduler logs
tail -f logs/public_notifications.log
tail -f logs/finder_notifications.log
```

## Security Checklist

- [ ] Change database password (if applicable)
- [ ] Update CORS origins to production URLs only
- [ ] Set DEBUG=False in production
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set up firewall rules
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## Monitoring

```bash
# Watch backend logs
tail -f ~/traceback/backend/logs/*.log

# Monitor resource usage
htop

# Check service status
sudo systemctl status traceback-backend
sudo systemctl status traceback-public-scheduler
sudo systemctl status traceback-finder-scheduler
```

## Backup Strategy

```bash
# Daily database backup (add to crontab)
0 2 * * * cp ~/traceback/backend/traceback_100k.db ~/backups/traceback_$(date +\%Y\%m\%d).db
```

## Updates and Maintenance

```bash
# Pull latest code
cd ~/traceback
git pull origin main

# Rebuild frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart traceback-backend
pm2 restart traceback-frontend
```

## Support

For issues, contact the development team or refer to:
- Backend logs: `~/traceback/backend/logs/`
- System logs: `sudo journalctl -u traceback-backend`
- Database location: `~/traceback/backend/traceback_100k.db`
