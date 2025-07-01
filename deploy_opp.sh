#!/bin/bash

set -e 
set -o pipefail

W_IMAGE_NAME="worker_dependent"
W_DOCKERFILE="Dockerfile.workerLog"

DEPLOYMENT_YAML="manifests/opp_dep.yaml"
DEPLOYMENT_NAME="mongo-test"
NAMESPACE="default"

IMAGE_NAME="scaler_assigner"
DOCKERFILE="Dockerfile.opp"

echo "🔨 Building Docker image: $W_IMAGE_NAME"
docker build -t $W_IMAGE_NAME:v8 -f $W_DOCKERFILE .

echo "📦 Loading image into Minikube"
minikube image load $W_IMAGE_NAME:v8

echo "🔨 Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME:v8 -f $DOCKERFILE .

echo "📦 Loading image into Minikube"
minikube image load $IMAGE_NAME:v8

echo "🚀 Applying Kubernetes deployment: $DEPLOYMENT_YAML"
kubectl apply -f $DEPLOYMENT_YAML

# echo "⏳ Waiting for deployment to become ready..."
# kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# echo "📋 Fetching logs from deployment: $DEPLOYMENT_NAME"
# kubectl logs deployment/$DEPLOYMENT_NAME -n $NAMESPACE --tail=100 -f