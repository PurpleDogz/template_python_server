#!/bin/bash

# Build the image

# Import env
if [ -f .env ]; then
  set -o allexport
  source .env
  set +o allexport
fi

echo Build docker..
ROOT=`pwd`
cd app
make build_image

cd $ROOT
