#!/bin/bash

MODE=$1

if [[ -v DOCKER_REPO_USERNAME ]]; then
  echo "Attempting to log onto ${DEFAULT_DOCKER_REPO} with ${DOCKER_REPO_USERNAME}"
  docker login ${DEFAULT_DOCKER_REPO} --username ${DOCKER_REPO_USERNAME} --password ${DOCKER_REPO_PASSWORD}
fi

echo Stopping Docker..
docker-compose -f docker-compose-$MODE.yaml down
echo stopped.

echo Run Docker..
docker-compose -f docker-compose-$MODE.yaml up --remove-orphans
#docker-compose -f docker-compose-$MODE.yaml up -d --remove-orphans

echo Cleanup old images..
docker image prune -f
