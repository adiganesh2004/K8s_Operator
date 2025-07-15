import kopf
import pymongo
import os
import logging
from datetime import datetime
import uuid
from kubernetes import client, config
import asyncio
from queue import Queue

# Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# MongoDB config from env
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "mydatabase")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "records")

# Constants
WORKER_IMAGE = os.getenv("WORKER_IMAGE", "worker_dependent:v2")
NAMESPACE = os.getenv("POD_NAMESPACE", "default")
MAX_PODS = int(os.getenv("MAX_PARALLEL_PODS", "10"))

# Init Mongo client
mongo = pymongo.MongoClient(MONGO_URI)
collection = mongo[DB_NAME][COLLECTION_NAME]

# Init Kubernetes client
config.load_incluster_config()
core_v1 = client.CoreV1Api()
q = Queue()


async def poll_loop(**_):
    while True:
        logger.info(f"[{datetime.utcnow()}] Checking for unprocessed records...")

        try:
            # Atomically find & update records from "new" → "fetched"
            updated_records = collection.find(
                {"status": "new", "retryCount": {"$lt": 3}}
            )

            ids_to_update = [record["_id"] for record in updated_records]

            if ids_to_update:
                result = collection.update_many(
                    {"_id": {"$in": ids_to_update}},
                    {"$set": {"status": "fetched", "fetchedAt": datetime.utcnow()}}
                )

                logger.info(f"Fetched and marked {result.modified_count} records.")

                # Push record IDs to queue
                for _id in ids_to_update:
                    q.put(_id)

        except Exception as e:
            logger.error(f"Polling error: {e}")

        await asyncio.sleep(30)


# Function to pop n IDs from queue
def get_n_records(n):
    ids = []
    for _ in range(n):
        if q.empty():
            break
        ids.append(q.get())
    return ids





