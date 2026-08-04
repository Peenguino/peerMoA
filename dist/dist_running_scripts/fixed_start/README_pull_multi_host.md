Per usare la nuova architettura pull con 3 host Ollama distinti in fixed placement:

1. Preparare i tre server Ollama su ciascuna macchina fisica.
2. Creare il file di mapping degli host, ad esempio:
   - dist/dist_fixed_configs/pull_ollama_hosts.json
3. Avviare il master con:
   - export PEERMOA_PULL_OLLAMA_HOSTS_FILE=/path/to/pull_ollama_hosts.json
   - ./dist/dist_running_scripts/fixed_start/master_fixed_start.sh dist/dist_fixed_configs/machine_a_master.json
4. Avviare i worker con gli stessi file di configurazione esistenti:
   - ./dist/dist_running_scripts/fixed_start/worker_fixed_start.sh dist/dist_fixed_configs/machine_b_worker.json
   - ./dist/dist_running_scripts/fixed_start/worker_fixed_start.sh dist/dist_fixed_configs/machine_c_worker.json

Il mapping viene usato dal servizio pull per indirizzare ogni worker verso il proprio host Ollama.
