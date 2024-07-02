import matplotlib.pyplot as plt
import os
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator
from tabulate import tabulate

def create_folder_if_not_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def read_whole_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    return code

def codebleu_create_graph(pkl_file_path, png_file_path):
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
    plt.title('CodeBLEU performance')
    plt.xlabel('Categories')
    plt.ylabel('Scores')

    ax = plt.gca()
    xticks = ax.get_xticks()
    xticklabels = ax.get_xticklabels()

    if xticklabels:
        xticklabels = [label.get_text() for label in xticklabels]
        xticklabels[0] = "CodeBLEU"
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        ax.get_xticklabels()[0].set_fontweight('bold')

    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{int(y * 100)}%'))
    ax.yaxis.set_major_locator(MultipleLocator(0.05))

    # Add a legend
    plt.legend()

    # Add grid
    plt.grid(True)

    # Save the plot to a file
    plt.savefig(png_file_path)

    # Show the plot
    plt.show()

def codebleu_create_latex_table(tex_file, results, result_keys, headers):
    table_data = []

    all_keys = set().union(*(result.keys() for result in results))

    for key in all_keys:
        row = [key]
        for result in results:
            if key in result:
                row.append(f"{result[key]:.2%}")
        table_data.append(row)

    with open(tex_file, 'w') as f:
        f.write(tabulate(table_data, headers, tablefmt="latex"))
