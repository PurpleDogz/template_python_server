#!/bin/bash

SERVICE=python_server

MODE=$1

echo Updating from GitHub..
git pull

echo Stopping Docker..
docker-compose -f docker-compose-$MODE.yaml down
echo stopped.

echo Build docker..
ROOT=`pwd`
cd app
make build_image

cd $ROOT

echo Run Docker..
docker-compose -f docker-compose-$MODE.yaml up
#docker-compose -f docker-compose-$MODE.yaml up -d

echo Cleanup old images..
docker image prune -f
