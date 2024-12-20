import numpy as np
import os
import argparse
from cmflib import cmf
import random
import string
import time

def generate_random_string(length=8):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


def create_artifacts(temp_folder: str,size_artifact: int):
    artifact_name=generate_random_string()
    temp_folder = os.path.join(temp_folder, generate_random_string())
    os.makedirs(temp_folder, exist_ok=True)
    artifact_path = os.path.join(temp_folder, f"{artifact_name}.npy")
    
    # Create random artifact of fixed size in MB
    size_in_bytes = size_artifact * 1024 * 1024
    num_elements = size_in_bytes // np.dtype(np.float64).itemsize
    random_data = np.random.rand(num_elements)
    
    np.save(artifact_path, random_data)
    print(f"Artifact created at {artifact_path} with size {size_artifact} MB")
    return artifact_path

def main():
    parser = argparse.ArgumentParser(description="Pipeline script")
    parser.add_argument('--stages', type=int, required=True, help='Number of stages')
    parser.add_argument('--executions', type=int, required=True, help='Number of executions')
    parser.add_argument('--artifact_size', type=int, required=True, help='Size of the artifact in MB')
    parser.add_argument('--artifact_number', type=int, required=True, help='Path to the graph file')
    args = parser.parse_args()

    temp_folder = "temp"  
    pipeline_name=generate_random_string()
    graph_env = os.getenv("NEO4J", "False")
    graph = True if graph_env == "True" or graph_env == "TRUE" else False
    metawriter = cmf.Cmf(filepath=pipeline_name, pipeline_name=pipeline_name, graph=graph)
    
    for stage in range(args.stages):
        stage_name = generate_random_string()
        _ = metawriter.create_context(pipeline_stage=str(stage_name))
       
        for execution in range(args.executions):
            execution_name=generate_random_string()
            _ = metawriter.create_execution(execution_type=str(execution_name))


            
            print(f"Stage {stage + 1}, Execution {execution + 1}")
            for artifact in range(args.artifact_number):
                input_dir=create_artifacts(temp_folder, args.artifact_size)
                output_dir=create_artifacts(temp_folder, args.artifact_size)
                _ = metawriter.log_dataset(input_dir, "input")
                _ = metawriter.log_dataset(output_dir, "output")
    log_dir = "/app/timing_results"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "timing_results.log")

    start_time = time.time()
    cmf.artifact_push(pipeline_name, pipeline_name)
    end_time = time.time()
    artifact_push_time = end_time - start_time

    print(f"artifact_push execution time: {artifact_push_time} seconds")

    # Measure and log the time for metadata_push
    start_time = time.time()
    cmf.metadata_push(pipeline_name, pipeline_name)
    end_time = time.time()
    metadata_push_time = end_time - start_time

    print(f"metadata_push execution time: {metadata_push_time} seconds")        
    with open(log_file_path, "a") as log_file:
        log_file.write(f"artifact_push execution time: {artifact_push_time} seconds\n")
        log_file.write(f"metadata_push execution time: {metadata_push_time} seconds\n")

    


if __name__ == "__main__":
    main()

