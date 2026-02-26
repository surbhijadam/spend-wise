# Developer's Guide - MongoDB Integration

This guide explains how to use MongoDB and the database utilities in SpendWise development.

## Architecture Overview

```
app.py (Main Flask Application)
├── init_mongodb() - Initialize connection
├── Database Collections
│   ├── expenses_collection
│   ├── users_collection
│   ├── income_col
│   ├── budgets_collection
│   └── groups_collection
└── db_utils.py (Database Helper Module)
    ├── MongoDBConnection (Singleton)
    ├── DatabaseHelper (Helper Methods)
    └── Utility Functions
```

## Using MongoDB in Code

### Method 1: Direct Collections (Existing Code)

Use the collections already initialized in `app.py`:

```python
from app import expenses_collection, users_collection

# Add expense
result = expenses_collection.insert_one({
    'user': 'john_doe',
    'amount': 50.00,
    'category': 'Food',
    'date': '2025-02-25'
})
expense_id = result.inserted_id

# Query expenses
expenses = list(expenses_collection.find({'user': 'john_doe'}))

# Update expense
expenses_collection.update_one(
    {'_id': ObjectId(expense_id)},
    {'$set': {'amount': 75.00}}
)

# Delete expense
expenses_collection.delete_one({'_id': ObjectId(expense_id)})
```

### Method 2: Database Utilities (Recommended for New Code)

Use helper functions for cleaner code:

```python
from db_utils import DatabaseHelper
from app import db

# Get database connection
db = DatabaseHelper.connect()

# Check if user exists
if DatabaseHelper.user_exists(db, 'john_doe'):
    print("User found!")

# Get user info
user = DatabaseHelper.get_user(db, 'john_doe')
print(user['email'])

# Add expense
expense_id = DatabaseHelper.add_expense(
    db,
    username='john_doe',
    amount=50.00,
    category='Food',
    note='Lunch at restaurant',
    date='2025-02-25'
)

# Get all expenses
expenses = DatabaseHelper.get_expenses(db, 'john_doe', limit=50)

# Get expenses by category
by_category = DatabaseHelper.get_expenses_by_category(db, 'john_doe')
# Returns: {'Food': 125.50, 'Transport': 45.00, ...}

# Get monthly expenses
monthly = DatabaseHelper.get_monthly_expenses(db, 'john_doe')
# Returns: {'2025-01': 250.00, '2025-02': 180.00}

# Delete expense
deleted = DatabaseHelper.delete_expense(db, expense_id_str, 'john_doe')
```

### Method 3: Aggregation Pipeline (Complex Queries)

For complex data operations use MongoDB aggregation:

```python
from app import expenses_collection

# Get top spending categories
pipeline = [
    {'$match': {'user': 'john_doe'}},
    {'$group': {
        '_id': '$category',
        'total': {'$sum': '$amount'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'total': -1}},
    {'$limit': 5}
]

top_categories = list(expenses_collection.aggregate(pipeline))
# Returns: [
#   {'_id': 'Food', 'total': 250.50, 'count': 15},
#   {'_id': 'Transport', 'total': 120.00, 'count': 8},
#   ...
# ]

# Get spending trend over months
pipeline = [
    {'$match': {'user': 'john_doe'}},
    {'$project': {
        'amount': '$amount',
        'year_month': {'$substr': ['$date', 0, 7]}
    }},
    {'$group': {
        '_id': '$year_month',
        'total': {'$sum': '$amount'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'_id': 1}}
]

monthly_trend = list(expenses_collection.aggregate(pipeline))
# Returns: [
#   {'_id': '2025-01', 'total': 1000.00, 'count': 45},
#   {'_id': '2025-02', 'total': 850.50, 'count': 38},
#   ...
# ]
```

## Common Patterns

### Pattern 1: User-Based Query

Always filter by user for data isolation:

```python
# ✓ CORRECT - Filters by user
expenses = expenses_collection.find({'user': username})

# ✗ AVOID - No user filter allows data leakage
expenses = expenses_collection.find({'amount': {'$gt': 100}})
```

### Pattern 2: ObjectId Handling

Convert between strings and ObjectIds:

```python
from bson import ObjectId

# String to ObjectId
expense_id = ObjectId('507f1f77bcf86cd799439011')

# ObjectId to string
expense_id_str = str(expense_id)

# Always use ObjectId for _id queries
expense = expenses_collection.find_one({'_id': ObjectId(id_str)})
```

### Pattern 3: Error Handling

Handle database errors gracefully:

```python
from pymongo.errors import PyMongoError, DuplicateKeyError

try:
    users_collection.insert_one(user_doc)
except DuplicateKeyError:
    return jsonify({'error': 'username or email already exists'}), 409
except PyMongoError as e:
    print(f"Database error: {e}")
    return jsonify({'error': 'database error'}), 500
```

### Pattern 4: Transaction-like Operations

For operations affecting multiple documents:

```python
from pymongo import UpdateOne

# Batch updates
updates = [
    UpdateOne({'_id': id1}, {'$set': {'status': 'processed'}}),
    UpdateOne({'_id': id2}, {'$set': {'status': 'processed'}}),
]
expenses_collection.bulk_write(updates)
```

## Query Examples

### Find Single Document
```python
# By username
user = users_collection.find_one({'username': 'john_doe'})

# By ObjectId
expense = expenses_collection.find_one({'_id': ObjectId(id)})
```

