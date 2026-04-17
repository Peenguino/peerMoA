import re
from ollama import AsyncClient
from eclypse.remote.service import Service

class OutputNodeService(Service):

    '''
    Assuming that the default model is qwen2.5, we are
    overwriting this field from the UI module
    '''
    selected_model = 'qwen2.5:1.5b'

    # Options for the char synthesize
    elab_into_char_configuration = {
        'model': selected_model,
        'options': {
                'temperature': 0.1, 
                'num_predict': 5, 
                'stop': ["\n", "Question:", "Answer:"] 
            }
    }

    # Options for the string synthesize
    elab_into_string_configuration = {
        'model': selected_model,
        'options': {
            'temperature': 0.7, 
        }
    }

    def __init__(self, service_id, expected_messages=3, is_final_layer=True, comm_interface="mpi", store_step=False):
        super().__init__(service_id, comm_interface, store_step)
        self.message_map = {}
        self.expected_messages = expected_messages
        self.is_final_layer = is_final_layer

# ==== CHAR SYNTH: Used on each OutputService, it allows to calculate intermediate and final score

    @staticmethod
    def get_char_prompt(*agentAnswers):
        num_agents = len(agentAnswers)
        agents_lines = "\n".join([f"| Agent {i+1} says: {answer}" for i, answer in enumerate(agentAnswers)])
        
        system_content = f"""You have been provided with a set of responses from {num_agents} open-source 
models to a multiple-choice question. Your task is to synthesize these responses into a single, 
high-quality response. It is crucial to critically evaluate the information provided in these responses, 
recognizing that some of it may be biased or incorrect. Your response should not simply replicate the 
given answers but should offer a refined, accurate, and comprehensive reply to the instruction. 
Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy 
and reliability.
Output ONLY the final correct letter (A, B, C, or D)

Responses from models:
{agents_lines}"""
        
        return system_content

    @staticmethod
    async def elab_into_char(system_prompt, original_prompt):
        response = await AsyncClient().chat(
            model=OutputNodeService.elab_into_char_configuration['model'],
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': original_prompt
                }
            ],
            options=OutputNodeService.elab_into_char_configuration['options']
        )

        raw_res = response['message']['content'].strip().upper()

        if len(raw_res) > 0:
            import re
            match = re.search(r'[ABCD]', raw_res)
            return match.group(0) if match else ""
        return ""
    
# ==== STRING SYNTH: Used only if the service it's not the last one

    @staticmethod
    def get_string_prompt(*agentAnswers):
        num_agents = len(agentAnswers)
        agents_lines = "\n".join([f"| Agent {i+1} says: {answer}" for i, answer in enumerate(agentAnswers)])
        
        system_content = f"""You have been provided with a set of responses from {num_agents} open-source 
models to a multiple-choice question. Your task is to synthesize these responses into a single, 
high-quality response. It is crucial to critically evaluate the information provided in these responses, 
recognizing that some of it may be biased or incorrect. Your response should not simply replicate the 
given answers but should offer a refined, accurate, and comprehensive reply to the instruction. 
Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy 
and reliability.

Responses from models:
{agents_lines}"""
        return system_content

    @staticmethod
    async def elab_into_string(system_prompt, original_prompt):
        response = await AsyncClient().chat(
            model=OutputNodeService.elab_into_string_configuration['model'],
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': original_prompt}
            ],
            options=OutputNodeService.elab_into_string_configuration['options']
        )
        return response['message']['content'].strip()
        
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

            if count_same_question == self.expected_messages:
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} all messages received for query ID: {msg_id}. Starting evaluation...\n")
                receivedDictList = self.message_map[msg_id]

                original_prompt = receivedDictList[0]['originalPrompt']
                answers_list = [msg['generatedText'] for msg in receivedDictList]

                char_system_prompt = OutputNodeService.get_char_prompt(*answers_list)
                elaborated_char = await self.elab_into_char(char_system_prompt, original_prompt)
                
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} answered: {elaborated_char}\n")

                history = list(receivedDictList[0].get("layerPredictions", []))
                history.append(elaborated_char)

                if self.is_final_layer:
                    elaborated_text = elaborated_char
                    self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} is final layer. Synth into char.\n")
                else:
                    self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} generating reasoning text for next layer...\n")
                    string_prompt = OutputNodeService.get_string_prompt(*answers_list)
                    elaborated_text = await OutputNodeService.elab_into_string(string_prompt, original_prompt)

                sentDict = {
                    **(receivedDictList[0]),
                    "predictedAnswer": elaborated_char,
                    "generatedText": elaborated_text,
                    "layerPredictions": history,
                    "count": 0
                }

                await self.mpi.bcast(sentDict)
                self.logger.info(f"=====\n OutputNodeService ID: {self._service_id} sent evaluation forward. \n")

                del self.message_map[msg_id]
