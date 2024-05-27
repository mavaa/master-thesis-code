import os
import pytest
import subprocess
from unittest.mock import MagicMock, call
from src.r2runner import R2Runner

command = "aaa"
test_sample_path = "tests/sample.o"

def test_r2_run():
    mock_subprocess = MagicMock()
    r2_runner = R2Runner(mock_subprocess)

    output = MagicMock()
    error = MagicMock()

    r2_runner.run(command, test_sample_path, output, error)

    mock_subprocess.run.assert_called_once_with(
            ['radare2', '-qc', command, test_sample_path],
            stdout=output,
            stderr=error,
            check=True)

def test_r2_run_custom():
    mock_subprocess = MagicMock()
    custom_path = "/usr/bin/r2"
    custom_flags = "abc"
    r2_runner = R2Runner(mock_subprocess, r2_path=custom_path, r2_default_flags=custom_flags)

    output = MagicMock()
    error = MagicMock()

    r2_runner.run(command, test_sample_path, output, error)

    mock_subprocess.run.assert_called_once_with(
            [custom_path, f"-{custom_flags}", command, test_sample_path],
            stdout=output,
            stderr=error,
            check=True)

def test_r2_run(tmp_path):
    r2_runner = R2Runner(subprocess)
    out_path = os.path.join(tmp_path, "test_out.txt")

    r2_runner.run(command, test_sample_path, output=open(out_path, 'w'))

    assert os.path.exists(out_path), f"r2 output file ({out_path}) does not exist after r2 execution."
