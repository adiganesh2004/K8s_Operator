import os
import pymongo

mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb-service:27017/")
try:
    client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    client.server_info()  # Force a call to check connection
    print("✅ Connected to MongoDB")
except Exception as e:
    print("❌ Could not connect to MongoDB:", e)

db = client["rawdata"]
queue = db["queue"]

record = queue.find_one_and_update(
    {"status": "waiting"},
    {"$set": {"status": "processing"}},
)

if record:
    print(f"Processing record: {record}")
    queue.update_one({"_id": record["_id"]}, {"$set": {"status": "done"}})
else:
    print("No records to process")
client.close()
