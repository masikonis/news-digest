# tests/test_news_digest.py
import unittest
from unittest.mock import patch, MagicMock

class TestNewsDigest(unittest.TestCase):
    @patch('os.getenv')
    @patch('os.environ')
    @patch('langchain_openai.ChatOpenAI')
    @patch('dotenv.load_dotenv')
    def test_news_digest(self, mock_load_dotenv, mock_ChatOpenAI, mock_environ, mock_getenv):
        # Mock the return values for environment variables
        mock_getenv.side_effect = lambda k: {
            "LANGCHAIN_TRACING_V2": "true",
            "LANGCHAIN_API_KEY": "fake_langchain_api_key",
            "OPENAI_API_KEY": "fake_openai_api_key"
        }.get(k, None)

        # Import the module under test
        import src.news_digest

        # Assert that load_dotenv was called with override=True
        mock_load_dotenv.assert_called_once_with(override=True)

        # Assert that the environment variables were set correctly
        mock_getenv.assert_any_call("LANGCHAIN_TRACING_V2")
        mock_getenv.assert_any_call("LANGCHAIN_API_KEY")
        mock_getenv.assert_any_call("OPENAI_API_KEY")
        mock_environ.__setitem__.assert_any_call("OPENAI_API_KEY", "fake_openai_api_key")

        # Assert that the ChatOpenAI model was initialized with the correct parameters
        mock_ChatOpenAI.assert_called_once_with(model="gpt-4o", temperature=0)

if __name__ == "__main__":
    unittest.main()
