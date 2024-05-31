import sys
import os
import argparse
import pickle
import subprocess
from src.compiler.gcccompiler import GCCCompiler
from src.disassembler.objdumpdisassembler import ObjdumpDisassembler
from src.disassembler.r2disassembler import R2Disassembler
from src.decompiler.r2ghidradecompiler import R2GdhidraDecompiler
from src.openaimodel import OpenAIModel
from src.pipeline import Pipeline
from src.r2runner import R2Runner
from tabulate import tabulate

def run_pipeline_prepare(pipeline, args):
    for source_file in pipeline.get_sources():
        compile_disassemble_reference(pipeline, source_file)

def run_pipeline_print(pipeline, args):
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
def run_pipeline_evaluate(pipeline, args):
    for source_file in pipeline.get_sources():
        executable_filename = compile_disassemble_reference(pipeline, source_file)
        print("Generating prediction...")
        pipeline.generate_and_save_prediction(executable_filename)
        print()

    print("Evaluating LLM...")
    result_llm = pipeline.evaluate_llm()
    print("Results:")
    for key, value in result_llm.items():
        print(f"{key}: {value:.2%}")

    print()
    print("Evaluating R2...")
    result_r2 = pipeline.evaluate_r2()
    print("Results:")
    for key, value in result_r2.items():
        print(f"{key}: {value:.2%}")

    results = {
        'LLM': result_llm,
        'R2': result_r2
    }

    # Save results to a file
    with open(os.path.join(pipeline.data_path, args.results), 'wb') as f:
        pickle.dump(results, f)

    # Print results in a table format for LaTeX
    headers = ["Metric", "LLM Score", "R2 Score"]
    table_data = []
    for key in result_llm.keys():
        table_data.append([key, f"{result_llm[key]:.2%}", f"{result_r2[key]:.2%}"])

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
    pipeline.decompile(executable_filename)
    print("Adding to reference dataset...")
    pipeline.add_source_to_dataset(source_file)
    return executable_filename

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run pipeline commands.')
    parser.add_argument('-d', '--data-path', type=str, default='data', help='Data directory')
    parser.add_argument('-r', '--results', type=str, default='results.pkl', help='Results filename')
    parser.add_argument('-m', '--model', type=str, default='gpt-3.5-turbo', help='Model name')
    parser.add_argument('-s', '--strip', action='store_true', help='Strip the binary during compilation')
    parser.add_argument('-x', '--disassembler', choices=['objdump', 'r2'], default='r2', help='Disassembler to run')
    parser.add_argument('command', choices=['clean', 'prepare', 'print', 'evaluate'], help='Command to execute')

    args = parser.parse_args()

    model = OpenAIModel(os.environ.get("OPENAI_API_KEY"), args.model, 0)

    compiler = GCCCompiler(subprocess, args.strip)

    r2_runner = R2Runner(subprocess)

    decompiler = R2GdhidraDecompiler(r2_runner)

    disassembler = None

    if args.disassembler == 'objdump':
        disassembler = ObjdumpDisassembler(subprocess)
    elif args.disassembler == 'r2':
        disassembler = R2Disassembler(r2_runner)
    else:
        print(f'Error: Unknown disassembler {args.disassembler}')
        sys.exit(1)

    pipeline = Pipeline(
            prediction_model=model,
            compiler = compiler,
            decompiler = decompiler,
            disassembler=disassembler,
            data_path=args.data_path)

    if args.command == 'clean':
        pipeline.clean()
    elif args.command == 'prepare':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_prepare(pipeline, args)
    elif args.command == 'print':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_print(pipeline, args)
    elif args.command == 'evaluate':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_evaluate(pipeline, args)
    else:
        print(f'Error: Unknown command {args.command}')
