# CMF Server K3s Deployment

This directory contains Kubernetes manifests to deploy the CMF (Common Metadata Framework) server stack on K3s.

## Components

The deployment includes the following components:

1. **PostgreSQL** - Primary database for metadata storage
2. **Neo4j** - Graph database for lineage tracking  
3. **MinIO** - S3-compatible object storage for artifacts
4. **TensorBoard** - Visualization for ML experiments
5. **CMF Server** - Main API server
6. **CMF UI** - Web interface

## Prerequisites

- K3s cluster running
- kubectl configured to access your cluster
- Docker images built for CMF server and UI:
  ```bash
  # Build CMF Server image
  docker build -t server:latest -f server/Dockerfile .
  
  # Build CMF UI image  
  docker build -t ui:latest -f ui/Dockerfile ./ui
  ```

## Configuration

### Secrets and ConfigMaps

Before deploying, you may want to update the secrets in `01-configmap-secrets.yaml`:

```bash
# Generate base64 encoded passwords
echo -n "your_postgres_password" | base64
echo -n "your_neo4j_password" | base64  
echo -n "your_minio_password" | base64
```

### Storage

The deployment uses PersistentVolumeClaims for data persistence:
- PostgreSQL: 10Gi
- Neo4j: 10Gi
- MinIO: 20Gi
- TensorBoard: 5Gi
- CMF Server: 10Gi

## Deployment

### Quick Deploy

Run the deployment script:

```bash
./deploy.sh
```

### Manual Deploy

Apply manifests in order:

```bash
# Create namespace
kubectl apply -f 00-namespace.yaml

# Create configs and secrets
kubectl apply -f 01-configmap-secrets.yaml
kubectl apply -f 09-configmaps-scripts.yaml

# Deploy infrastructure services
kubectl apply -f 02-postgres.yaml
kubectl apply -f 03-neo4j.yaml
kubectl apply -f 04-minio.yaml
kubectl apply -f 05-tensorboard.yaml

# Wait for postgres to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n cmf --timeout=300s

# Deploy application services
kubectl apply -f 06-cmf-server.yaml
kubectl apply -f 07-cmf-ui.yaml

# Create ingress
kubectl apply -f 08-ingress.yaml
```

## Accessing Services

Add these entries to your `/etc/hosts` file:

```
127.0.0.1 cmf.local neo4j.cmf.local minio.cmf.local minio-api.cmf.local
```

Then access:

- **CMF UI**: http://cmf.local
- **CMF API**: http://cmf.local/api
- **TensorBoard**: http://cmf.local/tensorboard
- **Neo4j Browser**: http://neo4j.cmf.local
- **MinIO Console**: http://minio.cmf.local
- **MinIO API**: http://minio-api.cmf.local

## Default Credentials

- **PostgreSQL**: 
  - User: `cmf_user`
  - Password: `cmf_password`
  - Database: `mlmd`

- **Neo4j**:
  - User: `neo4j`
  - Password: `cmf_neo4j`

- **MinIO**:
  - User: `minioadmin`
  - Password: `minioadmin`

## Monitoring

Check deployment status:

```bash
# Check all pods
kubectl get pods -n cmf

# Check services  
kubectl get svc -n cmf

# Check ingress
kubectl get ingress -n cmf

# View logs
kubectl logs -l app=cmf-server -n cmf
kubectl logs -l app=postgres -n cmf
```

## Cleanup

To remove the deployment:

```bash
kubectl delete namespace cmf
```

## Customization

### Resource Limits

Add resource limits to deployments as needed:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi" 
    cpu: "500m"
```

### Load Balancer

To use a LoadBalancer instead of Ingress:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: cmf-ui-lb
spec:
  type: LoadBalancer
  selector:
    app: cmf-ui
  ports:
  - port: 80
    targetPort: 3000
```

### Persistent Volume Configuration

For production use, consider using specific StorageClasses:

```yaml
spec:
  storageClassName: fast-ssd
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```
