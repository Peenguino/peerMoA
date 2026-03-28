import ollama
import questionary
from datasets import get_dataset_config_names
from src.services.benchmarkServices import BenchmarkService
from src.services.midNodeService import MidNodeService
from src.services.outputNodeService import OutputNodeService
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

    # Asking for the benchmark topic

    if not list_topics:
        questionary.print("\nError during the dataset topics API fetch.", style="bold fg:red")
        return -1

    BenchmarkService.selected_topic = questionary.select(
        "Select the benchmark's topic:",
        choices=list_topics,
        use_arrow_keys=True
    ).ask()

    # Asking for the application to run

    config_application_map = get_applications_mapping_config()
    applications_list = list(config_application_map.keys())

    selected_application = questionary.select(
        "Select the application to start:",
        choices=applications_list,
        use_shortcuts=True,
        use_arrow_keys=True
    ).ask()

    questionary.print(
        f"\n Ready! Model: {selected_model} | Topic: {BenchmarkService.selected_topic} | Application: {selected_application} ",
        style="bold fg:green"
    )

    return {
        "app_name": selected_application,
        "functions": config_application_map[selected_application]
    }


