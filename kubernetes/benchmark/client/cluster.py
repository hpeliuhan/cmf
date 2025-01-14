import os
from kubernetes import client, config as kube_config
import subprocess
from kubernetes import stream
import yaml
import shutil
import time
from minio import Minio
from minio.error import S3Error
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import paramiko

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

###############Reset server#################
#######minio###########
def create_bucket(bucket_name, endpoint, access_key, secret_key):
    """Create a MinIO bucket."""
    # Initialize the MinIO client
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False  # Set to True if using HTTPS
    )

    try:
        # Check if the bucket already exists
        if client.bucket_exists(bucket_name):
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            # Create the bucket
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created successfully.")
    except S3Error as e:
        print(f"Error: {e}")

def reset_minio(config):
    endpoint = config['server_cluster']['minio']['endpoint']
    access_key = config['server_cluster']['minio']['access_key']
    secret_key = config['server_cluster']['minio']['secret_key']
    bucket_name = config['server_cluster']['minio']['bucket_name']
    remove_bucket(bucket_name, endpoint, access_key, secret_key)
    create_bucket(bucket_name, endpoint, access_key, secret_key)

def remove_bucket(bucket_name, endpoint, access_key, secret_key):
    """Remove a MinIO bucket and its contents."""
    # Initialize the MinIO client
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False  # Set to True if using HTTPS
    )

    try:
        # Check if the bucket exists
        if not client.bucket_exists(bucket_name):
            print(f"Bucket '{bucket_name}' does not exist.")
            return

        # List and delete all objects in the bucket
        print(f"Removing all objects in bucket '{bucket_name}'...")
        objects = client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            #print(f"Deleting object: {obj.object_name}")
            client.remove_object(bucket_name, obj.object_name)

        # Remove the bucket
        #print(f"Removing bucket '{bucket_name}'...")
        client.remove_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' removed successfully.")

    except S3Error as e:
        print(f"Error: {e}")


#######mlmd###########
def reset_mlmd(config):
    host=config['server_cluster']['server']['host']
    username=config['server_cluster']['server']['username']
    password=config['server_cluster']['server']['password']
    remote_path=config['server_cluster']['server']['remote_path']
    ssh_client = ssh_connect(host, username, password=password, key_filepath=None)
    if ssh_client:
        remove_remote_file(ssh_client, remote_path)
        ssh_client.close()

def ssh_connect(host, username, password=None, key_filepath=None):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if key_filepath:
            # Use SSH key for authentication
            ssh_client.connect(host, username=username, key_filename=key_filepath)
        else:
            # Use password for authentication
            ssh_client.connect(host, username=username, password=password)
        
        return ssh_client
    except Exception as e:
        print(f"Failed to connect to {host}: {e}")
        return None

def file_exists(ssh_client, remote_path):
    try:
        sftp_client = ssh_client.open_sftp()
        try:
            sftp_client.stat(remote_path)  # Check if the file exists
            return True
        except FileNotFoundError:
            return False
    except Exception as e:
        print(f"Error checking file existence: {e}")
        return False  

def remove_remote_file(ssh_client, remote_path):
    if file_exists(ssh_client, remote_path):
        try:
            ssh_client.exec_command(f"rm -f {remote_path}")
            print(f"File {remote_path} has been removed.")
        except Exception as e:
            print(f"Failed to remove file {remote_path}: {e}")
    else:
        print(f"File {remote_path} does not exist. Skipping removal.")

def query_cmf_server_mlmd_size(config,result_dir):
    host=config['server_cluster']['server']['host']
    username=config['server_cluster']['server']['username']
    password=config['server_cluster']['server']['password']
    remote_path=config['server_cluster']['server']['remote_path']
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the remote server
        ssh.connect(hostname=host, port=22, username=username, password=password)
        print(f"Connected to {host}")
        
        # Run command to list files and their sizes
        command = f"ls -lh {remote_path} | awk '{{print $5, $9}}'"  # Adjust as needed for file size and name
        stdin, stdout, stderr = ssh.exec_command(command)
        
        # Get the output
        file_info = stdout.read().decode().strip()
        #save to txt:
        with open(f"{result_dir}/file_info.txt", 'w') as file:
            file.write(f"server mlmd file size:{file_info}")
        
        # Handle errors
        error = stderr.read().decode().strip()
        if error:
            print(f"Error: {error}")

    finally:
        # Close the SSH connection
        ssh.close()
        print("Connection closed.")


def reset_server(config):
    reset_minio(config)
    reset_mlmd(config)





