import os
import pymongo
from bson import ObjectId

# Read environment variables
mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb-service:27017/")
record_ids_str = os.getenv("RECORD_IDS")  # Comma-separated string of ObjectIds

# Validate input
if not record_ids_str:
    print("No RECORD_IDS provided. Exiting.")
    exit(1)

# Parse ObjectId strings into ObjectId instances
try:
    record_ids = [ObjectId(rid.strip()) for rid in record_ids_str.split(',') if rid.strip()]
except Exception as parse_error:
    print(f"Error parsing RECORD_IDS: {parse_error}")
    exit(1)

# Attempt to connect to MongoDB
try:
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    mongo_client.server_info()  # Force connection check
    print("Connected to MongoDB")
except Exception as conn_error:
    print(f"Could not connect to MongoDB: {conn_error}")
    exit(1)

# Access the target database and collection
db = mongo_client["rawdata"]
queue_collection = db["queue"]

# Process each record ID
for oid in record_ids:
    try:
        record = queue_collection.find_one({"_id": oid})

        if record and record.get("status") == "waiting":
            print(f"Processing record: {oid}")
            queue_collection.update_one({"_id": oid}, {"$set": {"status": "processing"}})

            # Simulate processing here
            # Example: perform some logic or data transformation
            queue_collection.update_one({"_id": oid}, {"$set": {"status": "done"}})
            print(f"Finished processing record: {oid}")
        else:
            print(f"Record {oid} not found or already processed.")

    except Exception as record_error:
        print(f"Error processing record {oid}: {record_error}")

# Close the MongoDB connection
mongo_client.close()
print("Worker finished. MongoDB connection closed.")
