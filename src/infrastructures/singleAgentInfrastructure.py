from eclypse.graph.infrastructure import Infrastructure

def get_single_agent_infrastructure() -> Infrastructure:

    singleAgentInfrastructure = Infrastructure(
        infrastructure_id="singleAgentInfrastructure"
    )

    # === Handling node assignment

    singleAgentInfrastructure.add_node(
        "HeadBenchmarkNode"
    )

    singleAgentInfrastructure.add_node(
        "MidNode"
    )

    singleAgentInfrastructure.add_node(
        "OutputNode"
    )

    singleAgentInfrastructure.add_node(
        "TailBenchmarkNode"
    )

    # === Handling edges assignment

    singleAgentInfrastructure.add_edge(
        "HeadBenchmarkNode",
        "MidNode"
    )

    singleAgentInfrastructure.add_edge(
        "MidNode",
        "OutputNode"
    )

    singleAgentInfrastructure.add_edge(
        "OutputNode",
        "TailBenchmarkNode"
    )

    return singleAgentInfrastructure
