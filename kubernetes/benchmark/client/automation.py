import click
import numpy as np
import os
from benchmark import *

#from cluster_functions import 



def generate_workload_configuration(workload: str):
    if workload == 'full_test_case_pipelines':
        pipelines = np.array([20,40,60,80,100])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([60])


    if workload == 'full_test_case_stages':
        pipelines = np.array([60])
        stages = np.array([2,3,4,5,6])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([60])

    if workload == 'full_test_case_executions':
        pipelines = np.array([60])
        stages = np.array([4])
        executions = np.array([2,3,4,5,6])
        artifacts = np.array([6])
        artifact_sizes = np.array([60]) 

    if workload == 'full_test_case_artifacts':
        pipelines = np.array([60])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([2,4,6,8,10])
        artifact_sizes = np.array([60])  

    if workload == 'full_test_case_artifact_sizes':
        pipelines = np.array([60])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([20,40,60,80,100])  

    if workload == 'full_test_case_min':
        #2x2x2x2x2 = 32 values
        pipelines = np.array([1,2])
        stages = np.array([1,2])
        executions = np.array([1,2])
        artifacts = np.array([1,2])
        artifact_sizes = np.array([1,2])  

    if workload == 'test_case_pipelines':
        pipelines = np.array([10,20,30,40,50,60,70,80,90,100])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([10])
    
    if workload == 'test_case_pipelines_3':
        pipelines = np.array([50,60,70,80,90,100,110,120])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([10])

    if workload == 'test_case_artifact_sizes_2':
        pipelines = np.array([50])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([10,20,30,40,50,60,70,80,90,100])  




    if workload == 'test_case_stages':
        pipelines = np.array([50])
        stages = np.array([2,3,4,5,6])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([10])

    if workload == 'test_case_executions':
        pipelines = np.array([50])
        stages = np.array([4])
        executions = np.array([2,3,4,5,6])
        artifacts = np.array([6])
        artifact_sizes = np.array([10])    
    
    if workload == 'test_case_artifacts':
        pipelines = np.array([50])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([2,4,6,8,10])
        artifact_sizes = np.array([10])  

    if workload == 'test_case_artifact_sizes':
        pipelines = np.array([50])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([10,20,30,40,50])   


    if workload == 'test_case_artifact_sizes_2':
        pipelines = np.array([50])
        stages = np.array([4])
        executions = np.array([4])
        artifacts = np.array([6])
        artifact_sizes = np.array([10,20,30,40,50,60,70,80,90,100])          

    if workload == 'Artifact_number':
        pipelines = np.arange(100, 300, 100)  # 100 to 200 (2 values)
        stages = np.arange(4, 7, 1)            # 4 to 6 (3 values)
        executions = np.arange(4, 11, 2)       # 4 to 10 (4 values)
        artifacts = np.arange(100, 1100, 100)  # 100 to 1000 (10 values)
        artifact_sizes = np.arange(10, 110, 10)  # 10 to 100 (10 values)

    if workload == 'Artifact_size':
        pipelines = np.arange(100, 300, 100)  # 100 to 200 (2 values)
        stages = np.arange(4, 7, 1)            # 4 to 6 (3 values)
        executions = np.arange(4, 11, 2)       # 4 to 10 (4 values)
        artifacts = np.arange(10, 00, 100)  # 100 to 1000 (10 values)
        artifact_sizes = np.arange(10, 110, 10)  # 10 to 100 (10 values)

    if workload == 'Compelxity':
        pipelines = np.arange(100, 300, 100)  # 100 to 200 (2 values)
        stages = np.arange(3, 9, 1)            # 3 to 8 (6 values)
        executions = np.arange(3, 11, 1)       # 3 to 10 (8 values)
        artifacts = np.arange(100, 1100, 100)  # 100 to 1000 (10 values)
        artifact_sizes = np.arange(10, 110, 30)  # 10 to 100 (10 values)

    if workload == 'Scalability':    
        pipelines = np.arange(100, 1100, 100)  # 100 to 1000 (10 values)
        stages = np.arange(4, 7, 1)            # 4 to 6 (3 values)
        executions = np.arange(4, 11, 2)       # 4 to 10 (4 values)
        artifacts = np.arange(100, 1100, 100)  # 100 to 1000 (10 values)
        artifact_sizes = np.arange(10, 110, 10)  # 10 to 100 (10 values)

    if workload == 'artifact_size_test':
        #total 32 values
        pipelines = np.array([10,20,30,40])
        stages = np.array([3,4,5])
        exec_commands = np.array([3,4,5])
        artifacts = np.array([10,20,30,40])
        artifact_sizes = np.array([10,20,30,40])


    if workload == 'Stage_Execution_Test': 
        #total    9 values
        pipelines = np.array([10])  
        stages = np.array([2,4,6])            
        executions = np.array([6,4,2])       
        artifacts = np.array([20])  
        artifact_sizes = np.array([5]) 
    
    if workload == 'pipeline_test':
         #total    7 values
        pipelines = np.array([5,10,15,20,25,30,35])  
        stages = np.array([4])            
        executions = np.array([4])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10])            

    if workload == 'pipeline_test_2':
         #total    7 values
        pipelines = np.array([35,40,45,50,55,60,65])  
        stages = np.array([4])            
        executions = np.array([4])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10])  

    if workload == 'stages_test':
         #total    4 values
        pipelines = np.array([5])  
        stages = np.array([3,4,5,6])            
        executions = np.array([4])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10]) 

    if workload == 'stages_test_2':
         #total    4 values
        pipelines = np.array([35])  
        stages = np.array([3,4,5,6])            
        executions = np.array([4])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10])     

    if workload == 'executions_test':
         #total    4 values
        pipelines = np.array([5])  
        stages = np.array([4])            
        executions = np.array([3,4,5,6])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10])    

    if workload == 'executions_test_2':    
        pipelines = np.array([5])  
        stages = np.array([4])            
        executions = np.array([1,2,3,4,5,6])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10]) 

    if workload == 'executions_test_3':    
        pipelines = np.array([35])  
        stages = np.array([4])            
        executions = np.array([1,2,3,4,5,6])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([10])    

    if workload == 'artifacts_test':
         #total    4 values
        pipelines = np.array([10])  
        stages = np.array([4])            
        executions = np.array([4])       
        artifacts = np.array([1,10,20,30,40])  
        artifact_sizes = np.array([10])  

    if workload == 'artifacts_test_2':
         #total    4 values
        pipelines = np.array([35])  
        stages = np.array([4])            
        executions = np.array([4])       
        artifacts = np.array([1,2,10,20,30,40])  
        artifact_sizes = np.array([10])

    if workload == 'artifacts_size_test_2':
         #total    4 values
        pipelines = np.array([35])  
        stages = np.array([4])            
        executions = np.array([4])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([1,10,20,50,70,100])




    if workload == 'Artifact_size_Test': 
        #total    16 values
        pipelines = np.array([5])  
        stages = np.array([4,6])            
        executions = np.array([1,2])       
        artifacts = np.array([2])  
        artifact_sizes = np.array([1,10,50,100]) 

    #for test purposes
    if workload ==  'min':
        pipelines = np.array([2])  
        stages = np.array([1])            
        executions = np.array([1])       
        artifacts = np.array([1])  
        artifact_sizes = np.array([1])   

    configurations = np.zeros(
        (len(pipelines), len(stages), len(executions), len(artifacts), len(artifact_sizes))
    )
    print("Configuratoins:\n","Pipelines:",pipelines,"\nStages:",stages,"\nExecutions:",executions,"\nArtifacts:",artifacts,"\nArtifact Sizes:",artifact_sizes)
    print("Configurations shape:", configurations.shape)
    return configurations, pipelines, stages, executions, artifacts, artifact_sizes

