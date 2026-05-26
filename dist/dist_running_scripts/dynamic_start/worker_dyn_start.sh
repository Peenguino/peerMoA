#!/bin/bash
source .venv/bin/activate

# Not using --resources, so it's Ray that assigns Nodes to Machines 
ray start --address='192.168.1.50:6379'