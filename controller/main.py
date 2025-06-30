import kopf
import kubernetes
import os

# Load Kubernetes configuration from within the cluster
kubernetes.config.load_incluster_config()

# Initialize the Kubernetes Batch API client (used to create Job resources)
batch_api = kubernetes.client.BatchV1Api()

# Handler triggered when a MongoDBQueue custom resource is created
@kopf.on.create('yourdomain.com', 'v1', 'mongodbqueues')
def create_worker_job(spec, name, namespace, **kwargs):
    """
    Create a Kubernetes Job to process a batch of MongoDB record IDs
    when a MongoDBQueue custom resource is created.
    """

    # Extract the list of MongoDB record IDs from the CR spec
    record_ids = spec.get("recordIds")

    # Validate that recordIds is a non-empty list
    if not record_ids or not isinstance(record_ids, list):
        raise kopf.TemporaryError("Missing or invalid 'recordIds' in spec", delay=10)

    # Convert the list of record IDs to a comma-separated string
    record_ids_str = ','.join(record_ids)

    # Define the Kubernetes Job manifest
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
                            {'name': 'RECORD_IDS', 'value': record_ids_str}
                        ]
                    }],
                    'restartPolicy': 'Never'
                }
            },
            'backoffLimit': 4
        }
    }

    # Attempt to create the Job in Kubernetes
    try:
        batch_api.create_namespaced_job(namespace=namespace, body=job_manifest)

        # Log success using Kopf
        kopf.info(
            body=job_manifest,
            reason='JobCreated',
            message=f"Worker job created for recordIds: {record_ids}"
        )

        print(f"Job 'worker-job-{name}' created in namespace '{namespace}' for IDs: {record_ids}")

    except kubernetes.client.exceptions.ApiException as api_error:
        # Log failure and raise a retryable error
        error_message = (
            f"Failed to create Job 'worker-job-{name}' in namespace '{namespace}': {api_error.reason}"
        )
        print(error_message)
        raise kopf.TemporaryError(error_message, delay=15)
