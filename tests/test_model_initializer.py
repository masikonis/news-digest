# tests/test_model_initializer.py
import unittest
from unittest.mock import patch, MagicMock
import os

class TestModelInitializer(unittest.TestCase):
    @patch('src.model_initializer.load_dotenv')
    @patch('src.model_initializer.ChatOpenAI')
    def test_initialize_model_openai(self, mock_ChatOpenAI, mock_load_dotenv):
        # Mock the model initialization to return a MagicMock instance
        mock_model = MagicMock()
        mock_ChatOpenAI.return_value = mock_model

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'fake_openai_api_key'}):
            from src.model_initializer import initialize_model
            model = initialize_model('basic', provider="openai")

            mock_load_dotenv.assert_called_once_with(override=True)
            mock_ChatOpenAI.assert_called_once_with(model="gpt-4o-mini", temperature=0)
            self.assertEqual(model, mock_model)

    @patch('src.model_initializer.load_dotenv')
    @patch('src.model_initializer.ChatGoogleGenerativeAI')
    def test_initialize_model_gemini(self, mock_ChatGemini, mock_load_dotenv):
        # Mock the model initialization to return a MagicMock instance
        mock_model = MagicMock()
        mock_ChatGemini.return_value = mock_model

        with patch.dict('os.environ', {'GEMINI_API_KEY': 'fake_gemini_api_key'}):
            from src.model_initializer import initialize_model
            model = initialize_model('basic', provider="gemini")

            mock_load_dotenv.assert_called_once_with(override=True)
            mock_ChatGemini.assert_called_once_with(
                model="gemini-1.5-pro",
                google_api_key='fake_gemini_api_key',
                temperature=0
            )
            self.assertEqual(model, mock_model)

    @patch('src.model_initializer.load_dotenv')
    def test_initialize_model_invalid_provider(self, mock_load_dotenv):
        from src.model_initializer import initialize_model
        with self.assertRaises(ValueError) as context:
            initialize_model('basic', provider="invalid_provider")
        self.assertTrue("Unknown provider: invalid_provider" in str(context.exception))

    @patch('src.model_initializer.load_dotenv')
    def test_initialize_model_invalid_purpose(self, mock_load_dotenv):
        from src.model_initializer import initialize_model
        with self.assertRaises(ValueError) as context:
            initialize_model('invalid_purpose')
        self.assertTrue("Unknown model purpose: invalid_purpose" in str(context.exception))

    @patch('src.model_initializer.load_dotenv')
    @patch('src.model_initializer.OpenAIEmbeddings')
    def test_initialize_model_embeddings_openai(self, mock_OpenAIEmbeddings, mock_load_dotenv):
        # Mock the model initialization to return a MagicMock instance
        mock_model = MagicMock()
        mock_OpenAIEmbeddings.return_value = mock_model

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'fake_openai_api_key'}):
            from src.model_initializer import initialize_model
            model = initialize_model('embeddings', provider="openai")

            mock_load_dotenv.assert_called_once_with(override=True)
            mock_OpenAIEmbeddings.assert_called_once_with(
                model="text-embedding-3-small",
                dimensions=1536
            )
            self.assertEqual(model, mock_model)

    @patch('src.model_initializer.load_dotenv')
    def test_missing_api_key_gemini(self, mock_load_dotenv):
        with patch.dict('os.environ', {}, clear=True):
            from src.model_initializer import initialize_model
            with self.assertRaises(ValueError) as context:
                initialize_model('basic', provider="gemini")
            self.assertTrue("GEMINI_API_KEY not found" in str(context.exception))

if __name__ == "__main__":
    unittest.main()
