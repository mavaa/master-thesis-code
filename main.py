import sys
import os
import argparse
from src.pipeline import Pipeline
from src.openaimodel import OpenAIModel
import pickle
from tabulate import tabulate

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
        with open(os.path.join(pipeline.data_path, 'sources', source_file)) as file:
            print(file.read())
        print()
        print("Prediction:")
        print(prediction)
        print()
        input()

# Run predictions and evaluate
def run_pipeline_evaluate(pipeline, results_filename):
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

    results = {
        'LLM': result_llm,
        'R2': result_r2
    }

    # Save results to a file
    with open(os.path.join(pipeline.data_path, results_filename), 'wb') as f:
        pickle.dump(results, f)

    # Print results in a table format for LaTeX
    headers = ["Metric", "LLM Score", "R2 Score"]
    table_data = []
    for key in result_llm.keys():
        table_data.append([key, result_llm[key], result_r2[key]])

    print("\nLaTeX Table:")
    print(tabulate(table_data, headers, tablefmt="latex"))

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
    return executable_filename

def create_new_pipeline(path, model_name):
    model = OpenAIModel(os.environ.get("OPENAI_API_KEY"), model_name, 0)
    return Pipeline(model, path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run pipeline commands.')
    parser.add_argument('-d', '--data-dir', type=str, default='data', help='Data directory')
    parser.add_argument('-r', '--results', type=str, default='results.pkl', help='Results filename')
    parser.add_argument('-m', '--model', type=str, default='gpt-3.5-turbo', help='Model name')
    parser.add_argument('command', choices=['clean', 'prepare', 'print', 'evaluate'], help='Command to execute')

    args = parser.parse_args()

    pipeline = create_new_pipeline(args.data_dir, args.model)

    if args.command == 'clean':
        pipeline.clean()
    elif args.command == 'prepare':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_prepare(pipeline)
    elif args.command == 'print':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_print(pipeline)
    elif args.command == 'evaluate':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_evaluate(pipeline, args.results)
    else:
        print(f'Error: Unknown command {args.command}')
