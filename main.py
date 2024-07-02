import sys
import os
import argparse
import pickle
import subprocess
from codebleu import calc_codebleu
from src.compiler.gcccompiler import GCCCompiler
from src.disassembler.objdumpdisassembler import ObjdumpDisassembler
from src.disassembler.r2disassembler import R2Disassembler
from src.predictor.r2decompilepredictor import R2DecompilePredictor
from src.evaluator.codebleuevaluator import CodeBleuEvaluator
from src.predictor.openaimodelpredictor import OpenAIModelPredictor
from src.pipeline import Pipeline
from src.r2runner import R2Runner
from src.util import create_folder_if_not_exists, codebleu_create_graph, codebleu_create_latex_table

default_llm_prompt="""
**Prompt:**

Below is a snippet of assembly code. Please reconstruct the original C code as accurately as possible and provide only the code block without any explanations or additional text.

**Assembly Code:**
```
{disassembly}
```

**Reconstructed C Code:**
```c

"""

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

def run_pipeline_evaluate(pipeline, args, eval_path):
    for source_file in pipeline.get_sources():
        executable_filename = compile_disassemble_reference(pipeline, source_file)
        print("Generating predictions...")
        pipeline.generate_and_save_predictions(executable_filename, status_callback=print_prediction_status)
        print()

    evaluate(pipeline, args, eval_path)

def print_prediction_status(status, predictor_name):
    if status == 0:
        print(f"Generating for {predictor_name}...", end='', flush=True)
    else:
        print(" Done!")

def evaluate(pipeline, args, eval_path):
    print("Evaluating...")
    results = pipeline.evaluate()
    print("Results:")
    for key, score in results.items():
        print("==")
        print(key)
        for score_key, score_value in score.items():
            print(f"{score_key}: {score_value:.2%}")
        print("==")

    # Save results to a file
    with open(os.path.join(eval_path, args.results_pkl), 'wb') as f:
        pickle.dump(results, f)

    # Define headers for the LaTeX table
    headers = ["Metric"] + list(results.keys())

    codebleu_create_latex_table(
        os.path.join(eval_path, args.results_latex),
        results.values(),
        results.keys(),
        headers)

    codebleu_create_graph(
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
    print("Adding to reference dataset...")
    pipeline.add_source_to_dataset(source_file)
    return executable_filename

def determine_dataset_size(sources_path):
    if sources_path == 'data/sources':
        return 'small'
    else:
        return 'large'

def determine_models_used(models):
    if len(models) > 1:
        return 'multiple'
    else:
        return models[0]

def determine_strip(strip):
    return 'strip' if strip else 'nostrip'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run pipeline commands.')
    parser.add_argument('-b', '--base-prompt', type=str, default=default_llm_prompt, help='Base prompt to send to LLMs. Use `{disassembly}` in the string where you want to place the disassembled code.')
    parser.add_argument('-d', '--data-path', type=str, default='data', help='Data directory')
    parser.add_argument('-a', '--auto-data-path', action='store_true', help='Generate the data path automatically from flags')
    parser.add_argument('-i', '--sources-path', type=str, default='data/sources', help='Source code directory')
    parser.add_argument('-r', '--results-pkl', type=str, default='results.pkl', help='Results filename')
    parser.add_argument('-l', '--results-latex', type=str, default='table.tex', help='Results latex table filename')
    parser.add_argument('-p', '--plot-filename', type=str, default='plot.png', help='Plot graph filename')
    parser.add_argument('-m', '--models', type=str, nargs='+', default=['gpt-3.5-turbo'], help='List of model names')
    parser.add_argument('-s', '--strip', action='store_true', help='Strip the binary during compilation')
    parser.add_argument('-x', '--disassembler', choices=['objdump', 'r2'], default='r2', help='Disassembler to run')
    parser.add_argument('command', choices=['clean', 'prepare', 'print', 'full-run', 'evaluate'], default='full-run', help='Command to execute')

    args = parser.parse_args()

    data_path = args.data_path

    # This is pretty specific for generating output folders to be used for the thesis report
    if args.auto_data_path:
        dataset_size = determine_dataset_size(args.sources_path)
        models_used = determine_models_used(args.models)
        strip_status = determine_strip(args.strip)

        data_path = f"data_{dataset_size}_{models_used}_{strip_status}_{args.disassembler}/"
        print(f"Auto data path set to: {data_path}")

    eval_path = os.path.join(data_path, 'evaluation')

    create_folder_if_not_exists(eval_path)

    r2_runner = R2Runner(subprocess)

    predictors = [
        OpenAIModelPredictor(os.environ.get("OPENAI_API_KEY"), model, 0, args.base_prompt)
        for model in args.models
        ] + [R2DecompilePredictor(r2_runner)]

    compiler = GCCCompiler(subprocess, args.strip)

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
            compiler=compiler,
            disassembler=disassembler,
            predictors=predictors,
            evaluator=evaluator,
            sources_path=args.sources_path,
            data_path=data_path)

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
        evaluate(pipeline, args, eval_path)
    elif args.command == 'full-run':
        pipeline.clean()
        pipeline.init_folders()
        run_pipeline_evaluate(pipeline, args, eval_path)
    else:
        print(f'Error: Unknown command {args.command}')
