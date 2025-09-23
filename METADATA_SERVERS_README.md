# Metadata Servers K3s Deployment Suite

This repository contains Kubernetes (K3s) deployment configurations for multiple metadata tracking and experiment management platforms:

- **CMF (Common Metadata Framework)** - HPE's metadata framework
- **MLflow** - Popular ML experiment tracking platform
- **Weights & Biases (W&B)** - Commercial ML experiment tracking and visualization
- **Neptune** - Cloud-based experiment management platform (self-hosted)
- **AIM** - Open-source experiment tracking and visualization

## Architecture Overview

Each deployment includes:

### Core Components
- **PostgreSQL** - Primary database for metadata storage
- **MinIO** - S3-compatible object storage for artifacts
- **Redis** - Caching layer (where applicable)
- **Web UI** - Dashboard for visualization and management
- **API Server** - RESTful API endpoints

### Platform-Specific Components
- **CMF**: Neo4j for graph relationships, TensorBoard integration
- **MLflow**: Built-in artifact serving capabilities
- **W&B**: Advanced collaboration and team features
- **Neptune**: Custom metadata API server
- **AIM**: File-based storage with optional database backend

## Quick Start

### Prerequisites

1. **K3s cluster running**:
   ```bash
   curl -sfL https://get.k3s.io | sh -
   ```

2. **kubectl configured**:
   ```bash
   sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
   sudo chown $USER ~/.kube/config
   ```

3. **Add hosts entries** (for each platform you want to deploy):
   ```bash
   # Add to /etc/hosts
   127.0.0.1 cmf.local neo4j.cmf.local minio.cmf.local minio-api.cmf.local
   127.0.0.1 mlflow.local minio-mlflow.local minio-api-mlflow.local
   127.0.0.1 wandb.local minio-wandb.local minio-api-wandb.local
   127.0.0.1 neptune.local minio-neptune.local minio-api-neptune.local
   127.0.0.1 aim.local aim-api.local minio-aim.local minio-api-aim.local
   ```

### Deployment Commands

Choose one or more platforms to deploy:

```bash
# Deploy CMF Server
cd k3s && ./deploy.sh

# Deploy MLflow
cd k3s-mlflow && ./deploy.sh

# Deploy Weights & Biases
cd k3s-wandb && ./deploy.sh

# Deploy Neptune
cd k3s-neptune && ./deploy.sh

# Deploy AIM
cd k3s-aim && ./deploy.sh
```

## Platform Access URLs

| Platform | Web UI | API | MinIO Console | Default Credentials |
|----------|--------|-----|---------------|-------------------|
| **CMF** | http://cmf.local | http://cmf.local/api | http://minio.cmf.local | postgres: cmf_user/cmf_password<br>minio: minioadmin/minioadmin |
| **MLflow** | http://mlflow.local | http://mlflow.local/api | http://minio-mlflow.local | postgres: mlflow_user/mlflow_password<br>minio: minio/minio123 |
| **W&B** | http://wandb.local | http://wandb.local/api | http://minio-wandb.local | postgres: wandb/wandb_password<br>minio: wandb/wandb123 |
| **Neptune** | http://neptune.local | http://neptune.local/api | http://minio-neptune.local | postgres: neptune/neptune_password<br>minio: neptune/neptune123 |
| **AIM** | http://aim.local | http://aim-api.local | http://minio-aim.local | postgres: aim/aim_password<br>minio: aim/aim123 |

## Storage Requirements

Default storage allocations per platform:

| Platform | PostgreSQL | MinIO | Additional | Total |
|----------|------------|-------|------------|-------|
| **CMF** | 10Gi | 20Gi | Neo4j: 10Gi, TensorBoard: 5Gi, Server: 10Gi | 55Gi |
| **MLflow** | 10Gi | 50Gi | - | 60Gi |
| **W&B** | 20Gi | 100Gi | Redis: 5Gi | 125Gi |
| **Neptune** | 20Gi | 100Gi | Redis: 5Gi, Storage: 50Gi | 175Gi |
| **AIM** | 10Gi | 50Gi | Repo: 20Gi | 80Gi |

