import sys
import os
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import subprocess
from codebleu import calc_codebleu
from src.compiler.gcccompiler import GCCCompiler
from src.disassembler.objdumpdisassembler import ObjdumpDisassembler
from src.disassembler.r2disassembler import R2Disassembler
from src.decompiler.r2ghidradecompiler import R2GdhidraDecompiler
from src.evaluator.codebleuevaluator import CodeBleuEvaluator
from src.openaimodel import OpenAIModel
from src.pipeline import Pipeline
from src.r2runner import R2Runner
from src.util import create_folder_if_not_exists
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
def run_pipeline_evaluate(pipeline, args, eval_path):
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
    with open(os.path.join(eval_path, args.results_pkl), 'wb') as f:
        pickle.dump(results, f)

    # Print results in a table format for LaTeX
    headers = ["Metric", "LLM Score", "R2 Score"]
    table_data = []
    for key in result_llm.keys():
        table_data.append([key, f"{result_llm[key]:.2%}", f"{result_r2[key]:.2%}"])

    # Save results to a file
    with open(os.path.join(eval_path, args.results_latex), 'w') as f:
        f.write(tabulate(table_data, headers, tablefmt="latex"))

    create_graph(
            os.path.join(eval_path, args.results_pkl),
            os.path.join(eval_path, args.plot_filename))

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

def create_graph(pkl_file_path, png_file_path):
    # Load the data from the pickle file
    data = pd.read_pickle(pkl_file_path)

    # Transform the dictionary into a dataframe for plotting
    df = pd.DataFrame(data)

    # Resetting index for easier plotting
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'Category'})

    # Plotting
    plt.figure(figsize=(10, 6))

    # Plot each algorithm's scores
    for column in df.columns[1:]:  # Skipping the first column which is 'Category'
        plt.plot(df['Category'], df[column], marker='o', label=column)

    # Add titles and labels
    plt.title('Algorithm Performance Across Categories')
    plt.xlabel('Categories')
    plt.ylabel('Scores')

    # Add a legend
    plt.legend()

    # Add grid
    plt.grid(True)

    # Save the plot to a file
    plt.savefig(png_file_path)

    # Show the plot
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run pipeline commands.')
    parser.add_argument('-d', '--data-path', type=str, default='data', help='Data directory')
    parser.add_argument('-r', '--results-pkl', type=str, default='results.pkl', help='Results filename')
    parser.add_argument('-l', '--results-latex', type=str, default='table.tex', help='Results latex table filename')
    parser.add_argument('-p', '--plot-filename', type=str, default='plot.png', help='Plot graph filename')
    parser.add_argument('-m', '--model', type=str, default='gpt-3.5-turbo', help='Model name')
    parser.add_argument('-s', '--strip', action='store_true', help='Strip the binary during compilation')
    parser.add_argument('-x', '--disassembler', choices=['objdump', 'r2'], default='r2', help='Disassembler to run')
    parser.add_argument('command', choices=['clean', 'prepare', 'print', 'evaluate'], help='Command to execute')

    args = parser.parse_args()

    eval_path = os.path.join(args.data_path, 'evaluation')

    create_folder_if_not_exists(eval_path)

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

    evaluator = CodeBleuEvaluator(calc_codebleu)

    pipeline = Pipeline(
            prediction_model=model,
            compiler = compiler,
            decompiler = decompiler,
            disassembler=disassembler,
            evaluator=evaluator,
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
        run_pipeline_evaluate(pipeline, args, eval_path)
    else:
        print(f'Error: Unknown command {args.command}')
