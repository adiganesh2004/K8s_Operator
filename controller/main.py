import kopf
import kubernetes
import os

# Load in-cluster Kubernetes configuration so the operator can interact with the API
kubernetes.config.load_incluster_config()

# Create a Kubernetes Batch API client to create Job resources
batch_api = kubernetes.client.BatchV1Api()

# Register a handler for when a MongoDBQueue resource is created
@kopf.on.create('yourdomain.com', 'v1', 'mongodbqueues')
def create_worker_job(spec, name, namespace, **kwargs):
    record_id = spec.get("recordId")
    if not record_id:
        raise kopf.TemporaryError("Missing recordId in spec", delay=10)

    job_manifest = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': f'worker-job-{name}',
            'namespace': namespace
        },
        'spec': {
            'template': {
                'metadata': {
                    'labels': {
                        'app': 'worker-job'
                    }
                },
                'spec': {
                    'containers': [{
                        'name': 'worker',
                        'image': 'adiganesh2004/worker-app:latest',
                        'env': [
                            {'name': 'MONGO_URL', 'value': 'mongodb://mongodb-service:27017'},
                            {'name': 'RECORD_ID', 'value': record_id}
                        ]
                    }],
                    'restartPolicy': 'Never'
                }
            },
            'backoffLimit': 4
        }
    }

    batch_api.create_namespaced_job(namespace=namespace, body=job_manifest)
    kopf.info(body=job_manifest, reason='JobCreated', message=f"Created worker job for recordId: {record_id}")

