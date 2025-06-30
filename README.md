**Architecture Overview:**

This project uses KEDA to automatically scale a Python worker app based on the number of unprocessed records in a MongoDB collection.

A worker script (rawdata-worker.py) connects to MongoDB using environment variables and keeps checking the rawdata_queue collection. It picks one record at a time with status: "unprocessed", marks it as 
"processing" while working on it, and then updates the status to "processed" when done. This prevents duplicate processing.

KEDA watches this MongoDB collection using a ScaledObject. If more than 5 unprocessed records are found, it starts scaling the number of worker pods. The scaling is automatic and happens between 2 and 10
replicas. The worker Deployment is initially set to 0 replicas, because KEDA fully controls how many pods run based on the load.

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

# === Configuration ===
mongo_username = "your_username"
mongo_password = "your_password"
mongo_host_name = "your.mongodb.host.com"  # or IP address
mongo_db_name = "your_db"
mongo_collection_name = "your_collection"
cert_file = "/path/to/your/certificate.pem"

# === Build Mongo URI ===
mongo_uri = f"mongodb+srv://{mongo_username}:{mongo_password}@{mongo_host_name}/?tls=true&tlsCAFile={cert_file}"

try:
    # Create MongoDB client
    client = MongoClient(mongo_uri)

    # Access the database and collection
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    # Test the connection by pinging the server
    client.admin.command('ping')
    print("✅ Connected to MongoDB!")

    # Optionally, list some documents
    sample = collection.find_one()
    if sample:
        print("Sample document:", sample)
    else:
        print("No documents found in collection.")

except (ConnectionFailure, ConfigurationError) as e:
    print("❌ Connection failed:", e)
