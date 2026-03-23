def get_synth_string(originalPrompt, *agentAnswers):
    num_agents = len(agentAnswers)
    
    agents_lines = "\n".join([f"| Agent {i+1} says: {answer}" for i, answer in enumerate(agentAnswers)])
    
    prompt = f"""You are an expert evaluator. You are given a multiple-choice question and the proposed
answers from {num_agents} different AI agents. Your task is to analyze their answers, find the consensus or the most
logical answer, and output ONLY the final correct letter (A, B, C, or D).
Question: {originalPrompt}
{agents_lines}
Final Answer:"""

    return prompt