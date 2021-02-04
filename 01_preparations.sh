#!/bin/bash
# set up everything needed for running the experiments

source ./timestamp.sh

echo "$(timestamp)  start experiment creation"

# download data and unpack it
cd datasets
wget --progress=bar https://data.uni-hannover.de/dataset/25a28ec2-f9a8-412f-a6e8-6808b66ef957/resource/63814547-67d7-4d24-8c69-e28b6259374d/download/virtuoso-db.zip
unzip virtuoso-db.zip
rm virtuoso-db.zip
cd ..

# prepare Docker environment
docker network create shacl_experiment
docker-compose -f ./datasets/docker-compose.yml up -d
docker-compose -f ./engines/docker-compose.yml build
docker-compose -f ./analysis/docker-compose.yml build

echo "$(timestamp)  preparation done"
