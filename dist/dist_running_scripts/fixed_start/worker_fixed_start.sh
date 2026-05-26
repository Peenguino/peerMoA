#!/bin/bash
source .venv/bin/activate

CONFIG_FILE=$1

# File checks
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: Provide a config file JSON."
    echo "Use: ./worker_fixed_start.sh topology_configs/machine_b_worker.json"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: File $CONFIG_FILE not exists."
    exit 1
fi

# Clearing whitespaces
RESOURCES=$(cat "$CONFIG_FILE" | tr -d ' \n')

echo "Starting node Ray Worker with tags for Nodes: $RESOURCES"

ray start --address='192.168.1.50:6379' --resources="$RESOURCES"