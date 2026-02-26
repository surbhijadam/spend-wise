"""
MongoDB Utilities for SpendWise
This module provides helper functions for database operations and connection management.
"""

import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

load_dotenv()


class MongoDBConnection:
    """Singleton class for MongoDB connection management."""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection."""
        try:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            db_name = os.getenv("MONGODB_DB_NAME", "SpendWiseDB")
            
            self._client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True,
                maxPoolSize=50,
                minPoolSize=10
            )
            
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[db_name]
            print("✓ MongoDB connection established")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    def get_db(self):
        """Get database instance."""
        return self._db
    
    def get_client(self):
        """Get MongoDB client."""
        return self._client
    
    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            print("✓ MongoDB connection closed")


class DatabaseHelper:
    """Helper class for common database operations."""
    
    @staticmethod
    def connect():
        """Get database connection."""
        return MongoDBConnection().get_db()
    
    @staticmethod
    def user_exists(db, username: str) -> bool:
        """Check if user exists."""
        users_col = db["users"]
        return users_col.find_one({"username": username}) is not None
    
    @staticmethod
    def get_user(db, username: str) -> Optional[Dict]:
        """Get user document."""
        users_col = db["users"]
        return users_col.find_one({"username": username})
    
    @staticmethod
    def create_user(db, username: str, email: str, password_hash: str) -> bool:
        """Create new user."""
        try:
            users_col = db["users"]
            result = users_col.insert_one({
                "username": username,
                "email": email,
                "password": password_hash,
                "created_at": db.client.admin.command("ping")  # Get server time
            })
            return result.inserted_id is not None
        except PyMongoError as e:
            print(f"Error creating user: {e}")
            return False
    
    @staticmethod
    def add_expense(db, username: str, amount: float, category: str, 
                   note: str = "", date: str = None, group_id: str = None) -> Optional[str]:
        """Add new expense."""
        try:
            from datetime import datetime
            expenses_col = db["expenses"]
            expense = {
                "user": username,
                "amount": amount,
                "category": category,
                "note": note,
                "date": date or datetime.utcnow().strftime('%Y-%m-%d'),
                "created_at": datetime.utcnow()
            }
            if group_id:
                expense["group_id"] = group_id
            
            result = expenses_col.insert_one(expense)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error adding expense: {e}")
            return None
    
    @staticmethod
    def get_expenses(db, username: str, limit: int = 100) -> List[Dict]:
        """Get all expenses for a user."""
        try:
            expenses_col = db["expenses"]
            expenses = list(expenses_col.find({"user": username}).sort("date", -1).limit(limit))
            
            # Convert ObjectId to string
            for exp in expenses:
                exp['id'] = str(exp.pop('_id'))
            
            return expenses
        except PyMongoError as e:
            print(f"Error getting expenses: {e}")
            return []
    
    @staticmethod
    def get_expenses_by_category(db, username: str) -> Dict[str, float]:
        """Get total expenses grouped by category."""
        try:
            expenses_col = db["expenses"]
            pipeline = [
                {"$match": {"user": username}},
                {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
                {"$sort": {"total": -1}}
            ]
            result = expenses_col.aggregate(pipeline)
            return {doc["_id"]: doc["total"] for doc in result}
        except PyMongoError as e:
            print(f"Error getting expenses by category: {e}")
            return {}
    
    @staticmethod
    def get_monthly_expenses(db, username: str) -> Dict[str, float]:
        """Get total expenses by month."""
        try:
            expenses_col = db["expenses"]
            pipeline = [
                {"$match": {"user": username}},
                {"$project": {"amount": "$amount", "month": {"$substr": ["$date", 0, 7]}}},
                {"$group": {"_id": "$month", "total": {"$sum": "$amount"}}},
                {"$sort": {"_id": 1}}
            ]
            result = expenses_col.aggregate(pipeline)
            return {doc["_id"]: doc["total"] for doc in result}
        except PyMongoError as e:
            print(f"Error getting monthly expenses: {e}")
            return {}
    
    @staticmethod
    def delete_expense(db, expense_id: str, username: str) -> bool:
        """Delete an expense."""
        try:
            from bson import ObjectId
            expenses_col = db["expenses"]
            result = expenses_col.delete_one({
                "_id": ObjectId(expense_id),
                "user": username
            })
            return result.deleted_count > 0
        except PyMongoError as e:
            print(f"Error deleting expense: {e}")
            return False
    
    @staticmethod
    def create_backup():
        """Create a backup reference/snapshot."""
        # This is a placeholder for backup functionality
        # In production, use mongodump or other backup solutions
        pass


# Export singleton
def get_db():
    """Get database instance."""
    return MongoDBConnection().get_db()


def close_db():
    """Close database connection."""
    MongoDBConnection().close()
