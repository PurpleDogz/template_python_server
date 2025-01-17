#!make

SHELL := /bin/bash
.ONESHELL:
.SILENT:

# Handle windows..
export PYTHON=python3.12
export PYTHON_VENV=bin/

ifeq ($(OS),Windows_NT) 
  PYTHON=python
  PYTHON_VENV=scripts/
endif

# default target (=first)
run : run-local

include .scripts/local-setup.mk

# run-local: setup-local start-infra-local
# 	# spin up apps in parallel in the foreground
# 	make -j run-producer-local run-consumer-local

run-local: setup-local
	source .venv/${PYTHON_VENV}activate && MYAPP_ENV_PATH=./local.env ${PYTHON} -m pyapp $*

# TODO: dockerise for pipeline
static-analysis:
	echo Running mypy; mypy .
	echo Running isort; isort .
	echo Running black; black .

tests: unit-tests integration-tests

unit-tests: setup-local
	./.venv/${PYTHON_VENV}${PYTHON} -m pytest --log-cli-level INFO --cov=. --cov-report xml:reports/coverage.xml --cov-report term  --junitxml=reports/unittest.xml -s ./pyapp


# start-infra-local:
# 	docker-compose --env-file local.env up -d

# stop-infra-local:
# 	docker-compose --env-file local.env down

# integration-tests: integration-tests-local

# integration-tests-local: setup-local
# 	# spins up new local infra and runs 10 seconds of tests on it
# 	MYAPP_ENV_PATH=local.env .venv/${PYTHON_VENV}${PYTHON} ./integration_tests.py
