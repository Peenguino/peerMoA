from datasets import *

class BenchmarkUtils():

    # === Using Few-Shot prefix approach
    # = It helps the agent to setup the format of the answer, using it in the prompt
    @staticmethod
    def create_few_shot_prefix(dev_data, n_shots=5):
        prefix = "Instruction: Answer the following multiple choice questions by giving only the letter (A, B, C, or D) of the correct answer.\n\n"
        for i in range(n_shots):
            current_entry = dev_data[i]
            prefix += f"Question: {current_entry['question']}\n"

            # = Iterate on the tuple (key, value) = (index, choice)
            for idx, choice in enumerate(['A', 'B', 'C', 'D']):
                prefix += f"{choice}. {current_entry['choices'][idx]}\n"

            prefix += f"Answer: {['A', 'B', 'C', 'D'][current_entry['answer']]}\n\n"
        return prefix

    @staticmethod
    def startBenchmark(agent_target, dataset_test: Dataset, dataset_dev: Dataset | None = None):
        if(dataset_dev is not None):
            prefix = BenchmarkUtils.create_few_shot_prefix(dataset_dev)
        else:
            prefix = ""

        correct_count = 0
        print(f"Start test on {len(dataset_test)} questions...")

        for item in dataset_test:
            prompt = prefix + f"Question: {item['question']}\n"
            for idx, choice in enumerate(['A', 'B', 'C', 'D']):
                prompt += f"{choice}. {item['choices'][idx]}\n"
            prompt += "Answer: "

            prediction = agent_target.elab(prompt)

            actual = ['A', 'B', 'C', 'D'][item['answer']]
        
            print(f"Predicted {prediction}, answer was {actual}")

            if prediction == actual:
                correct_count += 1
        
        # === Final score
        accuracy = (correct_count / len(dataset_test)) * 100
        print(f"\n--- Results ---")
        print(f"Accuracy: {accuracy:.2f}% ({correct_count}/{len(dataset_test)})")