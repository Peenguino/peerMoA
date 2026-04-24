import sys
import os
from datetime import datetime
from src.userInterfaceConfig import ask_configuration_settings
from src.userInterfaceConfig import get_applications_mapping_config

from eclypse.simulation import (
    Simulation,
    SimulationConfig
)

def detach_and_run_in_background(log_filename="benchmark_output.log"):
    try:
        # First fork
        if os.fork() > 0:
            print(f"\n Benchmark going in background...")
            print(f"\nLast run will be saved into {log_filename} also.")
            sys.exit(0)
    except OSError:
        sys.exit(1)

    # Creation of a new session from the child process
    os.setsid()

    # Using the Double-Fork approach:
    # - forking another time will ensure that the new process is not the session leader
    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    # Handling std output and error streams to avoid crashes closing the SSH session
    # - flushing current streams
    sys.stdout.flush()
    sys.stderr.flush()

    # - opening streams with context manager with:
    # -- Redirecting stdin into /dev/null
    # -- Redirecting stdout into last run logs `log_filename`
    # -- Redirecting stderr into last run logs `log_filename`
    with open('/dev/null', 'r') as stdin, open(log_filename, 'w') as stdout:
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stdout.fileno(), sys.stderr.fileno())

    with open('.main_pid.txt', 'w') as pid_file:
        pid_file.write(str(os.getpid()))

if __name__ == "__main__":

    gui_res = ask_configuration_settings()
    map_config = get_applications_mapping_config()

    if gui_res == -1:
        print("Error during UI configuration. Exiting the process.")
        sys.exit(1)

    # Handling the process detach
    detach_and_run_in_background()

    # Accessing the current configuration for the selected application
    app_name = gui_res["app_name"]
    app_config = map_config[app_name]

    app_shortname = app_config["shortName"]
    app_functions = gui_res["functions"]
    num_layers = gui_res.get("num_layers", 1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = f"./logs/{app_shortname}_{timestamp}/"

    seed = 2
    sim_config = SimulationConfig(
        seed=seed,
        max_steps=1000000,
        step_every_ms=10,
        log_to_file=True,
        path=log_path,
        remote=True,
        log_level="INFO",
        include_default_metrics=False,
    )

    simulation = Simulation(
        app_functions["infrastructureFunction"](num_layers=num_layers),
        simulation_config=sim_config
    )

    simulation.register(
        app_functions["applicationFunction"](num_layers=num_layers),
        app_functions["deployStrategyFunction"](num_layers=num_layers)
    )

    simulation.start()
    simulation.wait()