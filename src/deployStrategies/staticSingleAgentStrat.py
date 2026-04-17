from eclypse.placement.strategies import StaticStrategy

def get_static_single_agent_deploy_strategy(**kwargs):
    mappingServiceToNode = {
        # mapping ServiceID to NodeID
        "HeadBenchmarkService": "HeadBenchmarkNode",
        "MidNodeService": "MidNode",
        "OutputNodeService": "OutputNode",
        "TailBenchmarkService": "TailBenchmarkNode"
    }

    staticStrategy = StaticStrategy(mapping=mappingServiceToNode)
    return staticStrategy