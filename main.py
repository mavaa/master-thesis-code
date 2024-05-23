import sys
import os
from src.pipeline import Pipeline
from src.openaimodel import OpenAIModel

def run_pipeline_prepare(pipeline):
    for source_file in pipeline.get_sources():
        compile_disassemble_reference(pipeline, source_file)

def run_pipeline_print(pipeline):
    for source_file in pipeline.get_sources():
        executable_filename = compile_disassemble_reference(pipeline, source_file)

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

# Run predictions and evaluate
def run_pipeline_evaluate(pipeline):
    for source_file in pipeline.get_sources():
        executable_filename = compile_disassemble_reference(pipeline, source_file)
        print("Generating prediction...")
        pipeline.generate_and_save_prediction(executable_filename)
        print()

    print("Evaluating LLM...")
    result_llm = pipeline.evaluate_llm()
    print("Results:")
    for key, value in result_llm.items():
        print(f"{key}: {value}")

    print()
    print("Evaluating R2...")
    result_r2 = pipeline.evaluate_r2()
    print("Results:")
    for key, value in result_r2.items():
        print(f"{key}: {value}")

def compile_disassemble_reference(pipeline, source_file):
    print("==============")
    print(f"File: {source_file}")
    print("==============")
    executable_filename = os.path.splitext(source_file)[0]
    print("Compiling...")
    pipeline.compile(source_file, executable_filename)
    print("Creating disassembly...")
    pipeline.disassemble(executable_filename)
    print("Creating r2 decompiled files")
    pipeline.r2_decompile(executable_filename)
    print("Adding to reference dataset...")
    pipeline.add_source_to_dataset(source_file)
    return executable_filename;

def create_new_pipeline(path):
    model_name = "gpt-3.5-turbo"
    # model_name = "gpt-4"
    model = OpenAIModel(os.environ.get("OPENAI_API_KEY"), model_name, 0)
    return Pipeline(model, path)


if __name__ == '__main__':
    # Check if any command-line arguments were provided
    if len(sys.argv) > 2:
        pipeline = create_new_pipeline(sys.argv[2])
        # If the first argument is 'clean', run the clean function
        if sys.argv[1] == 'clean':
            pipeline.clean()
        elif sys.argv[1] == 'prepare':
            pipeline.clean()
            pipeline.init_folders()
            run_pipeline_prepare(pipeline)
        elif sys.argv[1] == 'print':
            pipeline.clean()
            pipeline.init_folders()
            run_pipeline_print(pipeline)
        elif sys.argv[1] == 'evaluate':
            pipeline.clean()
            pipeline.init_folders()
            run_pipeline_evaluate(pipeline)
        else:
            print(f'Error: Unknown argument {sys.argv[1]}')
    else:
        print(f'Error: expected \'clean\', \'print\' or \'evaluate\' argument and data path')
