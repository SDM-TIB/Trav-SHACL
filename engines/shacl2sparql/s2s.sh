#!/bin/bash

for n in {1..3}; do
  docker exec -it s2stest bash -c "java -jar build/valid-1.0-SNAPSHOT.jar -d $1 \"$2\" /output/run_$n"
done
