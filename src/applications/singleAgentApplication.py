from src.services.midNodeService import MidNodeService
from src.services.outputNodeService import OutputNodeService
from src.services.benchmarkServices import HeadBenchmarkService, TailBenchmarkService
from eclypse.graph import Application

class SingleAgentApplication(Application):
    def __init__(self, application_id, node_update_policy = None, edge_update_policy = None, node_assets = None, edge_assets = None, include_default_assets = False, requirement_init = "min", flows = None, seed = None):
        super().__init__(application_id, node_update_policy, edge_update_policy, node_assets, edge_assets, include_default_assets, requirement_init, flows, seed)

def get_single_agent_application(**kwargs):

    singleAgentApplication = SingleAgentApplication(
        "singleAgentApplication"
    )

    # === Handling services assignment

    singleAgentApplication.add_service(
        HeadBenchmarkService("HeadBenchmarkService")
    )

    singleAgentApplication.add_service(
        MidNodeService("MidNodeService")
    )

    singleAgentApplication.add_service(
        OutputNodeService("OutputNodeService", expected_messages=1)
    )

    singleAgentApplication.add_service(
        TailBenchmarkService("TailBenchmarkService")
    )

    # === Handling edges assignment

    singleAgentApplication.add_edge(
        "HeadBenchmarkService",
        "MidNodeService"
    )

    singleAgentApplication.add_edge(
        "MidNodeService",
        "OutputNodeService"
    )

    singleAgentApplication.add_edge(
        "OutputNodeService",
        "TailBenchmarkService"
    )

    # Handling ACK for backpropagation
    # singleAgentApplication.add_edge("TailBenchmarkService", "HeadBenchmarkService")

    return singleAgentApplication
