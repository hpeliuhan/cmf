# Kubernetes Pod Metrics Collector using cAdvisor

This directory contains scripts and configurations for collecting CPU, Memory, and I/O metrics from Kubernetes pods using cAdvisor.

## Files Overview

- `cadvisor.py` - Main metrics collection script
- `cadvisor_examples.py` - Usage examples and demonstrations
- `cadvisor-daemonset.yaml` - Kubernetes DaemonSet to deploy cAdvisor
- `requirements-cadvisor.txt` - Python dependencies
- `README-cadvisor.md` - This documentation

## Prerequisites

### 1. Kubernetes Cluster Access
Ensure you have `kubectl` configured and can access your cluster:
```bash
kubectl cluster-info
kubectl get nodes
```

### 2. Python Dependencies
Install required Python packages:
```bash
pip install -r requirements-cadvisor.txt
```

### 3. cAdvisor Deployment (Optional)
Deploy cAdvisor as a DaemonSet if not already available:
```bash
kubectl apply -f cadvisor-daemonset.yaml
```

Verify cAdvisor is running:
```bash
kubectl get pods -n kube-system -l app=cadvisor
```

## Usage

### Basic Usage

```bash
# Collect metrics for all pods in all namespaces
python3 cadvisor.py

# Collect metrics for a specific namespace
python3 cadvisor.py --namespace kube-system

# Use different output formats
python3 cadvisor.py --output json
python3 cadvisor.py --output csv
python3 cadvisor.py --output table
```

### Advanced Usage

```bash
# Continuous monitoring every 30 seconds
python3 cadvisor.py --interval 30

# Use kubectl top as fallback (when cAdvisor unavailable)
python3 cadvisor.py --use-kubectl

# Verbose logging
python3 cadvisor.py --verbose

# Export to CSV file
python3 cadvisor.py --output csv > pod_metrics.csv
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--namespace, -n` | Specific namespace to monitor | All namespaces |
| `--output, -o` | Output format (json/csv/table/summary) | summary |
| `--interval, -i` | Collection interval in seconds (0 = once) | 0 |
| `--use-kubectl` | Use kubectl top instead of cAdvisor | False |
| `--verbose, -v` | Enable verbose logging | False |

## Collected Metrics

### CPU Metrics
- `cpu_usage_cores` - Current CPU usage in cores
- `cpu_usage_percent` - CPU usage percentage (when available)

### Memory Metrics
- `memory_usage_bytes` - Current memory usage in bytes
- `memory_usage_mb` - Current memory usage in MB
- `memory_limit_bytes` - Memory limit (when available)

### Network I/O Metrics
- `network_rx_bytes` - Total bytes received
- `network_tx_bytes` - Total bytes transmitted

### Filesystem I/O Metrics
- `filesystem_reads_bytes` - Total bytes read from filesystem
- `filesystem_writes_bytes` - Total bytes written to filesystem

### Metadata
- `pod_name` - Name of the pod
- `namespace` - Kubernetes namespace
- `node_name` - Node where pod is running
- `timestamp` - Collection timestamp
- `containers` - List of container names in the pod

## Output Formats

### Summary Format (Default)
Human-readable summary showing key metrics for each pod:
```
Pod Metrics Summary (5 pods)
==================================================
Pod: coredns-558bd4d5db-abc123 (Namespace: kube-system)
  CPU: 0.002 cores
  Memory: 13.5 MB
  Network RX: 1,234,567 bytes
  Network TX: 987,654 bytes
```

### JSON Format
Machine-readable JSON for programmatic processing:
```json
[
  {
    "pod_name": "coredns-558bd4d5db-abc123",
    "namespace": "kube-system",
    "cpu_usage_cores": 0.002,
    "memory_usage_mb": 13.5,
    "timestamp": "2025-09-23T10:30:00Z"
  }
]
```

### CSV Format
Spreadsheet-compatible format:
```csv
pod_name,namespace,cpu_usage_cores,memory_usage_mb,timestamp
coredns-558bd4d5db-abc123,kube-system,0.002,13.5,2025-09-23T10:30:00Z
```

