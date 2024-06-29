import os
import pickle
from codebleu import calc_codebleu
from src.util import read_whole_file, codebleu_create_graph, codebleu_create_latex_table

if __name__ == '__main__':
    base_path = "data_codebleu_examples"
    reference_file = os.path.join(base_path, "reference.txt")
    eval_path = "evaluation_results"
    os.makedirs(eval_path, exist_ok=True)

    reference_code = read_whole_file(reference_file)
    results = []
    results_dict = {}

    for i in range(4):
        filename = f'src{i+1}.txt'
        prediction_code = read_whole_file(os.path.join(base_path, filename))
        bleu = calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)

        results.append(bleu)
        results_dict[f'src{i+1}'] = bleu

    # Save results to a file
    results_pkl = os.path.join(eval_path, "results.pkl")
    with open(results_pkl, 'wb') as f:
        pickle.dump(results_dict, f)

    # Define headers for the LaTeX table
    headers = ["Metric"] + [f"src{i+1}" for i in range(4)]

    # Call the generic function to create and save the LaTeX table
    results_latex = os.path.join(eval_path, "results_fourcases.tex")
    codebleu_create_latex_table(
            results_latex,
            results,
            [f"src{i+1}" for i in range(4)],
            headers)

    # Call the function to create a graph from the results
    plot_filename = os.path.join(eval_path, "results_plot.png")
    codebleu_create_graph(results_pkl, plot_filename)
