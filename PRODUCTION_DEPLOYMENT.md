# 🚀 Production Deployment Guide - Cassini Server

## 📋 Pre-Deployment Checklist

### ✅ Dependencies Verified
- [x] `requirements.txt` - All Flask backend dependencies
- [x] `requirements_ml.txt` - All ML/AI dependencies  
- [x] `package.json` - All Next.js frontend dependencies
- [x] `pytz==2024.1` - Added for ET timezone support

### ✅ Recent Critical Updates (December 2, 2025)

1. **Moderator Access Control System** 🔐
   - Fixed security vulnerability: Added database-driven moderator checks
   - Created `grant_moderator_access.py` management tool
   - Protected all moderation endpoints with access control
   - Frontend access denied page for non-moderators

2. **Timezone Standardization** 🕐
   - All timestamps now use ET (Eastern Time) consistently
   - Fixed 72-hour privacy window calculation
   - Added `get_et_now()`, `get_et_now_str()`, `parse_et_datetime()` utilities

3. **Claimed Items Bug Fix** ⏰
   - Fixed "Competition Window Closed" premature display
   - Corrected time remaining calculation (was using parseInt on formatted string)

4. **Dependencies Fixed** 📦
   - ESLint version conflict resolved (downgraded eslint-config-next to 14.2.33)
   - Pillow updated to 10.4.0 (fixed build errors)
   - All ML dependencies installed and verified

---

## 📦 Installation Steps for Cassini Server

### 1. Backend Setup

```bash
# Navigate to backend directory
cd traceback/backend

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements_ml.txt

# Verify installations
python -c "import flask; import pytz; import torch; print('✅ All imports successful')"
```

### 2. Frontend Setup

```bash
# Navigate to project root
cd traceback

# Install Node.js dependencies
npm install

# Build for production
npm run build

# Verify build
npm run start
```

### 3. Database Setup

```bash
cd traceback/backend

# Database file should be present
ls -lh traceback_100k.db

# Grant moderator access to team members
python grant_moderator_access.py grant achapala@kent.edu
python grant_moderator_access.py grant vkoniden@kent.edu
python grant_moderator_access.py grant bdharav1@kent.edu

# Verify moderators
python grant_moderator_access.py list
```

---

## 🔧 Configuration Files to Update

### 1. Backend Configuration (`backend/config.py` or `comprehensive_app.py`)

**Update these settings for production:**

```python
# Change from development to production
app.config['DEBUG'] = False

# Update CORS for production domain
CORS(app, origins=[
    "https://your-domain.com",
    "https://cassini.cs.kent.edu"
])

# Update database path if needed
DB_PATH = '/path/to/production/traceback_100k.db'
```

### 2. Frontend Configuration

**Update API URL in frontend files:**

Search and replace in all frontend files:
- Find: `http://localhost:5000`
- Replace: `https://your-backend-domain.com` or appropriate Cassini URL

**Files to check:**
- `app/**/page.js` (all page components)
- `components/**/*.js` (all components)
- `utils/**/*.js` (all utilities)

### 3. Environment Variables

Create `.env` file in backend:
```bash
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=/path/to/traceback_100k.db
EMAIL_HOST=smtp.gmail.com  # or your email server
EMAIL_PORT=587
```

---

## 🚀 Running in Production

### Option 1: Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run backend with gunicorn
cd traceback/backend
gunicorn -w 4 -b 0.0.0.0:5000 comprehensive_app:app
```

### Option 2: Using systemd Service

Create `/etc/systemd/system/traceback-backend.service`:

```ini
[Unit]
Description=TraceBack Flask Backend
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/traceback/backend
Environment="PATH=/path/to/traceback/backend/venv/bin"
ExecStart=/path/to/traceback/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 comprehensive_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable traceback-backend
sudo systemctl start traceback-backend
sudo systemctl status traceback-backend
```

### Frontend with PM2 (Production Process Manager)

```bash
# Install PM2
npm install -g pm2

# Start Next.js in production
cd traceback
pm2 start npm --name "traceback-frontend" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

---

## 📁 Files & Directories Structure

```
traceback/
├── backend/
│   ├── comprehensive_app.py          # Main Flask application (ET timezone support)
│   ├── requirements.txt              # Flask dependencies (with pytz)
│   ├── requirements_ml.txt           # ML dependencies
│   ├── grant_moderator_access.py     # Moderator management tool
│   ├── traceback_100k.db            # SQLite database
│   ├── email_verification_service.py
│   ├── ml_matching_service.py
│   ├── image_similarity.py
│   └── uploads/                      # User-uploaded images
├── app/                              # Next.js pages
├── components/                       # React components
├── utils/                           # Utility functions
├── package.json                     # Node.js dependencies (fixed)
├── next.config.js
└── tailwind.config.js
```

