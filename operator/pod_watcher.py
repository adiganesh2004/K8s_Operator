import threading
import time
from kubernetes import client, config, watch
import os

# Load Kubernetes config (inside or outside cluster)
if os.getenv("KUBERNETES_SERVICE_HOST"):
    config.load_incluster_config()
else:
    config.load_kube_config()

core_v1 = client.CoreV1Api()
w = watch.Watch()

# Configurable values
NAMESPACE = os.getenv("POD_NAMESPACE", "default")
LABEL_SELECTOR = os.getenv("LABEL_SELECTOR", "app=mongo-worker")
MAX_PODS = int(os.getenv("MAX_PARALLEL_PODS", "6"))

# Shared state
_free_pod_count = MAX_PODS
_lock = threading.Lock()


def get_free_pod_count():
    """Thread-safe method to get the current number of free worker pods."""
    with _lock:
        return _free_pod_count


def _update_free_pod_count(change: int):
    global _free_pod_count
    with _lock:
        _free_pod_count += change
        # Clamp between 0 and MAX_PODS
        _free_pod_count = max(0, min(MAX_PODS, _free_pod_count))


def pod_watch_loop():
    """Watches pod lifecycle and updates free pod counter accordingly."""
    global _free_pod_count
    print(f"🧵 [PodWatcher] Starting pod watch loop in namespace '{NAMESPACE}'...")

    try:
        for event in w.stream(core_v1.list_namespaced_pod, namespace=NAMESPACE, label_selector=LABEL_SELECTOR):
            pod = event['object']
            event_type = event['type']
            name = pod.metadata.name
            phase = pod.status.phase

            print(f"[{event_type}] Pod: {name}, Phase: {phase}")

            if event_type == "ADDED":
                print(f"🔻 Pod {name} started → decreasing free count")
                _update_free_pod_count(-1)

            elif event_type == "MODIFIED" and phase in ("Succeeded", "Failed"):
                print(f"✅ Pod {name} completed → increasing free count")
                _update_free_pod_count(+1)

    except Exception as e:
        print(f"❌ [PodWatcher] Error: {e}")
    finally:
        print("👋 [PodWatcher] Watch loop stopped.")


def start_pod_watcher_thread():
    """Starts the pod watcher in a separate background thread."""
    thread = threading.Thread(target=pod_watch_loop, daemon=True)
    thread.start()
