from codebleu import calc_codebleu
import openai
import os
import shutil
import subprocess
from .util import create_folder_if_not_exists

build_folder = "data/builds"

def compile(source, output):
    create_folder_if_not_exists(os.path.dirname(output))

    subprocess.run(['gcc', '-o', output, source], check=True)

def disassemble(executable, output_folder):
    create_folder_if_not_exists(output_folder)

    basename = os.path.basename(executable)

    # Note to self: Running `r2 -qc pd @.main main` doesn't work,
    # since only 'pd' will be passed to r2 as command.
    # Have to use `r2 -qc "pd @.main" main`.
    subprocess.run(
            ['r2', '-qc', f'pd @.{basename}', f'{executable}'],
            stdout=open(f'{output_folder}/{basename}_d.txt', 'w'), check=True)

def prepare_dataset(source_file_path, references_file_path):
    with open(source_file_path, 'r') as file:
        source_code = file.read().replace('\n', ' ')
    with open(references_file_path, 'w') as file:
        file.write(source_code)

def generate_prediction(disassembly):
    openai.api_key = 'your_api_key_here'
    response = openai.Completion.create(
      engine="code-davinci-002",
      prompt=f"Reconstruct the original C source code from the following disassembly:\n{disassembly}",
      temperature=0.5,
      max_tokens=150
    )
    return response.choices[0].text.strip()

def save_prediction():
    with open('disassembly.txt', 'r') as file:
        disassembly = file.read()
    prediction = generate_prediction(disassembly)
    with open('predictions.txt', 'w') as file:
        file.write(prediction.replace('\n', ' '))


def read_code_from_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    return code

def evaluate():
    # Read reference and prediction from their respective files

    reference_code = read_code_from_file(reference_file_path)
    prediction_code = read_code_from_file(prediction_file_path)

    result = calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)
    print(result)

def run_pipeline(test_program_folder):
    test_program="main"
    references_file_path = "references.txt"
    prediction_file_path = "predictions.txt"

    compile_and_disassemble(test_program_folder, test_program)
    prepare_dataset(
            os.path.join(test_program_folder, f"{test_program}.c"),
            references_file_path)

def clean():
    if os.path.isdir(build_folder):
        shutil.rmtree(build_folder)

