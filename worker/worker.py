import os
import pymongo
from bson import ObjectId

mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb-service:27017/")
record_id = os.getenv("RECORD_ID")

if not record_id:
    print("❌ No RECORD_ID passed. Exiting.")
    exit(1)

try:
    client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    client.server_info()
    print("✅ Connected to MongoDB")
except Exception as e:
    print("❌ Could not connect to MongoDB:", e)
    exit(1)

db = client["rawdata"]
queue = db["queue"]

oid = ObjectId(record_id)
record = queue.find_one({"_id": oid})

if record and record.get("status") == "waiting":
    print(f"Processing record: {record}")
    queue.update_one({"_id": oid}, {"$set": {"status": "processing"}})
    # simulate processing
    queue.update_one({"_id": oid}, {"$set": {"status": "done"}})
else:
    print("Record not found or already processed")

client.close()
