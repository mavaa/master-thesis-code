import os
import pytest
from src.evaluator.codebleuevaluator import CodeBleuEvaluator
from src.util import read_whole_file
from unittest.mock import MagicMock, call
from codebleu import calc_codebleu

test_sample_path = "tests/data"

def test_evaluate():
    reference_file = "void source_sample(){}"
    prediction_file =  "void source_sample_pred(){}"
    codebleu_func = MagicMock()
    expected_return_value = {"score": 0.85}
    codebleu_func.return_value = expected_return_value
    lang="java"
    weights=(0.30, 0.2, 0.14, 0.36)
    tokenizer=MagicMock
    evaluator = CodeBleuEvaluator(codebleu_func, lang, weights, tokenizer)

    result = evaluator.evaluate(reference_file, prediction_file)

    codebleu_func.assert_called_once_with([reference_file], \
                                          [prediction_file], \
                                          lang=lang, \
                                          weights=weights, \
                                          tokenizer=tokenizer)

    assert result == expected_return_value, f'Unexpected score: {result}'

@pytest.mark.parametrize("prediction_filename,expected_score", [
    ("r2_predictions.txt",
    {
        'codebleu': 0.11998266390587671,
        'ngram_match_score': 0.034006187762971735,
        'weighted_ngram_match_score': 0.07284754478361201,
        'syntax_match_score': 0.12307692307692308,
        'dataflow_match_score': 0.25
    }),
    ("references.txt",
    {
        'codebleu': 1.0,
        'ngram_match_score': 1.0,
        'weighted_ngram_match_score': 1.0,
        'syntax_match_score': 1.0,
        'dataflow_match_score': 1.0
    }),
])
def test_evaluate_integration(prediction_filename, expected_score):
    reference_file = os.path.join(test_sample_path, 'references.txt')
    prediction_file = os.path.join(test_sample_path, prediction_filename)
    evaluator = CodeBleuEvaluator(calc_codebleu)

    result = evaluator.evaluate(read_whole_file(reference_file), read_whole_file(prediction_file))
    print(f"THE SCORE FOR {prediction_filename}")
    for key, value in result.items():
        print(f"{key}: {value:.2%}")

    assert result == expected_score, f'Unexpected score: {result}'
