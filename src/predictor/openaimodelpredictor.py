from openai import OpenAI

class OpenAIModelPredictor:
    def __init__(self, api_key, model, temperature, base_prompt):
        self.client = OpenAI(
            api_key=api_key
        )
        self.model = model
        self.temperature = temperature
        self.base_prompt = base_prompt
        self.name = f"OpenAI-{model}"

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
        response = chat_completion.choices[0].message.content.replace("```", "")

        lines = response.split('\n')
        if lines and lines[0].strip().lower() == "c":
            lines = lines[1:]

        response = "\n".join(lines)

        return response
