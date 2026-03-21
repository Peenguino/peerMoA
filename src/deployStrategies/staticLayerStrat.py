from eclypse.placement.strategies import StaticStrategy

def get_static_layer_deploy_strategy():
    mappingServiceToNode = {
        # mapping ServiceID to NodeID
        "HeadBenchmarkService": "HeadBenchmarkNode",
        "InputNodeService": "InputNode",
        "MidNodeService-(1)": "MidNode-(1)",
        "MidNodeService-(2)": "MidNode-(2)",
        "MidNodeService-(3)": "MidNode-(3)",
        "OutputNodeService": "OutputNode",
        "TailBenchmarkService": "TailBenchmarkNode"
    }

    staticStrategy = StaticStrategy(mapping=mappingServiceToNode)
    return staticStrategy