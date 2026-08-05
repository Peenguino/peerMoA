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

export PYTHONPATH="$REPO_ROOT"

export RAY_health_check_period_ms=15000
export RAY_health_check_timeout_ms=30000
export RAY_health_check_failure_threshold=8

# IP of the machine hosting the Ray head. Keep it in sync with the value printed
# by master_fixed_start.sh; override with PEERMOA_MASTER_IP when DHCP moves it.
MASTER_IP="${PEERMOA_MASTER_IP:-192.168.1.12}"

# Fail fast with a readable message instead of Ray's 30s GCS timeout.
if ! timeout 5 bash -c "cat < /dev/null > /dev/tcp/$MASTER_IP/6379" 2>/dev/null; then
    echo "Error: cannot reach the Ray head at $MASTER_IP:6379."
    echo "Check that 'ray start --head' is already running on the master and that"
    echo "PEERMOA_MASTER_IP matches its current IP."
    exit 1
fi

# Safety: make sure no stale Ollama-host override leaks into this run
unset PEERMOA_PULL_OLLAMA_HOSTS
unset PEERMOA_PULL_OLLAMA_HOSTS_FILE

# Clearing whitespaces
RESOURCES=$(cat "$CONFIG_FILE" | tr -d ' \n')

echo "Starting node Ray Worker with tags for Nodes: $RESOURCES"

ray start --address="$MASTER_IP:6379" --resources="$RESOURCES"
