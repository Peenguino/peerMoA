from src.services.inputNodeService import InputNodeService
from src.services.midNodeService import MidNodeService
from src.services.outputNodeService import OutputNodeService
from src.services.benchmarkServices import HeadBenchmarkService, TailBenchmarkService
from eclypse.graph import Application

class LayerApplication(Application):
    def __init__(self, application_id, node_update_policy = None, edge_update_policy = None, node_assets = None, edge_assets = None, include_default_assets = False, requirement_init = "min", flows = None, seed = None):
        super().__init__(application_id, node_update_policy, edge_update_policy, node_assets, edge_assets, include_default_assets, requirement_init, flows, seed)

def get_layer_application():

    layerApplication = LayerApplication(
        "layerApplication"
    )

    # === Handling services assignment

    layerApplication.add_service(
        HeadBenchmarkService("HeadBenchmarkService")
    )

    layerApplication.add_service(
        InputNodeService("InputNodeService")
    )

    layerApplication.add_service(
        MidNodeService("MidNodeService-(1)")
    )

    layerApplication.add_service(
        MidNodeService("MidNodeService-(2)")
    )

    layerApplication.add_service(
        MidNodeService("MidNodeService-(3)")
    )

    layerApplication.add_service(
        OutputNodeService("OutputNodeService", expected_messages=3)
    )

    layerApplication.add_service(
        TailBenchmarkService("TailBenchmarkService")
    )

    # === Handling edges assignment

    layerApplication.add_edge(
        "HeadBenchmarkService",
        "InputNodeService"
    )

    layerApplication.add_edge(
        "InputNodeService",
        "MidNodeService-(1)"
    )

    layerApplication.add_edge(
        "InputNodeService",
        "MidNodeService-(2)"
    )

    layerApplication.add_edge(
        "InputNodeService",
        "MidNodeService-(3)"
    )

    layerApplication.add_edge(
        "MidNodeService-(1)",
        "OutputNodeService"
    )

    layerApplication.add_edge(
        "MidNodeService-(2)",
        "OutputNodeService"
    )

    layerApplication.add_edge(
        "MidNodeService-(3)",
        "OutputNodeService"
    )

    layerApplication.add_edge(
        "OutputNodeService",
        "TailBenchmarkService"
    )

    return layerApplication