# SpendWise 2.0 - Quick Start Guide

## Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Virtual environment with dependencies installed

## 1. Start MongoDB

### Option A: Windows
MongoDB should be running as a service. If not:
- Open Services (services.msc)
- Find "MongoDB" and click "Start"
- Or open PowerShell as Administrator and run:
  ```powershell
  net start MongoDB
  ```

### Option B: macOS
```bash
brew services start mongodb-community
```

### Option C: Linux
```bash
sudo systemctl start mongod
```

### Option D: Docker
```bash
docker run -d -p 27017:27017 --name spendwise-mongo mongo:latest
```

### Verify MongoDB is Running
```bash
mongosh
# Or use old shell:
mongo
```

## 2. Initialize the Database

Run the database initialization script:
```bash
cd "d:\Dell2\Documents\SpendWise 2.0"
python init_db.py
```

This will:
- Create the SpendWiseDB database
- Create all necessary collections
- Build performance indexes

## 3. Start the SpendWise App

```bash
cd "d:\Dell2\Documents\SpendWise 2.0"
python app.py
```

You should see:
```
✓ MongoDB connected successfully to SpendWiseDB
✓ Database indexes created
✓ Gemini AI client initialized
Starting SpendWise app
...
Running on http://127.0.0.1:5000
```

## 4. Access the Application

Open your browser and go to:
- **http://localhost:5000** - Main app
- **http://127.0.0.1:5000** - Alternative localhost

## Features Available

### User Management
- Sign up at `/signup`
- Login at `/login`
- Logout via `/logout`

### Expense Tracking
- Add expenses: `/add-expense-page`
- View expenses: `/view-expense-page`
- Manage expenses with CRUD operations

### Income Tracking
- Add income: `/add-income`
- View income: `/view-income`

### Analytics
- View spending analytics: `/analytics-page`
- Predict monthly spending: `API /api/predict`
- Generate reports: `API /api/reports`

### Budgeting
- Set budgets: `API /api/budget` (POST)
- Get budgets: `API /api/budget` (GET)
- Manage budget groups: `/budgeting`

### AI Features
- AI analysis: `API /api/ai` (requires GEMINI_API_KEY)

## API Endpoints

### Authentication
- `POST /api/signup` - User registration
- `POST /api/login` - User login
- `GET /logout` - User logout

### Expenses
- `POST /add-expense` - Add expense
- `GET /get-expenses` - List expenses
- `PUT /api/expense/<id>` - Update expense
- `DELETE /api/expense/<id>` - Delete expense

### Income
- `POST /add-income` - Add income
- `GET /view-income` - List income

### Analytics
- `GET /api/analytics` - Get analytics
- `GET /api/summary` - Get summary
- `GET /api/reports` - Generate reports
- `GET /api/predict` - Predict spending

### Budgets
- `GET /api/budget` - Get budget
- `POST /api/budget` - Set budget

### Groups
- `POST /api/group` - Create group
- `GET /api/groups` - List groups
- `GET /api/group/<id>` - Get group details
- `GET /api/group/<id>/invite` - Get invite link
- `POST /api/group/<id>/expense` - Add group expense
- `GET /join-group/<token>` - Join group

## Environment Configuration

Edit `.env` file to configure:

```env
# Flask
FLASK_SECRET=your-secret-key
FLASK_ENV=development

# MongoDB (Local)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=SpendWiseDB

# MongoDB Atlas (Cloud)
# MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/

# Gemini AI
GEMINI_API_KEY=your-api-key
```

## Database Structure

### Collections
- **users** - User accounts
- **expenses** - Expense records
- **income** - Income records
- **budgets** - Budget limits
- **groups** - Shared expense groups

### Using Database Utilities

```python
from db_utils import DatabaseHelper

db = DatabaseHelper.connect()
expenses = DatabaseHelper.get_expenses(db, 'username')
by_category = DatabaseHelper.get_expenses_by_category(db, 'username')
```

## Troubleshooting

### MongoDB Connection Failed
1. Ensure MongoDB is running: `mongosh`
2. Check MONGODB_URI in `.env`
3. Verify firewall not blocking port 27017
4. Run `python init_db.py` to initialize

### Can't Create User (Duplicate Key Error)
- MongoDB enforces unique username/email
- Delete existing user first
- Or use different username/email

### Gemini API Error
- Gemini API is optional
- If not configured, AI features appear unavailable
- Get API key from https://ai.google.dev/

### Port 5000 Already in Use
- Find process: `netstat -ano | findstr :5000` (Windows)
- Change port in `.env` (SERVER_PORT=5001)

## Performance Tips

- Indexes are auto-created for fast queries
- Connection pooling handles concurrent users
- Aggregation pipelines used for analytics
- Data organized by user for security

## For More Help

- See [MONGODB_SETUP.md](MONGODB_SETUP.md) for detailed MongoDB setup
- Check [requirements.txt](requirements.txt) for dependencies
- Review [init_db.py](init_db.py) for database initialization
- Check [db_utils.py](db_utils.py) for utility functions

## Running in Production

For production deployment:
1. Use MongoDB Atlas or managed MongoDB service
2. Update MONGODB_URI with cloud connection string
3. Change FLASK_SECRET to strong random value
4. Set FLASK_ENV=production
5. Use WSGI server (gunicorn, waitress)
6. Enable SSL/TLS
7. Set up monitoring and backups

Enjoy using SpendWise! 🚀
