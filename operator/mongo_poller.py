import time, os, logging
from .shared_queue import size, add_records
from pymongo import MongoClient

logger = logging.getLogger(__name__)
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")
COLL = os.getenv("MONGO_COLLECTION")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

client = MongoClient(MONGO_URI)
col = client[DB_NAME][COLL]

def mongo_poller_loop():
    while True:
        if size() == 0:
            logger.info("Queue empty → pulling from MongoDB")
            docs = list(col.find({"status": "new"}).limit(BATCH_SIZE))
            if docs:
                ids = [d["_id"] for d in docs]
                col.update_many({"_id": {"$in": ids}}, {"$set": {"status": "queued"}})
                add_records(docs)
                logger.info(f"Queued {len(docs)} records")
            else:
                logger.info("No new records")
        time.sleep(5)
