from eclypse.remote.service import Service
from src.utils.elabClassUtils import ElabClassUtils

class OutputNodeService(Service, ElabClassUtils):
    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        
    async def step(self):
        waitedMessages = 3
        receivedDictList = []

        self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} waiting for messages...\n")
        for i in range(waitedMessages):
            receivedDict = await self.mpi.recv()
            self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} received message {i} \n")
            receivedDictList.append(receivedDict)
        
        synthetized_prompt = f"""
You are an expert evaluator. You are given a multiple-choice question and the proposed
answers from 3 different AI agents. Your task is to analyze their answers, find the consensus or the most
logical answer, and output ONLY the final correct letter (A, B, C, or D).
Question: {receivedDictList[0]['originalPrompt']}
| Agent 1 says: {receivedDictList[0]['predictedAnswer']}
| Agent 2 says: {receivedDictList[1]['predictedAnswer']}
| Agent 3 says: {receivedDictList[2]['predictedAnswer']}
Final Answer:
"""
        
        elaborated = await self.elab(synthetized_prompt)
        self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} answered: {elaborated}\n")

        sentDict = {
            **(receivedDictList[0]),
            "predictedAnswer": elaborated,
            "count": 0
        }

        await self.mpi.bcast(sentDict)
        self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} sent final evaluation to TailService. \n")
