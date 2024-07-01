import os
import shutil
import subprocess
from .util import create_folder_if_not_exists, read_whole_file

class Pipeline:
    def __init__(
            self,
            compiler,
            disassembler,
            predictors,
            evaluator,
            data_path="data"):
        self.compiler = compiler
        self.disassembler = disassembler
        self.predictors = predictors
        self.evaluator = evaluator
        self.data_path = data_path

        self.sources_path = os.path.join(data_path, "sources")
        self.builds_path = os.path.join(data_path, "builds")
        self.disassemblies_path = os.path.join(data_path, "disassemblies")
        self.predictions_path = os.path.join(data_path, "predictions")
        self.references_file_path = os.path.join(data_path, "references.txt")

    def init_folders(self):
        create_folder_if_not_exists(self.builds_path)
        create_folder_if_not_exists(self.disassemblies_path)
        create_folder_if_not_exists(self.predictions_path)

    def get_sources(self):
        return sorted(os.listdir(self.sources_path))

    def compile(self, source, output):
        self.compiler.compile(
                os.path.join(self.sources_path, source),
                os.path.join(self.builds_path, output))

    def disassemble(self, executable):
        self.disassembler.disassemble(
            os.path.join(self.builds_path, executable),
            os.path.join(self.disassemblies_path, f'{executable}_d.txt'))

    def add_source_to_dataset(self, source):
        source_path = os.path.join(self.sources_path, source)

        with open(source_path, 'r') as file:
            source_code = self.put_code_on_single_line(file)
        with open(self.references_file_path, 'a') as file:
            file.write(source_code + '\n')

    def generate_prediction(self, executable, predictor):
        build_path = os.path.join(self.builds_path, executable)
        disassembly_path = os.path.join(self.disassemblies_path, f'{executable}_d.txt')

        prediction = predictor.generate_prediction(build_path, disassembly_path)

        prediction_file_path = os.path.join(self.predictions_path, f'{predictor.name}_{executable}.c')
        with open(prediction_file_path, 'w') as file:
            file.write(prediction)

        combined_predictions_file_path = os.path.join(self.predictions_path, f'{predictor.name}_all.txt')
        with open(combined_predictions_file_path, 'a') as file:
            file.write(self.put_code_on_single_line(prediction.split('\n')) + '\n')

        return prediction

    def generate_and_save_predictions(self, executable):
        for predictor in self.predictors:
            self.generate_prediction(executable, predictor)

    def put_code_on_single_line(self, input_file):
        return ' '.join([line.strip() for line in input_file if line.strip()])

    def evaluate(self):
        reference_code = read_whole_file(self.references_file_path)
        results = {}

        for predictor in self.predictors:
            combined_predictions_file_path = os.path.join(self.predictions_path, f'{predictor.name}_all.txt')
            prediction_code = read_whole_file(combined_predictions_file_path)
            results[predictor.name] = self.evaluator.evaluate(reference_code, prediction_code)

        return results

    def clean(self):
        if os.path.isdir(self.builds_path):
            shutil.rmtree(self.builds_path)
        if os.path.isdir(self.disassemblies_path):
            shutil.rmtree(self.disassemblies_path)
        if os.path.isdir(self.predictions_path):
            shutil.rmtree(self.predictions_path)
        if os.path.exists(self.references_file_path):
            os.remove(self.references_file_path)
