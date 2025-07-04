import kopf
import pymongo
import os
import logging
from datetime import datetime
import uuid
from kubernetes import client, config
import asyncio

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
batch_v1 = client.BatchV1Api()

@kopf.on.startup()
async def poll_loop(**_):
    while True:
        logger.info(f"[{datetime.utcnow()}] Checking for unprocessed records...")

        try:
            records = list(collection.find(
                {"status": "new", "retryCount": {"$lt": 3}}
            ).limit(MAX_PODS))  # Limit to max parallel pods

            logger.info(f"Found {len(records)} unprocessed records.")

            for record in records:
                assign_and_spawn_worker(record)

        except Exception as e:
            logger.error(f"Polling error: {e}")

        await asyncio.sleep(30)


def assign_and_spawn_worker(record):
    record_id = record["_id"]
    job_id = str(uuid.uuid4())[:8]
    job_name = f"mongo-worker-{job_id}"

    # Atomically update status if still new
    result = collection.update_one(
        {"_id": record_id, "status": "new"},
        {"$set": {"status": "assigned", "jobId": job_id}}
    )

    if result.modified_count == 0:
        logger.warning(f"❌ Failed to claim record {record_id}, likely already taken.")
        return

    logger.info(f"✅ Claimed record {record_id} for job {job_name}")

    # Define the Job
    job = client.V1Job(
        metadata=client.V1ObjectMeta(
            name=job_name,
            labels={"app": "mongo-worker"}
        ),
        spec=client.V1JobSpec(
            backoff_limit=2,
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": "mongo-worker"}),
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    containers=[
                        client.V1Container(
                            name="worker",
                            image=WORKER_IMAGE,
                            image_pull_policy="Never",
                            env=[
                                client.V1EnvVar(name="RECORD_IDS", value=str(record_id)),
                                client.V1EnvVar(name="JOB_ID", value=job_id),
                                client.V1EnvVar(name="MONGO_URI", value=MONGO_URI),
                                client.V1EnvVar(name="MONGO_DB", value=DB_NAME),
                                client.V1EnvVar(name="MONGO_COLLECTION", value=COLLECTION_NAME),
                            ]
                        )
                    ]
                )
            )
        )
    )

    # Submit the Job
    try:
        batch_v1.create_namespaced_job(namespace=NAMESPACE, body=job)
        logger.info(f"🚀 Spawned worker job: {job_name} for record {record_id}")
    except Exception as e:
        logger.error(f"❌ Failed to create job {job_name}: {e}")
