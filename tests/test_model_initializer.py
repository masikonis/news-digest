# tests/test_model_initializer.py
import unittest
from unittest.mock import patch, MagicMock

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

        # Mock the model initialization
        mock_model = MagicMock()
        mock_ChatOpenAI.return_value = mock_model

        # Import the function under test
        from src.model_initializer import initialize_model

        # Call the function
        model = initialize_model()

        # Assert that load_dotenv was called with override=True
        mock_load_dotenv.assert_called_once_with(override=True)

        # Assert that the environment variable was set correctly
        mock_getenv.assert_any_call("OPENAI_API_KEY")
        mock_environ.__setitem__.assert_any_call("OPENAI_API_KEY", "fake_openai_api_key")

        # Assert that the ChatOpenAI model was initialized with the correct parameters
        mock_ChatOpenAI.assert_called_once_with(model="gpt-4o", temperature=0)

        # Assert that the returned model is the mocked model
        self.assertEqual(model, mock_model)

if __name__ == "__main__":
    unittest.main()
