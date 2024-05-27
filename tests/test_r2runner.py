import os
import pytest
import subprocess
from unittest.mock import MagicMock, call, mock_open, patch
from src.r2runner import R2Runner

command = "aaa"
test_sample_path = "tests/sample.o"

@pytest.fixture
def mock_open_fixture():
    with patch("builtins.open", mock_open()) as mock_file:
        yield mock_file

def test_r2_run(mock_open_fixture):
    mock_subprocess = MagicMock()
    r2_runner = R2Runner(mock_subprocess)

    output_path = "output.txt"
    error = MagicMock()

    r2_runner.run(command, test_sample_path, output_path, error)

    mock_open_fixture.assert_called_once_with(output_path, 'w')
    mock_subprocess.run.assert_called_once_with(
            ['radare2', '-qc', command, test_sample_path],
            stdout=mock_open_fixture(),
            stderr=error,
            check=True)

def test_r2_run_no_stderr(mock_open_fixture):
    mock_subprocess = MagicMock()
    r2_runner = R2Runner(mock_subprocess)

    output_path = "output.txt"

    r2_runner.run(command, test_sample_path, output_path)

    mock_open_fixture.assert_called_once_with(output_path, 'w')
    mock_subprocess.run.assert_called_once_with(
            ['radare2', '-qc', command, test_sample_path],
            stdout=mock_open_fixture(),
            stderr=mock_subprocess.DEVNULL,
            check=True)

def test_r2_run_custom(mock_open_fixture):
    mock_subprocess = MagicMock()
    custom_path = "/usr/bin/r2"
    custom_flags = "abc"
    r2_runner = R2Runner(mock_subprocess, r2_path=custom_path, r2_default_flags=custom_flags)

    output_path = "output.txt"
    error = MagicMock()

    r2_runner.run(command, test_sample_path, output_path, error)

    mock_open_fixture.assert_called_once_with(output_path, 'w')
    mock_subprocess.run.assert_called_once_with(
            [custom_path, f'-{custom_flags}', command, test_sample_path],
            stdout=mock_open_fixture(),
            stderr=error,
            check=True)

def test_r2_run(tmp_path):
    r2_runner = R2Runner(subprocess)
    out_path = os.path.join(tmp_path, "test_out.txt")

    r2_runner.run(command, test_sample_path, out_path)

    assert os.path.exists(out_path), f"r2 output file ({out_path}) does not exist after r2 execution."
