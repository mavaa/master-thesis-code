from codebleu import calc_codebleu
import openai
import os
import shutil
import subprocess
import sys

# Globals
test_program_folder="data/sources"

def compile_and_disassemble(folder_path, name):
    build_dir = 'build/'
    build_dir_relative = os.path.join(folder_path, build_dir)
    if not os.path.exists(build_dir_relative):
        os.makedirs(build_dir_relative)

    # Compile the code
    subprocess.run(['gcc', '-o', f'{build_dir}{name}', f'{name}.c'], check=True, cwd=folder_path)

    # Create disassembly file
    # Note to self: Running `r2 -qc pd @.main main` doesn't work, since only 'pd' will be passed to r2
    # as command. Have to use `r2 -qc "pd @.main" main`.
    subprocess.run(
            ['r2', '-qc', f'pd @.{name}', f'{build_dir}{name}'],
            stdout=open(f'{build_dir_relative}/{name}_disassembly.txt', 'w'), check=True, cwd=folder_path)

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

def clean(test_program_folder):
    clean_path=f'{test_program_folder}/build'
    if os.path.isdir(clean_path):
        shutil.rmtree(clean_path)

if __name__ == '__main__':
    # Check if any command-line arguments were provided
    if len(sys.argv) > 1:
        # If the first argument is 'clean', run the clean function
        if sys.argv[1] == 'clean':
            clean(test_program_folder)
        else:
            print(f'Error: Unknown argument {sys.argv[1]}')
    else:
        # If no arguments were provided, run the run_pipeline function
        run_pipeline(test_program_folder)
