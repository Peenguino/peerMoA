from ollama import AsyncClient
from eclypse.remote.service import Service

class OutputNodeService(Service):

    '''
    Assuming that the default model is qwen2.5, we are
    overwriting this field from the UI module
    '''
    selected_model = 'qwen2.5:1.5b'

    elab_into_char_configuration = {
            'model': selected_model,
            'options': {
                    'temperature': 0.7, 
                    'num_predict': 5, 
                    'stop': ["\n", "Question:", "Answer:"] 
                }
        }

    @staticmethod
    def get_prompt(originalPrompt, *agentAnswers):
        num_agents = len(agentAnswers)
        
        agents_lines = "\n".join([f"| Agent {i+1} says: {answer}" for i, answer in enumerate(agentAnswers)])
        
        prompt = f"""You have been provided with a set of responses from {num_agents} open-source models 
        to a multiple-choice question. Your task is to synthesize these responses into a single, high-quality 
    response. It is crucial to critically evaluate the information provided in these responses, recognizing 
    that some of it may be biased or incorrect. Your response should not simply replicate the given answers 
    but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response 
    is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.
    Output ONLY the final correct letter (A, B, C, or D)
    Question: {originalPrompt}
    Answers from open-source agent models: 
    {agents_lines}
    """
        return prompt

    @staticmethod
    async def elab_into_char(prompt):
        response = await AsyncClient().generate(
            **OutputNodeService.elab_into_char_configuration,
            prompt=prompt
        )

        raw_res = response['response'].strip().upper()

        if len(raw_res) > 0:
            return raw_res[0]
        else:
            return ""

    def __init__(self, service_id, expected_messages=3, comm_interface="mpi", store_step=False):
        super().__init__(service_id, comm_interface, store_step)
        self.message_map = {}
        self.expected_messages = expected_messages
        
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
            self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} received message for query ID: {msg_id}. Progress: {count_same_question}/{self.expected_messages} \n")

            if count_same_question == 3:
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} all messages received for query ID: {msg_id}. Starting evaluation...\n")
                receivedDictList = self.message_map[msg_id]

                original_prompt = receivedDictList[0]['originalPrompt']
                answers_list = [msg['generatedText'] for msg in receivedDictList]

                synthetized_prompt = OutputNodeService.get_prompt(original_prompt, *answers_list)
        
                elaborated = await self.elab_into_char(synthetized_prompt)
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} answered: {elaborated}\n")

                sentDict = {
                    **(receivedDictList[0]),
                    "predictedAnswer": elaborated,
                    "count": 0
                }

                await self.mpi.bcast(sentDict)
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} sent final evaluation to TailService. \n")
                
                del self.message_map[msg_id]