def benchmark_tracker(workload:str,workload_tracker_file_path:str,configuration:np.array,i:int,j:int,k:int,l:int,m:int):
    #if the 
    workload_tracker=np.load(workload_tracker_file_path)
    print("current value",workload_tracker[i,j,k,l,m])
    if workload_tracker[i,j,k,l,m]==1:
        return True
    else:  
        return False

def creat_config_file(test_config_file:str,i:int,j:int,k:int,l:int,m:int):
    config = load_config(test_config_file)
    #print(config)
    config['no_pipelines'] = int (i)
    config['no_stages'] = int (j)
    config['no_executions'] = int (k)
    config['no_artifacts'] = int (l)
    config['size_artifact'] = int (m)
    #print(config)
    with open(test_config_file, 'w') as file:
        yaml.safe_dump(config, file)

def automation(workload: str):  

    configuration,pipelines, stages,executions,artifacts,artifact_sizes = generate_workload_configuration(workload)
    #create a workload benchmark tracker if none is present
    workload_tracker_path=f"workload_tracker"
    os.makedirs(workload_tracker_path, exist_ok=True)
    workload_tracker_file = f"{workload}_tracker.npy"
    workload_tracker_file_path= os.path.join(workload_tracker_path,workload_tracker_file)
    print(workload_tracker_file_path)
    if not os.path.exists(workload_tracker_file_path):
        np.save(workload_tracker_file_path , configuration)
    #create workload benchmark tracker log folder
    parent_log_dir= "logs"
    workload_log_name = f"{workload}_logs"
    workload_log_dir = os.path.join(parent_log_dir, workload_log_name)
    os.makedirs(workload_log_dir, exist_ok=True)
    #iterate the matrix and run the workload benchmark
    for i, p in enumerate(pipelines):
        for j, s in enumerate(stages):
            for k, e in enumerate(executions):
                for l, a in enumerate(artifacts):
                    for m, size in enumerate(artifact_sizes):
                        if benchmark_tracker(workload,workload_tracker_file_path,configuration,i,j,k,l,m):
                            #print(f"configuration:{i,j,k,l,m}",f"Skipping: {p,s,e,a,size}")
                            continue     
                        else:
                            #run the benchmark
                            test_config_file = 'config.yaml'
                            cluster_config_file = 'cluster.yaml'
                            log_files_name = f"pipeline{p}_stages{s}_executions{e}_aritifacts{a}_size{size}"
                            #log_files_dir = os.path.join(workload_log_dir, log_files_name)
                            log_files_dir_pull= os.path.join(workload_log_dir, f"pull_{log_files_name}")
                            log_files_dir_push= os.path.join(workload_log_dir, f"push_{log_files_name}")
                            log_files_dir_merge= os.path.join(workload_log_dir, f"merge_{log_files_name}")

                            os.makedirs(log_files_dir_pull, exist_ok=True)
                            os.makedirs(log_files_dir_push, exist_ok=True)
                            os.makedirs(log_files_dir_merge, exist_ok=True)
                            #print("test:",p,s,e,a,size)
                            creat_config_file(test_config_file,p,s,e,a,size)
                            benchmark_push(test_config_file=test_config_file,cluster_config_file=cluster_config_file,parent_log_dir=log_files_dir_push) 
                            benchmark_pull(test_config_file=test_config_file,cluster_config_file=cluster_config_file,parent_log_dir=log_files_dir_pull) 
                            benchmark_merge(test_config_file=test_config_file,cluster_config_file=cluster_config_file,parent_log_dir=log_files_dir_merge) 
                            workload_tracker=np.load(workload_tracker_file_path)
                            workload_tracker[i,j,k,l,m]=1
                            np.save(workload_tracker_file_path,workload_tracker)

                  

@click.command()
@click.argument('workload', required=True, type=str)
def automation_cli(workload:str):
    click.echo(f"Choose from workloads: Artifact_number,Artifact_size,Compelxity,Scalability,min")
    automation(workload)

if __name__=="__main__":
    automation_cli()






