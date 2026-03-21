from ollama import AsyncClient

class ElabClassUtils():

    async def elab(self, prompt):
        response = await AsyncClient().generate(
            model='qwen2.5:1.5b',
            prompt=prompt,
            options={
                'temperature': 0, 
                'num_predict': 5, 
                'stop': ["\n", "Question:", "Answer:"] 
            }
        )
        raw_res = response['response'].strip().upper()

        if len(raw_res) > 0:
            return raw_res[0]
        else:
            return ""