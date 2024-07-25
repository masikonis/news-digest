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
    get_zoneinfo,
    main,
    load_config,
    get_current_year_and_week,
    load_existing_news_data,
    add_new_items
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
    def test_load_existing_data_empty_file(self, mock_file):
        with patch("os.path.exists", return_value=True):
            mock_file.return_value.read.return_value = ""
            data = load_existing_data("mock_path")
            self.assertEqual(data, [])

    @patch("builtins.open", new_callable=mock_open)
    def test_load_existing_data_invalid_json(self, mock_file):
        with patch("os.path.exists", return_value=True):
            mock_file.return_value.read.return_value = "{invalid json"
            data = load_existing_data("mock_path")
            self.assertEqual(data, [])

    @patch("builtins.open", new_callable=mock_open)
    def test_save_data(self, mock_file):
        save_data("mock_path", self.mock_data)
        mock_file.assert_called_once_with("mock_path", 'w')
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

    @patch.dict('sys.modules', {'zoneinfo': None})
    def test_get_zoneinfo_importerror(self):
        ZoneInfo = get_zoneinfo()
        self.assertTrue(hasattr(ZoneInfo, 'utcoffset'))

    def test_handle_request_exception(self):
        with patch('time.sleep') as mock_sleep, patch('logging.error') as mock_error, patch('logging.info') as mock_info:
            handle_request_exception(Exception("Test error"), "http://example.com/rss", 0, 3, 2)
            mock_error.assert_called_with("Error fetching http://example.com/rss: Test error")
            mock_info.assert_called_with("Retrying in 2 seconds...")

    @patch("builtins.open", new_callable=mock_open, read_data='{"categories": {"category": "http://example.com/rss"}, "base_folder": "base_folder", "log_file": "log_file"}')
    @patch("src.rss_scraper.get_current_year_and_week", return_value=(2023, 30))
    @patch("src.rss_scraper.scrape_rss_feed", return_value=[])
    @patch("src.rss_scraper.setup_logging")
    @patch("src.rss_scraper.save_data")
    @patch("src.rss_scraper.load_existing_news_data", return_value=([], set()))
    @patch("src.rss_scraper.add_new_items")
    def test_main(self, mock_add_new_items, mock_load_existing_news_data, mock_save_data, mock_setup_logging, mock_scrape_rss_feed, mock_get_current_year_and_week, mock_open):
        main("config_path")
        mock_setup_logging.assert_called_once_with(os.path.abspath(os.path.join("..", "log_file")))
        mock_scrape_rss_feed.assert_called_once()
        mock_save_data.assert_called_once()
        mock_add_new_items.assert_called_once()

if __name__ == "__main__":
    unittest.main()
