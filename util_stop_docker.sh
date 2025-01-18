#!/bin/bash

MODE=$1

echo Stopping Docker..
docker-compose -f docker-compose-$MODE.yaml down
