import os
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

# Load Kubernetes config (in-cluster or fallback to kubeconfig for dev)
try:
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
        print("✅ Loaded in-cluster config.")
    else:
        config.load_kube_config()
        print("✅ Loaded kubeconfig from local environment.")
except Exception as e:
    print(f"❌ Failed to load Kubernetes config: {e}")
    exit(1)

# Setup client and watcher
v1 = client.CoreV1Api()
w = watch.Watch()

# Configurable environment variables
NAMESPACE = os.getenv("POD_NAMESPACE", "default")
LABEL_SELECTOR = os.getenv("LABEL_SELECTOR", "app=mongo-worker")

print(f"🔍 Watching pods in namespace '{NAMESPACE}' with label selector '{LABEL_SELECTOR}'")

try:
    for event in w.stream(v1.list_namespaced_pod, namespace=NAMESPACE, label_selector=LABEL_SELECTOR):
        pod = event['object']
        event_type = event['type']
        name = pod.metadata.name
        phase = pod.status.phase

        print(f"[{event_type}] Pod: {name}, Phase: {phase}")

except KeyboardInterrupt:
    print("👋 Watch interrupted by user.")
except ApiException as e:
    print(f"❌ API Error: {e.status} {e.reason}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
finally:
    print("🔚 Watcher stopped.")
