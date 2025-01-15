import time
import os  
from cmflib import cmf
import argparse
def get_file_size_in_mb(file_path):
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)  # Convert bytes to MB
    return file_size_mb

def cmf_pull(pipeline_name):
    log_dir = "/app/timing_results"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "timing_results.log")


    artifat_path="./tmp"
    os.makedirs(artifat_path, exist_ok=True)

    # Measure and log the time for metadata_push
    start_time = time.time()
    #metawriter = cmf.Cmf(filepath=f"./{pipeline_name}", pipeline_name=pipeline_name)


    cmf.metadata_pull(pipeline_name,pipeline_name)
    #end_time = time.time()
    metadata_pull_time = time.time() - start_time

    print(f"metadata_pull execution time: {metadata_pull_time} seconds") 

    start_time = time.time()
    cmf.artifact_pull(f"{pipeline_name}",f"./{pipeline_name}")
    #end_time = time.time()
    artifact_pull_time = time.time() - start_time
    print(f"artifact_pull execution time: {artifact_pull_time} seconds")  
    file_size_mb = get_file_size_in_mb(pipeline_name)
   
         
    with open(log_file_path, "a") as log_file:
        log_file.write(f"pipeline mlmd size in MB: {file_size_mb} \n")
        log_file.write(f"artifact_pull execution time: {artifact_pull_time} seconds\n")
        log_file.write(f"metadata_pull execution time: {metadata_pull_time} seconds\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline script")
    parser.add_argument('--pipeline_name', type=str, required=True, help='pipeline_name')
    args = parser.parse_args()
    pipeline_name = args.pipeline_name
    cmf_pull(pipeline_name)
