#!/usr/bin/env python3
"""
cAdvisor Kubernetes Pod Metrics Collector

This script queries CPU, Memory, and I/O metrics for all pods in a Kubernetes cluster
using the cAdvisor API endpoint and Kubernetes API.

Requirements:
- pip install kubernetes requests pandas psutil
- kubectl configured with cluster access
- cAdvisor running on nodes (usually available at :4194/metrics/cadvisor)

Usage:
    python cadvisor.py [--namespace <namespace>] [--output <format>] [--interval <seconds>]
"""

import argparse
import json
import time
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import requests
from kubernetes import client, config
import pandas as pd
import warnings

# Suppress SSL warnings for development
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KubernetesPodMetricsCollector:
    """Collects pod metrics from Kubernetes cluster using cAdvisor."""
    
    def __init__(self, namespace: Optional[str] = None):
        """
        Initialize the metrics collector.
        
        Args:
            namespace: Specific namespace to monitor, None for all namespaces
        """
        self.namespace = namespace
        self.k8s_v1 = None
        self.nodes = []
        self._init_kubernetes_client()
        self._discover_nodes()
    
    def _init_kubernetes_client(self):
        """Initialize Kubernetes client."""
        try:
            # Try in-cluster config first, then local config
            try:
                config.load_incluster_config()
                logger.info("Using in-cluster Kubernetes configuration")
            except config.ConfigException:
                config.load_kube_config()
                logger.info("Using local Kubernetes configuration")
            
            self.k8s_v1 = client.CoreV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            sys.exit(1)
    
    def _discover_nodes(self):
        """Discover all nodes in the cluster."""
        try:
            nodes_list = self.k8s_v1.list_node()
            self.nodes = []
            
            for node in nodes_list.items:
                node_info = {
                    'name': node.metadata.name,
                    'internal_ip': None,
                    'external_ip': None,
                    'cadvisor_url': None
                }
                
                # Get node IP addresses
                if node.status.addresses:
                    for addr in node.status.addresses:
                        if addr.type == 'InternalIP':
                            node_info['internal_ip'] = addr.address
                        elif addr.type == 'ExternalIP':
                            node_info['external_ip'] = addr.address
                
                # Use internal IP for cAdvisor URL, fallback to external IP
                ip = node_info['internal_ip'] or node_info['external_ip']
                if ip:
                    node_info['cadvisor_url'] = f"http://{ip}:4194"
                
                self.nodes.append(node_info)
                logger.info(f"Discovered node: {node_info['name']} at {ip}")
                
        except Exception as e:
            logger.error(f"Failed to discover nodes: {e}")
            sys.exit(1)
    
    def get_pods(self) -> List[Dict[str, Any]]:
        """Get list of pods to monitor."""
        try:
            if self.namespace:
                pods_list = self.k8s_v1.list_namespaced_pod(self.namespace)
            else:
                pods_list = self.k8s_v1.list_pod_for_all_namespaces()
            
            pods = []
            for pod in pods_list.items:
                if pod.status.phase == 'Running':
                    pod_info = {
                        'name': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'node_name': pod.spec.node_name,
                        'uid': pod.metadata.uid,
                        'containers': [c.name for c in pod.spec.containers],
                        'created': pod.metadata.creation_timestamp
                    }
                    pods.append(pod_info)
            
            logger.info(f"Found {len(pods)} running pods")
            return pods
            
        except Exception as e:
            logger.error(f"Failed to get pods: {e}")
            return []
    
    def _query_cadvisor_metrics(self, node_url: str) -> Optional[Dict]:
        """Query cAdvisor metrics from a specific node."""
        try:
            # Try different cAdvisor endpoints
            endpoints = [
                f"{node_url}/metrics/cadvisor",
                f"{node_url}/api/v1.3/containers",
                f"{node_url}/api/v1.3/machine"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(
                        endpoint, 
                        timeout=10, 
                        verify=False,
                        headers={'Accept': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        if 'application/json' in response.headers.get('content-type', ''):
                            return response.json()
                        else:
                            # Parse Prometheus metrics format
                            return self._parse_prometheus_metrics(response.text)
                except requests.exceptions.RequestException:
                    continue
            
            logger.warning(f"Could not connect to cAdvisor on {node_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error querying cAdvisor metrics from {node_url}: {e}")
            return None
    
    def _parse_prometheus_metrics(self, metrics_text: str) -> Dict:
        """Parse Prometheus format metrics from cAdvisor."""
        metrics = {}
        current_time = time.time()
        
        for line in metrics_text.split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            try:
                # Parse metric line: metric_name{labels} value timestamp
                if '{' in line:
                    metric_part, value_part = line.rsplit(' ', 1)
                    metric_name = metric_part.split('{')[0]
                    labels_str = metric_part.split('{')[1].split('}')[0]
                    
                    # Parse labels
                    labels = {}
                    for label_pair in labels_str.split(','):
                        if '=' in label_pair:
                            key, value = label_pair.split('=', 1)
                            labels[key.strip()] = value.strip('"')
                    
                    # Store metric
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    
                    metrics[metric_name].append({
                        'labels': labels,
                        'value': float(value_part),
                        'timestamp': current_time
                    })
                    
            except (ValueError, IndexError) as e:
                continue
        
        return metrics
    
    def _extract_pod_metrics(self, cadvisor_data: Dict, pod_info: Dict) -> Dict:
        """Extract specific pod metrics from cAdvisor data."""
        pod_metrics = {
            'pod_name': pod_info['name'],
            'namespace': pod_info['namespace'],
            'node_name': pod_info['node_name'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cpu_usage_cores': 0.0,
            'cpu_usage_percent': 0.0,
            'memory_usage_bytes': 0,
            'memory_usage_mb': 0.0,
            'memory_limit_bytes': 0,
            'network_rx_bytes': 0,
            'network_tx_bytes': 0,
            'filesystem_reads_bytes': 0,
            'filesystem_writes_bytes': 0,
            'containers': []
        }
        
        try:
            # Look for container metrics in different cAdvisor response formats
            containers_data = None
            
            if isinstance(cadvisor_data, dict):
                # Check for different response formats
                if 'container_cpu_usage_seconds_total' in cadvisor_data:
                    # Prometheus format
                    pod_metrics.update(self._extract_from_prometheus(cadvisor_data, pod_info))
                elif 'containers' in cadvisor_data:
                    # JSON API format
                    containers_data = cadvisor_data['containers']
                elif isinstance(cadvisor_data, list):
                    containers_data = cadvisor_data
                else:
                    # Direct container data
                    containers_data = cadvisor_data
            
            # Process container data if available
            if containers_data:
                pod_metrics.update(self._extract_from_json_api(containers_data, pod_info))
                    
        except Exception as e:
            logger.error(f"Error extracting metrics for pod {pod_info['name']}: {e}")
        
        return pod_metrics
    
    def _extract_from_prometheus(self, metrics: Dict, pod_info: Dict) -> Dict:
        """Extract metrics from Prometheus format data."""
        result = {}
        
        # CPU metrics
        if 'container_cpu_usage_seconds_total' in metrics:
            cpu_metrics = metrics['container_cpu_usage_seconds_total']
            for metric in cpu_metrics:
                labels = metric.get('labels', {})
                if (labels.get('pod') == pod_info['name'] and 
                    labels.get('namespace') == pod_info['namespace']):
                    result['cpu_usage_cores'] += metric['value']
        
        # Memory metrics
        if 'container_memory_usage_bytes' in metrics:
            memory_metrics = metrics['container_memory_usage_bytes']
            for metric in memory_metrics:
                labels = metric.get('labels', {})
                if (labels.get('pod') == pod_info['name'] and 
                    labels.get('namespace') == pod_info['namespace']):
                    result['memory_usage_bytes'] = metric['value']
                    result['memory_usage_mb'] = metric['value'] / (1024 * 1024)
        
        # Network metrics
        if 'container_network_receive_bytes_total' in metrics:
            network_rx_metrics = metrics['container_network_receive_bytes_total']
            for metric in network_rx_metrics:
                labels = metric.get('labels', {})
                if (labels.get('pod') == pod_info['name'] and 
                    labels.get('namespace') == pod_info['namespace']):
                    result['network_rx_bytes'] += metric['value']
        
        if 'container_network_transmit_bytes_total' in metrics:
            network_tx_metrics = metrics['container_network_transmit_bytes_total']
            for metric in network_tx_metrics:
                labels = metric.get('labels', {})
                if (labels.get('pod') == pod_info['name'] and 
                    labels.get('namespace') == pod_info['namespace']):
                    result['network_tx_bytes'] += metric['value']
        
        # Filesystem metrics
        if 'container_fs_reads_bytes_total' in metrics:
            fs_read_metrics = metrics['container_fs_reads_bytes_total']
            for metric in fs_read_metrics:
                labels = metric.get('labels', {})
                if (labels.get('pod') == pod_info['name'] and 
                    labels.get('namespace') == pod_info['namespace']):
                    result['filesystem_reads_bytes'] += metric['value']
        
        if 'container_fs_writes_bytes_total' in metrics:
            fs_write_metrics = metrics['container_fs_writes_bytes_total']
            for metric in fs_write_metrics:
                labels = metric.get('labels', {})
                if (labels.get('pod') == pod_info['name'] and 
                    labels.get('namespace') == pod_info['namespace']):
                    result['filesystem_writes_bytes'] += metric['value']
        
        return result
    
    def _extract_from_json_api(self, containers_data: List, pod_info: Dict) -> Dict:
        """Extract metrics from JSON API format data."""
        result = {}
        
        # This would need to be implemented based on the actual JSON structure
        # returned by the cAdvisor JSON API
        logger.debug(f"Processing JSON API data for pod {pod_info['name']}")
        
        return result
    
    def collect_metrics(self) -> List[Dict]:
        """Collect metrics for all pods from all nodes."""
        pods = self.get_pods()
        all_metrics = []
        
        for node in self.nodes:
            if not node['cadvisor_url']:
                continue
                
            logger.info(f"Querying metrics from node: {node['name']}")
            cadvisor_data = self._query_cadvisor_metrics(node['cadvisor_url'])
            
            if not cadvisor_data:
                continue
            
            # Find pods running on this node
            node_pods = [p for p in pods if p['node_name'] == node['name']]
            
            for pod in node_pods:
                try:
                    pod_metrics = self._extract_pod_metrics(cadvisor_data, pod)
                    all_metrics.append(pod_metrics)
                    logger.debug(f"Collected metrics for pod: {pod['name']}")
                except Exception as e:
                    logger.error(f"Failed to collect metrics for pod {pod['name']}: {e}")
        
        return all_metrics
    
    def collect_kubectl_metrics(self) -> List[Dict]:
        """Fallback method using kubectl top command."""
        try:
            import subprocess
            
            # Get pod metrics using kubectl top
            cmd = ['kubectl', 'top', 'pods', '--all-namespaces', '--no-headers']
            if self.namespace:
                cmd = ['kubectl', 'top', 'pods', '-n', self.namespace, '--no-headers']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"kubectl top failed: {result.stderr}")
                return []
            
            metrics = []
            current_time = datetime.now(timezone.utc).isoformat()
            
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 4:
                    if self.namespace:
                        namespace = self.namespace
                        pod_name, cpu, memory = parts[0], parts[1], parts[2]
                    else:
                        namespace, pod_name, cpu, memory = parts[0], parts[1], parts[2], parts[3]
                    
                    # Parse CPU (remove 'm' for millicores)
                    cpu_cores = 0.0
                    if cpu.endswith('m'):
                        cpu_cores = float(cpu[:-1]) / 1000
                    else:
                        cpu_cores = float(cpu)
                    
                    # Parse memory (handle Mi, Gi suffixes)
                    memory_mb = 0.0
                    if memory.endswith('Mi'):
                        memory_mb = float(memory[:-2])
                    elif memory.endswith('Gi'):
                        memory_mb = float(memory[:-2]) * 1024
                    elif memory.endswith('Ki'):
                        memory_mb = float(memory[:-2]) / 1024
                    
                    metrics.append({
                        'pod_name': pod_name,
                        'namespace': namespace,
                        'timestamp': current_time,
                        'cpu_usage_cores': cpu_cores,
                        'memory_usage_mb': memory_mb,
                        'memory_usage_bytes': memory_mb * 1024 * 1024,
                        'source': 'kubectl_top'
                    })
            
            logger.info(f"Collected metrics for {len(metrics)} pods using kubectl top")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics using kubectl: {e}")
            return []


def format_output(metrics: List[Dict], output_format: str) -> str:
    """Format metrics for output."""
    if not metrics:
        return "No metrics collected"
    
    if output_format == 'json':
        return json.dumps(metrics, indent=2)
    
    elif output_format == 'csv':
        df = pd.DataFrame(metrics)
        return df.to_csv(index=False)
    
    elif output_format == 'table':
        df = pd.DataFrame(metrics)
        # Select key columns for display
        display_columns = [
            'pod_name', 'namespace', 'cpu_usage_cores', 
            'memory_usage_mb', 'network_rx_bytes', 'network_tx_bytes'
        ]
        available_columns = [col for col in display_columns if col in df.columns]
        return df[available_columns].to_string(index=False)
    
    else:  # summary format
        summary = []
        summary.append(f"Pod Metrics Summary ({len(metrics)} pods)")
        summary.append("=" * 50)
        
        for metric in metrics:
            summary.append(f"Pod: {metric['pod_name']} (Namespace: {metric['namespace']})")
            summary.append(f"  CPU: {metric.get('cpu_usage_cores', 0):.3f} cores")
            summary.append(f"  Memory: {metric.get('memory_usage_mb', 0):.1f} MB")
            if 'network_rx_bytes' in metric:
                summary.append(f"  Network RX: {metric['network_rx_bytes']:,} bytes")
            if 'network_tx_bytes' in metric:
                summary.append(f"  Network TX: {metric['network_tx_bytes']:,} bytes")
            summary.append("")
        
        return "\n".join(summary)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Collect Kubernetes pod metrics using cAdvisor',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--namespace', '-n',
        help='Specific namespace to monitor (default: all namespaces)'
    )
    
    parser.add_argument(
        '--output', '-o',
        choices=['json', 'csv', 'table', 'summary'],
        default='summary',
        help='Output format (default: summary)'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=0,
        help='Collection interval in seconds (0 = single collection, default: 0)'
    )
    
    parser.add_argument(
        '--use-kubectl',
        action='store_true',
        help='Use kubectl top instead of cAdvisor (fallback method)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize collector
    collector = KubernetesPodMetricsCollector(namespace=args.namespace)
    
    try:
        if args.interval > 0:
            logger.info(f"Starting continuous collection every {args.interval} seconds")
            while True:
                if args.use_kubectl:
                    metrics = collector.collect_kubectl_metrics()
                else:
                    metrics = collector.collect_metrics()
                    if not metrics:
                        logger.warning("No metrics from cAdvisor, falling back to kubectl")
                        metrics = collector.collect_kubectl_metrics()
                
                print(f"\n--- Metrics collected at {datetime.now()} ---")
                print(format_output(metrics, args.output))
                print(f"--- End of metrics ---\n")
                
                time.sleep(args.interval)
        else:
            # Single collection
            if args.use_kubectl:
                metrics = collector.collect_kubectl_metrics()
            else:
                metrics = collector.collect_metrics()
                if not metrics:
                    logger.warning("No metrics from cAdvisor, falling back to kubectl")
                    metrics = collector.collect_kubectl_metrics()
            
            print(format_output(metrics, args.output))
    
    except KeyboardInterrupt:
        logger.info("Collection stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
