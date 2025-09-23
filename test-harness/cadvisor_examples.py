#!/usr/bin/env python3
"""
Example usage of the cAdvisor Pod Metrics Collector

This script demonstrates different ways to use the cadvisor.py script
and shows how to process the collected metrics data.
"""

import subprocess
import json
import time
from datetime import datetime


def run_cadvisor_command(args):
    """Run the cadvisor script with given arguments."""
    cmd = ['python3', 'cadvisor.py'] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Command timed out", 1


def example_basic_collection():
    """Example: Basic metrics collection."""
    print("=== Basic Metrics Collection ===")
    stdout, stderr, returncode = run_cadvisor_command(['--output', 'summary'])
    
    if returncode == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")


def example_namespace_specific():
    """Example: Collect metrics for specific namespace."""
    print("\n=== Namespace-Specific Collection (kube-system) ===")
    stdout, stderr, returncode = run_cadvisor_command([
        '--namespace', 'kube-system',
        '--output', 'table'
    ])
    
    if returncode == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")


def example_json_output():
    """Example: Get JSON output for programmatic processing."""
    print("\n=== JSON Output Example ===")
    stdout, stderr, returncode = run_cadvisor_command([
        '--output', 'json',
        '--namespace', 'default'
    ])
    
    if returncode == 0:
        try:
            metrics = json.loads(stdout)
            print(f"Collected metrics for {len(metrics)} pods:")
            for metric in metrics[:3]:  # Show first 3 pods
                print(f"  - {metric['pod_name']}: "
                      f"CPU: {metric.get('cpu_usage_cores', 0):.3f} cores, "
                      f"Memory: {metric.get('memory_usage_mb', 0):.1f} MB")
        except json.JSONDecodeError:
            print("Failed to parse JSON output")
    else:
        print(f"Error: {stderr}")


def example_continuous_monitoring():
    """Example: Continuous monitoring for a short period."""
    print("\n=== Continuous Monitoring (30 seconds) ===")
    print("Starting 30-second monitoring with 10-second intervals...")
    
    start_time = time.time()
    while time.time() - start_time < 30:
        stdout, stderr, returncode = run_cadvisor_command([
            '--output', 'summary',
            '--namespace', 'default'
        ])
        
        if returncode == 0:
            print(f"\n--- {datetime.now().strftime('%H:%M:%S')} ---")
            # Just show the first few lines
            lines = stdout.split('\n')[:10]
            print('\n'.join(lines))
        else:
            print(f"Error: {stderr}")
        
        time.sleep(10)


def example_kubectl_fallback():
    """Example: Using kubectl fallback method."""
    print("\n=== Using kubectl top (Fallback Method) ===")
    stdout, stderr, returncode = run_cadvisor_command([
        '--use-kubectl',
        '--output', 'table'
    ])
    
    if returncode == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")


def example_csv_export():
    """Example: Export metrics to CSV format."""
    print("\n=== CSV Export Example ===")
    stdout, stderr, returncode = run_cadvisor_command([
        '--output', 'csv',
        '--namespace', 'kube-system'
    ])
    
    if returncode == 0:
        # Save to file
        with open('pod_metrics.csv', 'w') as f:
            f.write(stdout)
        print("Metrics exported to pod_metrics.csv")
        print("First few lines:")
        print('\n'.join(stdout.split('\n')[:5]))
    else:
        print(f"Error: {stderr}")


def main():
    """Run all examples."""
    print("cAdvisor Pod Metrics Collector - Usage Examples")
    print("=" * 60)
    
    # Check if the cadvisor script exists
    try:
        with open('cadvisor.py', 'r') as f:
            pass
    except FileNotFoundError:
        print("Error: cadvisor.py not found in current directory")
        return
    
    # Run examples
    try:
        example_basic_collection()
        example_namespace_specific()
        example_json_output()
        example_kubectl_fallback()
        example_csv_export()
        
        # Ask before running continuous monitoring
        response = input("\nRun continuous monitoring example? (y/N): ")
        if response.lower() == 'y':
            example_continuous_monitoring()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == '__main__':
    main()
