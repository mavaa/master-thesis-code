import pytest
import os
import magic
import re
import subprocess
from src.pipeline import Pipeline
from src.r2runner import R2Runner
from src.disassembler.objdumpdisassembler import ObjdumpDisassembler
from src.compiler.gcccompiler import GCCCompiler
from src.util import create_folder_if_not_exists, read_whole_file
from shutil import copyfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch, call

executable_filename = "helloworld"
source_filename = f"{executable_filename}.c"
mock_prediction_expected_result = "Mocked prediction"

def create_mock_predictor(name):
    mock_predictor = MagicMock()
    mock_predictor.name = name
    mock_predictor.generate_prediction.return_value = mock_prediction_expected_result
    return mock_predictor

def setup_pipeline(tmp_path, compiler, disassembler, predictors, evaluator):
    if compiler is None:
        compiler = GCCCompiler(subprocess)

    if disassembler is None:
        disassembler = ObjdumpDisassembler(subprocess)

    if predictors is None:
        predictors = [create_mock_predictor('test')]

    if evaluator is None:
        evaluator = MagicMock()

    # Setup data folders and copy main.c
    data_path = os.path.join(tmp_path, "data")
    create_folder_if_not_exists(data_path)

    sources_path = os.path.join(data_path, "sources")
    create_folder_if_not_exists(sources_path)

    copyfile(os.path.join("sources/small_test/", source_filename),
             os.path.join(sources_path, source_filename))

    pipeline = Pipeline(
            compiler=compiler,
            disassembler=disassembler,
            predictors=predictors,
            evaluator=evaluator,
            sources_path=sources_path,
            data_path=data_path)
    pipeline.init_folders()

    return pipeline

@pytest.fixture
def pipeline_factory(tmp_path):
    def create_pipeline(compiler=None, disassembler=None, predictors=None, evaluator=None):
        return setup_pipeline(tmp_path, compiler, disassembler, predictors, evaluator)
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

def test_add_source_to_dataset(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.add_source_to_dataset(source_filename)

    assert os.path.exists(pipeline.references_file_path), "Reference file does not exist after pipeline execution."

    with open(pipeline.references_file_path, 'r') as file:
        reference_file_content  = file.read()

    assert reference_file_content == '#include <stdio.h> int print_hello() { printf("Hello, World!\\n"); return 0; }\n'

def test_generate_prediction(pipeline_factory):
    pipeline = pipeline_factory()
    preditcor = create_mock_predictor('test')
    build_path = os.path.join(pipeline.builds_path, executable_filename)
    disassembly_path = os.path.join(pipeline.disassemblies_path, f'{executable_filename}_d.txt')
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)

    prediction = pipeline.generate_prediction(executable_filename, preditcor)

    preditcor.generate_prediction.assert_called_once_with(build_path, disassembly_path)

def test_generate_and_save_predictions(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    pipeline.generate_and_save_predictions(executable_filename)

    assert os.path.exists(pipeline.predictions_path), "Predictions folder does not exist."

    for predictor in pipeline.predictors:
        prediction_file_path = os.path.join(pipeline.predictions_path, f'{predictor.name}_{executable_filename}.c')
        with open(prediction_file_path, 'r') as file:
            assert file.read() == mock_prediction_expected_result

def test_generate_and_save_predictions_with_callback(pipeline_factory):
    pipeline = pipeline_factory()
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    mock_callback = MagicMock()
    pipeline.generate_and_save_predictions(executable_filename, status_callback=mock_callback)

    assert os.path.exists(pipeline.predictions_path), "Predictions folder does not exist."

    for predictor in pipeline.predictors:
        prediction_file_path = os.path.join(pipeline.predictions_path, f'{predictor.name}_{executable_filename}.c')
        with open(prediction_file_path, 'r') as file:
            assert file.read() == mock_prediction_expected_result

    # Verify the callback was called with the correct arguments
    expected_calls = []
    for predictor in pipeline.predictors:
        expected_calls.append(call.__bool__())
        expected_calls.append(((0, predictor.name),))
        expected_calls.append(call.__bool__())
        expected_calls.append(((1, predictor.name),))

    mock_callback.assert_has_calls(expected_calls, any_order=False)

@pytest.mark.parametrize("source,expected", [
    (["hey", "there", "you"], "hey there you"),
    (["quick", "brown", "", "fox"], "quick brown fox"),
    (["hey", "  you", "there  "], "hey you there")
])
def test_put_code_on_single_line(pipeline_factory, source, expected):
    pipeline = pipeline_factory()
    result = pipeline.put_code_on_single_line(source)
    assert result == expected

def test_evaluate_predictors(pipeline_factory):
    evaluator = MagicMock()
    predictors = [ create_mock_predictor('a'), create_mock_predictor('b'), create_mock_predictor('c')]

    pipeline = pipeline_factory(predictors=predictors, evaluator=evaluator)
    pipeline.compile(source_filename, executable_filename)
    pipeline.disassemble(executable_filename)
    pipeline.generate_and_save_predictions(executable_filename)
    pipeline.add_source_to_dataset(source_filename)
    results = pipeline.evaluate()

    for predictor in predictors:
        prediction_file_path = os.path.join(pipeline.predictions_path, f'{predictor.name}_all.txt')
        evaluator.evaluate.assert_any_call(
            read_whole_file(pipeline.references_file_path),
            read_whole_file(prediction_file_path))

    assert len(results) == len(predictors)

def test_clean_function(pipeline_factory):
    pipeline = pipeline_factory()
    Path(pipeline.references_file_path).touch()
    Path(pipeline.predictions_path).touch()
    assert os.path.exists(pipeline.builds_path), "Build directory does not exist before clean function execution."
    assert os.path.exists(pipeline.disassemblies_path), "Disassemblies directory does not exist before clean function execution."
    assert os.path.exists(pipeline.references_file_path), "Reference file does not exist before clean function execution."
    assert os.path.exists(pipeline.predictions_path), "LLM predictions file does not exist before clean function execution."

    pipeline.clean()
    assert not os.path.exists(pipeline.builds_path), "Build directory exists after clean function execution."
    assert not os.path.exists(pipeline.disassemblies_path), "Disassemblies directory exists after clean function execution."
    assert not os.path.exists(pipeline.references_file_path), "Reference file exists after clean function execution."
    assert not os.path.exists(pipeline.predictions_path), "Predictions file exists after clean function execution."

def str_contains_word(string, word):
    return re.search(r'\b' + word + r'\b', string) is not None

def is_stripped(file_type):
    return "not stripped" not in file_type and str_contains_word(file_type, "stripped")
