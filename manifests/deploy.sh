#!/bin/bash

set -e
set -o pipefail

NAMESPACE="default"

### --- Mongo Worker --- ###
WORKER_IMAGE="mongo-worker:latest"
WORKER_DOCKERFILE="Dockerfile.worker"


echo "🔨 Building image: $WORKER_IMAGE"
docker build -t $WORKER_IMAGE -f $WORKER_DOCKERFILE .

echo "📦 Loading $WORKER_IMAGE into Minikube"
minikube image load $WORKER_IMAGE


### --- Mongo Scaler --- ###
SCALER_IMAGE="mongo-operator:latest"
SCALER_DOCKERFILE="Dockerfile.opp"
SCALER_DEPLOYMENT_YAML="manifests/scaler_dep.yaml"
SCALER_DEPLOYMENT_NAME="mongo-scaler"

echo "🔨 Building image: $SCALER_IMAGE"
docker build -t $SCALER_IMAGE -f $SCALER_DOCKERFILE .

echo "📦 Loading $SCALER_IMAGE into Minikube"
minikube image load $SCALER_IMAGE

echo "🚀 Applying $SCALER_DEPLOYMENT_YAML"
kubectl apply -f $SCALER_DEPLOYMENT_YAML

echo "⏳ Waiting for $SCALER_DEPLOYMENT_NAME to be ready..."
kubectl rollout status deployment/$SCALER_DEPLOYMENT_NAME -n $NAMESPACE

### --- Logs (Optional Tail) --- ###
# echo "📋 Fetching logs for $WORKER_DEPLOYMENT_NAME"
# kubectl logs deployment/$WORKER_DEPLOYMENT_NAME -n $NAMESPACE --tail=100 -f &

# echo "📋 Fetching logs for $SCALER_DEPLOYMENT_NAME"
# kubectl logs deployment/$SCALER_DEPLOYMENT_NAME -n $NAMESPACE --tail=100 -f
