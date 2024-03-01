import pytest
import os
from src.util import create_folder_if_not_exists

def test_create_folder_if_not_exists(tmp_path):
    folder = os.path.join(tmp_path, "test")
    create_folder_if_not_exists(folder)

    # Check if the executable exists
    assert os.path.exists(folder), "Executable was not created"
