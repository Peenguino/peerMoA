from eclypse.graph.infrastructure import Infrastructure

def get_layer_infrastructure(num_layers=1, num_agents_per_layer=3) -> Infrastructure:

    layerInfrastructure = Infrastructure(infrastructure_id="layerInfrastructure")

    layerInfrastructure.add_node("HeadBenchmarkNode")
    layerInfrastructure.add_node("TailBenchmarkNode")

    for i in range(1, num_layers + 1):
        layerInfrastructure.add_node(f"InputNode-L{i}")
        for j in range(1, num_agents_per_layer + 1):
            layerInfrastructure.add_node(f"MidNode-L{i}-({j})")
        layerInfrastructure.add_node(f"OutputNode-L{i}")

    layerInfrastructure.add_edge("HeadBenchmarkNode", "InputNode-L1")

    for i in range(1, num_layers + 1):
        for j in range(1, num_agents_per_layer + 1):
            layerInfrastructure.add_edge(f"InputNode-L{i}", f"MidNode-L{i}-({j})")
            layerInfrastructure.add_edge(f"MidNode-L{i}-({j})", f"OutputNode-L{i}")
        
        if i < num_layers:
            layerInfrastructure.add_edge(f"OutputNode-L{i}", f"InputNode-L{i+1}")

    layerInfrastructure.add_edge(f"OutputNode-L{num_layers}", "TailBenchmarkNode")

    return layerInfrastructure