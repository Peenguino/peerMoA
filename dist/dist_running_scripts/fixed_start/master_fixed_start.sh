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

export RAY_health_check_period_ms=15000
export RAY_health_check_timeout_ms=30000
export RAY_health_check_failure_threshold=8

# Important: IP of Machine that hosts the Master.
# Auto-detected from the default route, so a new DHCP lease does not silently
# break the run. Override with: PEERMOA_MASTER_IP=x.x.x.x ./master_fixed_start.sh <config>
MASTER_IP="${PEERMOA_MASTER_IP:-$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1; i<=NF; i++) if ($i == "src") {print $(i+1); exit}}')}"

if [ -z "$MASTER_IP" ]; then
    echo "Error: could not auto-detect the master IP. Set PEERMOA_MASTER_IP manually."
    exit 1
fi

# The IP must belong to this machine, otherwise ray start --head binds fine but
# every client then times out on "Failed to connect to GCS at $MASTER_IP:6379".
if ! ip -4 -o addr show | grep -qw "$MASTER_IP"; then
    echo "Error: $MASTER_IP is not assigned to any local interface. Local IPs:"
    ip -4 -o addr show scope global | awk '{print "  - " $4}'
    exit 1
fi

echo "Master IP: $MASTER_IP (workers must use: PEERMOA_MASTER_IP=$MASTER_IP ./worker_fixed_start.sh <config>)"

# Safety: make sure no stale Ollama-host override leaks into this run
# (relevant for the pull architecture: workers must hit their own localhost Ollama)
unset PEERMOA_PULL_OLLAMA_HOSTS
unset PEERMOA_PULL_OLLAMA_HOSTS_FILE

# Clearing whitespaces
RESOURCES=$(cat "$CONFIG_FILE" | tr -d ' \n')

echo "Starting node Ray Master with tags for Nodes: $RESOURCES"
ray start --head --port=6379 --node-ip-address="$MASTER_IP" --resources="$RESOURCES"

echo "Waiting for Ray Head Node to fully initialize..."
sleep 3

# Ray address used by main.py
# export RAY_ADDRESS="ray://$MASTER_IP:6379"
export RAY_ADDRESS="auto"

# Flag for main.py: we are using fixed placement
export PEERMOA_RUN_MODE="dist_strict"

python main.py
