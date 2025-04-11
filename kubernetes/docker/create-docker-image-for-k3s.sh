#!/bin/bash
set -e

# Get absolute path of the script and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMF_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
TEMP_DOCKERFILE="$SCRIPT_DIR/Dockerfile.server.temp"

SERVER_DOCKERFILE_ORIGINAL="$CMF_ROOT/server/Dockerfile"

# Build server:latest
# Create temp Dockerfile with port 8080
echo "Building cmf-server image..."
cp "$SERVER_DOCKERFILE_ORIGINAL" "$TEMP_DOCKERFILE"
sed -i 's/--port", "80"/--port", "8080"/' "$TEMP_DOCKERFILE"

docker build -t server:latest -f "$TEMP_DOCKERFILE" "$CMF_ROOT"
rm "$TEMP_DOCKERFILE"

# Build ui:latest
echo "Building ui-server image..."
docker build -t ui:latest -f "$CMF_ROOT/ui/Dockerfile" "$CMF_ROOT/ui"

echo "cmf-server and ui images are built!"
