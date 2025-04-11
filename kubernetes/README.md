# Kubernetes Deployment of CMF
To scale the deployment of CMF with easy orchestration, user can follow the steps to deploy CMF core services and other supplimentry services such as minio, neo4j within kubernetes cluster.

## Deployment steps of CMF

### Prerequisites:
- Docker: Docker version 27.3.1, build ce12230
  Docker is needed to build containerization cmf server images.
- K3S: go version go1.22.6
  This guide is tested with k8s's lightweight version k3s. 
- clone the project:
```bash
git clone https://github.com/HewlettPackard/cmf.git
```

### Docker images build
CMF server has two components: cmf-server and cmf-ui.
Cmf-server is API server that listens to port 80 in the container. Cmf-ui is web server that listens to port 3000 in the container and cmf-ui will query data from cmf-server and display to the web UI.
In common cases, k3s has trarif as default loadbalancer where port 80 is binded. There is port conflict thus we will make changes to the port mapping when creating the docker images.

User can use the automation script to create the images:
```bash
sh cmf/kubernetes/docker/create-docker-image-for-k3s.sh
```


### Tag and push to docker registry.
Once the cmf-server and cmf-ui images are in places. User can push them into customized registry where k3s can load as container.
For example, a private docker registry can be used:
Start local docker registry:
```bash
docker run -d -p 5000:5000 --name registry registry:2
```

Tag and push the cmf-server image to the local docker registry:
```bash
docker tag server:latest localhost:5000/cmf-server:latest
docker push localhost:5000/cmf-server:latest
```

Tag and push the cmf-ui image to the local docker registry:
```bash
docker tag server:latest localhost:5000/cmf-server:latest
docker push localhost:5000/cmf-server:latest
```

### Kubernetes deployment files
CMF server maintains database of metadata. Below is an example to create stroage to store the data in the cmf-server.

create persistent volume:
```bash
kubectl apply -f cmf/kubernetes/server/cmfserver-pv.yaml
```
claim storage volume:
```bash
kubectl apply -f cmf/kubernetes/server/cmfserver-pvc.yaml
```
Then we can start the deployment of cmf-server and cmf-ui:
```bash
kubectl apply -f kubernetes/server/cmf-deployment.yaml
```

## Optional integrated deployments
### minio
CMF server uses thrid part object storage to store artifacts. Taking minio as an example:
```bash
kubectl apply -f kubernetes/minio/aws.yaml
```

### neo4j
neo4j is a graph database which can be used to display the lineage data when running pipeline:
We will start by creating cluster storage for neo4j:
```bash
kubectl apply -f kubernetes/neo4j/neo4j-pv.yaml 
kubectl apply -f kubernetes/neo4j/neo4j-pvc.yaml
```

Then start the neo4j deployment:
```bash
kubectl apply -f kubernetes/neo4j/neo4j.yaml
```

## Accessing services
To access the cmf-ui: http://{IP}:3000
To access the neo4j server: http://{IP}:7474
To access the minio server: http://{IP}:9000
