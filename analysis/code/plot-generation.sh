#!/bin/bash
# generating all the plots inside the Docker container

mkdir -p /results/plots/exec-time/ > /dev/null
mkdir -p /results/plots/traces/ > /dev/null
mkdir -p /results/plots/dieft/ > /dev/null
python3 time_summarize.py > /dev/null && python3 time_plots.py > /dev/null && python3 dief_summarize.py > /dev/null && Rscript dief_plots.R > /dev/null
