# tests/test_news_digest.py
import unittest
import os
from unittest.mock import patch, MagicMock
from src.news_digest import get_env_variable, generate_email_content, send_email, main

class TestNewsDigest(unittest.TestCase):

    @patch.dict(os.environ, {"TEST_ENV": "test_value"})
    def test_get_env_variable(self):
        self.assertEqual(get_env_variable("TEST_ENV"), "test_value")
        with self.assertRaises(EnvironmentError):
            get_env_variable("NON_EXISTENT_ENV")

    def test_generate_email_content(self):
        summaries = {"Category1": "Summary1", "Category2": "Summary2"}
        week_number = 42
        content = generate_email_content(summaries, week_number)
        self.assertIn("<p><b>Category1</b></p><p>Summary1</p><br>", content)
        self.assertIn("<p><b>Category2</b></p><p>Summary2</p><br>", content)

    @patch("src.news_digest.requests.post")
    def test_send_email(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        send_email(
            subject="Test Subject",
            html_content="<p>Test</p>",
            sender_name="Sender",
            sender_email="sender@example.com",
            recipient_email="recipient@example.com",
            mailgun_domain="example.com",
            mailgun_api_key="testkey"
        )

        mock_post.assert_called_once_with(
            "https://api.mailgun.net/v3/example.com/messages",
            auth=("api", "testkey"),
            data={
                "from": "Sender <sender@example.com>",
                "to": ["recipient@example.com"],
                "subject": "Test Subject",
                "html": "<p>Test</p>"
            }
        )

    @patch("src.news_digest.get_env_variable")
    @patch("src.news_digest.send_email")
    @patch("src.news_digest.generate_summaries_by_category")
    @patch("src.news_digest.load_config")
    @patch("src.news_digest.setup_logging")
    @patch("src.news_digest.datetime")
    def test_main(
        self, mock_datetime, mock_setup_logging, mock_load_config,
        mock_generate_summaries_by_category, mock_send_email, mock_get_env_variable
    ):
        mock_load_config.return_value = {"log_file": "output.log"}
        mock_get_env_variable.side_effect = [
            "Sender Name", "sender@example.com", "recipient@example.com",
            "example.com", "testkey"
        ]
        mock_generate_summaries_by_category.return_value = {
            "Category1": "Summary1",
            "Category2": "Summary2"
        }
        mock_datetime.now.return_value.isocalendar.return_value = (2023, 42, 1)

        main("src/config.json")

        mock_setup_logging.assert_called_once_with("output.log")
        mock_load_config.assert_called_once_with("src/config.json")
        mock_get_env_variable.assert_any_call("SENDER_NAME")
        mock_get_env_variable.assert_any_call("SENDER_EMAIL")
        mock_get_env_variable.assert_any_call("RECIPIENT_EMAIL")
        mock_get_env_variable.assert_any_call("MAILGUN_DOMAIN")
        mock_get_env_variable.assert_any_call("MAILGUN_API_KEY")
        mock_generate_summaries_by_category.assert_called_once_with("src/config.json")
        mock_send_email.assert_called_once_with(
            "Savaitės naujienų apžvalga",
            "<html><body><p><b>Category1</b></p><p>Summary1</p><br><p><b>Category2</b></p><p>Summary2</p><br></body></html>",
            "Sender Name", "sender@example.com", "recipient@example.com",
            "example.com", "testkey"
        )

if __name__ == "__main__":
    unittest.main()
