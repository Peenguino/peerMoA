# peerMoA

Tool for MMLU benchmarks on [HuggingFace datasets](https://github.com/huggingface/datasets) on distributed layers of [Mixture-Of-Agent](https://github.com/togethercomputer/MoA) approach based on [ECLYPSE framework](https://github.com/eclypse-org/eclypse) and [ollama](https://ollama.com/).

UNIPI Bachelor thesis's project.

## Installing

Before installing this python script **make sure** that you [installed ollama](https://ollama.com/download/linux) and an **SML**.

```BASH
ollama pull [your_model]
```

After that you can clone the repo and **setup the script** using a `venv`:

```BASH
git clone https://github.com/Peenguino/peerMoA.git
cd ./peerMoA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

To launch the script, being into the *peerMoA* directory:

```BASH
python3 -u main.py
```
or use the `./run.sh` script.

### Runtime UI

The UI asks each time configurations for the benchmark:

https://github.com/user-attachments/assets/50e76da3-9e35-4367-938a-3471c6b1d5d3

## Architecture

This project is based on [ECLYPSE framework](https://github.com/eclypse-org/eclypse), so each `Application` or `Service` is a subclass of their implementations.

### Services

Each service represent an agent, their behaviour is described into the `step()` function.

Each agent got an atomic role, so we are deploying same agents but in a different graph, defined by the `Application`.

They stores **agents behaviour**, each one got a *specific role*:
- [`HeadBenchmarkService`](./src/services/benchmarkServices.py)
    - Agent that starts the benchmark, his role is to read the questions in the dataset of the selected topic, sending the message in the [`messageDictTemplate`](./src/utils/messageDictUtils.py).
- [`InputNodeService`](./src/services/inputNodeService.py)
    - The first agent of the [`LayerApplication`](../applications/layerApplication.py). 
        - His role it's to broadcast the current message to the next three [`MidNodeServices`](./midNodeService.py).
- [`MidNodeService`](./src/services/midNodeService.py)
    - Agent that calls the selected model. He waits the questions and uses them to generate the prompt.
    - After the response from the model he sends to all his neighbours the message in the [`messageDictTemplate`](./src/utils/messageDictUtils.py) writing the generated text *value* at the `generatedText` *key* into `messageDict` map.
    - This service uses an high temperature value $t$.
    - The interaction with the model it's based on *system/user* format prompt:
        - `System Prompt` Describes meta informations, so for this `Service`
            - If the `Service` it's placed in the first `ApplicationLayer` the system prompt describes the service behaviour without any previous generated answer.
            - If the `Service` it's placed in any other position the system prompt describes the service behaviour using the answer generated from the previous `OutputNodeService`.
        - `User Prompt` Describes the real prompt, in this case the question from the dataset's entry.
- [`OutputNodeService`](./src/services/outputNodeService.py)
    - It waits for each of the previous layer's `Services`, the count it's defined in the constructor.
    - This service uses a low temperature $t$ value, because his role it's to synthesize previous generated text into the correct answer to the asked question.
    - The interaction with the model it's based on *system/user* prompt.
- [`TailBenchmarkService`](./src/services/benchmarkServices.py)
    - His role it's to handle a `messageDict` and compare two fields `expectedAnswer` and `predictedAnswer`.
    - At the and it print the score, using the count calculated before.

### Applications

In the `Application` we define how agents interacts with each other, deploying them in a graph.

So using applications we can compose `Services`.

#### Fixed Applications

- The tool offers some fixed `Applications`:

##### [1. *`SingleAgentApplication`*](./src/applications/singleAgentApplication.py)

It offers a single agent deploy, used to test the model without the Mixture of Agent approach on the benchmark's selected topic.
<div style="text-align: center; padding: 20pt">
<img src="./docs/img/SingleAgentApplication.drawio.png" width="600">
</div>

There are two `NodeService`, but the `OutputNodeService` calls the model on low temperature, his role it's to choose the correct option answer on the knowledge shared by the `MidNodeService`.

##### [2. *`LayerApplication`*](./src/applications/layerApplication.py)

Single layer of the Mixture of Agent approach.

<div style="text-align: center; padding: 20pt">
<img src="./docs/img/LayerApplication.drawio.png" width="1000">
</div>

#### Distributed Applications

- next
