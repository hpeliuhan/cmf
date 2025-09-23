#!/bin/bash
set -e

echo "Cleaning up CMF Server Stack from K3s..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not available. Please install kubectl first."
    exit 1
fi

echo "Removing ingress..."
kubectl delete -f 08-ingress.yaml --ignore-not-found=true

echo "Removing CMF UI..."
kubectl delete -f 07-cmf-ui.yaml --ignore-not-found=true

echo "Removing CMF Server..."
kubectl delete -f 06-cmf-server.yaml --ignore-not-found=true

echo "Removing TensorBoard..."
kubectl delete -f 05-tensorboard.yaml --ignore-not-found=true

echo "Removing MinIO..."
kubectl delete -f 04-minio.yaml --ignore-not-found=true

echo "Removing Neo4j..."
kubectl delete -f 03-neo4j.yaml --ignore-not-found=true

echo "Removing PostgreSQL..."
kubectl delete -f 02-postgres.yaml --ignore-not-found=true

echo "Removing configmaps and secrets..."
kubectl delete -f 09-configmaps-scripts.yaml --ignore-not-found=true
kubectl delete -f 01-configmap-secrets.yaml --ignore-not-found=true

echo "Removing namespace..."
kubectl delete -f 00-namespace.yaml --ignore-not-found=true

echo "Cleanup completed!"
echo ""
echo "Note: Persistent volumes may still exist. To delete them:"
echo "kubectl get pv | grep cmf"
echo "kubectl delete pv <pv-name>"
