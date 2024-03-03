import pytest
from unittest.mock import patch, MagicMock
from src.openaimodel import OpenAIModel

api_key = "replace_me"

@pytest.fixture
def setup_model():
    yield OpenAIModel(api_key)

def test_openaimodel_create(setup_model):
    assert setup_model.client.api_key == api_key, "API key was not set correctly"

# Test to do code coverage in the generate_prediction function
@pytest.fixture
def mock_openai_client():
    with patch('src.openaimodel.OpenAI') as mock:
        mock_instance = mock.return_value
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [{'message': {'content': 'mocked response'}}]
        mock_instance.chat.completions.create.return_value = mock_chat_completion
        yield mock

def test_openaimodel_generate_prediction(mock_openai_client, setup_model):
    # Call the method
    response = setup_model.generate_prediction("test-model", "test prompt", 0.5)

    # Assertions to ensure the mock was called as expected
    setup_model.client.chat.completions.create.assert_called_once_with(
        messages=[{'role': 'user', 'content': 'test prompt'}],
        model="test-model",
        temperature=0.5
    )

    # Assert the mock response is correctly returned
    assert response.choices[0]['message']['content'] == 'mocked response', "The response from generate_prediction was not as expected"
