import pytest
import os
from src.pipeline import compile, disassemble, clean # Import the functions directly
from src.util import create_folder_if_not_exists

sources_folder = "data/sources"
build_folder = "data/builds"

def do_compile_return_output_path(tmp_path):
    source = os.path.join(sources_folder, "main.c")
    executable = os.path.join(tmp_path, "main")
    compile(source, executable)
    return executable

def test_compile(tmp_path):
    executable = do_compile_return_output_path(tmp_path)

    # Check if the executable exists
    assert os.path.exists(executable), "Executable was not created"
    # Check if the file is executable
    assert os.access(executable, os.X_OK), "File is not executable"

def test_disassemble(tmp_path):
    executable = do_compile_return_output_path(tmp_path)
    disassembly_path = os.path.join(tmp_path, "disassembly")
    disassemble(executable, disassembly_path)
    executable_name = os.path.basename(executable)
    disassembly_file = os.path.join(disassembly_path, f'{executable_name}_d.txt')
    assert os.path.exists(disassembly_file), f"Disassembly file ({disassembly_file}) does not exist after pipeline execution."

def test_clean_function():
    create_folder_if_not_exists(build_folder)
    clean()
    assert not os.path.exists(build_folder), "Build directory exists after clean function execution."
