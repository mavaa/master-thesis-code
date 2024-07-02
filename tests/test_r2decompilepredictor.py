import os
import subprocess
from src.predictor.r2decompilepredictor import R2DecompilePredictor
from src.r2runner import R2Runner
from unittest.mock import MagicMock, call

test_sample_path = "tests/sample.o"

def test_generate_prediction():
    mock_r2_runner = MagicMock()
    executable_path = "/path/to/executable"
    expected_prediction =  "Expected prediction"
    mock_r2_runner.run_str.return_value = expected_prediction, None

    decompiler = R2DecompilePredictor(mock_r2_runner)

    prediction = decompiler.generate_prediction(executable_path, "not/used")

    mock_r2_runner.run_str.assert_called_once_with("aaa;pdg", executable_path)
    assert prediction == expected_prediction, f"Unexpected prediction: {prediction}"

def test_generate_prediction_integration(tmp_path):
    decompiler = R2DecompilePredictor(R2Runner(subprocess))

    result = decompiler.generate_prediction(test_sample_path, "not/used")

    assert result is not None
