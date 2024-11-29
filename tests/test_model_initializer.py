# tests/test_model_initializer.py
import unittest
from unittest.mock import patch, MagicMock

class TestModelInitializer(unittest.TestCase):
    @patch('src.model_initializer.load_dotenv')
    @patch('src.model_initializer.ChatOpenAI')
    def test_initialize_model(self, mock_ChatOpenAI, mock_load_dotenv):
        # Mock the model initialization to return a MagicMock instance
        mock_model = MagicMock()
        mock_ChatOpenAI.return_value = mock_model

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'fake_openai_api_key'}):
            from src.model_initializer import initialize_model
            model = initialize_model('basic')

            mock_load_dotenv.assert_called_once_with(override=True)
            mock_ChatOpenAI.assert_called_once_with(model="gpt-4o-mini", temperature=0)
            self.assertEqual(model, mock_model)

    @patch('src.model_initializer.load_dotenv')
    def test_initialize_model_invalid_purpose(self, mock_load_dotenv):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'fake_openai_api_key'}):
            from src.model_initializer import initialize_model
            with self.assertRaises(ValueError):
                initialize_model('invalid_purpose')

    @patch('src.model_initializer.load_dotenv')
    @patch('src.model_initializer.OpenAIEmbeddings')
    def test_initialize_model_embeddings(self, mock_OpenAIEmbeddings, mock_load_dotenv):
        # Mock the model initialization to return a MagicMock instance
        mock_model = MagicMock()
        mock_OpenAIEmbeddings.return_value = mock_model

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'fake_openai_api_key'}):
            from src.model_initializer import initialize_model
            model = initialize_model('embeddings')

            mock_load_dotenv.assert_called_once_with(override=True)
            mock_OpenAIEmbeddings.assert_called_once_with(model="text-embedding-3-small", dimensions=1536)
            self.assertEqual(model, mock_model)

if __name__ == "__main__":
    unittest.main()
