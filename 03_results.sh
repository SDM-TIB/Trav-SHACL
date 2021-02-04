#!/bin/bash
# preparing the plots for the result analysis

DOCKER_RESULT_ANALYSIS="resultanalysis"

source ./timestamp.sh

echo "$(timestamp)  start plot creation"
docker-compose -f ./analysis/docker-compose.yml up -d > /dev/null
docker exec -it $DOCKER_RESULT_ANALYSIS bash -c "./plot-generation.sh"
docker stop $DOCKER_RESULT_ANALYSIS > /dev/null
echo "$(timestamp)  finished plot creation"

