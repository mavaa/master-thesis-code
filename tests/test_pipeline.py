import pytest
import os
import magic
import re
import subprocess
from src.pipeline import Pipeline
from src.r2runner import R2Runner
from src.util import create_folder_if_not_exists
from shutil import copyfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

executable_filename = "helloworld"
source_filename = f"{executable_filename}.c"
r2_decompile_filename = f"r2d_{executable_filename}.txt"
mock_prediction = """```c
Mocked prediction
```"""
mock_prediction_expected_result = "Mocked prediction"

class Mock_Model:
    def __init__(self, api_key, model, temperature):
        self.api_key = api_key

    def generate_prediction(self, prompt):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=mock_prediction
                    )
                )
            ]
        )

def setup_pipeline(tmp_path, r2_runner):
    if r2_runner is None:
        r2_runner = R2Runner(subprocess)

    # Setup data folders and copy main.c
    data_path = os.path.join(tmp_path, "data")
    create_folder_if_not_exists(data_path)

    sources_path = os.path.join(data_path, "sources")
    create_folder_if_not_exists(sources_path)

    copyfile(os.path.join("data/sources/", source_filename),
             os.path.join(sources_path, source_filename))

    pipeline = Pipeline(
            Mock_Model("testkey", "test-model", 0.5),
            r2_runner,
            data_path)
    pipeline.init_folders()

    return pipeline

@pytest.fixture
def pipeline_factory(tmp_path):
    def create_pipeline(r2_runner=None):
        return setup_pipeline(tmp_path, r2_runner)
    return create_pipeline

def test_get_sources(pipeline_factory):
    sources = pipeline_factory().get_sources()
    assert sources == [source_filename], "The sources array does not contain the expected file"

@pytest.mark.parametrize("stripped", [True, False])
def test_compile(pipeline_factory, stripped):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename, stripped)
    executable_path = os.path.join(pipeline.data_path, "builds", executable_filename)

    # Check if the executable exists
    assert os.path.exists(executable_path), f"Executable {executable_path} was not created"

    # Check if the file is an object file
    file_type = magic.from_file(executable_path)
    assert str_contains_word(file_type, 'ELF') and str_contains_word(file_type, 'relocatable'), f"File {executable_path} is not a valid object file. Detected type: {file_type}"

    # Check if the compiled file was stripped according to parameter
    was_stripped = is_stripped(file_type)
    assert was_stripped == stripped, f"Strip parameter was not respected, expected {stripped}, but was {was_stripped}"

def test_disassemble(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)

    disassembly_file = os.path.join(pipeline.disassemblies_path, f'{executable_filename}_d.txt')
    assert os.path.exists(disassembly_file), f"Disassembly file ({disassembly_file}) does not exist after pipeline execution."

def test_disassemble_with_real_r2(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)

    disassembly_file = os.path.join(pipeline.disassemblies_path, f'{executable_filename}_d.txt')
    assert os.path.exists(disassembly_file), f"Disassembly file ({disassembly_file}) does not exist after pipeline execution."

def test_disassemble_calls_r2_func(pipeline_factory):
    mock_r2_runner = MagicMock()
    pipeline = pipeline_factory(mock_r2_runner)
    output_path = os.path.join(pipeline.disassemblies_path, f'{executable_filename}_d.txt')

    pipeline.disassemble(executable_filename)

    mock_r2_runner.run.assert_called_once_with(
            'pd',
            os.path.join(pipeline.builds_path, executable_filename),
            output_path)

def test_r2_run(pipeline_factory):
    pipeline = pipeline_factory()
    r2_out_path = os.path.join(pipeline.data_path, "r2_out.txt")
    pipeline.compile(source_filename, executable_filename)
    pipeline.r2_run('pd', executable_filename, r2_out_path)

    assert os.path.exists(r2_out_path), f"r2 output file ({r2_out_path}) does not exist after r2 execution."

