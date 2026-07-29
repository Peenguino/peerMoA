import asyncio
from ollama import AsyncClient
from eclypse.remote.service import Service

class ElabMidService(Service):
    """
    ElabMidService acts as a worker in the Pull Architecture.
    It pulls tasks from the QueueHeadService, processes them using Ollama,
    and routes them either back to the queue or to the SynthOutService.
    """
    
    # Assuming that the default model is qwen2.5, we are
    # overwriting this field from the UI module
    selected_model = 'qwen2.5:1.5b'

    elab_into_string_configuration = {
        'model': selected_model,
        'options': {
            'temperature': 0.7, 
        }
    }

    def __init__(self, service_id, max_elaborations=3, store_step: bool = False, *args, **kwargs):
        super().__init__(
            service_id,
            comm_interface="rest",
            *args, 
            **kwargs
        )
        self.max_elaborations = max_elaborations

    @staticmethod
    def get_system_prompt(elaborations):
        """
        Generates the system prompt based on the current elaborations array.
        """
        # Filter out any empty strings just in case
        valid_elaborations = [e for e in elaborations if e]

        if not valid_elaborations:
            return """You are a helpful, creative, and intelligent AI assistant. Provide a comprehensive,
    accurate, and well-structured answer to the user's multiple-choice question."""

        num_agents = len(valid_elaborations)
        agents_lines = "\n".join([f"| Insight {i+1}: {text}" for i, text in enumerate(valid_elaborations)])
        
        system_prompt = f"""You have been provided with a set of insights from {num_agents} previous evaluations 
    to a multiple-choice question. Your task is to synthesize these responses into a single, high-quality 
    response. It is crucial to critically evaluate the information provided, recognizing that some of it 
    may be biased or incorrect. Your response should not simply replicate the given answers but should offer 
    a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, 
    coherent, and adheres to the highest standards of accuracy and reliability.
    
    Previous insights:
    {agents_lines}
    """
        return system_prompt
        
    @staticmethod
    async def elab_into_string(original_prompt, elaborations):
        """
        Calls the Ollama model to generate a new string based on the original prompt and previous elaborations.
        """
        system_prompt = ElabMidService.get_system_prompt(elaborations)

        response = await AsyncClient().chat(
            model=ElabMidService.elab_into_string_configuration['model'],
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
            options=ElabMidService.elab_into_string_configuration['options']
        )

        content = response['message']['content'].strip()
        return content if len(content) > 0 else ""

    async def step(self):
        """
        The main worker loop: pulls a task, processes it, and pushes it to the next destination.
        """
        self.logger.info(f"=====\n ElabMidService '{self._service_id}': Idle. Requesting task from QueueHeadService... \n")
        
        # Pull a task from the queue via REST GET
        pull_response = await self.rest.get("QueueHeadService/pull")


        if pull_response.status_code == 200:
            response_body = pull_response.body
            
            if response_body and response_body.get("status") == "OK":
                task = response_body.get("task")
                self.logger.info(f"=====\n ElabMidService '{self._service_id}': Received Task ID {task['id']} (Current count: {task['count']}). \n")
                
                original_prompt = task["originalPrompt"]
                elaborations = task.get("elaborations", [])
                
                # Process the prompt with Ollama
                elaborated_text = await self.elab_into_string(original_prompt, elaborations)
                
                # Update the task state
                task["elaborations"].append(elaborated_text)
                task["count"] += 1
                
                self.logger.info(f"=====\n ElabMidService '{self._service_id}': Processed Task ID {task['id']}. New count: {task['count']}. \n")

                # Route the task based on the count
                if task["count"] >= self.max_elaborations:
                    # Task is fully processed, send to SynthOutService
                    self.logger.info(f"=====\n ElabMidService '{self._service_id}': Task {task['id']} reached max elaborations. Sending to SynthOutService... \n")
                    
                    # Assuming SynthOutService will expose a '/synthesize' endpoint
                    await self.rest.post("SynthOutService/synthesize", task=task)
                else:
                    # Task needs more processing, requeue to QueueHeadService
                    self.logger.info(f"=====\n ElabMidService '{self._service_id}': Task {task['id']} needs more processing. Requeuing... \n")
                    
                    await self.rest.post("QueueHeadService/requeue", task=task)
                    
            else:
                # The queue is currently empty. Sleep briefly to prevent hammering the server.
                self.logger.info(f"=====\n ElabMidService '{self._service_id}': Queue is empty. Waiting... \n")
                await asyncio.sleep(1.0)
        else:
            self.logger.warning(f"=====\n ElabMidService '{self._service_id}': Failed to pull. HTTP Code: {pull_response.status_code} \n")
            await asyncio.sleep(1.0)