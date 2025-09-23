#!/bin/bash
set -e

echo "Deploying Weights & Biases (W&B) Server Stack on K3s..."

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
kubectl wait --for=condition=ready pod -l app=postgres -n wandb --timeout=300s

echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n wandb --timeout=300s

echo "Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n wandb --timeout=300s

echo "Deploying W&B Server..."
kubectl apply -f 05-wandb-server.yaml

echo "Waiting for W&B Server to be ready..."
kubectl wait --for=condition=ready pod -l app=wandb-server -n wandb --timeout=600s

echo "Creating Ingress..."
kubectl apply -f 06-ingress.yaml

echo "Deployment completed!"
echo ""
echo "Services are being deployed. You can check the status with:"
echo "kubectl get pods -n wandb"
echo ""
echo "Once all pods are running, you can access:"
echo "- W&B UI: http://wandb.local"
echo "- MinIO Console: http://minio-wandb.local"
echo "- MinIO API: http://minio-api-wandb.local"
echo ""
echo "Make sure to add these entries to your /etc/hosts file:"
echo "127.0.0.1 wandb.local minio-wandb.local minio-api-wandb.local"
echo ""
echo "Default credentials:"
echo "- W&B: Create account through the web interface"
echo "- MinIO: wandb / wandb123"
echo "- PostgreSQL: wandb / wandb_password"
echo "- Redis: redis_password"
