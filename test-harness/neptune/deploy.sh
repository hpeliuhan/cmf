#!/bin/bash
set -e

echo "Deploying Neptune Metadata Server Stack on K3s..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not available. Please install kubectl first."
    exit 1
fi

# Apply configurations in order
echo "Creating namespace..."
kubectl apply -f 00-namespace.yaml

echo "Creating configmaps and secrets..."
kubectl apply -f 01-configmap-secrets.yaml

echo "Deploying PostgreSQL..."
kubectl apply -f 02-postgres.yaml

echo "Deploying Redis..."
kubectl apply -f 03-redis.yaml

echo "Deploying MinIO..."
kubectl apply -f 04-minio.yaml

echo "Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n neptune --timeout=300s

echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n neptune --timeout=300s

echo "Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n neptune --timeout=300s

echo "Deploying Neptune Server..."
kubectl apply -f 05-neptune-server.yaml

echo "Waiting for Neptune Server to be ready..."
kubectl wait --for=condition=ready pod -l app=neptune-server -n neptune --timeout=600s

echo "Creating Ingress..."
kubectl apply -f 06-ingress.yaml

echo "Deployment completed!"
echo ""
echo "Services are being deployed. You can check the status with:"
echo "kubectl get pods -n neptune"
echo ""
echo "Once all pods are running, you can access:"
echo "- Neptune API: http://neptune.local"
echo "- MinIO Console: http://minio-neptune.local"
echo "- MinIO API: http://minio-api-neptune.local"
echo ""
echo "Make sure to add these entries to your /etc/hosts file:"
echo "127.0.0.1 neptune.local minio-neptune.local minio-api-neptune.local"
echo ""
echo "Default credentials:"
echo "- MinIO: neptune / neptune123"
echo "- PostgreSQL: neptune / neptune_password"
echo "- Redis: neptune_redis"