### Find Multiple Documents
```python
# All expenses for user, sorted by date
expenses = list(expenses_collection.find(
    {'user': username}
).sort('date', -1))

# Limit results
recent = list(expenses_collection.find(
    {'user': username}
).sort('date', -1).limit(10))

# Skip (pagination)
page_2 = list(expenses_collection.find(
    {'user': username}
).skip(10).limit(10))
```

### Update Operations
```python
# Update single document
expenses_collection.update_one(
    {'_id': ObjectId(id)},
    {'$set': {'amount': 100.00}}
)

# Update multiple documents
expenses_collection.update_many(
    {'user': username, 'category': 'Food'},
    {'$set': {'category': 'Dining'}}
)

# Increment (for counters)
budgets_collection.update_one(
    {'_id': budget_id},
    {'$inc': {'used_amount': 50.00}}
)
```

### Delete Operations
```python
# Delete single document
expenses_collection.delete_one({'_id': ObjectId(id)})

# Delete multiple documents
expenses_collection.delete_many({'user': username, 'category': 'Old'})

# Delete with condition
expenses_collection.delete_many({
    'user': username,
    'date': {'$lt': '2025-01-01'}
})
```

### Aggregation Examples

#### Count Documents
```python
count = expenses_collection.count_documents({'user': username})
```

#### Sum, Average, Min, Max
```python
pipeline = [
    {'$match': {'user': username}},
    {'$group': {
        '_id': None,
        'total': {'$sum': '$amount'},
        'average': {'$avg': '$amount'},
        'min': {'$min': '$amount'},
        'max': {'$max': '$amount'},
        'count': {'$sum': 1}
    }}
]

stats = list(expenses_collection.aggregate(pipeline))[0]
```

#### Group By Multiple Fields
```python
pipeline = [
    {'$match': {'user': username}},
    {'$group': {
        '_id': {'category': '$category', 'month': {'$substr': ['$date', 0, 7]}},
        'total': {'$sum': '$amount'}
    }},
    {'$sort': {'_id.month': 1, 'total': -1}}
]

results = list(expenses_collection.aggregate(pipeline))
```

## Testing Database Code

### Unit Test Example
```python
import unittest
from db_utils import DatabaseHelper

class TestDatabaseHelper(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseHelper.connect()
    
    def test_add_expense(self):
        expense_id = DatabaseHelper.add_expense(
            self.db,
            username='test_user',
            amount=50.00,
            category='Test'
        )
        self.assertIsNotNone(expense_id)
        
        # Verify
        expenses = DatabaseHelper.get_expenses(self.db, 'test_user')
        self.assertTrue(any(e['id'] == str(expense_id) for e in expenses))

if __name__ == '__main__':
    unittest.main()
```

## Performance Considerations

### Use Indexes
```python
# Queries on indexed fields are fast
expenses_collection.find({'user': username})  # Fast, indexed
expenses_collection.find({'category': 'Food'})  # Consider indexing

# Create custom indexes
expenses_collection.create_index([('user', 1), ('date', -1)])
```

### Project Only Needed Fields
```python
# ✓ Efficient
expenses = expenses_collection.find(
    {'user': username},
    {'_id': 1, 'date': 1, 'amount': 1}
)

# Less efficient
expenses = expenses_collection.find({'user': username})
```

### Use Aggregation for Complex Queries
```python
# ✓ Efficient - server-side processing
avg_expense = expenses_collection.aggregate([...])

# Less efficient - process in Python
all_expenses = list(expenses_collection.find(...))
avg = sum(e['amount'] for e in all_expenses) / len(all_expenses)
```

## Debugging

### Enable Query Logging
```python
from pymongo import MongoClient
import logging

logging.basicConfig()
logging.getLogger('pymongo').setLevel(logging.DEBUG)

# Queries will be logged to console
```

### Inspect Document Structure
```python
import json
from bson import json_util

# Pretty print document
doc = expenses_collection.find_one({'user': 'john'})
print(json.dumps(doc, indent=2, default=json_util.default))
```

### Check Collection Statistics
```python
from app import db

for collection_name in db.list_collection_names():
    count = db[collection_name].count_documents({})
    print(f"{collection_name}: {count} documents")
```

## Best Practices

1. **Always validate input** before database operations
2. **Use ObjectId** for _id field, not strings
3. **Filter by user** for data security
4. **Handle exceptions** gracefully
5. **Use indexes** on frequently queried fields
6. **Paginate** large result sets
7. **Aggregate** on server side for complex queries
8. **Close connections** properly (handled by app)
9. **Document** custom database operations
10. **Test** database code before deployment

## Useful Resources

- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Query Language](https://docs.mongodb.com/manual/reference/operator/aggregation/)
- [MongoDB Performance](https://docs.mongodb.com/manual/administration/analyzing-mongodb-performance/)
- [BSON Types](https://docs.mongodb.com/manual/reference/bson-types/)

## Migration Guide

If moving from SQL to MongoDB or vice versa:

```python
# SQL Equivalent          MongoDB Equivalent
# SELECT * FROM users   →  users_collection.find()
# SELECT id FROM users  →  users_collection.find({}, {'_id': 1})
# WHERE user = 'x'      →  find({'user': 'x'})
# ORDER BY date DESC    →  find().sort('date', -1)
# DELETE FROM ...       →  delete_one/delete_many()
# INSERT INTO ...       →  insert_one/insert_many()
```

---

**Happy Coding!** 🚀

For questions or issues, refer to MongoDB documentation or SpendWise documentation files.
