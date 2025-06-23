**Architecture Overview:**

This project uses KEDA to automatically scale a Python worker app based on the number of unprocessed records in a MongoDB collection.

A worker script (rawdata-worker.py) connects to MongoDB using environment variables and keeps checking the rawdata_queue collection. It picks one record at a time with status: "unprocessed", marks it as 
"processing" while working on it, and then updates the status to "processed" when done. This prevents duplicate processing.

KEDA watches this MongoDB collection using a ScaledObject. If more than 5 unprocessed records are found, it starts scaling the number of worker pods. The scaling is automatic and happens between 2 and 10
replicas. The worker Deployment is initially set to 0 replicas, because KEDA fully controls how many pods run based on the load.