---

## 🔒 Security Checklist for Production

- [ ] Change `SECRET_KEY` to a secure random string
- [ ] Disable Flask debug mode (`DEBUG = False`)
- [ ] Update CORS to only allow production domain
- [ ] Set up HTTPS/SSL certificates
- [ ] Restrict database file permissions (`chmod 600 traceback_100k.db`)
- [ ] Set up firewall rules (only allow ports 80, 443, SSH)
- [ ] Configure rate limiting for API endpoints
- [ ] Set up backup schedule for database
- [ ] Review and rotate moderator access regularly
- [ ] Enable logging and monitoring

---

## 🔐 Moderator Management (Production)

### Grant Moderator Access
```bash
cd traceback/backend
python grant_moderator_access.py grant email@kent.edu
```

### List All Moderators
```bash
python grant_moderator_access.py list
```

### Revoke Moderator Access
```bash
python grant_moderator_access.py revoke email@kent.edu
```

### List All Users
```bash
python grant_moderator_access.py list-all
```

**Current Moderators:**
- achapala@kent.edu ✅

---

## 📊 Database Backup Strategy

```bash
# Create backup directory
mkdir -p /path/to/backups

# Backup database daily
sqlite3 traceback_100k.db ".backup '/path/to/backups/traceback_$(date +%Y%m%d).db'"

# Create cron job for daily backups
crontab -e
# Add: 0 2 * * * sqlite3 /path/to/traceback/backend/traceback_100k.db ".backup '/path/to/backups/traceback_$(date +\%Y\%m\%d).db'"
```

---

## 🧪 Testing Before Going Live

### Backend Health Check
```bash
curl http://localhost:5000/health
# Expected: {"status": "healthy", "database": "connected"}
```

### Frontend Build Check
```bash
cd traceback
npm run build
# Should complete without errors
```

### Database Check
```bash
cd traceback/backend
sqlite3 traceback_100k.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM found_items; SELECT COUNT(*) FROM lost_items;"
```

### Moderator Check
```bash
python grant_moderator_access.py list
# Should show at least one moderator
```

---

## 📝 Important Notes for Cassini Server

1. **Python Version**: Ensure Python 3.8+ is available
2. **Node.js Version**: Ensure Node.js 18+ is available
3. **Port Configuration**: Check if ports 3000 (frontend) and 5000 (backend) are available
4. **File Permissions**: Ensure upload directory is writable
5. **ML Models**: First run will download ML models (~1GB), ensure sufficient disk space
6. **Timezone**: Server will use ET (America/New_York) timezone consistently

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version

# Check dependencies
pip list | grep -E "flask|pytz|torch"

# Check database permissions
ls -l traceback_100k.db
```

### Frontend build fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Timezone issues
```bash
# Verify pytz is installed
python -c "import pytz; print(pytz.timezone('America/New_York'))"

# Check ET time
python -c "from datetime import datetime; import pytz; print(datetime.now(pytz.timezone('America/New_York')))"
```

### Moderator access not working
```bash
# Check database
sqlite3 traceback_100k.db "SELECT email, full_name, is_moderator FROM users WHERE is_moderator = 1;"

# Re-grant access
python grant_moderator_access.py grant email@kent.edu
```

---

## 📞 Support Contacts

- **Primary**: Akshitha (akshitha1024)
- **Team**: Check team member emails in grant_moderator_access.py

---

## ✅ Deployment Verification Checklist

After deployment, verify:

- [ ] Backend is running and accessible
- [ ] Frontend is running and accessible  
- [ ] Database is accessible and has data
- [ ] At least one moderator account exists
- [ ] Users can sign up and log in
- [ ] Users can report lost items
- [ ] Users can report found items
- [ ] ML matching is working
- [ ] 72-hour privacy window is enforced
- [ ] Claim attempts work
- [ ] Moderation dashboard is accessible (moderators only)
- [ ] All timestamps show in ET timezone
- [ ] Image uploads work
- [ ] Email verification works (if configured)

---

## 🎉 Production Ready!

Once all checks pass, your TraceBack application is ready for production use on Cassini server!

**Last Updated**: December 2, 2025
**Version**: 1.0.0 - Production Ready
