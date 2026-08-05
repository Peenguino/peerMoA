import time
from collections import deque
from datasets import load_dataset
from eclypse.remote.service import Service
from eclypse.remote.service import RESTService
from eclypse.remote.communication import rest
from src.utils.messageDictUtils import get_message_dict_template_pull

class QueueHeadService(RESTService):
    """
    QueueHeadService acts as the central task manager in the Pull Architecture.
    It progressively loads dataset entries to maintain a fixed queue size,
    preventing Out of Memory (OOM) issues.
    """
    
    selected_topic = "abstract_algebra"

    # Where a partially elaborated task is re-inserted by /requeue:
    # - "head": priority to work in progress, so a task finishes its layer sooner.
    #           A co-located worker can immediately re-pull what it just requeued,
    #           which starves the remote ones in a distributed deployment.
    # - "tail": the task goes behind the queue, breaking that self-feeding loop
    #           at the cost of more work in progress (and so higher E2E latency).
    REQUEUE_POLICIES = ("head", "tail")

    def __init__(self, service_id, requeue_policy: str = "head", store_step: bool = False, *args, **kwargs):
        super().__init__(
            service_id,
            *args,
            **kwargs
        )
        if requeue_policy not in self.REQUEUE_POLICIES:
            raise ValueError(
                f"Unknown requeue_policy '{requeue_policy}'. Expected one of {self.REQUEUE_POLICIES}."
            )
        self.requeue_policy = requeue_policy
        self.topic = self.selected_topic
        self.dataset_test = None
        
        # Internal queue
        self.task_queue = deque()
        self.dataset_loaded = False
        
        # Buffer state
        self.current_idx = 0
        # Equivalent to max_in_flight from the old architecture: defining fixed dimension on queue  
        self.target_queue_size = 25

    def on_deploy(self):
        """
        Method called on start of a RESTService.
        """
        self.logger.info(f"=====\n QueueHeadService '{self._service_id}': loading dataset... \n")
        self.logger.info(f"=====\n QueueHeadService: topic '{self.topic}' | requeue policy '{self.requeue_policy}' \n")
        self.dataset_test = load_dataset("cais/mmlu", self.topic, split="test")
        self.dataset_loaded = True
        
        # Adding messages into queue until target_queue_size reaching
        while len(self.task_queue) < self.target_queue_size and self.current_idx < len(self.dataset_test):
            self._replenish_one()
            
        self.logger.info(f"=====\n Dataset loaded. Initial queue populated with {len(self.task_queue)} tasks.\n")

    def _replenish_one(self):
        """
        Extracting and inserting one entry from dataset to queue.
        """
        item = self.dataset_test[self.current_idx]
        messageDict = get_message_dict_template_pull()
        
        prompt = f"Question: {item['question']}\n"
        for choice_idx, choice in enumerate(['A', 'B', 'C', 'D']):
            prompt += f"{choice}. {item['choices'][choice_idx]}\n"
        prompt += "Answer: "

        messageDict.update({
            "id": self.current_idx,
            "expectedAnswer": ['A', 'B', 'C', 'D'][item["answer"]],
            "originalPrompt": prompt,
            "total_expected": len(self.dataset_test)
        })
        
        self.task_queue.append(messageDict)
        self.current_idx += 1

    # ==========================================
    # REST ENDPOINTS
    # ==========================================

    @rest.endpoint("/pull", method="GET")
    async def pull(self, **kwargs):
        """
        Endpoint: GET QueueHeadService/pull
        Called by ElabMidService to request a task.
        """
        if len(self.task_queue) > 0:
            # Pop from the HEAD of the queue
            task = self.task_queue.popleft() 
            
            # Start E2E latency timer on the first pull assignment
            if task["start_time"] == 0.0:
                task["start_time"] = time.time()
                
            self.logger.info(f"=====\n Task ID {task['id']} pulled by worker. Remaining in queue: {len(self.task_queue)}\n")

            if len(self.task_queue) < self.target_queue_size and self.current_idx < len(self.dataset_test):
                self._replenish_one()

            return 200, {"status": "OK", "task": task}
        else:
            return 200, {"status": "EMPTY"}

    @rest.endpoint("/requeue", method="POST")
    async def requeue(self, task, **kwargs):
        """
        Endpoint: POST QueueHeadService/requeue
        Called by ElabMidService to re-insert a task with count < 3.
        """
        if self.requeue_policy == "head":
            # Priority to partially processed tasks so they finish faster.
            self.task_queue.appendleft(task)
        else:
            self.task_queue.append(task)
        self.logger.info(f"=====\n Task ID {task['id']} requeued (count: {task['count']}). Queue size: {len(self.task_queue)}\n")
        return 200, {"status": "OK"}