#!/bin/bash
set -e

echo "Deploying AIM Metadata Server Stack on K3s..."

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

echo "Deploying MinIO..."
kubectl apply -f 03-minio.yaml

echo "Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n aim --timeout=300s

echo "Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n aim --timeout=300s

echo "Deploying AIM Server..."
kubectl apply -f 04-aim-server.yaml

echo "Waiting for AIM Server to be ready..."
kubectl wait --for=condition=ready pod -l app=aim-server -n aim --timeout=600s

echo "Creating Ingress..."
kubectl apply -f 05-ingress.yaml

echo "Deployment completed!"
echo ""
echo "Services are being deployed. You can check the status with:"
echo "kubectl get pods -n aim"
echo ""
echo "Once all pods are running, you can access:"
echo "- AIM UI: http://aim.local"
echo "- AIM API: http://aim-api.local"
echo "- MinIO Console: http://minio-aim.local"
echo "- MinIO API: http://minio-api-aim.local"
echo ""
echo "Make sure to add these entries to your /etc/hosts file:"
echo "127.0.0.1 aim.local aim-api.local minio-aim.local minio-api-aim.local"
echo ""
echo "Default credentials:"
echo "- MinIO: aim / aim123"
echo "- PostgreSQL: aim / aim_password"
