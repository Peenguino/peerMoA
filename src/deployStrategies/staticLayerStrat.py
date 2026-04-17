from eclypse.placement.strategies import StaticStrategy

def get_static_layer_deploy_strategy(num_layers=1, num_agents_per_layer=3):
    mappingServiceToNode = {
        "HeadBenchmarkService": "HeadBenchmarkNode",
        "TailBenchmarkService": "TailBenchmarkNode"
    }

    for i in range(1, num_layers + 1):
        mappingServiceToNode[f"InputNodeService-L{i}"] = f"InputNode-L{i}"
        mappingServiceToNode[f"OutputNodeService-L{i}"] = f"OutputNode-L{i}"
        for j in range(1, num_agents_per_layer + 1):
            mappingServiceToNode[f"MidNodeService-L{i}-({j})"] = f"MidNode-L{i}-({j})"

    return StaticStrategy(mapping=mappingServiceToNode)