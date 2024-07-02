from openai import OpenAI
from ..util import read_whole_file

class OpenAIModelPredictor:
    def __init__(self, api_key, model, temperature, base_prompt):
        self.client = OpenAI(
            api_key=api_key
        )
        self.model = model
        self.temperature = temperature
        self.base_prompt = base_prompt
        self.name = f"OpenAI-{model}"

    def generate_prediction(self, binary_path, disassembly_path):
        disassembly = read_whole_file(disassembly_path)
        prompt = f"{self.base_prompt}\n{disassembly}"
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
        response = chat_completion.choices[0].message.content.replace("```", "")

        lines = response.split('\n')
        if lines and lines[0].strip().lower() == "c":
            lines = lines[1:]

        response = "\n".join(lines)

        return response
