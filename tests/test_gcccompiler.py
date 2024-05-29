import magic
import os
import pytest
import re
import subprocess
from src.compiler.gcccompiler import GCCCompiler
from unittest.mock import MagicMock, call

@pytest.mark.parametrize("should_strip", [True, False])
def test_compile(should_strip):
    mock_subprocess = MagicMock()
    source_path = "/path/to/source.c"
    output_path = "/path/to/binary"

    compiler = GCCCompiler(mock_subprocess, should_strip)

    compiler.compile(source_path, output_path)

    expected_calls = [call.run(['gcc', '-c', '-o', output_path, source_path], check=True)]

    if(should_strip):
        expected_calls.append(call.run(["strip", output_path], check=True))

    mock_subprocess.assert_has_calls(expected_calls, any_order=False)
    assert mock_subprocess.run.call_count == len(expected_calls)

@pytest.mark.parametrize("should_strip", [True, False])
def test_compile_integration(tmp_path, should_strip):
    output_path = os.path.join(tmp_path, 'binary')

    compiler = GCCCompiler(subprocess, should_strip)

    compiler.compile("data/sources/helloworld.c", output_path)

    assert os.path.exists(output_path), f"Binary file {output_path} not created"

    # Check if the file is an object file
    file_type = magic.from_file(output_path)
    assert str_contains_word(file_type, 'ELF') and str_contains_word(file_type, 'relocatable'), f"File {output_path} is not a valid object file. Detected type: {file_type}"

    # Check if the compiled file was stripped according to parameter
    was_stripped = is_stripped(file_type)
    assert was_stripped == should_strip, f"Strip parameter was not respected, expected {should_strip}, but was {was_stripped}"

def str_contains_word(string, word):
    return re.search(r'\b' + word + r'\b', string) is not None

def is_stripped(file_type):
    return "not stripped" not in file_type and str_contains_word(file_type, "stripped")
