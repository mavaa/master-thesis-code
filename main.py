import sys
import os
from src.pipeline import Pipeline
from src.openaimodel import OpenAIModel

def run_pipeline_print(pipeline):
    for source_file in pipeline.get_sources():
        print("==============")
        print(f"File: {source_file}")
        print("==============")
        executable_filename = os.path.splitext(source_file)[0]
        print("Compiling...")
        pipeline.compile(source_file, executable_filename)
        print("Creating disassembly...")
        pipeline.disassemble(executable_filename)
        print("Adding to reference dataset...")
        pipeline.add_source_to_dataset(source_file)
        print("Generating prediction...")
        prediction = pipeline.generate_prediction(executable_filename)
        print()
        print("Original code:")
        with open(os.path.join('data/sources', source_file)) as file:
            print(file.read())
        print()
        print("Prediction:")
        print(prediction)
        print()
        input()

def run_pipeline_save(pipeline):
    for source_file in pipeline.get_sources():
        print("==============")
        print(f"File: {source_file}")
        print("==============")
        executable_filename = os.path.splitext(source_file)[0]
        print("Compiling...")
        pipeline.compile(source_file, executable_filename)
        print("Creating disassembly...")
        pipeline.disassemble(executable_filename)
        print("Adding to reference dataset...")
        pipeline.add_source_to_dataset(source_file)
        print("Generating prediction...")
        prediction = pipeline.generate_and_save_prediction(executable_filename)
        print()

if __name__ == '__main__':
    pipeline = Pipeline(OpenAIModel(os.environ.get("OPENAI_API_KEY")), "data")
    # Check if any command-line arguments were provided
    if len(sys.argv) > 1:
        # If the first argument is 'clean', run the clean function
        if sys.argv[1] == 'clean':
            pipeline.clean()
        elif sys.argv[1] == 'print':
            run_pipeline_print(pipeline)
        elif sys.argv[1] == 'save':
            run_pipeline_save(pipeline)
        else:
            print(f'Error: Unknown argument {sys.argv[1]}')
    else:
        print(f'Error: expected \'clean\', \'print\' or \'save\' argument')
