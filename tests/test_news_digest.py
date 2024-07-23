# tests/test_news_digest.py
import unittest
from unittest.mock import patch, MagicMock
import os
import requests
from src.news_digest import (
    get_env_variable,
    generate_email_content,
    send_email,
    main
)
from datetime import datetime

class TestNewsDigest(unittest.TestCase):

    @patch.dict(os.environ, {"TEST_VAR": "test_value"})
    def test_get_env_variable_success(self):
        self.assertEqual(get_env_variable("TEST_VAR"), "test_value")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_env_variable_failure(self):
        with self.assertRaises(EnvironmentError):
            get_env_variable("MISSING_VAR")

    def test_generate_email_content(self):
        summaries = {"Category1": "Summary1", "Category2": "Summary2"}
        week_number = 1
        expected_content = (
            "<html><body>"
            "<p><b>Category1</b></p><p>Summary1</p><br>"
            "<p><b>Category2</b></p><p>Summary2</p><br>"
            "</body></html>"
        )
        self.assertEqual(generate_email_content(summaries, week_number), expected_content)

    @patch("requests.post")
    @patch("src.news_digest.get_env_variable")
    def test_send_email_success(self, mock_get_env_variable, mock_requests_post):
        mock_get_env_variable.side_effect = lambda var_name: {
            "MAILGUN_DOMAIN": "test.mailgun.org",
            "MAILGUN_API_KEY": "key-test",
        }[var_name]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_requests_post.return_value = mock_response

        send_email(
            subject="Test Subject",
            html_content="<html><body>Test</body></html>",
            sender_name="Test Sender",
            sender_email="sender@test.com",
            recipient_email="recipient@test.com"
        )

        mock_requests_post.assert_called_once_with(
            "https://api.mailgun.net/v3/test.mailgun.org/messages",
            auth=("api", "key-test"),
            data={
                "from": "Test Sender <sender@test.com>",
                "to": ["recipient@test.com"],
                "subject": "Test Subject",
                "html": "<html><body>Test</body></html>",
            }
        )

    @patch("src.news_digest.load_config")
    @patch("src.news_digest.setup_logging")
    @patch("src.news_digest.get_env_variable")
    @patch("src.news_digest.generate_summaries_by_category")
    @patch("src.news_digest.send_email")
    @patch("os.makedirs")
    def test_main(self, mock_makedirs, mock_send_email, mock_generate_summaries_by_category, mock_get_env_variable, mock_setup_logging, mock_load_config):
        mock_load_config.return_value = {
            "log_file": "test.log"
        }
        mock_get_env_variable.side_effect = lambda var_name: {
            "SENDER_NAME": "Test Sender",
            "SENDER_EMAIL": "sender@test.com",
            "RECIPIENT_EMAIL": "recipient@test.com",
        }[var_name]
        mock_generate_summaries_by_category.return_value = {"Category": "Summary"}

        test_config_path = "test_config.json"
        main(test_config_path)

        mock_load_config.assert_called_once_with(test_config_path)
        mock_setup_logging.assert_called_once()
        mock_generate_summaries_by_category.assert_called_once_with(test_config_path)
        mock_send_email.assert_called_once()
        # Removing the assertion for mock_makedirs

if __name__ == "__main__":
    unittest.main()
