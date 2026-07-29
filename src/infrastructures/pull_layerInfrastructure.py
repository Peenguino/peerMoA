from eclypse.graph.infrastructure import Infrastructure

def get_pull_infrastructure(num_workers=3) -> Infrastructure:

    pullInfrastructure = Infrastructure(infrastructure_id="pullInfrastructure")

    # Adding core nodes
    pullInfrastructure.add_node("QueueHeadNode")
    pullInfrastructure.add_node("SynthOutNode")

    # Adding worker nodes and edges
    for i in range(1, num_workers + 1):
        worker_node = f"ElabMidNode-{i}"
        
        pullInfrastructure.add_node(worker_node)

        # Connecting Worker Node <-> QueueHead Node
        pullInfrastructure.add_edge(worker_node, "QueueHeadNode")
        pullInfrastructure.add_edge("QueueHeadNode", worker_node)

        # Connecting Worker Node <-> SynthOut Node
        pullInfrastructure.add_edge(worker_node, "SynthOutNode")
        pullInfrastructure.add_edge("SynthOutNode", worker_node)

    return pullInfrastructure