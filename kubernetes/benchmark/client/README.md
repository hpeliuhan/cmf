## CMF Benchmark Test
This is to kick off the benchmarking of CMF server in terms of the number of users supported running various workload. The benchmarkt.py will copy pipeline.py script to each of the pods and run the pipeline.py to simulate the pipeline workflow.


### config.yaml
This is the configuration file that controls:
- number of pipelines
- number of stages in each pipeline
- number of executions in each stage
- number of artifactss in each excutions

### Dockerfile
This is to create a lightweight container based on python-slim image with cmf executable enviornment layered.
```bash
docker build -t cmf-client:latest .
```
The image will be tagged and pushed to the local registry
```bash
docker tag cmf-client:latest localhost:5000/cmf-client:latest
docker push localhost:5000/cmf-client:latest
```

### Start the test
```bash
kubernets apply -f cmf-client-deployment.yaml
python3 benchmark.py
```