import ollama
import questionary
from datasets import get_dataset_config_names
from src.services.benchmarkServices import BenchmarkService
from src.services.midNodeService import MidNodeService
from src.services.outputNodeService import OutputNodeService
from src.services.pull_elabMidService import ElabMidService
from src.services.pull_queueHeadService import QueueHeadService
from src.services.pull_synthOutService import SynthOutService
from src.userInterfaceConfig.applicationMappingConfig import get_applications_mapping_config

def ask_configuration_settings():
    # State of user locally installed SML
    list_models = ollama.list()
    models_list_name = [obj.model for obj in list_models.models]

    # List all benchmark topics on MMLU, inside a try/catch because we are querying a remote DB
    try:
        list_topics = get_dataset_config_names("cais/mmlu")
        list_topics.sort()
    except:
        list_topics = []

    questionary.print(
        "\nWelcome to PeerMoA!\n"
        "\nThis system uses ollama to run local Small Language Model (SLM) by agents distributed on graph nodes.\n"
        "\nReading SLM installed with ollama...\n",
        style="bold"
    )

    # Asking for the model

    if not models_list_name:
        questionary.print(
            "\nNo models installed locally with ollama.\n"
            "Install models with 'ollama pull [model_name]'",
            style="bold fg:red"
        )
        return -1

    selected_model = questionary.select(
        "Select the model:",
        choices=models_list_name,
        use_arrow_keys=True,
        use_shortcuts=True
    ).ask()

    MidNodeService.elab_into_string_configuration['model'] = selected_model
    OutputNodeService.elab_into_char_configuration['model'] = selected_model

    # The pull services keep their own copies: the configuration dicts are built at
    # class definition time, so setting `selected_model` alone would not reach them.
    # Without this the pull runs would silently ignore the choice above and stay on
    # the hardcoded default, making any push/pull comparison meaningless.
    ElabMidService.selected_model = selected_model
    ElabMidService.elab_into_string_configuration['model'] = selected_model
    SynthOutService.selected_model = selected_model
    SynthOutService.elab_into_string_configuration['model'] = selected_model
    SynthOutService.elab_into_char_configuration['model'] = selected_model

    # Asking for the benchmark topic

    if not list_topics:
        questionary.print("\nError during the dataset topics API fetch.", style="bold fg:red")
        return -1

    BenchmarkService.selected_topic = questionary.select(
        "Select the benchmark's topic:",
        choices=list_topics,
        use_arrow_keys=True
    ).ask()

    # Same reasoning as the model above: the pull services read their own attribute.
    QueueHeadService.selected_topic = BenchmarkService.selected_topic
    SynthOutService.selected_topic = BenchmarkService.selected_topic

    # Asking for the application to run

    config_application_map = get_applications_mapping_config()
    applications_list = list(config_application_map.keys())

    # Asking for type of pipeline if layer application has been selected

    selected_application = questionary.select(
        "Select the application to start:",
        choices=applications_list,
        use_shortcuts=True,
        use_arrow_keys=True
    ).ask()

    num_layers_selected = 1
    if selected_application == "layerApplication":
        num_layers_selected = int(questionary.text(
            "How many layers for the MoA pipeline?",
            default="1",
            # Forcing user input: no pipelines longer than 3 layers
            validate=lambda text: text.isdigit() and int(text) > 0 and int(text) < 4
        ).ask())

    # Asking for the number of workers and the queue policy, only for the pull scheme:
    # both are meaningless for the push applications, which have no shared task queue.
    num_workers_selected = 3
    requeue_policy_selected = "head"
    if selected_application == "pullApplication":
        num_workers_selected = int(questionary.text(
            "How many worker nodes for the Pull MoA scheme?",
            default="3",
            validate=lambda text: text.isdigit() and int(text) > 0
        ).ask())

        requeue_policy_label = questionary.select(
            "Requeue policy for partially elaborated tasks:",
            choices=[
                "head - priority to work in progress (a co-located worker can re-pull it immediately)",
                "tail - fairer across workers, at the cost of more work in progress",
            ],
            use_arrow_keys=True
        ).ask()
        requeue_policy_selected = requeue_policy_label.split(" - ")[0]

    ready_line = (
        f"\n Ready! Model: {selected_model} | Topic: {BenchmarkService.selected_topic} "
        f"| Application: {selected_application} "
    )
    if selected_application == "pullApplication":
        ready_line += f"| Requeue policy: {requeue_policy_selected} "

    questionary.print(ready_line, style="bold fg:green")

    return {
        "app_name": selected_application,
        "functions": config_application_map[selected_application],
        "num_layers": num_layers_selected,
        "num_workers": num_workers_selected,
        "requeue_policy": requeue_policy_selected
    }