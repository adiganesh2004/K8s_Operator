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

# MongoDB config from env
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "mydatabase")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "records")

# Worker image
WORKER_IMAGE = os.getenv("WORKER_IMAGE", "quay.io/yourname/mongo-worker:latest")
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
            unprocessed_count = collection.count_documents({
                "status": "new",
                "retryCount": {"$lt": 3}
            })

            logger.info(f"Found {unprocessed_count} unprocessed records.")

            pods_to_spawn = min(unprocessed_count, MAX_PODS)
            if pods_to_spawn <= 0:
                logger.info("No work to do.")
            else:
                for _ in range(pods_to_spawn):
                    spawn_worker_job()

        except Exception as e:
            logger.error(f"Polling error: {e}")

        await asyncio.sleep(300)

# Spawn one worker job (record will be claimed by the pod itself)
def spawn_worker_job():
    job_id = str(uuid.uuid4())[:8]
    job_name = f"mongo-worker-{job_id}"

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
                            env=[
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

    try:
        batch_v1.create_namespaced_job(namespace=NAMESPACE, body=job)
        logger.info(f"Spawned worker job: {job_name}")
    except Exception as e:
        logger.error(f"Failed to create job {job_name}: {e}")
