#!/usr/bin/env bash
set -euo pipefail

if [[ -v DOCKER_REPO_USERNAME ]]; then

    echo "Attempting to log onto ${DEFAULT_DOCKER_REPO} with ${DOCKER_REPO_USERNAME}"
    echo ${DOCKER_REPO_PASSWORD} | docker login ${DEFAULT_DOCKER_REPO} --username ${DOCKER_REPO_USERNAME} --password-stdin

    echo "Publishing ${IMAGE_NAME_TAG} to ${DEFAULT_DOCKER_REPO}"
    docker tag ${IMAGE_NAME_TAG} ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG}

    echo "Publishing ${IMAGE_NAME_TAG_LATEST} to ${DEFAULT_DOCKER_REPO}"
    #docker build -t ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG_LATEST} .
    docker tag ${IMAGE_NAME_TAG} ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG_LATEST}

    #echo "Pushing ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG}"
    #docker push ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG}

    echo "Pushing ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG_LATEST}"
    docker push ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG_LATEST}

    echo "Cleaning up"
    docker rmi ${IMAGE_NAME_TAG} -f || true
    docker rmi ${DEFAULT_DOCKER_REPO}/${IMAGE_NAME_TAG} -f || true
else
    echo "DEFAULT_DOCKER_REPO is not defined"
fi
