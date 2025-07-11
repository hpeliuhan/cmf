#!/bin/bash
# Script to generate a TLS secret for PostgreSQL in Kubernetes
# and create a local mount point, storing the path in a ConfigMap

set -e

# Set variables
NAMESPACE=default   
SECRET_NAME=postgres-secret
CONFIGMAP_NAME=cmf-mount-path-config
MOUNT_PATH_BASE="/home/ubuntu/data"


# Generate a random password using openssl
POSTGRES_PASSWORD=$(openssl rand -base64 24)
POSTGRES_USER=myuser
POSTGRES_DB=mlmd

# Create or replace the postgres-secret Secret for Postgres credentials
kubectl delete secret $SECRET_NAME --namespace $NAMESPACE --ignore-not-found
kubectl create secret generic $SECRET_NAME \
  --from-literal=POSTGRES_USER=$POSTGRES_USER \
  --from-literal=POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  --from-literal=POSTGRES_DB=$POSTGRES_DB \
  --namespace $NAMESPACE
echo "Secret '$SECRET_NAME' created with POSTGRES_USER, POSTGRES_PASSWORD (random), and POSTGRES_DB in namespace '$NAMESPACE'."



# Create local mount point if it doesn't exist
if [ ! -d "$MOUNT_PATH_BASE" ]; then
  mkdir -p "$MOUNT_PATH_BASE"
  echo "Created local mount point: $MOUNT_PATH_BASE"
else
  echo "Local mount point already exists: $MOUNT_PATH_BASE"
fi



# Store the mount path and db_init.sql in a ConfigMap (replace if exists)
kubectl delete configmap $CONFIGMAP_NAME --namespace $NAMESPACE --ignore-not-found
kubectl create configmap $CONFIGMAP_NAME \
  --from-literal=mountPath=$MOUNT_PATH_BASE \
  --from-file=db_init.sql=../db_init.sql \
  --namespace $NAMESPACE
echo "ConfigMap '$CONFIGMAP_NAME' created with mountPath=$MOUNT_PATH_BASE and db_init.sql in namespace '$NAMESPACE'."

# Create or replace db-init-sql-config ConfigMap for db_init.sql
kubectl delete configmap db-init-sql-config --namespace $NAMESPACE --ignore-not-found
kubectl create configmap db-init-sql-config \
  --from-file=db_init.sql=../db_init.sql \
  --namespace $NAMESPACE
echo "ConfigMap 'db-init-sql-config' created with db_init.sql in namespace '$NAMESPACE'."

# Create or replace custom-entrypoint-config ConfigMap for custom-entrypoint.sh
kubectl delete configmap custom-entrypoint-config --namespace $NAMESPACE --ignore-not-found
kubectl create configmap custom-entrypoint-config \
  --from-file=custom-entrypoint.sh=../custom-entrypoint.sh \
  --namespace $NAMESPACE
echo "ConfigMap 'custom-entrypoint-config' created with custom-entrypoint.sh in namespace '$NAMESPACE'."

# Create or replace the cmf-ui-config ConfigMap for UI protocol/port
kubectl delete configmap cmf-ui-config --namespace $NAMESPACE --ignore-not-found
kubectl create configmap cmf-ui-config \
  --from-literal=REACT_APP_API_PROTOCOL=https \
  --from-literal=REACT_APP_API_PORT=8000 \
  --namespace $NAMESPACE
echo "ConfigMap 'cmf-ui-config' created with REACT_APP_API_PROTOCOL=https and REACT_APP_API_PORT=8000 in namespace '$NAMESPACE'."

kubectl apply -f cmf-server-deployment.yaml

echo "Deployment 'cmf-server' applied."


openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=cmf-ui.local/O=cmf-ui.local"


kubectl delete secret cmf-tls-secret --namespace $NAMESPACE --ignore-not-found
kubectl create secret tls cmf-tls-secret \
  --cert=tls.crt --key=tls.key \
  --namespace $NAMESPACE
echo "TLS secret 'cmf-tls-secret' created for Ingress in namespace '$NAMESPACE'."



kubectl apply -f ingress-https.yaml
echo "Ingress 'cmf-ingress' deployed."

# Clean up local files (optional)
#rm tls.key tls.crt