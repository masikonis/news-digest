import unittest
from unittest.mock import patch, MagicMock
from src.rss_scraper import (
    load_existing_data, save_data, clean_html, parse_rss_feed, 
    get_weekly_file_path, load_config, get_current_year_and_week, 
    load_existing_news_data, add_new_items, setup_logging, main
)
import os
import json
from datetime import datetime
import shutil

class TestRSSScraper(unittest.TestCase):

    def setUp(self):
        self.test_dir = 'test_data'
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_file = os.path.join(self.test_dir, 'test.json')
        self.sample_data = [{'id': '1', 'title': 'Test Title', 'description': 'Test Description', 'category': 'Test Category', 'pub_date': 'Test Date'}]
        self.sample_xml = """
        <rss>
            <channel>
                <item>
                    <title>Test Title</title>
                    <description>Test Description</description>
                    <guid>1</guid>
                    <pubDate>Test Date</pubDate>
                </item>
            </channel>
        </rss>
        """
        self.config_path = os.path.join(self.test_dir, 'config.json')
        self.log_file = os.path.join(self.test_dir, 'rss_scraper.log')
        self.config_data = {
            "categories": {
                "Test Category": "https://example.com/rss"
            },
            "base_folder": self.test_dir,
            "retry_count": 3,
            "retry_delay": 2,
            "log_file": self.log_file
        }
        with open(self.config_path, 'w') as file:
            json.dump(self.config_data, file)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_existing_data(self):
        with open(self.test_file, 'w') as file:
            json.dump(self.sample_data, file)
        data = load_existing_data(self.test_file)
        self.assertEqual(data, self.sample_data)

    def test_save_data(self):
        save_data(self.test_file, self.sample_data)
        with open(self.test_file, 'r') as file:
            data = json.load(file)
        self.assertEqual(data, self.sample_data)

    def test_clean_html(self):
        raw_html = "<p>This is a <b>test</b> description.</p>"
        expected_text = "This is a test description."
        self.assertEqual(clean_html(raw_html), expected_text)

    def test_parse_rss_feed(self):
        expected_output = [{'id': '1', 'title': 'Test Title', 'description': 'Test Description', 'category': 'Test Category', 'pub_date': 'Test Date'}]
        self.assertEqual(parse_rss_feed(self.sample_xml, 'Test Category'), expected_output)

    def test_get_weekly_file_path(self):
        year, week = 2024, 20
        expected_path = os.path.join(self.test_dir, 'news_2024_20.json')
        self.assertEqual(get_weekly_file_path(self.test_dir, year, week), expected_path)

    def test_load_config(self):
        config = load_config(self.config_path)
        self.assertEqual(config, self.config_data)

    def test_get_current_year_and_week(self):
        current_date = datetime.now()
        year, week, _ = current_date.isocalendar()
        test_year, test_week = get_current_year_and_week()
        self.assertEqual((test_year, test_week), (year, week))

    def test_load_existing_news_data(self):
        with open(self.test_file, 'w') as file:
            json.dump(self.sample_data, file)
        existing_data, existing_ids = load_existing_news_data(self.test_file)
        self.assertEqual(existing_data, self.sample_data)
        self.assertEqual(existing_ids, {'1'})

    def test_add_new_items(self):
        new_items = [{'id': '2', 'title': 'New Title', 'description': 'New Description', 'category': 'Test Category', 'pub_date': 'New Date'}]
        existing_data = self.sample_data.copy()
        existing_ids = {'1'}
        added_count = add_new_items(new_items, existing_data, existing_ids)
        self.assertEqual(added_count, 1)
        self.assertEqual(len(existing_data), 2)
        self.assertEqual(existing_data[-1]['id'], '2')

    @patch('src.rss_scraper.requests.get')
    def test_main_function(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.sample_xml
        mock_get.return_value = mock_response
        
        main(self.config_path)
        
        with open(self.log_file, 'r') as file:
            log_content = file.read()
        self.assertIn("Script completed successfully", log_content)

if __name__ == '__main__':
    unittest.main()
