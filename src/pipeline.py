import openai
import os
import shutil
import subprocess
from codebleu import calc_codebleu
from .util import create_folder_if_not_exists

class CodePipeline:
    def __init__(self, build_folder="data/builds", openai_api_key='your_api_key_here'):
        self.build_folder = build_folder
        self.openai_api_key = openai_api_key

    def compile(self, source, output):
        create_folder_if_not_exists(os.path.dirname(output))

        subprocess.run(['gcc', '-o', output, source], check=True)

    def disassemble(self, executable, output_folder):
        create_folder_if_not_exists(output_folder)

        basename = os.path.basename(executable)

        # Note to self: Running `r2 -qc pd @.main main` doesn't work,
        # since only 'pd' will be passed to r2 as command.
        # Have to use `r2 -qc "pd @.main" main`.
        subprocess.run(
                ['r2', '-qc', f'pd @.{basename}', f'{executable}'],
                stdout=open(f'{output_folder}/{basename}_d.txt', 'w'), check=True)

    def prepare_dataset(self, source_file_path, references_file_path):
        with open(source_file_path, 'r') as file:
            source_code = file.read().replace('\n', ' ')
        with open(references_file_path, 'w') as file:
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

    def run_pipeline(self):
        test_program="main"
        references_file_path = "references.txt"
        prediction_file_path = "predictions.txt"

        self.compile_and_disassemble(test_program_folder, test_program)
        self.prepare_dataset(
                os.path.join(test_program_folder, f"{test_program}.c"),
                references_file_path)

    def clean(self):
        if os.path.isdir(self.build_folder):
            shutil.rmtree(self.build_folder)

