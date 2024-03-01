import pytest
import os
from src.pipeline import run_pipeline, clean # Import the functions directly

test_program_folder = "sources"

def test_pipeline():
    run_pipeline(test_program_folder)
    build_dir = os.path.join(test_program_folder, 'build')
    assert os.path.exists(build_dir), "Build directory does not exist after pipeline execution."

def test_clean_function():
    clean(test_program_folder)
    build_dir = os.path.join(test_program_folder, 'build')
    assert not os.path.exists(build_dir), "Build directory exists after clean function execution."
