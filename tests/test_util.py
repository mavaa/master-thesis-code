import os
import pytest
import pandas as pd
import pickle
from unittest.mock import patch
from src.util import create_folder_if_not_exists, read_whole_file, codebleu_create_graph, codebleu_create_latex_table

def test_create_folder_if_not_exists(tmp_path):
    test_folder = tmp_path / "test_folder"
    create_folder_if_not_exists(test_folder)
    assert test_folder.exists()
    assert test_folder.is_dir()

def test_read_whole_file(tmp_path):
    test_file = tmp_path / "test_file.txt"
    test_content = "Hello, world!"
    test_file.write_text(test_content)
    read_content = read_whole_file(test_file)
    assert read_content == test_content

def test_codebleu_create_graph(tmp_path):
    # Create sample data and save it as a pickle file
    data = {
        'LLM': {'Metric1': 0.9, 'Metric2': 0.85, 'Metric3': 0.88},
        'R2': {'Metric1': 0.92, 'Metric2': 0.87, 'Metric3': 0.89}
    }
    pkl_file_path = tmp_path / "results.pkl"
    with open(pkl_file_path, 'wb') as f:
        pickle.dump(data, f)

    png_file_path = tmp_path / "results.png"

    # Use patch to mock plt.show() during the test
    with patch("matplotlib.pyplot.show"):
        codebleu_create_graph(pkl_file_path, png_file_path)

    assert png_file_path.exists()
    assert png_file_path.is_file()

def test_codebleu_create_latex_table(tmp_path):
    eval_path = tmp_path
    results = [
        {'Metric1': 0.9, 'Metric2': 0.85, 'Metric3': 0.88},
        {'Metric1': 0.92, 'Metric2': 0.87, 'Metric3': 0.89}
    ]
    result_keys = ['LLM', 'R2']
    headers = ["Metric"] + result_keys
    filename = "results.tex"
    latex_file_path = eval_path / filename

    codebleu_create_latex_table(latex_file_path, results, result_keys, headers)

    assert latex_file_path.exists()
    assert latex_file_path.is_file()

    with open(latex_file_path, 'r') as f:
        latex_content = f.read()
        assert "Metric" in latex_content
        assert "LLM" in latex_content
        assert "R2" in latex_content
