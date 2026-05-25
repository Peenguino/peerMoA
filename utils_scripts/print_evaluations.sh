#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Error: Pass the logs namefile."
    echo "Usage: $0 <nome_file_log>"
    exit 1
fi

LOG_FILE=$1

if [ ! -f "$LOG_FILE" ]; then
    echo "Error: Il file '$LOG_FILE' does not exists."
    exit 1
fi

echo "--- Extracting evaluations from $LOG_FILE ---"
grep "TailBenchmarkService: Layer" "$LOG_FILE"