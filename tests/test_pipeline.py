import pytest
import os
import magic
import re
from src.pipeline import Pipeline
from src.util import create_folder_if_not_exists
from shutil import copyfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock

executable_filename = "helloworld"
source_filename = f"{executable_filename}.c"
r2_decompile_filename = f"r2d_{executable_filename}.txt"
mock_prediction = "Mocked prediction"

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

@pytest.fixture
def setup_pipeline(tmp_path):
    # Setup data folders and copy main.c
    data_path = os.path.join(tmp_path, "data")
    create_folder_if_not_exists(data_path)

    sources_path = os.path.join(data_path, "sources")
    create_folder_if_not_exists(sources_path)

    copyfile(os.path.join("data/sources/", source_filename),
             os.path.join(sources_path, source_filename))

    pipeline = Pipeline(Mock_Model("testkey", "test-model", 0.5), data_path)
    pipeline.init_folders()

    yield pipeline

def test_get_sources(setup_pipeline):
    sources = setup_pipeline.get_sources()
    assert sources == [source_filename], "The sources array does not contain the expected file"

def test_compile(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    executable_path = os.path.join(setup_pipeline.data_path, "builds", executable_filename)

    # Check if the executable exists
    assert os.path.exists(executable_path), f"Executable {executable_path} was not created"

    # Check if the file is an object file
    file_type = magic.from_file(executable_path)
    assert str_contains_word(file_type, 'ELF') and str_contains_word(file_type, 'relocatable'), f"File {executable_path} is not a valid object file. Detected type: {file_type}"

def test_disassemble(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.disassemble(executable_filename)

    disassembly_file = os.path.join(setup_pipeline.disassemblies_path, f'{executable_filename}_d.txt')
    assert os.path.exists(disassembly_file), f"Disassembly file ({disassembly_file}) does not exist after pipeline execution."

def test_disassemble_calls_r2_func(setup_pipeline):
    setup_pipeline.r2_run = MagicMock()

    setup_pipeline.disassemble(executable_filename)

    setup_pipeline.r2_run.assert_called_once()

def test_r2_run(setup_pipeline):
    r2_out_path = os.path.join(setup_pipeline.data_path, "r2_out.txt")
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.r2_run('pd', executable_filename, r2_out_path)

    assert os.path.exists(r2_out_path), f"r2 output file ({r2_out_path}) does not exist after r2 execution."

def test_decompile_r2(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.r2_decompile(executable_filename)

    decompiled_file = os.path.join(setup_pipeline.r2d_path, f'{executable_filename}.txt')
    assert os.path.exists(decompiled_file), f"Decompiled file ({decompiled_file}) does not exist."

def test_add_source_to_dataset(setup_pipeline):
    setup_pipeline.add_source_to_dataset(source_filename)

    assert os.path.exists(setup_pipeline.references_file_path), "Reference file does not exist after pipeline execution."

    with open(setup_pipeline.references_file_path, 'r') as file:
        reference_file_content  = file.read()

    assert reference_file_content == '#include <stdio.h> int print_hello() { printf("Hello, World!\\n"); return 0; }\n'

def test_generate_prediction(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.disassemble(executable_filename)
    prediction = setup_pipeline.generate_prediction(executable_filename)

    assert prediction == mock_prediction, f'Unexpected prediction: {prediction}'

def test_generate_and_save_prediction(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.disassemble(executable_filename)
    setup_pipeline.generate_and_save_prediction(executable_filename)

    assert os.path.exists(setup_pipeline.llm_predictions_file_path), "Predictions file does not exist."

    with open(setup_pipeline.llm_predictions_file_path, 'r') as file:
        prediction_file_content  = file.read()

    assert prediction_file_content == mock_prediction + '\n'

@pytest.mark.parametrize("source,expected", [
    (["hey", "there", "you"], "hey there you"),
    (["quick", "brown", "", "fox"], "quick brown fox"),
    (["hey", "  you", "there  "], "hey you there")
])
def test_put_code_on_single_line(source, expected, setup_pipeline):
    result = setup_pipeline.put_code_on_single_line(source)
    assert result == expected

def test_evaluate_llm(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.disassemble(executable_filename)
    setup_pipeline.generate_and_save_prediction(executable_filename)
    setup_pipeline.add_source_to_dataset(source_filename)
    result = setup_pipeline.evaluate_llm()

    assert isinstance(result['codebleu'], (int, float)), "Value is not a number"
    assert isinstance(result['ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['weighted_ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['syntax_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['dataflow_match_score'], (int, float)), "Value is not a number"

def test_evaluate_r2(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    setup_pipeline.r2_decompile(executable_filename)
    setup_pipeline.add_source_to_dataset(source_filename)
    result = setup_pipeline.evaluate_r2()

    assert isinstance(result['codebleu'], (int, float)), "Value is not a number"
    assert isinstance(result['ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['weighted_ngram_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['syntax_match_score'], (int, float)), "Value is not a number"
    assert isinstance(result['dataflow_match_score'], (int, float)), "Value is not a number"

def test_clean_function(setup_pipeline):
    Path(setup_pipeline.references_file_path).touch()
    Path(setup_pipeline.llm_predictions_file_path).touch()
    Path(setup_pipeline.r2_predictions_file_path).touch()
    assert os.path.exists(setup_pipeline.builds_path), "Build directory does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.disassemblies_path), "Disassemblies directory does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.references_file_path), "Reference file does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.llm_predictions_file_path), "LLM predictions file does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.r2_predictions_file_path), "R2 predictions file does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.r2d_path), "r2 decompilation directory does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.llmd_path), "llm decompilation directory does not exist before clean function execution."

    setup_pipeline.clean()
    assert not os.path.exists(setup_pipeline.builds_path), "Build directory exists after clean function execution."
    assert not os.path.exists(setup_pipeline.disassemblies_path), "Disassemblies directory exists after clean function execution."
    assert not os.path.exists(setup_pipeline.references_file_path), "Reference file exists after clean function execution."
    assert not os.path.exists(setup_pipeline.llm_predictions_file_path), "Predictions file exists after clean function execution."
    assert not os.path.exists(setup_pipeline.r2_predictions_file_path), "R2 predictions file exists after clean function execution."
    assert not os.path.exists(setup_pipeline.r2d_path), "r2 decompilation directory exists after clean function execution."
    assert not os.path.exists(setup_pipeline.llmd_path), "llm decompilation directory exists after clean function execution."

def str_contains_word(string, word):
    return re.search(r'\b' + word + r'\b', string) is not None
