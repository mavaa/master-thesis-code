import sys
import os
from src.pipeline import compile, disassemble, clean

# Globals
sources_folder="data/sources"
builds_folder = "data/builds"
disassemlies_folder = "data/disassemblies"

def run_pipeline():
    for source_file in os.listdir(sources_folder):
        executable_path = os.path.join(builds_folder, os.path.splitext(source_file)[0])
        compile(os.path.join(sources_folder, source_file), executable_path)
        disassemble(executable_path, disassemlies_folder)


if __name__ == '__main__':
    # Check if any command-line arguments were provided
    if len(sys.argv) > 1:
        # If the first argument is 'clean', run the clean function
        if sys.argv[1] == 'clean':
            clean()
        else:
            print(f'Error: Unknown argument {sys.argv[1]}')
    else:
        # If no arguments were provided, run the run_pipeline function
        run_pipeline()
