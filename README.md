# peerMoA

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

## Architecture

This project is based on [ECLYPSE framework](https://github.com/eclypse-org/eclypse), so each `Application` or `Service` is a subclass of their implementations.

### Services

Each service represent an agent, their behaviour is described into the `step()` function.

Each agent got an atomic role, so we are deploying same agents but in a different graph, defined by the `Application`.

They stores **agents behaviour**, each one got a *specific role*:
- [`HeadBenchmarkService`](./src/services/benchmarkServices.py)
    - Agent that starts the benchmark, his role is to read the questions in the dataset of the selected topic, sending the message in the [`messageDictTemplate`](./src/utils/messageDictUtils.py).
- [`InputNodeService`](./src/services/inputNodeService.py)
    - The first agent of the [`LayerApplication`](../applications/layerApplication.py). His role is to broadcast the current message to the next three [`MidNodeServices`](./midNodeService.py).
- [`MidNodeService`](./src/services/midNodeService.py)
    - Agent that calls the selected model. He waits the questions and uses them to generate the prompt.
    - After the response from the model he sends to all his neighbours the message in the [`messageDictTemplate`](./src/utils/messageDictUtils.py) writing the answer *value* at the `messageDict.predictedAnswer` *key*.
- [`OutputNodeService`](./src/services/outputNodeService.py)
    - write here
- [`TailBenchmarkService`](./src/services/benchmarkServices.py)
    - write here

### Applications

In the `Application` we define how agents interacts with each other, deploying them in a graph.

So using applications we can compose `Services`.

#### Fixed Applications

- The tool offers some fixed `Applications`:
    - [*`SingleAgentApplication`*](./src/applications/singleAgentApplication.py): It offers a single agent deploy, used to test the model without the Mixture of Agent approach on the benchmark's selected topic.
    - [*`LayerApplication`*](./src/applications/layerApplication.py)

#### P2P Applications

- next