## Configuration Customization

### Security (Production Setup)

1. **Update passwords** in `*-configmap-secrets.yaml`:
   ```bash
   echo -n "your_secure_password" | base64
   ```

2. **Enable TLS** in ingress configurations:
   ```yaml
   spec:
     tls:
     - hosts:
       - your-domain.com
       secretName: tls-secret
   ```

3. **Resource limits** in deployment files:
   ```yaml
   resources:
     requests:
       memory: "1Gi"
       cpu: "500m"
     limits:
       memory: "2Gi"
       cpu: "1000m"
   ```

### Storage Classes

For production, specify storage classes:

```yaml
spec:
  storageClassName: fast-ssd
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

## Monitoring and Troubleshooting

### Check Deployment Status

```bash
# Check all pods across namespaces
kubectl get pods --all-namespaces

# Check specific platform
kubectl get pods -n cmf
kubectl get pods -n mlflow
kubectl get pods -n wandb
kubectl get pods -n neptune
kubectl get pods -n aim

# Check services and ingress
kubectl get svc,ingress -n <namespace>
```

### View Logs

```bash
# Application logs
kubectl logs -f deployment/<app-name> -n <namespace>

# Database logs
kubectl logs -f deployment/postgres -n <namespace>

# Storage logs
kubectl logs -f deployment/minio -n <namespace>
```

### Common Issues

1. **Pods stuck in Pending**: Check storage availability
   ```bash
   kubectl describe pvc -n <namespace>
   ```

2. **Init containers failing**: Check network connectivity
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   ```

3. **Service not accessible**: Verify ingress and hosts file
   ```bash
   kubectl get ingress -n <namespace>
   curl -H "Host: app.local" http://localhost
   ```

## Cleanup

Remove specific platforms:

```bash
# Remove individual platforms
kubectl delete namespace cmf
kubectl delete namespace mlflow
kubectl delete namespace wandb
kubectl delete namespace neptune
kubectl delete namespace aim

# Or use cleanup scripts (if available)
cd k3s && ./cleanup.sh
```

## Integration Examples

### Python Client Examples

#### MLflow
```python
import mlflow
mlflow.set_tracking_uri("http://mlflow.local")

with mlflow.start_run():
    mlflow.log_param("alpha", 0.5)
    mlflow.log_metric("rmse", 0.8)
```

#### Weights & Biases
```python
import wandb
wandb.init(project="test", host="http://wandb.local")
wandb.log({"accuracy": 0.9})
```

#### Neptune
```python
import neptune
run = neptune.init_run(api_url="http://neptune.local")
run["accuracy"] = 0.95
```

#### AIM
```python
from aim import Run
run = Run(repo="http://aim-api.local")
run.track(0.9, name="accuracy")
```

## Advanced Configuration

### Multi-Node Setup

For production multi-node deployments, consider:

1. **Shared storage** (NFS, Ceph, or cloud storage)
2. **Database clustering** (PostgreSQL HA)
3. **Load balancing** (multiple replicas)
4. **Monitoring** (Prometheus + Grafana)

### Backup Strategies

1. **Database backups**:
   ```bash
   kubectl exec -it postgres-pod -n <namespace> -- pg_dump -U <user> <db> > backup.sql
   ```

2. **Object storage sync**:
   ```bash
   kubectl exec -it minio-pod -n <namespace> -- mc mirror /data /backup
   ```

## License

This deployment suite is provided under the same license terms as the respective upstream projects.

## Support

For issues specific to:
- **CMF**: Check the [CMF repository](https://github.com/HewlettPackard/cmf)
- **MLflow**: Check [MLflow documentation](https://mlflow.org/)
- **W&B**: Check [W&B documentation](https://docs.wandb.ai/)
- **Neptune**: Check [Neptune documentation](https://docs.neptune.ai/)
- **AIM**: Check [AIM documentation](https://aimstack.io/)

For K3s deployment issues, check the individual platform deployment directories.