#######kubernetes functions###########
class KubernetesCluster:
    def __init__(self, cluster_config):
        self.config_file = cluster_config['client_cluster']['client_cluster_config_path']
        self.deployment_name=cluster_config['client_cluster']['client_deployment_name']
        self.app_name=cluster_config['client_cluster']['app_name']
        self.namespace=cluster_config['client_cluster']['name_space']

    def cluster_init(self):
        #print(self.config_file)
        kube_config.load_kube_config(config_file=self.config_file)
        self.apps_v1=client.AppsV1Api()
        self.core_v1=client.CoreV1Api()
        self.deployment = self.apps_v1.read_namespaced_deployment(name=self.deployment_name, namespace=self.namespace)




    def deploy_clients(self, num_clients:int):
        self.cluster_init()
        print("Deploying{num_clients} clients")
        self.deployment.spec.replicas = num_clients
        self.apps_v1.patch_namespaced_deployment(name=self.deployment_name,namespace=self.namespace,body=self.deployment)
        print('Deployment updated. Number of replicas:', num_clients)
        time.sleep(2)

    def remove_clients(self):
        self.cluster_init()
        self.deployment.spec.replicas = 0
        self.apps_v1.patch_namespaced_deployment(name=self.deployment_name,namespace=self.namespace,body=self.deployment)   
        while True:
            pods = self.core_v1.list_namespaced_pod(namespace=self.namespace,label_selector=f"app={self.app_name}")
            teminating_pods=[pod for pod in pods.items]
            remaining_pods=len(teminating_pods)
            if remaining_pods == 0:
                print(f"All pods in deployment {self.deployment_name} have been removed.")
                break
            print(f"Waiting for {remaining_pods} terminating pods to be removed...")
            time.sleep(2)
        print(f"Deployment {self.deployment_name} removal complete.")
        time.sleep(5)


    def status_ready_clients(self,timeout=300,interval=10):
        self.cluster_init()
        """Check the status of all clients in the Kubernetes cluster."""
        start_time = time.time()       
        while time.time() - start_time < timeout:
            remaining_time = timeout - (time.time() - start_time)
            print("remaining_time: {remaining_time}")
            pods = self.core_v1.list_namespaced_pod(namespace=self.namespace,label_selector=f"app={self.app_name}")

            if not pods.items:
                print(f"No pods found with label selector: {label_selector}")
                return False
            
            all_ready = True
            for pod in pods.items:
                pod_name = pod.metadata.name
                ready = True  # Assume the pod is ready until proven otherwise

                # Check if the pod is in the "Running" state
                #print(pod.status.phase)
                if pod.status.phase != "Running":
                    all_ready = False
                    print(f"Pod {pod_name} is not in Running state. Current phase: {pod.status.phase}")
                    ready = False
                
                # Check the readiness state of all containers in the pod
                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        if container_status.ready is False:
                            ready = False
                            print(f"Pod {pod_name}: Container {container_status.name} is not ready.")
                            break  # No need to check other containers if one is not ready
                else:
                    print(f"Pod {pod_name} does not have container statuses.")

                if ready:
                    print(f"Pod {pod_name} is ready")
                else:
                    print(f"Pod {pod_name} is not ready")

                if not ready:
                    all_ready = False

            if all_ready:
                print("All pods are ready")
                return True
            else:
                print("Some pods are not ready, waiting...")
                time.sleep(interval)
        
        print("Timeout reached, some pods are still not ready")
        time.sleep(3)
        return False          

    '''
    def client_cmf_init():
        pods = self.core_v1.list_namespaced_pod(self.namespace, label_selector=f'app={self.app_name}'
        if not pods.items:
            print(f"No pods found with label selector: app={app_name}")
            return
    
        script_path = os.path.abspath('cmf_init.sh')
        for pod in pods.items:
            pod_name = pod.metadata.name
            container_name = pod.spec.containers[0].name  # Assuming the script needs to be copied to the first container

            # Copy the script to the container
            copy_command = f"kubectl cp {script_path} {self.namespace}/{pod_name}:/tmp/cmf_init.sh --kubeconfig={self.config_file}"
            subprocess.run(copy_command, shell=True, check=True)
            
            # Execute the script in the container
            exec_command = ['/bin/sh', '-c', 'chmod +x /tmp/cmf_init.sh && /tmp/cmf_init.sh']
            resp = stream.stream(self.core_v1.connect_get_namespaced_pod_exec, pod_name, self.namespace,
                                command=exec_command,
                                container=container_name,
                                stderr=True, stdin=False,
                                stdout=True, tty=False)
            print(f"Executed cmf_init.sh in pod {pod_name}: {resp}")
    '''
