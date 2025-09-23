#!/bin/bash
set -e

echo "Deploying MLflow Server Stack on K3s..."

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
kubectl wait --for=condition=ready pod -l app=postgres -n mlflow --timeout=300s

echo "Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n mlflow --timeout=300s

echo "Deploying MLflow Server..."
kubectl apply -f 04-mlflow-server.yaml

echo "Waiting for MLflow Server to be ready..."
kubectl wait --for=condition=ready pod -l app=mlflow-server -n mlflow --timeout=600s

echo "Creating Ingress..."
kubectl apply -f 05-ingress.yaml

echo "Deployment completed!"
echo ""
echo "Services are being deployed. You can check the status with:"
echo "kubectl get pods -n mlflow"
echo ""
echo "Once all pods are running, you can access:"
echo "- MLflow UI: http://mlflow.local"
echo "- MinIO Console: http://minio-mlflow.local"
echo "- MinIO API: http://minio-api-mlflow.local"
echo ""
echo "Make sure to add these entries to your /etc/hosts file:"
echo "127.0.0.1 mlflow.local minio-mlflow.local minio-api-mlflow.local"
echo ""
echo "Default MinIO credentials:"
echo "- Username: minio"
echo "- Password: minio123"
