#!/bin/bash

source .venv/bin/activate
export CUDA_VISIBLE_DEVICES=""
python3 -u main.py

sleep 5

MONITOR_LOGS="ram_usage_log.csv"

# Acquiring pid from main python process
if [ -f ".main_pid.txt" ]; then
    MAIN_PYTHON_PID=$(cat .main_pid.txt)
else
    echo "Errore: File .main_pid.txt not found."
    exit 1
fi

echo "Running background RAM monitoring..."

(
    echo "# MAIN_PYTHON_PID: $MAIN_PYTHON_PID" > "$MONITOR_LOGS"
    echo "# MONITOR_PID: $BASHPID" >> "$MONITOR_LOGS"

    echo -e "Timestamp\t\t\t\tUsed RAM\tFree RAM" >> "$MONITOR_LOGS"

    # Using dummy signal on the PID acquired before
    while kill -0 "$MAIN_PYTHON_PID" 2>/dev/null; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        ram_stats=$(free -m | awk 'NR==2{printf "\t\t%.2f GB\t\t%.2f GB", $3/1024, $4/1024}')
        echo -e "$timestamp\t$ram_stats" >> "$MONITOR_LOGS"
        # Monitoring RAM period
        sleep 40
    done

    echo -e "$(date '+%Y-%m-%d %H:%M:%S') \t MONITORING_FINISHED \t 0" >> "$MONITOR_LOGS"
    # Clearing tmp file containing main py process
    rm -f .main_pid.txt
) &

MONITOR_PID=$!
disown $MONITOR_PID

echo "PID python process: $MAIN_PYTHON_PID"
echo "PID monitor process: $MONITOR_PID"
echo "Now you can close your SSH session."
