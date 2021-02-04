#!/bin/bash
# running this script will automatically run
# the experiments and prepare the plots
# including preparation and clean-up
source ./timestamp.sh

echo "$(timestamp)  starting evaluation..."
source ./01_preparations.sh
source ./02_experiments.sh
source ./03_results.sh
source ./04_cleanup.sh
echo "$(timestamp)  ... finished evaluation"
