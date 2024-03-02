import pytest
import os
from src.pipeline import Pipeline # Import the functions directly
from src.util import create_folder_if_not_exists
from shutil import copyfile

source_filename = "main.c"
executable_filename = "main"

@pytest.fixture
def setup_pipeline(tmp_path):
    # Setup data folders and copy main.c
    data_path = os.path.join(tmp_path, "data")
    create_folder_if_not_exists(data_path)

    sources_path = os.path.join(data_path, "sources")
    create_folder_if_not_exists(sources_path)

    copyfile(os.path.join("data/sources/", source_filename),
             os.path.join(sources_path, source_filename))

    yield Pipeline(data_path)

def do_compile_return_data_path(setup_pipeline):
    setup_pipeline.compile(source_filename, executable_filename)
    return setup_pipeline.data_path

def test_compile(setup_pipeline):
    data_path = do_compile_return_data_path(setup_pipeline)
    executable_path = os.path.join(data_path, "builds", executable_filename)

    # Check if the executable exists
    assert os.path.exists(executable_path), f"Executable {executable_path} was not created"
    # Check if the file is executable
    assert os.access(executable_path, os.X_OK), "File is not executable"

def test_disassemble(setup_pipeline):
    data_path = do_compile_return_data_path(setup_pipeline)

    setup_pipeline.disassemble(executable_filename)

    disassembly_file = os.path.join(data_path, "disassemblies", f'{executable_filename}_d.txt')
    assert os.path.exists(disassembly_file), f"Disassembly file ({disassembly_file}) does not exist after pipeline execution."

def test_clean_function(setup_pipeline):
    assert os.path.exists(setup_pipeline.builds_path), "Build directory does not exist before clean function execution."
    assert os.path.exists(setup_pipeline.disassemblies_path), "Disassemblies directory does not exist before clean function execution."
    setup_pipeline.clean()
    assert not os.path.exists(setup_pipeline.builds_path), "Build directory exists after clean function execution."
    assert not os.path.exists(setup_pipeline.disassemblies_path), "Disassemblies directory exists after clean function execution."
