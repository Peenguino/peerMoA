import os
import signal
from eclypse.remote.service import Service
from datasets import load_dataset
from src.utils.messageDictUtils import get_message_dict_template

class BenchmarkService(Service):

    # Assuming that default value for topic is abstract algebra
    selected_topic = "abstract_algebra"

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)

        self.topic = BenchmarkService.selected_topic
        self.dataset_test = load_dataset("cais/mmlu", self.topic, split="test")
        self.dataset_dev = load_dataset("cais/mmlu", self.topic, split="dev")


class HeadBenchmarkService(BenchmarkService):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        self.current_idx = 0
        self.prefix = ""

        # Defining a sliding window:
        # - We were using single acks from TailBenchmarkService to allow sending new entry from current Service
        # - The goal was to reduce the Out Of Memory caused by the unlimited queue
        # - Now we assume that the max size of the sliding window is 10 entries
        self.max_in_flight = 10
        self.current_in_flight = 0

    def create_few_shot_prefix(self, dev_data, n_shots=5):
        prefix = "Instruction: Answer the following multiple choice questions by giving only the letter (A, B, C, or D) of the correct answer.\n\n"
        for i in range(n_shots):
            current_entry = dev_data[i]
            prefix += f"Question: {current_entry['question']}\n"

            for idx, choice in enumerate(['A', 'B', 'C', 'D']):
                prefix += f"{choice}. {current_entry['choices'][idx]}\n"

            prefix += f"Answer: {['A', 'B', 'C', 'D'][current_entry['answer']]}\n\n"
        return prefix

    async def step(self):

        if self.current_idx == 0:
            self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} started. \n")
        
        if len(self.prefix) == 0:
            # Currently not using the few shot prefix
            self.prefix = self.create_few_shot_prefix(self.dataset_dev)
            self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} loaded datasets on {self.topic}. \n")

        # Dataset end handling
        if self.current_idx >= len(self.dataset_test):
            # Checking if there are still in flight messages
            if self.current_in_flight > 0:
                ack_msg = await self.mpi.recv()
                if ack_msg and ack_msg.get("type") == "ACK":
                    self.current_in_flight -= 1
            else:
                if self.current_idx == len(self.dataset_test):
                    self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} all questions sent and all ACKs received. \n")
                    self.current_idx += 1

                # Blocking the microservice when his task is finished
                await self.mpi.recv()
            return

        # Full sliding window handling
        if self.current_in_flight >= self.max_in_flight:
            self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} sliding window is full ({self.max_in_flight}). Waiting for ACK... \n")
            
            ack_msg = await self.mpi.recv()
            if ack_msg and ack_msg.get("type") == "ACK":
                self.current_in_flight -= 1
                self.logger.info(f"=====\n New ACK ID {ack_msg['id']}. Now there is space in the sliding window.\n")
            
            return

        # Sending new message
        item = self.dataset_test[self.current_idx]

        messageDictTemplate = get_message_dict_template()

        messageDict = {
            **messageDictTemplate,
            "id": self.current_idx,
            "expectedAnswer": ['A', 'B', 'C', 'D'][item["answer"]],
            "count": 0
        }

        prompt = f"Question: {item['question']}\n"
        
        for choice_idx, choice in enumerate(['A', 'B', 'C', 'D']):
            prompt += f"{choice}. {item['choices'][choice_idx]}\n"
        prompt += "Answer: "

        messageDict['originalPrompt'] = prompt
        self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} ready to send messageDict ID: {messageDict['id']}. \n")
        
        await self.mpi.bcast(messageDict)
        
        # Updating window's state
        self.current_idx += 1
        self.current_in_flight += 1
        self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} sent messageDict ID: {messageDict['id']}. In flight: {self.current_in_flight}/{self.max_in_flight} \n")

class TailBenchmarkService(BenchmarkService):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        self.correct_count = 0
        self.received_count = 0
        self.total_expected = len(self.dataset_test)
        self.correct_counts_per_layer = []
    
    async def step(self):
        if self.received_count == 0:
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} started. \n")

        self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} checking for messages... \n")
        messageDict = await self.mpi.recv()

        if messageDict:
            actual = messageDict["expectedAnswer"]
            predictions = messageDict.get("layerPredictions", [])

            # Counters for each layer:
            # - We are defining an array of counters [0, ..., 0] for each layer
            if not self.correct_counts_per_layer:
                self.correct_counts_per_layer = [0] * len(predictions)

            # Checking each layer
            for i, prediction in enumerate(predictions):
                clean_prediction = str(prediction).strip().upper()
                self.logger.info(f"=====\n TailBenchmarkService: Layer {i+1} (Actual: {actual}, Predicted: {clean_prediction})")
                if clean_prediction == actual:
                    self.correct_counts_per_layer[i] += 1

            self.received_count += 1

            # Sending ACK to HeadBenchmarkService for backpressure
            ack_message = {"type": "ACK", "id": messageDict["id"]}
            await self.mpi.send("HeadBenchmarkService", ack_message)
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} sent ACK for msg {messageDict['id']}. \n")
            
            # Printing results
            if self.received_count == self.total_expected:
                self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} ======== RESULTS ========. \n")
                for i, count in enumerate(self.correct_counts_per_layer):
                    accuracy = (count / self.total_expected) * 100
                    self.logger.info(f"Layer {i+1} Accuracy: {accuracy:.2f}% ({count}/{self.total_expected})")

                # Handling simulation termination
                try:
                    with open('.main_pid.txt', 'r') as file_pid:
                        main_pid = int(file_pid.read().strip())
                        self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} sent SIGINT to main PID: {main_pid} to end simulation.\n")
                        os.kill(main_pid, signal.SIGINT)
                except Exception as err:
                    self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} error sending SIGINT to main PID: {main_pid}.\n")


