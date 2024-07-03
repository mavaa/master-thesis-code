import pandas as pd
from pathlib import Path

def get_max_codebleu_score(path):
    data = pd.read_pickle(Path("out") / path / "evaluation/results.pkl")
    df = pd.DataFrame(data)

    if 'codebleu' in df.index:
        max_codebleu = df.loc['codebleu'].max()
        model_with_max_codebleu = df.loc['codebleu'].idxmax()
        return max_codebleu, model_with_max_codebleu
    else:
        print(f"'codebleu' index not found in the DataFrame for folder: {path}")
        return None, None

def best_score(paths):
    scores = []

    for path in paths:
        max_codebleu, model_with_max_codebleu = get_max_codebleu_score(path)
        if max_codebleu is not None:
            scores.append((path, model_with_max_codebleu, max_codebleu))

    scores.sort(key=lambda x: x[2], reverse=True)

    for path, model, score in scores:
        print(f"{path}: {model} - {score * 100:.2f}%")

    print()

paths_large = [
    "data_large_multiple_nostrip_objdump",
    "data_large_multiple_nostrip_r2",
    "data_large_multiple_strip_objdump",
    "data_large_multiple_strip_r2",
]

paths_small = [
    "data_small_multiple_nostrip_objdump",
    "data_small_multiple_nostrip_r2",
    "data_small_multiple_strip_objdump",
    "data_small_multiple_strip_r2"
]

print("Large datasets:")
best_score(paths_large)

print("Small datasets:")
best_score(paths_small)
