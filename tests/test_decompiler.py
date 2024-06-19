import os
import subprocess
from src.decompiler.r2ghidradecompiler import R2GdhidraDecompiler
from src.r2runner import R2Runner
from unittest.mock import MagicMock, call

test_sample_path = "tests/sample.o"

def test_decompile():
    mock_r2_runner = MagicMock()
    executable_path = "/path/to/executable"
    output_path = "/path/to/decompiled.c"

    decompiler = R2GdhidraDecompiler(mock_r2_runner)

    decompiler.decompile(executable_path, output_path)

    mock_r2_runner.run.assert_called_once_with("aaa;pdg", executable_path, output_path)

def test_compile_integration(tmp_path):
    output_path = os.path.join(tmp_path, 'decompiled.c')

    decompiler = R2GdhidraDecompiler(R2Runner(subprocess))

    decompiler.decompile(test_sample_path, output_path)

    assert os.path.exists(output_path), f"Decompiled file {output_path} not created"
