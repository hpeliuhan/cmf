#!/bin/bash
chmod +x automation.py

# Run the automation script with a specified workload
python3 automation.py "test_case_pipelines"
python3 automation.py "test_case_stages"
python3 automation.py "test_case_executions"
python3 automation.py "test_case_artifacts"
python3 automation.py "test_case_artifact_sizes"