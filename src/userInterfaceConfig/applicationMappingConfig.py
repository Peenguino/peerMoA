from src.applications import get_single_agent_application, get_layer_application
from src.infrastructures import get_single_agent_infrastructure, get_layer_infrastructure
from src.deployStrategies import get_static_single_agent_deploy_strategy, get_static_layer_deploy_strategy
from src.applications import get_pull_application
from src.infrastructures import get_pull_infrastructure
from src.deployStrategies import get_static_pull_deploy_strategy

def get_applications_mapping_config():
    applicationsMappingConfig = {
        "singleAgentApplication": {
            "shortName": "SAA",
            "isPull": False,
            "applicationFunction": get_single_agent_application,
            "infrastructureFunction": get_single_agent_infrastructure,
            "deployStrategyFunction": get_static_single_agent_deploy_strategy
        },
        "layerApplication": {
            "shortName": "LA",
            "isPull": False,
            "applicationFunction": get_layer_application,
            "infrastructureFunction": get_layer_infrastructure,
            "deployStrategyFunction": get_static_layer_deploy_strategy
        },
        "pullApplication": {
            "shortName": "PULL",
            "is_pull": True,
            "applicationFunction": get_pull_application,
            "infrastructureFunction": get_pull_infrastructure,
            "deployStrategyFunction": get_static_pull_deploy_strategy
        }
    }
    return applicationsMappingConfig