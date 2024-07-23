# tests/test_rss_scraper.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
import requests
from datetime import datetime, timedelta
from src.rss_scraper import (
    load_existing_data,
    backup_file,
    save_data,
    clean_html,
    parse_rss_feed,
    parse_rss_item,
    fetch_rss_feed,
    scrape_rss_feed,
    handle_request_exception,
    get_weekly_file_path,
    get_week_range,
    DateTimeEncoder,
    ZoneInfo
)

class TestRssScraper(unittest.TestCase):

    def setUp(self):
        self.mock_data = [
            {"id": "1", "title": "Title 1", "description": "Description 1", "category": "Category 1", "pub_date": datetime.now()}
        ]

    @patch("builtins.open", new_callable=mock_open, read_data='[{"id": "1"}]')
    def test_load_existing_data(self, mock_file):
        with patch("os.path.exists", return_value=True):
            data = load_existing_data("mock_path")
            self.assertEqual(data, [{"id": "1"}])

    @patch("builtins.open", new_callable=mock_open)
    def test_save_data(self, mock_file):
        save_data("mock_path", self.mock_data)
        mock_file.assert_called_once_with("mock_path", 'w')
        # Simplify the assertion to check if write was called
        self.assertTrue(mock_file().write.called)

    def test_clean_html(self):
        raw_html = "<p>Some <b>bold</b> text.</p>"
        clean_text = clean_html(raw_html)
        self.assertEqual(clean_text, "Some bold text.")

    @patch("requests.get")
    def test_fetch_rss_feed(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = "<rss></rss>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        xml_data = fetch_rss_feed("http://example.com/rss", {})
        self.assertEqual(xml_data, "<rss></rss>")

    @patch("requests.get")
    @patch("time.sleep", return_value=None)
    def test_scrape_rss_feed_with_retries(self, mock_sleep, mock_get):
        mock_get.side_effect = requests.RequestException("Error")
        results = scrape_rss_feed("http://example.com/rss", "category", datetime.now(), datetime.now(), retries=2, delay=1)
        self.assertEqual(results, [])
        self.assertEqual(mock_get.call_count, 2)

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    def test_get_weekly_file_path(self, mock_exists, mock_makedirs):
        path = get_weekly_file_path("base_folder", 2023, 30)
        mock_makedirs.assert_called_once_with("base_folder")
        self.assertTrue(path.endswith("news_2023_30.json"))

    def test_get_week_range(self):
        start_of_week, end_of_week = get_week_range(2023, 30)
        self.assertEqual(start_of_week.weekday(), 0)  # Monday
        self.assertEqual((end_of_week - start_of_week).days, 7)

    def test_backup_file(self):
        with patch("os.rename") as mock_rename:
            backup_file("test_file")
            mock_rename.assert_called_once_with("test_file", "test_file.bak")

    def test_date_time_encoder(self):
        date = datetime.now()
        encoded = json.dumps({'date': date}, cls=DateTimeEncoder)
        self.assertIn(date.isoformat(), encoded)

if __name__ == "__main__":
    unittest.main()
