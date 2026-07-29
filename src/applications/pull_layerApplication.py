from src.services.pull_queueHeadService import QueueHeadService
from src.services.pull_elabMidService import ElabMidService
from src.services.pull_synthOutService import SynthOutService
from eclypse.graph import Application

class PullApplication(Application):
    def __init__(self, application_id, node_update_policy = None, edge_update_policy = None, node_assets = None, edge_assets = None, include_default_assets = False, requirement_init = "min", flows = None, seed = None):
        super().__init__(application_id, node_update_policy, edge_update_policy, node_assets, edge_assets, include_default_assets, requirement_init, flows, seed)

def get_pull_application(num_workers=3):

    pullApplication = PullApplication("pullApplication")

    # Adding core services
    pullApplication.add_service(QueueHeadService("QueueHeadService"))
    pullApplication.add_service(SynthOutService("SynthOutService"))

    # Adding worker services and edges
    for i in range(1, num_workers + 1):
        worker_id = f"ElabMidService-{i}"
        
        # Max elaborations could be passed here if needed
        pullApplication.add_service(ElabMidService(worker_id))

        # REST Communication: Worker <-> QueueHead (pull and requeue endpoints)
        # Bidirectional edges allow the request and the JSON response body to travel back
        pullApplication.add_edge(worker_id, "QueueHeadService")
        pullApplication.add_edge("QueueHeadService", worker_id)

        # REST Communication: Worker <-> SynthOut (synthesize endpoint)
        pullApplication.add_edge(worker_id, "SynthOutService")
        pullApplication.add_edge("SynthOutService", worker_id)

    return pullApplication