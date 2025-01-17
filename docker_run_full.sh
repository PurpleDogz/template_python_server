#!/bin/bash

# Import env
if [ -f .env ]; then
  echo "Importing .env file"
  set -o allexport
  source .env
  set +o allexport
fi

if [ "$1" = "build" ]; then
  source ./docker_docker.sh
fi

source ./docker_restart_full.sh
