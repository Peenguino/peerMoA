import sys
from datetime import datetime
from src.userInterfaceConfig import ask_configuration_settings
from src.userInterfaceConfig import get_applications_mapping_config

from eclypse.simulation import (
    Simulation,
    SimulationConfig
)

if __name__ == "__main__":

    gui_res = ask_configuration_settings()
    map_config = get_applications_mapping_config()

    if gui_res == -1:
        print("Error during UI configuration. Exiting the process.")
        sys.exit(1)

    # Accessing the current configuration for the selected application
    app_name = gui_res["app_name"]
    app_config = map_config[app_name]

    app_shortname = app_config["shortName"]
    app_functions = gui_res["functions"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = f"./logs/{app_shortname}_{timestamp}/"

    seed = 2
    sim_config = SimulationConfig(
        seed=seed,
        max_steps=3000,
        step_every_ms=1000,
        log_to_file=True,
        path=log_path,
        remote=True,
        log_level="INFO",
        include_default_metrics=True,
    )

    simulation = Simulation(
        app_functions["infrastructureFunction"](),
        simulation_config=sim_config
    )

    simulation.register(
        app_functions["applicationFunction"](),
        app_functions["deployStrategyFunction"]()
    )

    simulation.start()
    simulation.wait()
    print(simulation.report.application())