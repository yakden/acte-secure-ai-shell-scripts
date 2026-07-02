#!/bin/bash
set -e
# Build and tag the application image.
IMAGE="myapp:$(git rev-parse --short HEAD)"
docker build -t "$IMAGE" .
docker tag "$IMAGE" myapp:latest
echo "Built $IMAGE"
