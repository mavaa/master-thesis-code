import os
import shutil
import subprocess
from codebleu import calc_codebleu
from .util import create_folder_if_not_exists

class Pipeline:
    def __init__(self, prediction_model, data_path="data/builds"):
        self.data_path = data_path
        self.sources_path = os.path.join(data_path, "sources")
        self.builds_path = os.path.join(data_path, "builds")
        self.disassemblies_path = os.path.join(data_path, "disassemblies")
        self.references_file_path = os.path.join(data_path, "references.txt")
        self.predictions_file_path = os.path.join(data_path, "predictions.txt")
        self.prediction_model = prediction_model

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

        # Note to self: Running `radare2 -qc pd @ main main` doesn't work,
        # since only 'pd' will be passed to radare2 as command.
        # Have to use `radare2 -qc "pd @ main" main`.
        # TODO: Test this with 'pd @ main', 'pd @.main' and just 'pd'
        subprocess.run(
                ['radare2', '-qc', f'pd', f'{executable_path}'],
                stdout=open(output_path, 'w'), check=True)

    def add_source_to_dataset(self, source):
        source_path = os.path.join(self.sources_path, source)

        with open(source_path, 'r') as file:
            source_code = self.put_code_on_single_line(file)
        with open(self.references_file_path, 'w') as file:
            file.write(source_code)

    def generate_prediction(self, executable):
        disassembly_path = os.path.join(self.disassemblies_path, f'{executable}_d.txt')
        with open(disassembly_path, 'r') as file:
            prompt=f"Reconstruct the original C source code from the following disassembly:\n{file.read()}"

        #prediction = self.prediction_model.generate_prediction("gpt-4", prompt, 0)
        prediction = self.prediction_model.generate_prediction("gpt-3.5-turbo", prompt, 0)
        return prediction.choices[0].message.content

    def generate_and_save_prediction(self, executable):
        prediction = self.generate_prediction(executable)
        with open(self.predictions_file_path, 'w') as file:
            file.write(prediction.replace('\n', ' '))

    def read_code_from_file(self, file_path):
        with open(file_path, 'r') as file:
            code = file.read()
        return code

    def put_code_on_single_line(self, input_file):
        return ' '.join([line.strip() for line in input_file if line.strip()])

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