########run scripts in pod containers######
########cmf init: copy_script_to_pods('cmf_init.sh','/app/cmf_init.sh')######
########cmf init: run_script_in_pods('cmf_init.sh && /app/cmf_init.sh')######


########pipeline: copy_script_to_pods('pipeline.py','/app/pipeline.py')######
########piepline: run_script_in_pods('python /app/pipeline.py')######

######cmf_push: copy_script_to_pods('cmf_push.sh','/app/cmf_push.sh')######
######cmf_push: run_script_in_pods('cmf_push.sh && /app/cmf_push.sh')###### 


    def copy_script_to_pods(self,script_path,target_path):
        self.cluster_init()
        pods = self.core_v1.list_namespaced_pod(self.namespace, label_selector=f'app={self.app_name}')
        #print(pods)
        if not pods.items:
            print(f"No pods found with label selector: app={app_name}")
            return
        for pod in pods.items:
            pod_name = pod.metadata.name
            container_name = pod.spec.containers[0].name 
            
            copy_command=f'kubectl cp {script_path} {self.namespace}/{pod_name}:{target_path} --kubeconfig={self.config_file}'
           
            result = subprocess.run(copy_command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Copied {script_path} to pod {pod_name}")
            else:
                raise RuntimeError(f"Failed to copy pipeline.py to pod {pod_name}: {result.stderr}")
        time.sleep(3)
    '''
    def run_script_in_pod(self,pod_name,command,arguments:None):
        self.cluster_init()
        command =(
            f"{command}"
            f"{' '.join(arguments)}"
        )
        exec_command = ['/bin/sh', '-c', command]
        try:
            resp = stream.stream(self.core_v1.connect_get_namespaced_pod_exec, pod_name, self.namespace,
                                command=exec_command,
                                container=container_name,
                                stderr=True, stdin=False,
                                stdout=True, tty=False)
            print(f"Executed command in pod {pod_name}: {resp}")
        except Exception as e:
            print(f"Failed to execute command in pod {pod_name}: {e}")


    def run_script_in_pods(self,command,arguments:None):
        self.cluster_init()
        print("Executing pipeline.py in pods...")
        pods = self.core_v1.list_namespaced_pod(self.namespace, label_selector=f'app={self.app_name}')
        if not pods.items:
            print(f"No pods found with label selector: app={app_name}")
            return
        with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor: #configurable number of workers
            futures = [
                executor.submit(
                    self.run_script_in_pod,
                    pod.metadata.name,
                    command,
                    arguments
                )
                for pod in pods.items
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error executing pipeline in pod: {e}")    
    '''
    def run_script_in_pod(self, pod_name, command):
        #self.cluster_init()
       
        exec_command = ['/bin/sh', '-c', command]
        try:
            resp = stream.stream(self.core_v1.connect_get_namespaced_pod_exec, pod_name, self.namespace,
                                command=exec_command,
                                stderr=True, stdin=False,
                                stdout=True, tty=False)
            print(f"Executed command{exec_command} in pod {pod_name}: {resp}")
        except Exception as e:
            print(f"Failed to execute command in pod {pod_name}: {e}")
        print(f"Executed script in pod {pod_name}")
        time.sleep(3)

    def run_script_in_pods(self, command):
        #self.cluster_init()
        pods = self.core_v1.list_namespaced_pod(namespace=self.namespace, label_selector=f"app={self.app_name}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
            futures = [
                executor.submit(self.run_script_in_pod, pod.metadata.name, command)
                for pod in pods.items
            ]
            for future in  concurrent.futures.as_completed(futures):
                future.result()
        time.sleep(3)
    def copy_results_from_pods(self,result_dir):   
        self.cluster_init()
        os.makedirs(result_dir, exist_ok=True)
        pods = self.core_v1.list_namespaced_pod(self.namespace, label_selector=f'app={self.app_name}')
        for pod in pods.items:
            pod_name = pod.metadata.name
            # Use kubectl cp with the correct kubeconfig
            copy_command = f"kubectl cp {self.namespace}/{pod_name}:/app/timing_results/timing_results.log {result_dir}/timing_results_{pod_name}.log --kubeconfig={self.config_file}"
            
            result = subprocess.run(copy_command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Copied timing results from pod {pod_name}")
            else:
                print(f"Failed to copy timing results from pod {pod_name}: {result.stderr}")
