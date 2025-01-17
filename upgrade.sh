#!/bin/bash

# Default
MODE="full"
INPUT="$1"

# Environment
if [ ! -z "${DEPLOYMENT_MODE}" ]; then
    MODE=$DEPLOYMENT_MODE
fi

# Command line 
if [ ! -z "$INPUT" ]; then
    MODE=$INPUT
fi

echo Running Upgrade: $MODE

./docker_build.sh;./docker_publish.sh;./docker_run_$MODE.sh
