from openai import OpenAI

class OpenAIModel:
    def __init__(self, api_key, model, temperature):
        self.client = OpenAI(
            api_key=api_key
        )
        self.model = model
        self.temperature = temperature

    def generate_prediction(self, prompt):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.model,
            temperature=self.temperature
        )
        return chat_completion
