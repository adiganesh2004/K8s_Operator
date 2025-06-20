# watcher.py
import time
from pymongo import MongoClient
from kubernetes import client, config
import uuid

# Load in-cluster config
config.load_incluster_config()

# Set up Kubernetes API
api = client.CustomObjectsApi()

# Connect to MongoDB
mongo_url = 'mongodb://mongodb-service:27017'
client = MongoClient(mongo_url)
db = client['rawdata']
collection = db['queue']

# Track inserted IDs to avoid duplication
seen_ids = set()

print("Watcher started. Monitoring MongoDB queue...")

while True:
    for doc in collection.find():
        doc_id = str(doc.get('_id'))

        if doc_id not in seen_ids:
            seen_ids.add(doc_id)

            # Create MongoDBQueue CR
            cr_name = f"queue-{str(uuid.uuid4())[:8]}"
            body = {
                "apiVersion": "yourdomain.com/v1",
                "kind": "MongoDBQueue",
                "metadata": {
                    "name": cr_name,
                    "namespace": "rawdata"
                },
                "spec": {
                    "recordId": doc_id
                }
            }

            try:
                api.create_namespaced_custom_object(
                    group="yourdomain.com",
                    version="v1",
                    namespace="rawdata",
                    plural="mongodbqueues",
                    body=body
                )
                print(f"Created MongoDBQueue CR for record ID: {doc_id}")
            except Exception as e:
                print(f"Error creating CR for {doc_id}: {e}")

    time.sleep(5)  # Adjust based on desired polling frequency
