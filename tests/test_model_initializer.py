# tests/test_model_initializer.py
import unittest
from unittest.mock import patch, MagicMock, call

class TestModelInitializer(unittest.TestCase):
    @patch('os.getenv')
    @patch('os.environ')
    @patch('langchain_openai.ChatOpenAI')
    @patch('dotenv.load_dotenv')
    def test_initialize_model(self, mock_load_dotenv, mock_ChatOpenAI, mock_environ, mock_getenv):
        # Mock the return value for environment variable
        mock_getenv.side_effect = lambda k: {
            "OPENAI_API_KEY": "fake_openai_api_key"
        }.get(k, None)

        # Mock the model initialization to return a MagicMock instance
        mock_model = MagicMock()
        # Set return_value instead of side_effect to avoid exceptions during initialization
        mock_ChatOpenAI.return_value = mock_model

        # Import the function under test
        from src.model_initializer import initialize_model

        # Call the function with 'basic' purpose instead of default
        model = initialize_model('basic')

        # Assert that load_dotenv was called with override=True
        mock_load_dotenv.assert_called_once_with(override=True)

        # Assert that the environment variable was accessed
        mock_getenv.assert_any_call("OPENAI_API_KEY")

        # Update the expected calls to match new model configurations
        expected_calls = [
            call(model="gpt-4o-mini", temperature=0),  # For 'basic'
        ]
        # Update assertion to expect only one call
        self.assertEqual(mock_ChatOpenAI.call_count, 1)
        mock_ChatOpenAI.assert_has_calls(expected_calls, any_order=False)

        # Assert that the returned model is the mocked model
        self.assertEqual(model, mock_model)

if __name__ == "__main__":
    unittest.main()
