import os
import pymongo
from bson import ObjectId
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
record_ids_str = os.getenv("RECORD_IDS")
job_id = os.getenv("JOB_ID", "unknown")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION")

# Validate
if not all([MONGO_URI, DB_NAME, COLLECTION_NAME]):
    logger.error("Missing one or more required MongoDB env vars.")
    exit(1)

if not record_ids_str:
    logger.error("No RECORD_IDS provided. Exiting.")
    exit(1)

record_ids = [ObjectId(rid.strip()) for rid in record_ids_str.split(",")]

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

logger.info(f"[{datetime.utcnow()}] Job {job_id} processing records: {record_ids}")

records = list(collection.find({"_id": {"$in": record_ids}}))

for record in records:
    try:
        logger.info(f"Processing record {record['_id']} ...")

        # Your custom processing logic here...

        collection.update_one(
            {"_id": record["_id"]},
            {"$set": {
                "status": "done",
                "processedAt": datetime.utcnow(),
                "processedBy": job_id
            }}
        )
        logger.info(f"Record {record['_id']} marked as done.")

    except Exception as e:
        logger.error(f"Error processing record {record['_id']}: {e}")
        collection.update_one(
            {"_id": record["_id"]},
            {
                "$inc": {"retryCount": 1},
                "$set": {"status": "new"}
            }
        )

logger.info(f"Job {job_id} completed.")
