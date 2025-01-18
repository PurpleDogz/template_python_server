#!/bin/bash

# Import env
if [ -f .env ]; then
  set -o allexport
  source .env
  set +o allexport
fi

ROOT=`pwd`
cd app
make publish

cd $ROOT
