import yaml
from kubernetes import client, config as kube_config
import os
import numpy as np
import subprocess
from kubernetes import stream
import concurrent.futures
import time

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)['benchmark']
    return config






def create_artifacts(size_artifact: int):
    temp_folder = "temp"
    os.makedirs(temp_folder, exist_ok=True)
    artifact_path = os.path.join(temp_folder, "artifact.npy")
    
    # Create random artifact of fixed size in MB
    size_in_bytes = size_artifact * 1024 * 1024
    num_elements = size_in_bytes // np.dtype(np.float64).itemsize
    random_data = np.random.rand(num_elements)
    
    np.save(artifact_path, random_data)
    print(f"Artifact created at {artifact_path} with size {size_artifact} MB")

def deploy_clients(no_pipeline: int,deployment_name: str):
    kube_config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    deployment_name = deployment_name
    namespace = "default"  # Change this to your namespace if different

    # Get the deployment
    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    
    # Update the number of replicas
    deployment.spec.replicas = no_pipeline
    
    # Apply the updated deployment
    apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)
    print(f"Deployment {deployment_name} scaled to {no_pipeline} replicas")

def status_clients(deployment_name: str, timeout=300, interval=10):
    """Check the status of clients and wait until all pods are ready or timeout is reached."""
    kube_config.load_kube_config()
    core_v1 = client.CoreV1Api()
    namespace = "default"  # Change this to your namespace if different

    # Get the pods in the deployment
    app_name = "cmf-client"
    label_selector = f'app={app_name}'
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        pods = core_v1.list_namespaced_pod(namespace, label_selector=label_selector)
        
        if not pods.items:
            print(f"No pods found with label selector: {label_selector}")
            return False
        
        all_ready = True
        for pod in pods.items:
            pod_name = pod.metadata.name
            ready = False
            for condition in pod.status.conditions:
                if condition.type == "Ready" and condition.status == "True":
                    ready = True
                    break
            if not ready:
                all_ready = False
                print(f"Pod {pod_name} is not ready")
            else:
                print(f"Pod {pod_name} is ready")
        
        if all_ready:
            print("All pods are ready")
            return True
        else:
            print("Some pods are not ready, waiting...")
            time.sleep(interval)
    
    print("Timeout reached, some pods are still not ready")
    return False


def cmf_init(deployment_name: str):
    kube_config.load_kube_config()
    core_v1 = client.CoreV1Api()
    namespace = "default"  # Change this to your namespace if different
    app_name = "cmf-client"
    
    # Get the pods in the deployment
    pods = core_v1.list_namespaced_pod(namespace, label_selector=f'app={app_name}')
    
    if not pods.items:
        print(f"No pods found with label selector: app={app_name}")
        return
    
    script_path = os.path.abspath('cmf_init.sh')
    for pod in pods.items:
        pod_name = pod.metadata.name
        container_name = pod.spec.containers[0].name  # Assuming the script needs to be copied to the first container
        
        # Copy the script to the container
        copy_command = f"kubectl cp {script_path} {namespace}/{pod_name}:/tmp/cmf_init.sh"
        subprocess.run(copy_command, shell=True, check=True)
        
        # Execute the script in the container
        exec_command = ['/bin/sh', '-c', 'chmod +x /tmp/cmf_init.sh && /tmp/cmf_init.sh']
        resp = stream.stream(core_v1.connect_get_namespaced_pod_exec, pod_name, namespace,
                             command=exec_command,
                             container=container_name,
                             stderr=True, stdin=False,
                             stdout=True, tty=False)
        print(f"Executed cmf_init.sh in pod {pod_name}: {resp}")

def copy_pipeline_to_pod(pod_name, namespace):
    """Copy pipeline.py to a specific pod."""
    copy_command = f"kubectl cp pipeline.py {namespace}/{pod_name}:/app/pipeline.py"
    result = subprocess.run(copy_command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Copied pipeline.py to pod {pod_name}")
    else:
        raise RuntimeError(f"Failed to copy pipeline.py to pod {pod_name}: {result.stderr}")

def run_pipeline_in_pod(core_v1, pod_name, namespace, stages, artifact_size, artifact_number, executions):
    """Run pipeline.py in a specific pod."""
    command = (
        f"python3 /app/pipeline.py "
        f"--stages={stages} --artifact_size={artifact_size} "
        f"--artifact_number={artifact_number} --execution={executions}"
    )
    exec_command = ['/bin/sh', '-c', command]
    try:
        resp = stream.stream(
            core_v1.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        print(f"Executed pipeline.py in pod {pod_name}: {resp}")
    except Exception as e:
        raise RuntimeError(f"Error executing pipeline in pod {pod_name}: {e}")

def run_pipeline_in_pods(deployment_name: str, stages: int, artifact_size: int, artifact_number: int, executions: int):
    """Main function to copy and execute pipeline.py in all pods of a deployment."""
    # Load kubeconfig
    kube_config.load_kube_config()
    core_v1 = client.CoreV1Api()
    namespace = "default"  # Change this if your namespace is different
    app_name = "cmf-client"  # Update if using a different app label
    
    # Get pods by label selector
    try:
        pods = core_v1.list_namespaced_pod(namespace, label_selector=f'app={app_name}')
    except Exception as e:
        print(f"Error retrieving pods: {e}")
        return
    
    if not pods.items:
        print(f"No pods found with label selector: app={app_name}")
        return
    
    # Copy pipeline.py to each pod
    print("Copying pipeline.py to pods...")
    for pod in pods.items:
        try:
            copy_pipeline_to_pod(pod.metadata.name, namespace)
        except Exception as e:
            print(f"Failed to copy pipeline.py to pod {pod.metadata.name}: {e}")
    
    # Execute pipeline.py in each pod in parallel
    print("Executing pipeline.py in pods...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor: #configurable number of workers
        futures = [
            executor.submit(
                run_pipeline_in_pod,
                core_v1,
                pod.metadata.name,
                namespace,
                stages,
                artifact_size,
                artifact_number,
                executions
            )
            for pod in pods.items
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error executing pipeline in pod: {e}")
    copy_timing_results_from_pods(pods, namespace,"result")

def copy_timing_results_from_pods(pods, namespace, results_dir):
    os.makedirs(results_dir, exist_ok=True)

    for pod in pods.items:
        pod_name = pod.metadata.name
        copy_command = f"kubectl cp {namespace}/{pod_name}:/app/timing_results/timing_results.log {results_dir}/timing_results_{pod_name}.log"
        result = subprocess.run(copy_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Copied timing results from pod {pod_name}")
        else:
            print(f"Failed to copy timing results from pod {pod_name}: {result.stderr}")

if __name__=='__main__':
    config = load_config('config.yaml')
    print(config)
    no_artifact= config['no_artifact']
    size_artifact = config['size_artifact']
    no_pipeline = config['no_pipeline']
    no_stages = config['no_stages']
    no_excution = config['no_excution']
    client_deployment_name=config['client_deployment_name']
    #start the client deployment of number of pipelines
    deploy_clients(no_pipeline, client_deployment_name)
    #create

    #create_artifacts(size_artifact)

    status_clients(client_deployment_name)
        #check if all pods are ready
        #if all pods are ready break
        #else continue
    
    #cmf_init(client_deployment_name)
    #clean up the client deployment
    run_pipeline_in_pods(client_deployment_name, stages=no_stages, artifact_size=size_artifact, artifact_number=no_artifact, executions=no_excution)
    #clean up the tmp folder

    