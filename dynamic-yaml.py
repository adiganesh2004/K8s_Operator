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
core_v1 = client.CoreV1Api()



#collection



def assign_and_spawn_worker(record_ids):
    pod_id = str(uuid.uuid4())[:8]
    pod_name = f"mongo-worker-{pod_id}"

    # Atomic bulk update for all records that are still "new"
    result = collection.update_many(
        {
            "_id": {"$in": record_ids}
        },
        {
            "$set": {
                "status": "assigned",
                "podId": pod_id,
                "assignedAt": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        logger.warning("❌ No records were claimed (already taken). Skipping pod creation.")
        return

    logger.info(f"✅ Claimed {len(record_ids)} records for pod {pod_name}")

    containers = []
    for i, record in enumerate(record_ids):
        container = client.V1Container(
            name=f"worker-{i+1}",
            image=WORKER_IMAGE,
            image_pull_policy="Never",
            env=[
                client.V1EnvVar(name="RECORD_IDS", value=str(record["_id"])),
                client.V1EnvVar(name="POD_ID", value=f"{pod_id}-{i+1}"),
                client.V1EnvVar(name="MONGO_URI", value=MONGO_URI),
                client.V1EnvVar(name="MONGO_DB", value=DB_NAME),
                client.V1EnvVar(name="MONGO_COLLECTION", value=COLLECTION_NAME),
            ],
            volume_mounts=[
                client.V1VolumeMount(
                    name="secret-volume",
                    mount_path="/app/secret",
                    read_only=True
                )
            ]
        )
        containers.append(container)

    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=pod_name,
            labels={"app": "mongo-worker"}
        ),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=containers,
            volumes=[
                client.V1Volume(
                    name="secret-volume",
                    secret=client.V1SecretVolumeSource(
                        secret_name="my-secret-name"
                    )
                )
            ]
        )
    )

    try:
        core_v1.create_namespaced_pod(namespace=NAMESPACE, body=pod)
        logger.info(f"🚀 Spawned pod: {pod_name} with {len(record_ids)} containers")
    except Exception as e:
        logger.error(f"❌ Failed to create pod {pod_name}: {e}")