### Table Format
Tabular display using pandas:
```
                    pod_name    namespace  cpu_usage_cores  memory_usage_mb
0  coredns-558bd4d5db-abc123  kube-system             0.002             13.5
```

## Examples

Run the examples script to see the collector in action:
```bash
python3 cadvisor_examples.py
```

### Programmatic Usage

```python
from cadvisor import KubernetesPodMetricsCollector

# Initialize collector
collector = KubernetesPodMetricsCollector(namespace='default')

# Collect metrics once
metrics = collector.collect_metrics()

# Use kubectl fallback if cAdvisor unavailable
if not metrics:
    metrics = collector.collect_kubectl_metrics()

# Process metrics
for metric in metrics:
    print(f"Pod {metric['pod_name']}: "
          f"CPU: {metric['cpu_usage_cores']:.3f} cores, "
          f"Memory: {metric['memory_usage_mb']:.1f} MB")
```

## Troubleshooting

### cAdvisor Not Available
If cAdvisor is not available on your cluster, the script will automatically fall back to using `kubectl top pods`:

```bash
# Force kubectl mode
python3 cadvisor.py --use-kubectl
```

### Permission Issues
Ensure your kubectl context has sufficient permissions:
```bash
# Check permissions
kubectl auth can-i get pods --all-namespaces
kubectl auth can-i get nodes

# Check current context
kubectl config current-context
```

### Network Connectivity
If cAdvisor endpoints are not accessible, check:
```bash
# Check if cAdvisor pods are running
kubectl get pods -n kube-system -l app=cadvisor

# Check node IPs
kubectl get nodes -o wide

# Test cAdvisor endpoint (replace NODE_IP)
curl http://NODE_IP:4194/metrics/cadvisor
```

### Common Error Messages

| Error | Solution |
|-------|----------|
| "Failed to initialize Kubernetes client" | Check kubectl configuration |
| "Could not connect to cAdvisor" | Use `--use-kubectl` flag |
| "No metrics collected" | Check pod status and permissions |
| "kubectl top failed" | Ensure metrics-server is installed |

## Metrics Server Setup

If `kubectl top` is not working, install metrics-server:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For development clusters, you might need to disable TLS:
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

## Integration with Monitoring Systems

### Prometheus Integration
Export metrics to Prometheus format:
```python
# Custom Prometheus exporter example
from prometheus_client import CollectorRegistry, Gauge, generate_latest

registry = CollectorRegistry()
cpu_gauge = Gauge('pod_cpu_usage_cores', 'Pod CPU usage in cores', 
                  ['pod_name', 'namespace'], registry=registry)
memory_gauge = Gauge('pod_memory_usage_bytes', 'Pod memory usage in bytes',
                     ['pod_name', 'namespace'], registry=registry)

# Collect metrics and update gauges
collector = KubernetesPodMetricsCollector()
metrics = collector.collect_metrics()

for metric in metrics:
    cpu_gauge.labels(
        pod_name=metric['pod_name'], 
        namespace=metric['namespace']
    ).set(metric['cpu_usage_cores'])
    
    memory_gauge.labels(
        pod_name=metric['pod_name'], 
        namespace=metric['namespace']
    ).set(metric['memory_usage_bytes'])

# Generate Prometheus metrics
print(generate_latest(registry).decode())
```

### Grafana Dashboard
Use the JSON output to create Grafana dashboards:
```bash
# Collect metrics and send to time-series database
python3 cadvisor.py --output json | jq '.[].cpu_usage_cores'
```

## Performance Considerations

- **Collection Frequency**: Don't collect too frequently (recommended: 30+ seconds)
- **Namespace Filtering**: Use `--namespace` to reduce data volume
- **Output Format**: JSON is most efficient for large datasets
- **Network Overhead**: cAdvisor queries can be network-intensive

## Security Considerations

- The script requires cluster-wide read permissions
- cAdvisor exposes detailed system information
- Consider using service accounts with minimal required permissions
- Network policies may block cAdvisor access

## License

This monitoring suite follows the same license as the parent CMF project.
