# tests/test_rss_scraper.py

import unittest
from src.rss_scraper import load_existing_data, save_data, clean_html, parse_rss_feed, get_weekly_file_path
import os
import json

class TestRSSScraper(unittest.TestCase):

    def setUp(self):
        # Setup a temporary directory and test files
        self.test_dir = 'test_data'
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_file = os.path.join(self.test_dir, 'test.json')
        self.sample_data = [{'id': '1', 'title': 'Test Title', 'description': 'Test Description', 'category': 'Test Category', 'pub_date': 'Test Date'}]

    def tearDown(self):
        # Cleanup the temporary directory and files
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_load_existing_data(self):
        # Test loading existing data from a file
        with open(self.test_file, 'w') as file:
            json.dump(self.sample_data, file)
        data = load_existing_data(self.test_file)
        self.assertEqual(data, self.sample_data)

    def test_save_data(self):
        # Test saving data to a file
        save_data(self.test_file, self.sample_data)
        with open(self.test_file, 'r') as file:
            data = json.load(file)
        self.assertEqual(data, self.sample_data)

    def test_clean_html(self):
        # Test cleaning HTML content
        raw_html = "<p>This is a <b>test</b> description.</p>"
        expected_text = "This is a test description."
        self.assertEqual(clean_html(raw_html), expected_text)

    def test_parse_rss_feed(self):
        # Test parsing RSS feed XML data
        sample_xml = """
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
        expected_output = [{'id': '1', 'title': 'Test Title', 'description': 'Test Description', 'category': 'Test Category', 'pub_date': 'Test Date'}]
        self.assertEqual(parse_rss_feed(sample_xml, 'Test Category'), expected_output)

    def test_get_weekly_file_path(self):
        # Test generating the weekly file path
        year, week = 2024, 20
        expected_path = os.path.join(self.test_dir, 'news_2024_20.json')
        self.assertEqual(get_weekly_file_path(self.test_dir, year, week), expected_path)

if __name__ == '__main__':
    unittest.main()
