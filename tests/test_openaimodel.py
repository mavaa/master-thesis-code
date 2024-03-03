import pytest
from src.openaimodel import OpenAIModel
import openai

api_key = "replace_me"

@pytest.fixture
def setup_model():
    yield OpenAIModel(api_key)

def test_openaimodel_create(setup_model):
    assert setup_model.api_key == api_key, "API key was not set correctly"
