import kopf
import pymongo
import os
import logging
from datetime import datetime
import uuid
from kubernetes import client, config
import asyncio
import json

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
RECORDS_PER_WORKER = int(os.getenv("RECORDS_PER_WORKER", "10"))

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
            total_unprocessed = collection.count_documents({
                "status": "new",
                "retryCount": {"$lt": 3}
            })

            logger.info(f"Found {total_unprocessed} unprocessed records.")

            if total_unprocessed == 0:
                logger.info("No records to process.")
            else:
                pods_needed = (total_unprocessed + RECORDS_PER_WORKER - 1) // RECORDS_PER_WORKER
                pods_to_spawn = min(pods_needed, MAX_PODS)

                logger.info(f"Spawning {pods_to_spawn} worker pods...")

                for _ in range(pods_to_spawn):
                    assign_and_spawn_worker()

        except Exception as e:
            logger.error(f"Polling error: {e}")

        await asyncio.sleep(30)


def assign_and_spawn_worker():
    job_id = str(uuid.uuid4())[:8]
    job_name = f"mongo-worker-{job_id}"

    # Step 1: Fetch N unprocessed records
    candidate_records = list(collection.find(
        {"status": "new", "retryCount": {"$lt": 3}}
    ).limit(RECORDS_PER_WORKER))

    if not candidate_records:
        logger.info("No records available to assign.")
        return

    claimed_ids = [r["_id"] for r in candidate_records]
    record_ids = [str(rid) for rid in claimed_ids]

    logger.info(f"Attempting to update records with _id in: {claimed_ids}")

    pre_check = list(collection.find({"_id": {"$in": claimed_ids}}))
    for doc in pre_check:
        logger.info(f"Pre-update doc: id={doc['_id']} status={doc['status']} retryCount={doc['retryCount']}")


    # Step 2: Atomically claim them (only if still unassigned)
    result = collection.update_many(
        {"_id": {"$in": claimed_ids}, "status": "new"},
        {"$set": {"status": "assigned", "jobId": job_id}}
    )

    if result.modified_count == 0:
        logger.warning(f"❌ Update failed — none of these records were claimed: {record_ids}")
    else:
        logger.info(f"✅ Successfully updated {result.modified_count} record(s) to 'assigned'.")


    logger.info(f"Updated {result.modified_count} records to status='assigned' with jobId={job_id}")
    logger.info(f"Assigning records {record_ids} to job {job_name}")


    # Step 3: Define the Job
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
                                client.V1EnvVar(name="RECORD_IDS", value=",".join(record_ids)),
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

    # Step 4: Submit the Job
    try:
        batch_v1.create_namespaced_job(namespace=NAMESPACE, body=job)
        logger.info(f"Spawned worker job: {job_name}")
    except Exception as e:
        logger.error(f"Failed to create job {job_name}: {e}")
