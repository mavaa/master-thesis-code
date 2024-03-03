from openai import OpenAI

class OpenAIModel:
    def __init__(self, api_key='your_api_key_here'):
        self.client = OpenAI(
            api_key=api_key
        )

    def generate_prediction(self, model, prompt, temperature):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=temperature
        )
        return chat_completion
