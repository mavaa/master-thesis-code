import os
import subprocess
from src.disassembler.r2disassembler import R2Disassembler
from src.r2runner import R2Runner
from unittest.mock import MagicMock

test_sample_path = "tests/sample.o"

def test_disassemble_calls_runner():
    mock_r2_runner = MagicMock()
    output_path = "/path/to/output"
    disassembler = R2Disassembler(mock_r2_runner)

    disassembler.disassemble(test_sample_path, output_path)

    mock_r2_runner.run.assert_called_once_with(
            'pd',
            test_sample_path,
            output_path)

def test_disassemble_integration(tmp_path):
    output_path = os.path.join(tmp_path, 'r2_out.txt')
    disassembler = R2Disassembler(R2Runner(subprocess))

    disassembler.disassemble(test_sample_path, output_path)

    assert os.path.exists(output_path), "R2 output file not created"
