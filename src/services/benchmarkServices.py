from eclypse.remote.service import Service
from datasets import load_dataset

class BenchmarkService(Service):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)

        # TODO: Per ora stiamo hardcodando topic e datasets, poi possiamo passarli tramite file di config al costruttore di BenchmarkService
        self.topic = "abstract_algebra"
        self.dataset_test = load_dataset("cais/mmlu", self.topic, split="test")
        self.dataset_dev = load_dataset("cais/mmlu", self.topic, split="dev")

class HeadBenchmarkService(BenchmarkService):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        self.current_idx = 0
        self.prefix = ""

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
        self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} started. \n")
        
        if len(self.prefix) == 0:
            self.prefix = self.create_few_shot_prefix(self.dataset_dev)
            self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} loaded datasets on {self.topic}. \n")

        if self.current_idx >= len(self.dataset_test):
            if self.current_idx == len(self.dataset_test):
                self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} all questions sent. \n")
                self.current_idx += 1
            return
        
        item = self.dataset_test[self.current_idx]

        messageDict = {
            "id": self.current_idx,
            "originalPrompt": "",
            "expectedAnswer": ['A', 'B', 'C', 'D'][item["answer"]],
            "predictedAnswer": "",
            "count": 0
        }

        prompt = self.prefix + f"Question: {item['question']}\n"
        for choice_idx, choice in enumerate(['A', 'B', 'C', 'D']):
            prompt += f"{choice}. {item['choices'][choice_idx]}\n"
        prompt += "Answer: "

        messageDict['originalPrompt'] = prompt
        self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} ready to send messageDict ID: {messageDict['id']}. \n")
        
        await self.mpi.bcast(messageDict)
        self.logger.info(f"=====\n HeadBenchmarkService ID: {self._service_id} sent messageDict ID: {messageDict['id']}. \n")
        self.current_idx += 1

class TailBenchmarkService(BenchmarkService):

    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        self.correct_count = 0
        self.received_count = 0
        self.total_expected = len(self.dataset_test)
    
    async def step(self):

        if self.received_count == 0:
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} started. \n")

        if self.received_count == self.total_expected:        
            accuracy = (correct_count / len(self.dataset_test)) * 100
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} ======== RESULTS ========. \n")
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} Accuracy: {accuracy:.2f}% ({correct_count}/{len(self.dataset_test)})\n")

        if self.received_count >= self.total_expected:
            return

        self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} checking for messages... \n")
        messageDict = await self.mpi.recv()

        if messageDict:
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} received messageDict. \n")
            actual = messageDict["expectedAnswer"]
            predicted = str(messageDict["predictedAnswer"]).strip().upper()

            if predicted == actual:
                correct_count += 1

            self.received_count += 1
            self.logger.info(f"=====\n TailBenchmarkService ID: {self._service_id} Predicted {predicted}, answer was {actual}. \n")
        
