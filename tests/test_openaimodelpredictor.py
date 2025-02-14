import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.predictor.openaimodelpredictor import OpenAIModelPredictor

api_key = "replace_me"

base_promt = "test prompt with code: {disassembly}\nend"
test_code = "binary code would go here"

mock_prediction = """```c
Mocked prediction
```"""
mock_prediction_expected_result = "Mocked prediction\n"

@pytest.fixture
def setup_model():
    yield OpenAIModelPredictor(api_key, "test-model", 0.5, base_promt)

def test_openaimodel_create(setup_model):
    assert setup_model.client.api_key == api_key, "API key was not set correctly"

# Test to do code coverage in the generate_prediction function
@pytest.fixture
def mock_openai_client():
    with patch('src.predictor.openaimodelpredictor.OpenAI') as mock:
        mock_instance = mock.return_value
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock(message=MagicMock(content=mock_prediction))]
        mock_instance.chat.completions.create.return_value = mock_chat_completion
        yield mock

@pytest.fixture
def mock_file_open():
    m = mock_open(read_data=test_code)
    with patch('builtins.open', m):
        yield m

def test_openaimodel_generate_prediction(mock_openai_client, setup_model, mock_file_open):
    # Call the method
    response = setup_model.generate_prediction("binary_filename.o", "path/to/text_file.txt")

    # Assertions to ensure the mock was called as expected
    setup_model.client.chat.completions.create.assert_called_once_with(
        messages=[{'role': 'user', 'content': 'test prompt with code: binary code would go here\nend'}],
        model="test-model",
        temperature=0.5
    )

    # Assert the mock response is correctly returned
    assert response == mock_prediction_expected_result, "The response from generate_prediction was not as expected"
