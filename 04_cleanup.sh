#!/bin/bash
# cleaning up the Docker environment

source ./timestamp.sh

echo "$(timestamp)  start cleaning up"
docker-compose -f ./datasets/docker-compose.yml down -v
docker-compose -f ./engines/docker-compose.yml down -v
docker-compose -f ./analysis/docker-compose.yml down -v
docker network rm shacl_experiment
docker image rm kemele/virtuoso:7-stable shacl2sparql:www2021 shacl2sparql:py-www2021 travshacl:www2021 analysis:www2021
chown -R $(logname):$(logname) ./results
echo "$(timestamp)  finished cleaning up"
