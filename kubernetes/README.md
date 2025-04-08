# K3S Deployment of CMF
This branch helps user to use k3s for cmf deployment and other supplyment services.

## Deployment steps of CMF

### Prerequisites:
- Docker: Docker version 27.3.1, build ce12230
- K3S: go version go1.22.6


### Install CMF server/neo4j/minio using script.
A private docker registry is used for the Kubernetes to pull image and create container.
```bash
export MYIP= {IP}    #fill your IP address
sh setup_script.sh
```
Set up local registry
```bash
docker run -d -p 5000:5000 --name registry registry:2
```
Tag and push the server image to the local registry
```bash
docker tag server:latest localhost:5000/cmf-server:latest
```
### persistent volume claim
create persistent volume
```bash
kubectl apply -f kubernetes/<service>/*-pv.yaml
```
claim storage volume
```bash
kubectl apply -f kubernetes/<service>/*-pvc.yaml
```

### Deploy cmf server
```bash
kubectl apply -f kubernetes/server/cmf-deployment.yaml
kubectl apply -f kubernetes/server/tensorboard.yaml
```

### Deploy minio
```bash
kubectl apply -f kubernetes/minio/minio.yaml
kubectl apply -f kubernetes/minio/aws.yaml
```

### Deploy neo4j
```bash
kubectl apply -f kubernetes/neo4j/neo4j.yaml
```

To access the cmf server: http://{IP}:3000
To access the neo4j server: http://{IP}:7474
To access the minio server: http://{IP}:9000
