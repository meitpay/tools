#!/bin/bash

# This script is used to run the Flask application in a Docker container.

docker compose down --remove-orphans  # Stop and remove any existing containers
docker compose build --pull  # Build the Docker image, pulling the latest base image
docker compose up -d  # Start the container in detached mode
