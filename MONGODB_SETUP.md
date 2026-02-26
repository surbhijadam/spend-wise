# MongoDB Integration for SpendWise 2.0

## Overview
SpendWise 2.0 uses MongoDB as its primary database for storing expenses, income, budgets, users, and group data. This integration provides a flexible, scalable NoSQL solution for managing financial data.

## Prerequisites

### MongoDB Installation

**Windows:**
- Download MongoDB Community Edition from https://www.mongodb.com/try/download/community
- Run the installer and follow the setup wizard
- MongoDB will be installed as a Windows Service and start automatically
- Check if running:  `mongod --version`

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y mongodb
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Docker:**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Configuration

### Environment Variables

Configure MongoDB connection in `.env` file:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=SpendWiseDB

# For MongoDB Atlas (Cloud):
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
# MONGODB_DB_NAME=SpendWiseDB
```

### Connection Features

The MongoDB integration includes:
- **Connection Pooling**: Min 10, Max 50 connections
- **Automatic Retry**: Retries on transient failures
- **Timeouts**: 5s server selection timeout, 10s connection timeout
- **Error Handling**: Graceful handling of connection failures
- **Indexing**: Automatic index creation for performance

## Database Setup

### Automatic Setup (Recommended)

Run the initialization script:
```bash
python init_db.py
```

This will:
- Create the SpendWiseDB database
- Create all required collections
- Build indexes for optimal query performance
- Display database statistics

### Manual Setup

If you prefer manual setup:

```bash
# Start MongoDB shell
mongosh

# Create database and collections
use SpendWiseDB

db.createCollection("expenses")
db.createCollection("users")
db.createCollection("income")
db.createCollection("budgets")
db.createCollection("groups")

# Create indexes
db.expenses.createIndex({ "user": 1 })
db.expenses.createIndex({ "date": -1 })
db.expenses.createIndex({ "category": 1 })
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.budgets.createIndex({ "user": 1, "month": 1 })
db.groups.createIndex({ "created_by": 1 })
db.groups.createIndex({ "members": 1 })

# Verify
show collections
db.expenses.getIndexes()
```

## Database Schema

### Collections

#### **users**
```json
{
  "_id": ObjectId,
  "username": "string (unique)",
  "email": "string (unique)",
  "password": "string (hashed)",
  "created_at": "datetime"
}
```

#### **expenses**
```json
{
  "_id": ObjectId,
  "user": "string (username)",
  "amount": "float",
  "category": "string",
  "note": "string",
  "date": "string (YYYY-MM-DD)",
  "group_id": "string (optional)",
  "created_at": "datetime"
}
```

#### **income**
```json
{
  "_id": ObjectId,
  "amount": "float",
  "source": "string",
  "note": "string",
  "date": "datetime"
}
```

#### **budgets**
```json
{
  "_id": ObjectId,
  "user": "string",
  "month": "string (YYYY-MM)",
  "amount": "float",
  "created_at": "datetime"
}
```

#### **groups**
```json
{
  "_id": ObjectId,
  "name": "string",
  "budget": "float",
  "created_by": "string",
  "members": ["string"],
  "created_at": "datetime"
}
```

## Using the Database

### In Application Code

```python
from app import expenses_collection, users_collection

# Add an expense
expense = {
    'user': 'username',
    'amount': 50.00,
    'category': 'Food',
    'note': 'Lunch',
    'date': '2025-01-15'
}
result = expenses_collection.insert_one(expense)
print(f"Added expense with ID: {result.inserted_id}")

# Query expenses
expenses = list(expenses_collection.find({'user': 'username'}))
for exp in expenses:
    print(f"{exp['date']}: ${exp['amount']} - {exp['category']}")

# Aggregate expenses by category
pipeline = [
    {'$match': {'user': 'username'}},
    {'$group': {'_id': '$category', 'total': {'$sum': '$amount'}}},
    {'$sort': {'total': -1}}
]
result = list(expenses_collection.aggregate(pipeline))
```

### Using Database Utilities

```python
from db_utils import DatabaseHelper

db = DatabaseHelper.connect()

# Get user expenses
expenses = DatabaseHelper.get_expenses(db, 'username')

# Get expenses by category
by_category = DatabaseHelper.get_expenses_by_category(db, 'username')

# Get monthly expenses
monthly = DatabaseHelper.get_monthly_expenses(db, 'username')

# Add expense
expense_id = DatabaseHelper.add_expense(
    db,
    username='username',
    amount=50.00,
    category='Food',
    note='Lunch',
    group_id=None
)
```

## MongoDB Tools

### MongoDB Compass (GUI)
- Download from: https://www.mongodb.com/products/compass
- Connect to: `mongodb://localhost:27017`
- Browse collections, query data, and visualize documents

### MongoDB Shell (mongosh)
```bash
# Connect to local MongoDB
mongosh

# Connect to specific database
mongosh --authenticationDatabase admin

# Common commands
show dbs              # List all databases
use SpendWiseDB      # Select database
show collections      # List collections
db.expenses.find({}) # Query collection
db.expenses.count()  # Count documents
```

### Backup & Restore

**Backup:**
```bash
mongodump --uri="mongodb://localhost:27017/SpendWiseDB" --out=backup_folder
```

**Restore:**
```bash
mongorestore --uri="mongodb://localhost:27017/" backup_folder
```

## Troubleshooting

### Connection Issues

**"Cannot connect to MongoDB"**
- Verify MongoDB is running: `mongod --version`
- Check MONGODB_URI in .env file
- Ensure port 27017 is not blocked by firewall
- For Docker: verify container is running: `docker ps`

**"Database not found"**
- Ensure SpendWiseDB is created: `use SpendWiseDB` in mongosh
- Run: `python init_db.py` to auto-create

**"Duplicate key error"**
- Unique indexes on username and email
- Delete and recreate the user with different values
- Or drop the collection: `db.users.drop()`

### Performance Issues

- Check indexes are created: `db.expenses.getIndexes()`
- Analyze query performance: 
  ```javascript
  db.expenses.find({user: 'username'}).explain("executionStats")
  ```
- Enable profiling:
  ```javascript
  db.setProfilingLevel(1)
  db.system.profile.find().limit(5).sort({ts: -1}).pretty()
  ```

## Production Deployment

### Using MongoDB Atlas (Recommended)

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Create a database user
4. Get connection string
5. Update `.env`:
```env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

### Security Checklist

- [ ] Enable authentication (username/password)
- [ ] Use strong passwords
- [ ] Enable firewall/IP whitelisting
- [ ] Use TLS/SSL encryption
- [ ] Regular backups
- [ ] Limit connection pool size
- [ ] Enable audit logging
- [ ] Monitor database performance

## Performance Optimization

- **Indexes**: Already created on frequently queried fields
- **Connection Pooling**: Configured with optimal settings
- **Query Optimization**: Use aggregation pipeline for complex queries
- **Data Archiving**: Archive old data to separate collection if needed

## References

- [MongoDB Documentation](https://docs.mongodb.com/)
- [PyMongo Guide](https://pymongo.readthedocs.io/)
- [MongoDB Best Practices](https://docs.mongodb.com/manual/administration/best-practices/)

## Support

For issues or questions:
1. Check MongoDB logs: `tail -f /var/log/mongodb/mongod.log` (Linux/Mac)
2. Verify connection: `mongosh --eval "db.adminCommand('ping')"`
3. Review app logs for detailed error messages
