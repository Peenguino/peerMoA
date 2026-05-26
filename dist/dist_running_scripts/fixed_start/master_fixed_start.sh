#!/bin/bash
source .venv/bin/activate


CONFIG_FILE=$1

# File checks
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: Provide a config file JSON."
    echo "Use: ./master_fixed_start.sh topology_configs/machine_a_master.json"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: File $CONFIG_FILE not exists."
    exit 1
fi

# Clearing whitespaces
RESOURCES=$(cat "$CONFIG_FILE" | tr -d ' \n')

echo "Starting node Ray Master with tags for Nodes: $RESOURCES"
ray start --head --port=6379 --resources="$RESOURCES"

echo "Waiting for Ray Head Node to fully initialize..."
sleep 3

export RAY_ADDRESS="ray://192.168.1.50:6379"

# Flag for main.py: we are using fixed placement
export PEERMOA_RUN_MODE="dist_strict"

python main.py