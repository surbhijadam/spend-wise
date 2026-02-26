# MongoDB Setup for Windows - SpendWise Edition

## Quick Setup (Recommended)

### Step 1: Download MongoDB Community Edition

1. Go to: https://www.mongodb.com/try/download/community
2. Select **Windows** as the OS
3. Select **msi** as the package
4. Click **Download**
5. Run the installer

### Step 2: Run MongoDB Installer

1. Double-click the downloaded `.msi` file
2. Click **Next** through the setup wizard
3. Accept the License Agreement
4. Choose setup type: **Complete** (Recommended)
5. MongoDB will be installed to: `C:\Program Files\MongoDB\Server\<version>`
6. Service Configuration:
   - ✓ Install MongoDB as a Windows Service
   - ✓ Run the MongoDB service as Network Service user
7. Click **Install**
8. Wait for installation to complete
9. Click **Finish**

### Step 3: Verify Installation

Open PowerShell and run:
```powershell
mongod --version
```

You should see MongoDB version information.

## Starting MongoDB

### Method 1: Windows Service (Automatic)
MongoDB should start automatically with Windows. To manually control it:

```powershell
# Start MongoDB
net start MongoDB

# Stop MongoDB
net stop MongoDB

# Or use Services (services.msc) GUI
# Search for "Services" in Windows
# Find "MongoDB" and click "Start" or "Stop"
```

### Method 2: Command Line
```powershell
# Start MongoDB on default port (27017)
mongod

# Start on custom port
mongod --port 27018

# Enable logging
mongod --logpath "C:\data\db\mongod.log"

# Use specific data directory
mongod --dbpath "C:\data\db"
```

### Method 3: MongoDB Compass (GUI)
1. Download MongoDB Compass: https://www.mongodb.com/products/compass
2. Install and open it
3. Click "Connect"
4. MongoDB will start automatically if not running

## Create Data Directory (Optional)

If you get a data directory error:

```powershell
# Create directory structure
New-Item -ItemType Directory -Force -Path "C:\data\db"

# Run MongoDB with custom path
mongod --dbpath "C:\data\db"
```

## Connect to MongoDB

### Option 1: MongoDB Shell (mongosh)

```powershell
# Connect to local MongoDB
mongosh

# Commands in shell
show dbs              # List all databases
use SpendWiseDB      # Select database
show collections      # List collections
db.users.find()       # Query collection
exit                  # Exit shell
```

### Option 2: MongoDB Compass GUI

1. Open MongoDB Compass
2. Click "Connect" (auto-connects to localhost:27017)
3. Browse databases and collections visually

### Option 3: PyMongo (Python)

```python
from pymongo import MongoClient

# Connect
client = MongoClient("mongodb://localhost:27017/")
db = client["SpendWiseDB"]

# Query
users = db["users"].find()
for user in users:
    print(user)
```

## Verify MongoDB is Running

### Using PowerShell
```powershell
# Check if MongoDB process is running
Get-Process mongod

# If running, you'll see:
# Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     Id  ProcessName
#    1234      45    234567     345678       0.12  5678  mongod
```

### Using Port Check
```powershell
# Check if port 27017 is listening
netstat -ano | findstr :27017

# If running, you'll see a line with port 27017
```

### Using mongosh
```powershell
mongosh --eval "db.adminCommand('ping')"

# Success output:
# { ok: 1 }
```

## Troubleshooting

### MongoDB won't start

**Problem**: "mongod is not recognized" in PowerShell

**Solution**:
```powershell
# Add MongoDB to PATH or use full path
& "C:\Program Files\MongoDB\Server\<version>\bin\mongod.exe"

# Or add to Environment Variables:
# 1. Press Win + X, click "System"
# 2. Click "Advanced system settings"
# 3. Click "Environment Variables"
# 4. Add C:\Program Files\MongoDB\Server\<version>\bin to PATH
```

**Problem**: "Port 27017 already in use"

**Solution**:
```powershell
# Find process using port 27017
netstat -ano | findstr :27017

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use different port
mongod --port 27018
```

**Problem**: "Data directory does not exist"

**Solution**:
```powershell
# Create directory
New-Item -ItemType Directory -Force -Path "C:\data\db"

# Run MongoDB
mongod --dbpath "C:\data\db"
```

### Connection refused (Error 10061)

This is the error you're seeing:
```
No connection could be made because the target machine actively refused it
```

**Solution**:
1. MongoDB is not running - start the service:
   ```powershell
   net start MongoDB
   ```
2. Check if running:
   ```powershell
   Get-Process mongod
   ```
3. If not found, start manually:
   ```powershell
   mongod
   ```

### "taskkill" is not recognized

**Solution**:
Use PowerShell instead of Command Prompt, or use full path:
```powershell
# Method 1: Use the services panel
# Press Win + R, type "services.msc", find MongoDB

# Method 2: Use Stop-Process in PowerShell
Stop-Process -Name mongod

# Method 3: Stop the service
net stop MongoDB
```

## For SpendWise Development

### Quick Start Sequence

```powershell
# 1. Start MongoDB service
net start MongoDB

# 2. Verify connection
mongosh --eval "db.adminCommand('ping')"

# 3. Initialize database
cd "d:\Dell2\Documents\SpendWise 2.0"
python init_db.py

# 4. Run SpendWise app
python app.py

# 5. Open browser
# Navigate to http://localhost:5000
```

### Keep MongoDB Running

Add to PowerShell profile to auto-start MongoDB:

1. Open PowerShell as Administrator
2. Create profile if it doesn't exist:
   ```powershell
   if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force }
   ```
3. Edit profile:
   ```powershell
   notepad $PROFILE
   ```
4. Add these lines:
   ```powershell
   # Start MongoDB if not running
   $mongo = Get-Process mongod -ErrorAction SilentlyContinue
   if (-not $mongo) {
       net start MongoDB
       Write-Host "MongoDB service started"
   }
   ```
5. Save and restart PowerShell

## Windows Service Management

### View All MongoDB Services
```powershell
Get-Service | Where-Object {$_.Name -like "*mongo*"}
```

### Restart MongoDB Service
```powershell
Restart-Service MongoDB
```

### Remove MongoDB Service
```powershell
# Only if you want to remove MongoDB
sc delete MongoDB
```

## Advanced: MongoDB Atlas (Cloud)

If you prefer cloud MongoDB instead of local:

1. Go to: https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create a cluster
4. Get connection string
5. Update `.env`:
   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```
6. No need to run local mongod

## Performance Tips

- MongoDB automatically creates a `local` database for replication
- Data stored in: `C:\Program Files\MongoDB\Server\<version>\data\db`
- Logs stored in: `C:\Program Files\MongoDB\Server\<version>\logs`
- Connection pooling in SpendWise optimizes performance
- Indexes automatically created for faster queries

## Next Steps

After MongoDB is running:
1. Run: `python init_db.py` (create database and collections)
2. Run: `python app.py` (start SpendWise application)
3. Open: http://localhost:5000 in your browser
4. Create an account and start tracking expenses!

## Additional Resources

- MongoDB Windows Documentation: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/
- Download MongoDB: https://www.mongodb.com/try/download/community
- MongoDB Compass: https://www.mongodb.com/products/compass
- MongoDB Connection Strings: https://docs.mongodb.com/manual/reference/connection-string/

Happy tracking with SpendWise! 💰
