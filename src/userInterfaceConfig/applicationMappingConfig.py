from src.applications import get_single_agent_application, get_layer_application
from src.infrastructures import get_single_agent_infrastructure, get_layer_infrastructure
from src.deployStrategies import get_static_single_agent_deploy_strategy, get_static_layer_deploy_strategy

def get_applications_mapping_config():
    applicationsMappingConfig = {
        "singleAgentApplication": {
            "shortName": "SAA",
            "applicationFunction": get_single_agent_application,
            "infrastructureFunction": get_single_agent_infrastructure,
            "deployStrategyFunction": get_static_single_agent_deploy_strategy
        },
        "layerApplication": {
            "shortName": "LA",
            "applicationFunction": get_layer_application,
            "infrastructureFunction": get_layer_infrastructure,
            "deployStrategyFunction": get_static_layer_deploy_strategy
        }
    }
    return applicationsMappingConfig