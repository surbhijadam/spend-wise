"""
MongoDB Database Initialization Script for SpendWise
This script sets up the MongoDB database, creates collections, and establishes indexes.
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def init_database():
    """Initialize MongoDB database with collections and indexes."""
    
    # Get MongoDB connection details from environment
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGODB_DB_NAME", "SpendWiseDB")
    
    print(f"Connecting to MongoDB at {mongo_uri}...")
    
    try:
        # Connect to MongoDB
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            maxPoolSize=50,
            minPoolSize=10
        )
        
        # Test connection
        client.admin.command('ping')
        print("✓ MongoDB connection successful!")
        
        # Get database
        db = client[db_name]
        print(f"✓ Using database: {db_name}")
        
        # Create collections
        collections = ["expenses", "users", "income", "budgets", "groups"]
        existing_collections = db.list_collection_names()
        
        for collection_name in collections:
            if collection_name not in existing_collections:
                db.create_collection(collection_name)
                print(f"✓ Created collection: {collection_name}")
            else:
                print(f"  Collection already exists: {collection_name}")
        
        # Create indexes for performance
        print("\nCreating indexes...")
        
        # Expenses collection indexes
        db["expenses"].create_index([("user", ASCENDING)])
        db["expenses"].create_index([("date", DESCENDING)])
        db["expenses"].create_index([("category", ASCENDING)])
        db["expenses"].create_index([("group_id", ASCENDING)])
        db["expenses"].create_index([("user", ASCENDING), ("date", DESCENDING)])
        print("✓ Indexes created for 'expenses' collection")
        
        # Users collection indexes
        db["users"].create_index([("username", ASCENDING)], unique=True)
        db["users"].create_index([("email", ASCENDING)], unique=True)
        print("✓ Indexes created for 'users' collection")
        
        # Income collection indexes
        db["income"].create_index([("date", DESCENDING)])
        db["income"].create_index([("source", ASCENDING)])
        print("✓ Indexes created for 'income' collection")
        
        # Budgets collection indexes
        db["budgets"].create_index([("user", ASCENDING), ("month", ASCENDING)])
        print("✓ Indexes created for 'budgets' collection")
        
        # Groups collection indexes
        db["groups"].create_index([("created_by", ASCENDING)])
        db["groups"].create_index([("members", ASCENDING)])
        print("✓ Indexes created for 'groups' collection")
        
        # Display database statistics
        print("\n" + "="*50)
        print("Database Initialization Complete!")
        print("="*50)
        print(f"Database: {db_name}")
        print(f"Collections: {', '.join(collections)}")
        print("\nDatabase Statistics:")
        
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            print(f"  {collection_name}: {count} documents")
        
        print("\n✓ You can now start the SpendWise app!")
        print("  Run: python app.py")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Error initializing database: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MongoDB is running:")
        print("   - Windows: search for 'MongoDB' in Services or use: mongod")
        print("   - Mac: brew services start mongodb-community")
        print("   - Linux: sudo systemctl start mongod")
        print(f"\n2. Verify MongoDB URI: {mongo_uri}")
        print("3. Check your .env file configuration")
        return False


if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
