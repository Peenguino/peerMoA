from ollama import AsyncClient

class ElabClassUtils():

    elab_configuration = {
        'model': 'qwen2.5:1.5b',
        'options': {
                'temperature': 0, 
                'num_predict': 5, 
                'stop': ["\n", "Question:", "Answer:"] 
            }
    }

    async def elab(self, prompt):
        response = await AsyncClient().generate(
            **ElabClassUtils.elab_configuration,
            prompt=prompt
        )
        raw_res = response['response'].strip().upper()

        if len(raw_res) > 0:
            return raw_res[0]
        else:
            return ""