from eclypse.remote.service import Service
from src.utils.elabClassUtils import ElabClassUtils
from src.utils.synthStringUtils import get_synth_string

class OutputNodeService(Service, ElabClassUtils):
    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)
        self.message_map = {}
        
    async def step(self):

        self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} waiting for messages...\n")
        receivedDict = await self.mpi.recv()

        if receivedDict:
            msg_id = receivedDict['id']
            self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} received message {msg_id} \n")

            if msg_id not in self.message_map:
                self.message_map[msg_id] = []
            
            self.message_map[msg_id].append(receivedDict)

            count_same_question = len(self.message_map[msg_id])
            self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} received message for query ID: {msg_id}. Progress: {count_same_question}/3 \n")

            if count_same_question == 3:
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} all messages received for query ID: {msg_id}. Starting evaluation...\n")
                receivedDictList = self.message_map[msg_id]

                original_prompt = receivedDictList[0]['originalPrompt']
                answers_list = [msg['predictedAnswer'] for msg in receivedDictList]

                synthetized_prompt = get_synth_string(original_prompt, *answers_list)
        
                elaborated = await self.elab(synthetized_prompt)
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} answered: {elaborated}\n")

                sentDict = {
                    **(receivedDictList[0]),
                    "predictedAnswer": elaborated,
                    "count": 0
                }

                await self.mpi.bcast(sentDict)
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} sent final evaluation to TailService. \n")
