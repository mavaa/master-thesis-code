import os
import subprocess
from src.disassembler.objdumpdisassembler import ObjdumpDisassembler
from unittest.mock import MagicMock, mock_open, patch

test_sample_path = "tests/sample.o"

def test_disassemble_calls_subprocess():
    mock_subprocess = MagicMock()
    output_path = "path/to/output"

    disassembler = ObjdumpDisassembler(mock_subprocess)

    with patch("builtins.open", mock_open()) as mock_file:
        disassembler.disassemble(test_sample_path, output_path)

        mock_subprocess.run.assert_called_once_with(
                ["objdump", "-d", test_sample_path],
                           stdout=mock_file(), check=True)

def test_disassemble_integration(tmp_path):
    output_path = os.path.join(tmp_path, 'objdump_out.txt')

    disassembler = ObjdumpDisassembler(subprocess)

    disassembler.disassemble(test_sample_path, output_path)

    assert os.path.exists(output_path), "objdump output file not created"
