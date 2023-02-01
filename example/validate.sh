#!/bin/bash

docker exec -it travshacl_example_engine bash -c "python3 main.py -d /shapes/LUBM/ http://travshacl_example_data:8890/sparql /output/json/ DFS --heuristics TARGET IN BIG --orderby --selective --output"
