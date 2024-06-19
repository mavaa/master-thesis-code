import pytest
import os
import magic
import re
import subprocess
from src.pipeline import Pipeline
from src.r2runner import R2Runner
from src.decompiler.r2ghidradecompiler import R2GdhidraDecompiler
from src.disassembler.objdumpdisassembler import ObjdumpDisassembler
from src.compiler.gcccompiler import GCCCompiler
from src.util import create_folder_if_not_exists, read_whole_file
from shutil import copyfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

executable_filename = "helloworld"
source_filename = f"{executable_filename}.c"
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

def setup_pipeline(tmp_path, compiler, decompiler, disassembler, evaluator):
    if compiler is None:
        compiler = GCCCompiler(subprocess)

    if decompiler is None:
        decompiler = R2GdhidraDecompiler(R2Runner(subprocess))

    if disassembler is None:
        disassembler = ObjdumpDisassembler(subprocess)

    if evaluator is None:
        evaluator = MagicMock()

    # Setup data folders and copy main.c
    data_path = os.path.join(tmp_path, "data")
    create_folder_if_not_exists(data_path)

    sources_path = os.path.join(data_path, "sources")
    create_folder_if_not_exists(sources_path)

    copyfile(os.path.join("data/sources/", source_filename),
             os.path.join(sources_path, source_filename))

    pipeline = Pipeline(
            prediction_model=Mock_Model("testkey", "test-model", 0.5),
            compiler=compiler,
            decompiler=decompiler,
            disassembler=disassembler,
            evaluator=evaluator,
            data_path=data_path)
    pipeline.init_folders()

    return pipeline

@pytest.fixture
def pipeline_factory(tmp_path):
    def create_pipeline(compiler=None, decompiler=None, disassembler=None, evaluator=None):
        return setup_pipeline(tmp_path, compiler, decompiler, disassembler, evaluator)
    return create_pipeline

def test_get_sources(pipeline_factory):
    sources = pipeline_factory().get_sources()
    assert sources == [source_filename], "The sources array does not contain the expected file"

def test_compile_calls_compiler(pipeline_factory):
    compiler = MagicMock()
    pipeline = pipeline_factory(compiler=compiler)
    pipeline.compile(source_filename, executable_filename)

    compiler.compile.assert_called_once_with(
            os.path.join(pipeline.sources_path, source_filename),
            os.path.join(pipeline.builds_path, executable_filename))

def test_disassemble_calls_disassembler(pipeline_factory):
    mock_disassembler = MagicMock()
    pipeline = pipeline_factory(disassembler=mock_disassembler)
    output_path = os.path.join(pipeline.disassemblies_path, f'{executable_filename}_d.txt')

    pipeline.disassemble(executable_filename)

    mock_disassembler.disassemble.assert_called_once_with(
            os.path.join(pipeline.builds_path, executable_filename),
            output_path)

def test_decompile_calls_decompiler(pipeline_factory):
    mock_decompiler = MagicMock()
    pipeline = pipeline_factory(decompiler=mock_decompiler)
    output_path = os.path.join(pipeline.decompilations_path, f'{executable_filename}.txt')

    with patch("builtins.open", mock_open()) as mock_file:
        pipeline.decompile(executable_filename)

    mock_decompiler.decompile.assert_called_once_with(
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
    evaluator = MagicMock()
    pipeline = pipeline_factory(evaluator=evaluator)
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    pipeline.generate_and_save_prediction(executable_filename)
    pipeline.add_source_to_dataset(source_filename)
    result = pipeline.evaluate_llm()

    evaluator.evaluate.assert_called_once_with(
        read_whole_file(pipeline.references_file_path),
        read_whole_file(pipeline.llm_predictions_file_path))


def test_evaluate_r2(pipeline_factory):
    evaluator = MagicMock()
    pipeline = pipeline_factory(evaluator=evaluator)
    pipeline.compile(source_filename, executable_filename)
    pipeline.decompile(executable_filename)
    pipeline.add_source_to_dataset(source_filename)
    result = pipeline.evaluate_r2()

    evaluator.evaluate.assert_called_once_with(
        read_whole_file(pipeline.references_file_path),
        read_whole_file(pipeline.r2_predictions_file_path))

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
    assert os.path.exists(pipeline.decompilations_path), "r2 decompilation directory does not exist before clean function execution."
    assert os.path.exists(pipeline.llmd_path), "llm decompilation directory does not exist before clean function execution."

    pipeline.clean()
    assert not os.path.exists(pipeline.builds_path), "Build directory exists after clean function execution."
    assert not os.path.exists(pipeline.disassemblies_path), "Disassemblies directory exists after clean function execution."
    assert not os.path.exists(pipeline.references_file_path), "Reference file exists after clean function execution."
    assert not os.path.exists(pipeline.llm_predictions_file_path), "Predictions file exists after clean function execution."
    assert not os.path.exists(pipeline.r2_predictions_file_path), "R2 predictions file exists after clean function execution."
    assert not os.path.exists(pipeline.decompilations_path), "r2 decompilation directory exists after clean function execution."
    assert not os.path.exists(pipeline.llmd_path), "llm decompilation directory exists after clean function execution."

def str_contains_word(string, word):
    return re.search(r'\b' + word + r'\b', string) is not None

def is_stripped(file_type):
    return "not stripped" not in file_type and str_contains_word(file_type, "stripped")
