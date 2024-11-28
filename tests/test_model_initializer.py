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
        mock_ChatOpenAI.return_value = mock_model

        from src.model_initializer import initialize_model
        model = initialize_model('basic')

        mock_load_dotenv.assert_called_once_with(override=True)
        mock_getenv.assert_any_call("OPENAI_API_KEY")
        mock_ChatOpenAI.assert_called_once_with(model="gpt-4o-mini", temperature=0)
        self.assertEqual(model, mock_model)

    @patch('os.getenv')
    @patch('os.environ')
    @patch('langchain_openai.ChatOpenAI')
    @patch('dotenv.load_dotenv')
    def test_initialize_model_invalid_purpose(self, mock_load_dotenv, mock_ChatOpenAI, mock_environ, mock_getenv):
        mock_getenv.return_value = "fake_openai_api_key"
        
        from src.model_initializer import initialize_model
        with self.assertRaises(ValueError):
            initialize_model('invalid_purpose')

    @patch('os.getenv')
    @patch('os.environ')
    @patch('langchain_openai.ChatOpenAI')
    @patch('dotenv.load_dotenv')
    def test_initialize_model_embeddings(self, mock_load_dotenv, mock_ChatOpenAI, mock_environ, mock_getenv):
        mock_getenv.return_value = "fake_openai_api_key"
        
        from src.model_initializer import initialize_model
        model = initialize_model('embeddings')
        
        self.assertIsNone(model)
        mock_ChatOpenAI.assert_not_called()

if __name__ == "__main__":
    unittest.main()
