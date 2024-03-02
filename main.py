import sys
import os
from src.pipeline import Pipeline

def run_pipeline(pipeline):
    for source_file in pipeline.get_sources():
        executable_filename = os.path.splitext(source_file)[0]
        pipeline.compile(source_file, executable_filename)
        pipeline.disassemble(executable_filename)


if __name__ == '__main__':
    pipeline = Pipeline("data")
    # Check if any command-line arguments were provided
    if len(sys.argv) > 1:
        # If the first argument is 'clean', run the clean function
        if sys.argv[1] == 'clean':
            pipeline.clean()
        else:
            print(f'Error: Unknown argument {sys.argv[1]}')
    else:
        # If no arguments were provided, run the run_pipeline function
        run_pipeline(pipeline)