def test_r2_decompile(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.r2_decompile(executable_filename)

    decompiled_file = os.path.join(pipeline.r2d_path, f'{executable_filename}.txt')
    assert os.path.exists(decompiled_file), f"Decompiled file ({decompiled_file}) does not exist."

def test_r2_decompile_calls_r2_func(pipeline_factory):
    mock_r2_runner = MagicMock()
    pipeline = pipeline_factory(mock_r2_runner)
    output_path = os.path.join(pipeline.r2d_path, f'{executable_filename}.txt')

    with patch("builtins.open", mock_open()) as mock_file:
        pipeline.r2_decompile(executable_filename)

    mock_r2_runner.run.assert_called_once_with(
            'aaa;pdg',
            os.path.join(pipeline.builds_path, executable_filename),
            output_path)

def test_add_source_to_dataset(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.add_source_to_dataset(source_filename)

    assert os.path.exists(pipeline.references_file_path), "Reference file does not exist after pipeline execution."

    with open(pipeline.references_file_path, 'r') as file:
        reference_file_content  = file.read()

    assert reference_file_content == '#include <stdio.h> int print_hello() { printf("Hello, World!\\n"); return 0; }\n'

def test_generate_prediction(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    prediction = pipeline.generate_prediction(executable_filename)

    assert prediction == mock_prediction, f'Unexpected prediction: {prediction}'

def test_generate_and_save_prediction(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    pipeline.generate_and_save_prediction(executable_filename)

    assert os.path.exists(pipeline.llm_predictions_file_path), "Predictions file does not exist."

    with open(pipeline.llm_predictions_file_path, 'r') as file:
        prediction_file_content  = file.read()

    assert prediction_file_content == mock_prediction_expected_result + '\n'

@pytest.mark.parametrize("source,expected", [
    (["hey", "there", "you"], "hey there you"),
    (["quick", "brown", "", "fox"], "quick brown fox"),
    (["hey", "  you", "there  "], "hey you there")
])
def test_put_code_on_single_line(pipeline_factory, source, expected):
    pipeline = pipeline_factory()
    result = pipeline.put_code_on_single_line(source)
    assert result == expected

def test_evaluate_llm(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    pipeline.generate_and_save_prediction(executable_filename)
    pipeline.add_source_to_dataset(source_filename)
    result = pipeline.evaluate_llm()

    assert isinstance(result['codebleu'], (int, float)), "Value is not a number"
    assert isinstance(result['ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['weighted_ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['syntax_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['dataflow_match_score'], (int, float)), "Value is not a number"

def test_evaluate_r2(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.r2_decompile(executable_filename)
    pipeline.add_source_to_dataset(source_filename)
    result = pipeline.evaluate_r2()

    assert isinstance(result['codebleu'], (int, float)), "Value is not a number"
    assert isinstance(result['ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['weighted_ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['syntax_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['dataflow_match_score'], (int, float)), "Value is not a number"

def test_clean_function(pipeline_factory):
    pipeline = pipeline_factory()
    Path(pipeline.references_file_path).touch()
    Path(pipeline.llm_predictions_file_path).touch()
    Path(pipeline.r2_predictions_file_path).touch()
    assert os.path.exists(pipeline.builds_path), "Build directory does not exist before clean function execution."
    assert os.path.exists(pipeline.disassemblies_path), "Disassemblies directory does not exist before clean function execution."
    assert os.path.exists(pipeline.references_file_path), "Reference file does not exist before clean function execution."
    assert os.path.exists(pipeline.llm_predictions_file_path), "LLM predictions file does not exist before clean function execution."
    assert os.path.exists(pipeline.r2_predictions_file_path), "R2 predictions file does not exist before clean function execution."
    assert os.path.exists(pipeline.r2d_path), "r2 decompilation directory does not exist before clean function execution."
    assert os.path.exists(pipeline.llmd_path), "llm decompilation directory does not exist before clean function execution."

    pipeline.clean()
    assert not os.path.exists(pipeline.builds_path), "Build directory exists after clean function execution."
    assert not os.path.exists(pipeline.disassemblies_path), "Disassemblies directory exists after clean function execution."
    assert not os.path.exists(pipeline.references_file_path), "Reference file exists after clean function execution."
    assert not os.path.exists(pipeline.llm_predictions_file_path), "Predictions file exists after clean function execution."
    assert not os.path.exists(pipeline.r2_predictions_file_path), "R2 predictions file exists after clean function execution."
    assert not os.path.exists(pipeline.r2d_path), "r2 decompilation directory exists after clean function execution."
    assert not os.path.exists(pipeline.llmd_path), "llm decompilation directory exists after clean function execution."

def str_contains_word(string, word):
    return re.search(r'\b' + word + r'\b', string) is not None

def is_stripped(file_type):
    return "not stripped" not in file_type and str_contains_word(file_type, "stripped")
