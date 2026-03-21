from eclypse.placement.strategies import StaticStrategy

def get_static_single_agent_deploy_strategy():
    mappingServiceToNode = {
        # mapping ServiceID to NodeID
        #"Proposer-(1)": "proposer-(1)",
        #"Aggregator-(1-1)": "aggregator-(1-1)",
        "HeadBenchmarkService": "HeadBenchmarkNode",
        "MidNodeService": "MidNode",
        "TailBenchmarkService": "TailBenchmarkNode"
    }

    staticStrategy = StaticStrategy(mapping=mappingServiceToNode)
    return staticStrategy