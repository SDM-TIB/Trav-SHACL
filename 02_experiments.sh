#!/bin/bash
# running all the experiments

# names of the Docker containers for the SPARQL endpoints
DOCKER_BENCHMARK_LUBM_SKG_1="lubm_skg_1"
DOCKER_BENCHMARK_LUBM_SKG_2="lubm_skg_2"
DOCKER_BENCHMARK_LUBM_SKG_3="lubm_skg_3"
DOCKER_BENCHMARK_LUBM_MKG_1="lubm_mkg_1"
DOCKER_BENCHMARK_LUBM_MKG_2="lubm_mkg_2"
DOCKER_BENCHMARK_LUBM_MKG_3="lubm_mkg_3"
DOCKER_BENCHMARK_LUBM_LKG_1="lubm_lkg_1"
DOCKER_BENCHMARK_LUBM_LKG_2="lubm_lkg_2"
DOCKER_BENCHMARK_LUBM_LKG_3="lubm_lkg_3"

# names of the Docker containers for the SHACL engines
DOCKER_ENGINE_SHACL2SPARQL="shacl2sparql"
DOCKER_ENGINE_SHACL2SPARQLPY="shacl2sparqlpy"
DOCKER_ENGINE_TRAVSHACL="travshacl"

# method to clear system cache
clear_cache() {
  sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
}

source ./timestamp.sh

# print notification about experiment status
notification() {
  echo "$(timestamp)  $1: Run #$2 for $3 @ $4"
  docker restart $4 > /dev/null
  sleep 10s  # the endpoint needs some time to be responsive
}

# run the validation of an i-th run of a particular shape schema against a particular endpoint with all engines
run_validation() {
  benchmark=$1
  dataset=$2
  schema=$3
  run=$4

  outpath=$(echo "/output/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")

  # SHACL2SPARQL
  notification "SHACL2SPARQL" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_SHACL2SPARQL > /dev/null
  sleep 2s
  docker exec -it $DOCKER_ENGINE_SHACL2SPARQL bash -c "java -Xmx16G -jar build/valid-1.0-SNAPSHOT.jar -d $schema http://$dataset:8890/sparql $outpath > /dev/null 2>> /output/error_s2s.log"
  docker stop $DOCKER_ENGINE_SHACL2SPARQL > /dev/null

  # SHACL2SPARQLpy
  notification "SHACL2SPARQLpy" $run  ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_SHACL2SPARQLPY > /dev/null
  sleep 2s
  docker exec -it $DOCKER_ENGINE_SHACL2SPARQLPY bash -c "python3 main.py -d $schema http://$dataset:8890/sparql $outpath > /dev/null 2>> /output/error_s2spy.log"
  docker stop $DOCKER_ENGINE_SHACL2SPARQLPY > /dev/null

  # Trav-SHACL Config 1
  notification "Trav-SHACL Config 1" $run  ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config1/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath BFS --heuristics TARGET IN BIG --orderby --selective > /dev/null 2>> /output/error_travshacl_config1.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 2
  notification "Trav-SHACL Config 2" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config2/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath BFS --heuristics TARGET IN SMALL --orderby --selective > /dev/null 2>> /output/error_travshacl_config2.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 3
  notification "Trav-SHACL Config 3" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config3/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath BFS --heuristics TARGET OUT BIG --orderby --selective > /dev/null 2>> /output/error_travshacl_config3.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 4
  notification "Trav-SHACL Config 4" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config4/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath BFS --heuristics TARGET OUT SMALL --orderby --selective > /dev/null 2>> /output/error_travshacl_config4.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 5
  notification "Trav-SHACL Config 5" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config5/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath DFS --heuristics TARGET IN BIG --orderby --selective > /dev/null 2>> /output/error_travshacl_config5.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 6
  notification "Trav-SHACL Config 6" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config6/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath DFS --heuristics TARGET IN SMALL --orderby --selective > /dev/null 2>> /output/error_travshacl_config6.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 7
  notification "Trav-SHACL Config 7" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config7/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath DFS --heuristics TARGET OUT BIG --orderby --selective > /dev/null 2>> /output/error_travshacl_config7.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 8
  notification "Trav-SHACL Config 8" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config8/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath DFS --heuristics TARGET OUT SMALL --orderby --selective > /dev/null 2>> /output/error_travshacl_config8.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null

  # Trav-SHACL Config 9
  notification "Trav-SHACL Config 9" $run ${schema##*/} $dataset
  clear_cache
  docker start $DOCKER_ENGINE_TRAVSHACL > /dev/null
  sleep 2s
  outpath=$(echo "/output/config9/"$benchmark"/"$dataset"/"${schema##*/}"/"$run"/")
  docker exec -it $DOCKER_ENGINE_TRAVSHACL bash -c "python3 main.py -d $schema -a http://$dataset:8890/sparql $outpath DFS --heuristics --orderby --selective > /dev/null 2>> /output/error_travshacl_config9.log"
  docker stop $DOCKER_ENGINE_TRAVSHACL > /dev/null
}

docker-compose -f ./datasets/docker-compose.yml stop > /dev/null
docker-compose -f ./engines/docker-compose.yml up --no-start > /dev/null

echo "$(timestamp)  starting experiments"
declare -a BENCHMARKS=("LUBM")
for b in ${BENCHMARKS[@]}; do
  if [ $b == "LUBM" ]
  then
    declare -a datasets=($DOCKER_BENCHMARK_LUBM_SKG_1
                         $DOCKER_BENCHMARK_LUBM_SKG_2
                         $DOCKER_BENCHMARK_LUBM_SKG_3
                         $DOCKER_BENCHMARK_LUBM_MKG_1
                         $DOCKER_BENCHMARK_LUBM_MKG_2
                         $DOCKER_BENCHMARK_LUBM_MKG_3
                         $DOCKER_BENCHMARK_LUBM_LKG_1
                         $DOCKER_BENCHMARK_LUBM_LKG_2
                         $DOCKER_BENCHMARK_LUBM_LKG_3)
  fi

  for d in ${datasets[@]}; do
    docker start $d > /dev/null
    sleep 10s  # the endpoint needs some time to be responsive
    if [ $b == "LUBM" ]
    then
      declare -a schemas=("/shapes/lubm/schema1" "/shapes/lubm/schema2" "/shapes/lubm/schema3")
    fi
    for s in ${schemas[@]}; do
      for i in {1..5}; do
        run_validation $b $d $s $i
      done
    done
    docker stop $d > /dev/null
  done
done
echo "$(timestamp)  experiments done"
