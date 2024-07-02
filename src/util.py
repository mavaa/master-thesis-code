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

def codebleu_create_graph(pkl_file_path, png_file_path, show_plot=False):
    data = pd.read_pickle(pkl_file_path)

    df = pd.DataFrame(data)
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'Category'})

    codebleu_row = df[df['Category'] == 'codebleu']
    df = df[df['Category'] != 'codebleu']
    df = pd.concat([df, codebleu_row], ignore_index=True)

    def transform_label(label):
        if label != 'codebleu':
            label = label.replace('_match_score', '')
            label = label.replace('_', ' ')
            label = label.title()
        return label

    df['Category'] = df['Category'].apply(transform_label)

    plt.figure(figsize=(10, 6))

    for column in df.columns[1:]:
        line, = plt.plot(df['Category'][:-1], df[column][:-1], marker='o', label=column, linestyle='-')
        plt.plot(df['Category'][-2:], df[column][-2:], marker='o', linestyle='--', color=line.get_color())
        plt.scatter(df['Category'].iloc[-1], df[column].iloc[-1], color=line.get_color(), s=100, edgecolor='black', zorder=5)

    plt.title('CodeBLEU performance')
    plt.ylabel('Scores')

    ax = plt.gca()
    xticks = range(len(df['Category']))
    xticklabels = list(df['Category'])

    if xticklabels:
        xticklabels[-1] = "CodeBLEU"
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        ax.get_xticklabels()[-1].set_fontweight('bold')

    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{int(y * 100)}%'))
    ax.yaxis.set_major_locator(MultipleLocator(0.05))

    plt.legend()
    plt.grid(True)
    plt.savefig(png_file_path)

    if show_plot:
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
