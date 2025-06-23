import os
import pymongo
from bson.objectid import ObjectId
from datetime import datetime

# Load MongoDB config from environment
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "mydatabase")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "records")

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

# Atomically claim a new record
record = collection.find_one_and_update(
    filter={"status": "new", "retryCount": {"$lt": 3}},
    update={
        "$set": {
            "status": "processing",
            "claimedAt": datetime.utcnow()
        },
        "$inc": {"retryCount": 1}
    },
    return_document=pymongo.ReturnDocument.AFTER
)

if not record:
    print("No unprocessed record found.")
    exit(0)

print(f"Processing record: {record['_id']}")

# Your actual processing logic goes here
print("Hello World")

# Mark as completed
collection.update_one(
    {"_id": record["_id"]},
    {"$set": {"status": "completed", "completedAt": datetime.utcnow()}}
)

print(f"Record {record['_id']} marked as completed.")
