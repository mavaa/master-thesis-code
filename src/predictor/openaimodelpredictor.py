from openai import OpenAI

class OpenAIModelPredictor:
    def __init__(self, api_key, model, temperature, base_prompt):
        self.client = OpenAI(
            api_key=api_key
        )
        self.model = model
        self.temperature = temperature
        self.base_prompt = base_prompt

    def generate_prediction(self, binary_path, disassembly_code):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{self.base_prompt}\n{disassembly_code}",
                }
            ],
            model=self.model,
            temperature=self.temperature
        )
        return chat_completion
