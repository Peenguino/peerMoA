#!/bin/bash
source .venv/bin/activate

export RAY_ADDRESS="ray://192.168.1.50:6379"

# Imported flag into main.py: we are not using fixed placement
export PEERMOA_RUN_MODE="dist_dynamic"

python main.py