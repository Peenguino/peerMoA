from ollama import AsyncClient
from eclypse.remote.service import Service

class MidNodeService(Service):
    '''
    Assuming that the default model is qwen2.5, we are
    overwriting this field from the UI module
    '''
    selected_model = 'qwen2.5:1.5b'

    elab_into_string_configuration = {
        'model': selected_model,
        'options': {
                'temperature': 0.7, 
            }
    }

    @staticmethod
    def get_system_prompt(*agentAnswers):

        answers_generic_layer = [a for a in agentAnswers if a]

        if not answers_generic_layer:
            return """You are a helpful, creative, and intelligent AI assistant. Provide a comprehensive,
    accurate, and well-structured answer to the user's multiple-choice question.
    """

        num_agents = len(answers_generic_layer)
        agents_lines = "\n".join([f"| Agent {i+1} says: {answer}" for i, answer in enumerate(answers_generic_layer)])
        
        system_prompt = f"""You have been provided with a set of responses from {num_agents} open-source models 
        to a multiple-choice question. Your task is to synthesize these responses into a single, high-quality 
    response. It is crucial to critically evaluate the information provided in these responses, recognizing 
    that some of it may be biased or incorrect. Your response should not simply replicate the given answers 
    but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response 
    is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.
    Answers from open-source agent models:
    {agents_lines}
    """
        return system_prompt
        
    @staticmethod
    async def elab_into_string(original_prompt, *agentAnswers):
        system_prompt = MidNodeService.get_system_prompt(*agentAnswers)

        response = await AsyncClient().chat(
            model=MidNodeService.elab_into_string_configuration['model'],
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
            options=MidNodeService.elab_into_string_configuration['options']
        )

        content = response['message']['content'].strip()

        if len(content) > 0:
            return content
        else:
            return ""
        
    def __init__(self, service_id, comm_interface = "mpi", store_step = False):
        super().__init__(service_id, comm_interface, store_step)

    async def step(self):
        self.logger.info(f"=====\n MidNodeService ID: {self._service_id} checking for messages... \n")
        receivedDict = await self.mpi.recv()
        
        if receivedDict:
            original_prompt = receivedDict["originalPrompt"]

            previous_layer_synth_text = receivedDict.get("generatedText", "")
            
            self.logger.info(f"=====\n MidNodeService ID: {self._service_id} received: \n {original_prompt}")

            elaborated = await self.elab_into_string(original_prompt, previous_layer_synth_text)
            self.logger.info(f"=====\n MidNodeService ID: {self._service_id} answered: {elaborated}\n")

            sentDict = {
                **receivedDict,
                "generatedText": elaborated,
            }
            await self.mpi.bcast(sentDict)
            self.logger.info(f"=====\n MidNodeService ID: {self._service_id} sent: {sentDict.get('predictedAnswer', '')}\n")
