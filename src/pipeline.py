import openai
import os
import shutil
import subprocess
from codebleu import calc_codebleu
from .util import create_folder_if_not_exists

class Pipeline:
    def __init__(self, data_path="data/builds", openai_api_key='your_api_key_here'):
        self.data_path = data_path
        self.sources_path = os.path.join(data_path, "sources")
        self.builds_path = os.path.join(data_path, "builds")
        self.disassemblies_path = os.path.join(data_path, "disassemblies")
        self.references_file_path = os.path.join(data_path, "references.txt")
        self.openai_api_key = openai_api_key

        create_folder_if_not_exists(self.builds_path)
        create_folder_if_not_exists(self.disassemblies_path)

    def get_sources(self):
        return os.listdir(self.sources_path)

    def compile(self, source, output):
        output_path = os.path.join(self.builds_path, output)
        source_path = os.path.join(self.sources_path, source)
        subprocess.run(['gcc', '-o', output_path, source_path], check=True)

    def disassemble(self, executable):
        executable_path = os.path.join(self.builds_path, executable)
        output_path = os.path.join(self.disassemblies_path, f'{executable}_d.txt')

        # Note to self: Running `radare2 -qc pd @.main main` doesn't work,
        # since only 'pd' will be passed to radare2 as command.
        # Have to use `radare2 -qc "pd @.main" main`.
        subprocess.run(
                ['radare2', '-qc', f'pd @.{executable}', f'{executable_path}'],
                stdout=open(output_path, 'w'), check=True)

    def add_source_to_dataset(self, source):
        source_path = os.path.join(self.sources_path, source)

        with open(source_path, 'r') as file:
            source_code = ' '.join([line.strip() for line in file if line.strip()])
        with open(self.references_file_path, 'w') as file:
            file.write(source_code)

    def generate_prediction(self, disassembly):
        openai.api_key = self.openai_api_key
        response = openai.Completion.create(
          engine="code-davinci-002",
          prompt=f"Reconstruct the original C source code from the following disassembly:\n{disassembly}",
          temperature=0.5,
          max_tokens=150
        )
        return response.choices[0].text.strip()

    def save_prediction(self):
        with open('disassembly.txt', 'r') as file:
            disassembly = file.read()
        prediction = self.generate_prediction(disassembly)
        with open('predictions.txt', 'w') as file:
            file.write(prediction.replace('\n', ' '))

    def read_code_from_file(self, file_path):
        with open(file_path, 'r') as file:
            code = file.read()
        return code

    def evaluate(self):
        # Read reference and prediction from their respective files

        reference_code = self.read_code_from_file(reference_file_path)
        prediction_code = self.read_code_from_file(prediction_file_path)

        result = calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)
        print(result)

    def clean(self):
        if os.path.isdir(self.builds_path):
            shutil.rmtree(self.builds_path)
        if os.path.isdir(self.disassemblies_path):
            shutil.rmtree(self.disassemblies_path)

