import time
import uuid
from pymongo import MongoClient, errors
from kubernetes import client, config

# Load Kubernetes configuration from within the cluster
config.load_incluster_config()

# Initialize Kubernetes CustomObjects API
custom_api = client.CustomObjectsApi()

# MongoDB connection URI (service name inside the cluster)
mongo_uri = 'mongodb://mongodb-service:27017'

# Attempt to establish MongoDB connection
try:
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    print("Successfully connected to MongoDB.")
except errors.ServerSelectionTimeoutError as conn_err:
    print(f"MongoDB connection failed: {conn_err}")
    exit(1)

# Reference the target database and collection
db = mongo_client['rawdata']
queue_collection = db['queue']

# Track already-processed document IDs
processed_ids = set()

print("Watcher service started. Monitoring MongoDB queue...")

def chunk_list(lst, chunk_size):
    """Split a list into chunks of a specified maximum size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

while True:
    all_new_ids = []

    # Find all unprocessed documents
    for doc in queue_collection.find():
        doc_id = str(doc.get('_id'))
        if doc_id not in processed_ids:
            processed_ids.add(doc_id)
            all_new_ids.append(doc_id)

    # Chunk the IDs into groups of 10
    for batch in chunk_list(all_new_ids, 10):
        cr_name = f"queue-{uuid.uuid4().hex[:8]}"
        cr_body = {
            "apiVersion": "yourdomain.com/v1",
            "kind": "MongoDBQueue",
            "metadata": {
                "name": cr_name,
                "namespace": "rawdata"
            },
            "spec": {
                "recordIds": batch
            }
        }

        # DEBUG LOG: Confirm CR body before sending
        print(f"DEBUG: Creating MongoDBQueue CR '{cr_name}' with recordIds: {batch}")
        print("Full CR body:", cr_body)

        try:
            custom_api.create_namespaced_custom_object(
                group="yourdomain.com",
                version="v1",
                namespace="rawdata",
                plural="mongodbqueues",
                body=cr_body
            )
            print(f"Created MongoDBQueue CR '{cr_name}' for record IDs: {batch}")
        except Exception as api_err:
            print(f"Failed to create CR '{cr_name}': {api_err}")

    time.sleep(5)
