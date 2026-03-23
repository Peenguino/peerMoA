from src.applications import get_single_agent_application, get_layer_application
from src.infrastructures import get_single_agent_infrastructure, get_layer_infrastructure
from src.deployStrategies import get_static_single_agent_deploy_strategy, get_static_layer_deploy_strategy

from eclypse.simulation import (
    Simulation,
    SimulationConfig
)
from eclypse.utils.constants import DEFAULT_SIM_PATH

if __name__ == "__main__":

    seed = 2
    sim_config = SimulationConfig(
        seed=seed,
        max_steps=3000,
        step_every_ms=1000,
        log_to_file=True,
        path="./logs/date",
        remote=True,
        log_level="INFO",
        include_default_metrics=True,
    )

    '''
    simulation = Simulation(
        get_single_agent_infrastructure(),
        simulation_config=sim_config
    )

    simulation.register(
        get_single_agent_application(),
        get_static_single_agent_deploy_strategy()
    )
    '''

    simulation = Simulation(
        get_layer_infrastructure(),
        simulation_config=sim_config
    )

    simulation.register(
        get_layer_application(),
        get_static_layer_deploy_strategy()
    )

    simulation.start()
    simulation.wait()
    print(simulation.report.application())