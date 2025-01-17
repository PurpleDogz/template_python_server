# Use some sensible default shell settings
SHELL := /bin/bash
.ONESHELL:
.SILENT:

RED='\033[1;31m'
CYAN='\033[0;36m'
NC='\033[0m'

WORKING_DIR=/workspace/app

ifndef IMAGE_NAME
IMAGE_NAME=olympia
endif

ifndef IMAGE_TAG
IMAGE_TAG=latest
endif

RUN_BLACK=docker-compose run -f docker-compose.scanner.yaml --rm black
RUN_ISORT=docker-compose run -f docker-compose.scanner.yaml --rm --entrypoint isort isort

export IMAGE_NAME_TAG = ${IMAGE_NAME}:${IMAGE_TAG}
export IMAGE_NAME_TAG_LATEST = ${IMAGE_NAME}:latest

export REVISION
export DEFAULT_DOCKER_REPO
export ARTIFACTORY_URL
export ARTIFACTORY_USERNAME
export ARTIFACTORY_ACCESS_TOKEN
export GITGUARDIAN_API_KEY

.PHONY: build
build: unit_test
#build: unit_test scan build_image scan_image

.PHONY: unit_test
unit_test: 
ifdef BUILDKITE
	env | grep -e "^BUILDKITE" -e "^SONAR" -e "^GITHUB" > bk.env
	docker-compose run -f docker-compose.scanner.yaml --rm python /workspace/app/cmd/scripts/unit-test.sh
else
	cd cmd;make unit-tests
endif

.PHONY: api_test
api_test: build
	cd cmd;make integration-tests

.PHONY: build_image
build_image:
	docker build --tag ${IMAGE_NAME_TAG} \
				 --build-arg REVISION=${REVISION} \
				 --build-arg DOCKER_REPO=${DEFAULT_DOCKER_REPO} \
				 --build-arg ARTIFACTORY_URL=${ARTIFACTORY_URL} \
				 --build-arg ARTIFACTORY_USERNAME=${ARTIFACTORY_USERNAME} \
				 --build-arg ARTIFACTORY_ACCESS_TOKEN=${ARTIFACTORY_ACCESS_TOKEN} .

.PHONY: scan_image
scan_image:
ifdef BUILDKITE
	echo -e --- $(CYAN)Scan Image ...$(NC)
	./scan-image.sh
else
	echo -e --- $(CYAN)Skipping Image Secret scan as running outside of Buildkite ...$(NC)
endif

.PHONY: scan
scan:
ifdef BUILDKITE
	echo -e --- $(CYAN)Running SonarQube scan ...$(NC)
	# Sonar analysis (needs sonar.env to be available with env values from build)
	env | grep -e "^BUILDKITE" -e "^SONAR" -e "^GITHUB" > bk.env
	docker-compose run -f docker-compose.scanner.yaml --rm sonar-scanner
else
	echo -e --- $(CYAN)Skipping SonarQube scan as running outside of Buildkite ...$(NC)
endif

.PHONY: publish
publish:
	./publish-image.sh

.PHONY: lint
lint:
	pip install ruff
	ruff check
	ruff format

.PHONY: host_local
host_local:
	cd cmd;make