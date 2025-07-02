import os
from pymongo import MongoClient

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
host = os.getenv("MONGO_HOST")
dbname = os.getenv("MONGO_DB")

mongo_uri = f"mongodb+srv://{user}:{password}@{host}/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(mongo_uri)

try:
    dbs = client.list_database_names()
    print("Available databases:")
    for db in dbs:
        print(f"- {db}")
except Exception as e:
    print(f"Connection failed: {e}")