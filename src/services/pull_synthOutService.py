import os
import signal
import time
import re
from ollama import AsyncClient
from eclypse.remote.service import RESTService
from eclypse.remote.communication import rest

class SynthOutService(RESTService):
    """
    SynthOutService collects fully elaborated tasks, synthesizes a final character 
    answer (A, B, C, or D), calculates metrics, and triggers simulation shutdown.
    """
    
    selected_topic = "abstract_algebra"
    selected_model = 'qwen2.5:1.5b'

    elab_into_char_configuration = {
        'model': selected_model,
        'options': {
            'temperature': 0.1, 
            'num_predict': 5, 
            'stop': ["\n", "Question:", "Answer:"] 
        }
    }

    def __init__(self, service_id, store_step: bool = False, *args, **kwargs):
        super().__init__(
            service_id,
            *args,
            **kwargs
        )
        self.topic = self.selected_topic
        
        # State and Metrics Tracking
        self.received_count = 0
        self.correct_count = 0
        self.total_expected = None
        
        self.global_start_time = None
        self.total_e2e_latency = 0.0

    @staticmethod
    def get_char_prompt(elaborations):
        """
        Creates the prompt instructing the model to synthesize the multiple string
        elaborations into a single letter.
        """
        num_agents = len(elaborations)
        agents_lines = "\n".join([f"| Agent {i+1} says: {answer}" for i, answer in enumerate(elaborations)])
        
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
        """
        Calls the Ollama model to generate the final character output.
        """
        response = await AsyncClient().chat(
            model=SynthOutService.elab_into_char_configuration['model'],
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': original_prompt}
            ],
            options=SynthOutService.elab_into_char_configuration['options']
        )

        raw_res = response['message']['content'].strip().upper()

        if len(raw_res) > 0:
            match = re.search(r'[ABCD]', raw_res)
            return match.group(0) if match else ""
        return ""

    def _print_final_results_and_terminate(self, elapsed_time):
        """
        Logs the final benchmark metrics and sends a SIGINT to stop the simulation.
        """
        self.logger.info(f"=====\n SynthOutService ID: {self._service_id} ======== RESULTS ========. \n")
        
        avg_e2e_latency = self.total_e2e_latency / self.total_expected
        final_throughput = self.total_expected / elapsed_time
        accuracy = (self.correct_count / self.total_expected) * 100
        
        self.logger.info(f"FINAL METRICS | Avg E2E Latency: {avg_e2e_latency:.2f}s | Global Throughput: {final_throughput:.2f} msg/s")
        self.logger.info(f"Final Accuracy: {accuracy:.2f}% ({self.correct_count}/{self.total_expected})")
        
        try:
            with open('.main_pid.txt', 'r') as file_pid:
                main_pid = int(file_pid.read().strip())
                self.logger.info(f"=====\n SynthOutService ID: {self._service_id} sent SIGINT to main PID: {main_pid} to end simulation.\n")
                os.kill(main_pid, signal.SIGINT)
        except Exception as err:
            self.logger.error(f"=====\n SynthOutService ID: {self._service_id} error sending SIGINT to main PID: {main_pid}. {err}\n")

    # ==========================================
    # REST ENDPOINTS
    # ==========================================

    @rest.endpoint("/synthesize", method="POST")
    async def synthesize(self, task, **kwargs):
        """
        Endpoint: POST SynthOutService/synthesize
        Called by ElabMidService when a task reaches its max elaborations.
        """
        if self.global_start_time is None:
            self.global_start_time = time.time()
            self.logger.info(f"=====\n SynthOutService ID: {self._service_id} started. Global timer initiated.\n")

        if self.total_expected is None:
            self.total_expected = task.get("total_expected")
            self.logger.info(f"=====\n SynthOutService ID: {self._service_id} total expected messages set to {self.total_expected}. \n")

        msg_id = task.get('id')
        self.logger.info(f"=====\n SynthOutService ID: {self._service_id} received message {msg_id} for synthesis... \n")

        # Process character synthesis
        char_system_prompt = self.get_char_prompt(task.get("elaborations", []))
        elaborated_char = await self.elab_into_char(char_system_prompt, task["originalPrompt"])
        task["predictedAnswer"] = elaborated_char

        # Check correctness
        actual = task["expectedAnswer"]
        self.logger.info(f"=====\n SynthOutService: (Actual: {actual}, Predicted: {elaborated_char})")
        if elaborated_char == actual:
            self.correct_count += 1

        # Calculate metrics
        current_time = time.time()
        
        # E2E Latency on single message
        prompt_start_time = task.get("start_time", current_time)
        e2e_latency = current_time - prompt_start_time
        self.total_e2e_latency += e2e_latency
        
        self.received_count += 1
        
        # Throughput
        elapsed_time = max(current_time - self.global_start_time, 0.001)
        current_throughput = self.received_count / elapsed_time

        self.logger.info(f"=====\n LIVE METRICS | Msg ID: {msg_id} | E2E Latency: {e2e_latency:.2f}s | Current Throughput: {current_throughput:.2f} msg/s \n")

        # End of simulation check
        if self.total_expected and self.received_count >= self.total_expected:
            self._print_final_results_and_terminate(elapsed_time)

        return 200, {"status": "OK", "predictedAnswer": elaborated_char}