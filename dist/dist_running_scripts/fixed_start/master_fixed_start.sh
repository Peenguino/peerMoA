#!/bin/bash

# First file check
if [ -z "$1" ]; then
    echo "Error: Provide a config file JSON."
    echo "Use: ./master_fixed_start.sh topology_configs/machine_a_master.json"
    exit 1
fi

CONFIG_FILE=$(realpath "$1")

# Second file check
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: File $CONFIG_FILE not exists."
    exit 1
fi

# cd to root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." &> /dev/null && pwd)"
cd "$REPO_ROOT" || exit 1

source .venv/bin/activate

export PYTHONPATH="$REPO_ROOT"

# Important: IP of Machine that hosts the Master
MASTER_IP="10.66.66.11"

# Clearing whitespaces
RESOURCES=$(cat "$CONFIG_FILE" | tr -d ' \n')

echo "Starting node Ray Master with tags for Nodes: $RESOURCES"
ray start --head --port=6379 --node-ip-address="$MASTER_IP" --resources="$RESOURCES"

echo "Waiting for Ray Head Node to fully initialize..."
sleep 3

# Ray address used by main.py
# export RAY_ADDRESS="ray://$MASTER_IP:6379"

# Flag for main.py: we are using fixed placement
export PEERMOA_RUN_MODE="dist_strict"

python main.py