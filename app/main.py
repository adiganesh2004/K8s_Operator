from pymongo import MongoClient
import os
import time

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGO_DB", "mydb")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "rawdata_queue")

client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

def process_record(record):
    print(f"Processing record: {record['_id']}")
    # Simulate processing time
    time.sleep(2)
    collection.update_one({'_id': record['_id']}, {'$set': {'status': 'processed'}})

while True:
    record = collection.find_one_and_update(
        {'status': 'unprocessed'},
        {'$set': {'status': 'processing'}}
    )

    if record:
        process_record(record)
    else:
        print("No unprocessed records. Sleeping...")
        time.sleep(10)
