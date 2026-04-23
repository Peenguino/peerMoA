from src.services.inputNodeService import InputNodeService
from src.services.midNodeService import MidNodeService
from src.services.outputNodeService import OutputNodeService
from src.services.benchmarkServices import HeadBenchmarkService, TailBenchmarkService
from eclypse.graph import Application

class LayerApplication(Application):
    def __init__(self, application_id, node_update_policy = None, edge_update_policy = None, node_assets = None, edge_assets = None, include_default_assets = False, requirement_init = "min", flows = None, seed = None):
        super().__init__(application_id, node_update_policy, edge_update_policy, node_assets, edge_assets, include_default_assets, requirement_init, flows, seed)

def get_layer_application(num_layers=1, num_agents_per_layer=3):

    layerApplication = LayerApplication("layerApplication")

    layerApplication.add_service(HeadBenchmarkService("HeadBenchmarkService"))
    layerApplication.add_service(TailBenchmarkService("TailBenchmarkService"))

    for i in range(1, num_layers + 1):
        # Input Node layer i
        layerApplication.add_service(InputNodeService(f"InputNodeService-L{i}"))

        # Mid Nodes layer i
        for j in range(1, num_agents_per_layer + 1):
            layerApplication.add_service(MidNodeService(f"MidNodeService-L{i}-({j})"))

        # Output Node layer i
        is_final = (i == num_layers)
        layerApplication.add_service(
            OutputNodeService(f"OutputNodeService-L{i}", expected_messages=num_agents_per_layer, is_final_layer=is_final)
        )

    layerApplication.add_edge("HeadBenchmarkService", "InputNodeService-L1")

    for i in range(1, num_layers + 1):
        for j in range(1, num_agents_per_layer + 1):
            layerApplication.add_edge(f"InputNodeService-L{i}", f"MidNodeService-L{i}-({j})")
            layerApplication.add_edge(f"MidNodeService-L{i}-({j})", f"OutputNodeService-L{i}")

        if i < num_layers:
            layerApplication.add_edge(f"OutputNodeService-L{i}", f"InputNodeService-L{i+1}")

    layerApplication.add_edge(f"OutputNodeService-L{num_layers}", "TailBenchmarkService")

    # Handling ACK for backpropagation
    layerApplication.add_edge("TailBenchmarkService", "HeadBenchmarkService")

    return layerApplication