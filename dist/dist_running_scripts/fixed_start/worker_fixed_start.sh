#!/bin/bash

# First file check
if [ -z "$1" ]; then
    echo "Error: Provide a config file JSON."
    echo "Use: ./worker_fixed_start.sh topology_configs/machine_*_worker.json"
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

MASTER_IP="10.66.66.11"

# Clearing whitespaces
RESOURCES=$(cat "$CONFIG_FILE" | tr -d ' \n')

echo "Starting node Ray Worker with tags for Nodes: $RESOURCES"

ray start --address="$MASTER_IP:6379" --resources="$RESOURCES"