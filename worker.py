import os
import pymongo
from bson import ObjectId
import logging
from datetime import datetime
import json

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
record_id_str = os.getenv(RECORD_ID)  # Only one record ID now
pod_id = os.getenv(POD_ID, unknown)  # Renamed from JOB_ID to POD_ID

MONGO_URI = os.getenv(MONGO_URI)
DB_NAME = os.getenv(MONGO_DB)
COLLECTION_NAME = os.getenv(MONGO_COLLECTION)

# Validate
if not all([MONGO_URI, DB_NAME, COLLECTION_NAME])
    logger.error(Missing one or more required MongoDB env vars.)
    exit(1)

if not record_id_str
    logger.error(No RECORD_ID provided. Exiting.)
    exit(1)

record_id = ObjectId(record_id_str.strip())

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

logger.info(f[{datetime.utcnow()}] Pod {pod_id} processing record {record_id})

record = collection.find_one({_id record_id})

if record
    try
        logger.info(fProcessing record {record['_id']} ...)

        # Deserialize payload
        payload = record.get(payload, )
        try
            deserialized_payload = json.loads(payload)
            logger.info(fDeserialized payload for {record['_id']} {deserialized_payload})
        except json.JSONDecodeError as e
            logger.error(fFailed to deserialize payload for {record['_id']} {e})
            raise

        # Your custom processing logic here...

        collection.update_one(
            {_id record[_id]},
            {$set {
                status done,
                processedAt datetime.utcnow(),
                processedBy pod_id
            }}
        )
        logger.info(fRecord {record['_id']} marked as done.)

    except Exception as e
        logger.error(fError processing record {record['_id']} {e})
        collection.update_one(
            {_id record[_id]},
            {
                $inc {retryCount 1},
            }
        )
else
    logger.error(fRecord with ID {record_id} not found.)

logger.info(fPod {pod_id} completed.)
