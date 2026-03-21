from eclypse.graph.infrastructure import Infrastructure

def get_layer_infrastructure() -> Infrastructure:

    layerInfrastructure = Infrastructure(
        infrastructure_id="layerInfrastructure"
    )

    # === Handling node assignment

    layerInfrastructure.add_node(
        "HeadBenchmarkNode"
    )

    layerInfrastructure.add_node(
        "InputNode"
    )

    layerInfrastructure.add_node(
        "MidNode-(1)"
    )

    layerInfrastructure.add_node(
        "MidNode-(2)"
    )

    layerInfrastructure.add_node(
        "MidNode-(3)"
    )

    layerInfrastructure.add_node(
        "OutputNode"
    )

    layerInfrastructure.add_node(
        "TailBenchmarkNode"
    )

    # === Handling edges assignment

    layerInfrastructure.add_edge(
        "HeadBenchmarkNode",
        "InputNode"
    )

    layerInfrastructure.add_edge(
        "InputNode",
        "MidNode-(1)"
    )

    layerInfrastructure.add_edge(
        "InputNode",
        "MidNode-(2)"
    )

    layerInfrastructure.add_edge(
        "InputNode",
        "MidNode-(3)"
    )

    layerInfrastructure.add_edge(
        "MidNode-(1)",
        "OutputNode"
    )

    layerInfrastructure.add_edge(
        "MidNode-(2)",
        "OutputNode"
    )

    layerInfrastructure.add_edge(
        "MidNode-(3)",
        "OutputNode"
    )

    layerInfrastructure.add_edge(
        "OutputNode",
        "TailBenchmarkNode"
    )

    return layerInfrastructure