import time
import os  
from cmflib import cmf
def get_file_size_in_mb(file_path):
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)  # Convert bytes to MB
    return file_size_mb

def cmf_push():
    with open("pipeline_name.txt", "r") as file:
        pipeline_name = file.read()
        
    log_dir = "/app/timing_results"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "timing_results.log")

    start_time = time.time()
    cmf.artifact_push(pipeline_name, pipeline_name)
    #end_time = time.time()
    artifact_push_time = time.time() - start_time

    print(f"artifact_push execution time: {artifact_push_time} seconds")

    # Measure and log the time for metadata_push
    start_time = time.time()
    cmf.metadata_push(pipeline_name, pipeline_name)
    #end_time = time.time()
    metadata_push_time = time.time() - start_time
    file_size_mb = get_file_size_in_mb(pipeline_name)
    print(f"metadata_push execution time: {metadata_push_time} seconds")        
    with open(log_file_path, "a") as log_file:
        log_file.write(f"pipeline mlmd size in MB: {file_size_mb} \n")
        log_file.write(f"artifact_push execution time: {artifact_push_time} seconds\n")
        log_file.write(f"metadata_push execution time: {metadata_push_time} seconds\n")

if __name__ == "__main__":
    cmf_push()