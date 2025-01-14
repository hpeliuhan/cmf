import os
from cluster import *

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def benchmark(test_config_file="config.yaml",cluster_config_file="cluster.yaml",parent_log_dir="test"):    
    
    cluster_config = load_config("cluster.yaml")

    #reset cmf server
    reset_server(cluster_config)
    #start
    test_config = load_config(test_config_file)
    no_artifacts = test_config['no_artifacts']
    no_pipelines = test_config['no_pipelines']
    no_stages = test_config['no_stages']
    no_executions = test_config['no_executions']
    size_artifact = test_config['size_artifact']

    #reset client cluster
    cluster=KubernetesCluster(cluster_config)
    cluster.cluster_init()
    cluster.remove_clients()

    #deploy the clients
    cluster.deploy_clients(no_pipelines)
    cluster.status_ready_clients()
    
    #run the cmf initilization
    cmf_init_script = f"cmf_init.sh"
    cmf_init_script_target=f"/app/{cmf_init_script}"
    cmf_init_command=f"/app/cmf_init.sh"
    cluster.copy_script_to_pods(cmf_init_script,cmf_init_script_target)
    time.sleep(10)
    cluster.run_script_in_pods(cmf_init_command)
    time.sleep(10)
    
    #run the pipeplines
    pipeline_script = f"pipeline.py"
    pipeline_script_target = f'/app/{pipeline_script}'
    pipeline_command =(
        f"python3 pipeline.py "
        f"--stages={no_stages} --artifact_size={size_artifact} "
        f"--artifact_number={no_artifacts} --execution={no_executions}"
    )
    print(pipeline_command)
    cluster.copy_script_to_pods(pipeline_script,pipeline_script_target)
    time.sleep(20)
    cluster.run_script_in_pods(pipeline_command)
    time.sleep(10)

    #run the cmf push
    cmf_push_script = f"cmf_push.py"
    cmf_push_script_target = f'/app/{cmf_push_script}'
    cmf_push_command =(
        f"python3 cmf_push.py"
    )
    print(cmf_push_command)
    cluster.copy_script_to_pods(cmf_push_script,cmf_push_script_target)
    time.sleep(10)
    cluster.run_script_in_pods(cmf_push_command)
    time.sleep(10)

    
    cluster.copy_results_from_pods(parent_log_dir)
    query_cmf_server_mlmd_size(cluster_config,parent_log_dir)
    #push_script=f"cmf_push.sh"
    #cluster.copy_script_to_pods(push_script)
    #cluster.run_script_in_pods(push_script)

if __name__=="__main__":
    benchmark(test_config_file="config.yaml",cluster_config_file="cluster.yaml",parent_log_dir="test")
