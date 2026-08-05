import sys
import os
from datetime import datetime
from src.userInterfaceConfig import ask_configuration_settings
from src.userInterfaceConfig import get_applications_mapping_config
from src.utils.dynamicPlacementFactory import DynamicPlacementFactory
from eclypse.remote.bootstrap import RayOptionsFactory, RemoteBootstrap

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

def select_run_mode():
    run_mode = os.environ.get("PEERMOA_RUN_MODE", "local").lower()
    remote_config = ""

    if run_mode == "local":
        # Local run: only 1 machine
        remote_config = True
    elif run_mode == "dist_strict":
        # Fixed Cluster: fixed assignments defined by the user
        remote_config = RemoteBootstrap(ray_options_factory=DynamicPlacementFactory())
    else: 
        # Dynamic Cluster: assignments handled by Ray
        remote_config = RemoteBootstrap(ray_options_factory=RayOptionsFactory())
    
    return remote_config

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
    num_workers = gui_res.get("num_workers", 3)
    requeue_policy = gui_res.get("requeue_policy", "head")

    # Naming the run after the configuration it belongs to, so the six benchmark
    # runs are identifiable from the log directory alone.
    # PUSH-LOCAL, PUSH-DIST, PULL-LOCAL-HEAD, PULL-DIST-HEAD, PULL-LOCAL-TAIL, PULL-DIST-TAIL
    deploy_tag = "LOCAL" if os.environ.get("PEERMOA_RUN_MODE", "local").lower() == "local" else "DIST"
    run_tag = f"{app_shortname}-{deploy_tag}"
    if app_config.get("is_pull", False):
        run_tag += f"-{requeue_policy.upper()}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = f"./logs/{run_tag}_{timestamp}/"

    seed = 2
    sim_config = SimulationConfig(
        seed=seed,
        max_steps=100000000,
        step_every_ms=10,
        log_to_file=True,
        path=log_path,
        remote=select_run_mode(),
        log_level="INFO",
        include_default_metrics=False,
    )

    # Determine which arguments to pass based on a custom flag in the UI mapping.
    # If the app is flagged as "is_pull", we instantiate it with num_workers instead of num_layers.
    is_pull_architecture = app_config.get("is_pull", False)

    if is_pull_architecture:
        print(f"=====\n Starting Pull Architecture [{run_tag}] with {num_workers} workers, requeue policy '{requeue_policy}'... \n=====")
        infrastructure = app_functions["infrastructureFunction"](num_workers=num_workers)

        app_kwargs = {"num_workers": num_workers, "requeue_policy": requeue_policy}
        ollama_hosts = os.environ.get("PEERMOA_PULL_OLLAMA_HOSTS")
        if ollama_hosts:
            app_kwargs["ollama_hosts"] = ollama_hosts

        application = app_functions["applicationFunction"](**app_kwargs)
        deploy_strategy = app_functions["deployStrategyFunction"](num_workers=num_workers)
    else:
        print(f"=====\n Starting Push Architecture with {num_layers} layers... \n=====")
        infrastructure = app_functions["infrastructureFunction"](num_layers=num_layers)
        application = app_functions["applicationFunction"](num_layers=num_layers)
        deploy_strategy = app_functions["deployStrategyFunction"](num_layers=num_layers)

    simulation = Simulation(
        infrastructure,
        simulation_config=sim_config
    )

    simulation.register(
        application,
        deploy_strategy
    )

    simulation.start()
    simulation.wait()