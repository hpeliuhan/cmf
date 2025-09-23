#!/bin/bash
set -e

echo "Deploying CMF Server Stack on K3s..."

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
kubectl apply -f 09-configmaps-scripts.yaml

echo "Deploying PostgreSQL..."
kubectl apply -f 02-postgres.yaml

echo "Deploying Neo4j..."
kubectl apply -f 03-neo4j.yaml

echo "Deploying MinIO..."
kubectl apply -f 04-minio.yaml

echo "Deploying TensorBoard..."
kubectl apply -f 05-tensorboard.yaml

echo "Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n cmf --timeout=300s

echo "Deploying CMF Server..."
kubectl apply -f 06-cmf-server.yaml

echo "Waiting for CMF Server to be ready..."
kubectl wait --for=condition=ready pod -l app=cmf-server -n cmf --timeout=300s

echo "Deploying CMF UI..."
kubectl apply -f 07-cmf-ui.yaml

echo "Creating Ingress..."
kubectl apply -f 08-ingress.yaml

echo "Deployment completed!"
echo ""
echo "Services are being deployed. You can check the status with:"
echo "kubectl get pods -n cmf"
echo ""
echo "Once all pods are running, you can access:"
echo "- CMF UI: http://cmf.local"
echo "- CMF API: http://cmf.local/api"
echo "- TensorBoard: http://cmf.local/tensorboard"
echo "- Neo4j: http://neo4j.cmf.local"
echo "- MinIO Console: http://minio.cmf.local"
echo "- MinIO API: http://minio-api.cmf.local"
echo ""
echo "Make sure to add these entries to your /etc/hosts file:"
echo "127.0.0.1 cmf.local neo4j.cmf.local minio.cmf.local minio-api.cmf.local"
