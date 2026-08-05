import json
import os

from src.services.pull_queueHeadService import QueueHeadService
from src.services.pull_elabMidService import ElabMidService
from src.services.pull_synthOutService import SynthOutService
from eclypse.graph import Application


class PullApplication(Application):
    def __init__(self, application_id, node_update_policy=None, edge_update_policy=None, node_assets=None, edge_assets=None, include_default_assets=False, requirement_init="min", flows=None, seed=None):
        super().__init__(application_id, node_update_policy, edge_update_policy, node_assets, edge_assets, include_default_assets, requirement_init, flows, seed)


def _resolve_ollama_hosts(ollama_hosts=None):
    if ollama_hosts is None:
        env_value = os.environ.get("PEERMOA_PULL_OLLAMA_HOSTS", "")
        if env_value:
            ollama_hosts = env_value
        else:
            host_file = os.environ.get("PEERMOA_PULL_OLLAMA_HOSTS_FILE", "")
            if host_file:
                with open(host_file, "r", encoding="utf-8") as handle:
                    return json.load(handle)
            return None

    if isinstance(ollama_hosts, str):
        cleaned = ollama_hosts.strip()
        if not cleaned:
            return None
        if cleaned.startswith("{"):
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None
        return None

    if isinstance(ollama_hosts, dict):
        return ollama_hosts

    return None


def get_pull_application(num_workers=9, ollama_hosts=None, requeue_policy="head"):

    pullApplication = PullApplication("pullApplication")
    resolved_hosts = _resolve_ollama_hosts(ollama_hosts)

    # Adding core services
    pullApplication.add_service(QueueHeadService("QueueHeadService", requeue_policy=requeue_policy))
    pullApplication.add_service(SynthOutService("SynthOutService"))

    # Adding worker services and edges
    for i in range(1, num_workers + 1):
        worker_id = f"ElabMidService-{i}"

        default_server_url = "http://127.0.0.1:11434"

        server_url = default_server_url
        if resolved_hosts:
            server_url = (
                resolved_hosts.get(worker_id)
                or resolved_hosts.get(str(i))
                or resolved_hosts.get(f"ElabMidNode-{i}")
                or default_server_url
            )

        pullApplication.add_service(ElabMidService(worker_id, ollama_host=server_url))

        # REST Communication: Worker <-> QueueHead (pull and requeue endpoints)
        # Bidirectional edges allow the request and the JSON response body to travel back
        pullApplication.add_edge(worker_id, "QueueHeadService")
        pullApplication.add_edge("QueueHeadService", worker_id)

        # REST Communication: Worker <-> SynthOut (synthesize endpoint)
        pullApplication.add_edge(worker_id, "SynthOutService")
        pullApplication.add_edge("SynthOutService", worker_id)

        # Edge for virtual layers implementation
        pullApplication.add_edge("SynthOutService", "QueueHeadService")
        pullApplication.add_edge("QueueHeadService", "SynthOutService")

    return pullApplication