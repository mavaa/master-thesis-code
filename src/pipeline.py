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
        self.r2d_path = os.path.join(data_path, "r2_decompile")
        self.llmd_path = os.path.join(data_path, "llm_decompile")
        self.references_file_path = os.path.join(data_path, "references.txt")
        self.r2_predictions_file_path = os.path.join(data_path, "r2_predictions.txt")
        self.llm_predictions_file_path = os.path.join(data_path, "llm_predictions.txt")
        self.prediction_model = prediction_model

    def init_folders(self):
        create_folder_if_not_exists(self.builds_path)
        create_folder_if_not_exists(self.disassemblies_path)
        create_folder_if_not_exists(self.r2d_path)
        create_folder_if_not_exists(self.llmd_path)

    def get_sources(self):
        return sorted(os.listdir(self.sources_path))

    def compile(self, source, output, strip=False):
        output_path = os.path.join(self.builds_path, output)
        source_path = os.path.join(self.sources_path, source)
        subprocess.run(['gcc', '-c', '-o', output_path, source_path], check=True)

        if strip:
            subprocess.run(["strip", output_path], check=True)

    def disassemble(self, executable):
        output_path = os.path.join(self.disassemblies_path, f'{executable}_d.txt')
        executable_path = os.path.join(self.builds_path, executable)

        # Note to self: Running `radare2 -qc pd @ main main` doesn't work,
        # since only 'pd' will be passed to radare2 as command.
        # Have to use `radare2 -qc "pd @ main" main`.
        # TODO: Test this with 'pd @ main', 'pd @.main' and just 'pd'
        # TODO: Should look into the warnings that are supressed by the DEVNULL stderr
        subprocess.run(["objdump", "-d", executable_path],
                       stdout=open(output_path, 'w'), check=True)

    def r2_decompile(self, executable):
        output_path = os.path.join(self.r2d_path, f'{executable}.txt')
        self.r2_run('aaa;s main;pdg', executable, output_path)

        with open(output_path, 'r') as output_file:
            source_code = self.put_code_on_single_line(output_file)
        with open(self.r2_predictions_file_path, 'a') as pred_file:
            pred_file.write(source_code + '\n')

    def r2_run(self, command, executable, output_path):
        executable_path = os.path.join(self.builds_path, executable)

        subprocess.run(
                ['radare2', '-qc', command, executable_path],
                stdout=open(output_path, 'w'), check=True, stderr=subprocess.DEVNULL)

    def add_source_to_dataset(self, source):
        source_path = os.path.join(self.sources_path, source)

        with open(source_path, 'r') as file:
            source_code = self.put_code_on_single_line(file)
        with open(self.references_file_path, 'a') as file:
            file.write(source_code + '\n')

    def generate_prediction(self, executable):
        disassembly_path = os.path.join(self.disassemblies_path, f'{executable}_d.txt')
        with open(disassembly_path, 'r') as file:
            prompt=f"Reconstruct the original C source code from the following disassembly:\n{file.read()}"

        prediction = self.prediction_model.generate_prediction(prompt)
        return prediction.choices[0].message.content

    def generate_and_save_prediction(self, executable):
        prediction = self.generate_prediction(executable).replace("```", "")

        lines = prediction.split('\n')
        if lines and lines[0].strip().lower() == "c":
            lines = lines[1:]

        prediction = "\n".join(lines)

        with open(self.llm_predictions_file_path, 'a') as file:
            file.write(self.put_code_on_single_line(prediction.split('\n')) + '\n')

        decompile_path = os.path.join(self.llmd_path, f'{executable}.c')
        with open(decompile_path, 'w') as d_file:
            d_file.write(prediction)

    def read_code_from_file(self, file_path):
        with open(file_path, 'r') as file:
            code = file.read()
        return code

    def put_code_on_single_line(self, input_file):
        return ' '.join([line.strip() for line in input_file if line.strip()])

    def evaluate_llm(self):
        # Read reference and prediction from their respective files

        reference_code = self.read_code_from_file(self.references_file_path)
        prediction_code = self.read_code_from_file(self.llm_predictions_file_path)

        return calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)

    def evaluate_r2(self):
        # Read reference and prediction from their respective files

        reference_code = self.read_code_from_file(self.references_file_path)
        prediction_code = self.read_code_from_file(self.r2_predictions_file_path)

        return calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)

    def clean(self):
        if os.path.isdir(self.builds_path):
            shutil.rmtree(self.builds_path)
        if os.path.isdir(self.disassemblies_path):
            shutil.rmtree(self.disassemblies_path)
        if os.path.isdir(self.r2d_path):
            shutil.rmtree(self.r2d_path)
        if os.path.isdir(self.llmd_path):
            shutil.rmtree(self.llmd_path)
        if os.path.exists(self.references_file_path):
            os.remove(self.references_file_path)
        if os.path.exists(self.llm_predictions_file_path):
            os.remove(self.llm_predictions_file_path)
        if os.path.exists(self.r2_predictions_file_path):
            os.remove(self.r2_predictions_file_path)
