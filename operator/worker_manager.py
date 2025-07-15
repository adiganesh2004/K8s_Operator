import threading, os, logging, time, uuid
from .shared_queue import get_batch, size
from kubernetes import client, config, watch

logger = logging.getLogger(__name__)
config.load_incluster_config()
core = client.CoreV1Api()

NAMESPACE = os.getenv("POD_NAMESPACE", "default")
MAX_PODS = int(os.getenv("MAX_PODS", "6"))
WORKER_IMAGE = os.getenv("WORKER_IMAGE")
RECS_PER_WORKER = int(os.getenv("RECORDS_PER_WORKER", "10"))

def spawn_worker(records):
    jid = str(uuid.uuid4())[:8]
    pod_name = f"worker-{jid}"
    env = [
        client.V1EnvVar(name="RECORD_IDS", value=",".join(str(r["_id"]) for r in records)),
        client.V1EnvVar(name="JOB_ID", value=jid),
        client.V1EnvVar(name="MONGO_URI", value=os.getenv("MONGO_URI")),
        client.V1EnvVar(name="MONGO_DB", value=os.getenv("MONGO_DB")),
        client.V1EnvVar(name="MONGO_COLLECTION", value=os.getenv("MONGO_COLLECTION")),
    ]
    containers = [client.V1Container(name=f"worker-{i}", image=WORKER_IMAGE, env=env)
                  for i in range(int(os.getenv("Y_CONTAINERS", "1")))]
    spec = client.V1PodSpec(containers=containers, restart_policy="Never")
    pod = client.V1Pod(metadata=client.V1ObjectMeta(name=pod_name, labels={"app": "mongo-worker"}),
                      spec=spec)
    core.create_namespaced_pod(namespace=NAMESPACE, body=pod)
    logger.info(f"Spawned pod {pod_name} with {len(records)} records")

def manager_loop():
    w = watch.Watch()
    # Start watch in separate thread
    def watch_pods():
        for ev in w.stream(core.list_namespaced_pod, namespace=NAMESPACE, label_selector="app=mongo-worker"):
            p = ev["object"]
            phase = p.status.phase
            if phase in ("Succeeded", "Failed"):
                logger.info(f"Pod {p.metadata.name} completed → spawning next")
                attempt_spawn()

    threading.Thread(target=watch_pods, daemon=True).start()

    def attempt_spawn():
        while size() > 0 and len([p for p in core.list_namespaced_pod(NAMESPACE, label_selector="app=mongo-worker").items if p.status.phase in ("Pending", "Running")]) < MAX_PODS:
            batch = get_batch(RECS_PER_WORKER)
            if not batch:
                break
            spawn_worker(batch)

    # continuous manager loop
    while True:
        attempt_spawn()
        time.sleep(3)
