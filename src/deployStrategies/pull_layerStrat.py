from eclypse.placement.strategies import StaticStrategy

def get_static_pull_deploy_strategy(num_workers=3):
    
    # 1:1 Static mapping between Service and Node
    mappingServiceToNode = {
        "QueueHeadService": "QueueHeadNode",
        "SynthOutService": "SynthOutNode"
    }

    # Map the 3 workers
    for i in range(1, num_workers + 1):
        mappingServiceToNode[f"ElabMidService-{i}"] = f"ElabMidNode-{i}"

    return StaticStrategy(mapping=mappingServiceToNode)