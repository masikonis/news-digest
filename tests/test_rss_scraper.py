# tests/test_rss_scraper.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
import requests
import xml.etree.ElementTree as ET
import argparse
from datetime import datetime, timedelta, timezone
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
    add_new_items,
    parse_arguments,
    run
)

# Ensure ZoneInfo is imported correctly
ZoneInfo = get_zoneinfo()

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

    @patch("os.path.exists", return_value=False)
    def test_load_existing_data_file_not_exist(self, mock_exists):
        data = load_existing_data("mock_path")
        self.assertEqual(data, [])

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

    @patch("requests.get")
    def test_scrape_rss_feed_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = """
        <rss>
            <channel>
                <item>
                    <title>Title 1</title>
                    <description><![CDATA[<p>Description 1</p>]]></description>
                    <guid>1</guid>
                    <pubDate>Mon, 25 Jul 2022 10:00:00 +0000</pubDate>
                </item>
                <item>
                    <title>Title 2</title>
                    <description><![CDATA[<p>Description 2</p>]]></description>
                    <guid>2</guid>
                    <pubDate>Mon, 25 Jul 2022 15:00:00 +0000</pubDate>
                </item>
            </channel>
        </rss>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        start_of_week = datetime(2022, 7, 25, tzinfo=ZoneInfo("Europe/Vilnius"))
        end_of_week = start_of_week + timedelta(days=7)

        results = scrape_rss_feed("http://example.com/rss", "Test Category", start_of_week, end_of_week)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Title 1')
        self.assertEqual(results[1]['title'], 'Title 2')

    @patch("os.makedirs")
    @patch("os.path.exists", side_effect=[False, True])
    def test_get_weekly_file_path(self, mock_exists, mock_makedirs):
        path = get_weekly_file_path("base_folder", 2023, 30)
        mock_exists.assert_called_with("base_folder")
        mock_makedirs.assert_called_once_with("base_folder")
        self.assertTrue(path.endswith("news_2023_30.json"))

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=True)
    def test_get_weekly_file_path_exists(self, mock_exists, mock_makedirs):
        path = get_weekly_file_path("base_folder", 2023, 30)
        mock_exists.assert_called_with("base_folder")
        mock_makedirs.assert_not_called()
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
    
    def test_date_time_encoder_direct_call(self):
        encoder = DateTimeEncoder()
        result = encoder.default("test_string")
        self.assertEqual(result, "test_string")

    def test_date_time_encoder_non_datetime(self):
        data = {'key': 'value'}
        encoded = json.dumps(data, cls=DateTimeEncoder)
        self.assertIn('"key": "value"', encoded)

    @patch.dict('sys.modules', {'zoneinfo': None})
    def test_get_zoneinfo_importerror(self):
        ZoneInfo = get_zoneinfo()
        self.assertTrue(hasattr(ZoneInfo, 'utcoffset'))

    def test_handle_request_exception(self):
        with patch('time.sleep') as mock_sleep, patch('logging.error') as mock_error, patch('logging.info') as mock_info:
            handle_request_exception(Exception("Test error"), "http://example.com/rss", 0, 3, 2)
            mock_error.assert_called_with("Error fetching http://example.com/rss: Test error")
            mock_info.assert_called_with("Retrying in 2 seconds...")

    def test_parse_rss_feed(self):
        xml_data = """
        <rss>
            <channel>
                <item>
                    <title>Title 1</title>
                    <description><![CDATA[<p>Description 1</p>]]></description>
                    <guid>1</guid>
                    <pubDate>Mon, 25 Jul 2022 10:00:00 +0000</pubDate>
                </item>
                <item>
                    <title>Title 2</title>
                    <description><![CDATA[<p>Description 2</p>]]></description>
                    <guid>2</guid>
                    <pubDate>Mon, 25 Jul 2022 15:00:00 +0000</pubDate>
                </item>
                <item>
                    <title>Title 3</title>
                    <description><![CDATA[<p>Description 3</p>]]></description>
                    <guid>3</guid>
                    <pubDate>Mon, 01 Aug 2022 10:00:00 +0000</pubDate>
                </item>
            </channel>
        </rss>
        """
        category = "Test Category"
        start_of_week = datetime(2022, 7, 25, tzinfo=ZoneInfo("Europe/Vilnius"))
        end_of_week = start_of_week + timedelta(days=7)

        result = parse_rss_feed(xml_data, category, start_of_week, end_of_week)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Title 1')
        self.assertEqual(result[1]['title'], 'Title 2')

    def test_parse_rss_item_value_error(self):
        item = ET.Element('item')
        ET.SubElement(item, 'title').text = "Title"
        ET.SubElement(item, 'description').text = "<p>Description</p>"
        ET.SubElement(item, 'guid').text = "123"
        ET.SubElement(item, 'pubDate').text = "Invalid Date"
        with self.assertLogs(level='ERROR') as cm:
            result = parse_rss_item(item, "category")
            self.assertIsNone(result)
            self.assertIn("ERROR:root:Unable to parse date: Invalid Date", cm.output[0])

    def test_parse_rss_item_missing_pub_date(self):
        item = ET.Element('item')
        ET.SubElement(item, 'title').text = "Title"
        ET.SubElement(item, 'description').text = "<p>Description</p>"
        ET.SubElement(item, 'guid').text = "123"
        result = parse_rss_item(item, "category")
        self.assertIsNone(result)

    @patch("src.rss_scraper.datetime")
    def test_get_current_year_and_week(self, mock_datetime):
        fixed_date = datetime(2023, 7, 25, tzinfo=ZoneInfo("Europe/Vilnius"))
        mock_datetime.now.return_value = fixed_date
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        year, week = get_current_year_and_week()
        self.assertEqual(year, 2023)
        self.assertEqual(week, 30)

    @patch("src.rss_scraper.load_existing_data")
    def test_load_existing_news_data(self, mock_load_existing_data):
        mock_load_existing_data.return_value = [
            {"id": "1", "title": "Title 1", "description": "Description 1", "category": "Category 1", "pub_date": datetime.now()},
            {"id": "2", "title": "Title 2", "description": "Description 2", "category": "Category 2", "pub_date": datetime.now()}
        ]
        existing_data, existing_ids = load_existing_news_data("mock_path")
        self.assertEqual(len(existing_data), 2)
        self.assertEqual(existing_ids, {"1", "2"})

    def test_add_new_items(self):
        existing_data = [
            {"id": "1", "title": "Title 1", "description": "Description 1", "category": "Category 1", "pub_date": datetime.now()}
        ]
        existing_ids = {"1"}
        new_items = [
            {"id": "2", "title": "Title 2", "description": "Description 2", "category": "Category 2", "pub_date": datetime.now()},
            {"id": "3", "title": "Title 3", "description": "Description 3", "category": "Category 3", "pub_date": datetime.now()},
            {"id": "1", "title": "Title 1", "description": "Description 1", "category": "Category 1", "pub_date": datetime.now()}  # Duplicate
        ]
        new_items_count = add_new_items(new_items, existing_data, existing_ids)
        self.assertEqual(new_items_count, 2)
        self.assertEqual(len(existing_data), 3)
        self.assertEqual(existing_ids, {"1", "2", "3"})

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

    @patch('argparse.ArgumentParser.parse_args',
           return_value=argparse.Namespace(config='test_config.json'))
    def test_parse_arguments(self, mock_parse_args):
        args = parse_arguments()
        self.assertEqual(args.config, 'test_config.json')

    @patch("src.rss_scraper.parse_arguments", return_value=argparse.Namespace(config='test_config.json'))
    @patch("src.rss_scraper.main")
    def test_run(self, mock_main, mock_parse_arguments):
        run()
        mock_parse_arguments.assert_called_once()
        mock_main.assert_called_once_with('test_config.json')

    @patch.dict('sys.modules', {'zoneinfo': None})
    def test_zoneinfo_fallback(self):
        ZoneInfo = get_zoneinfo()
        zi = ZoneInfo("Europe/Vilnius")
        self.assertEqual(zi.name, "Europe/Vilnius")
        self.assertEqual(zi.utcoffset(None), timezone(timedelta(hours=2)).utcoffset(None))
        self.assertEqual(zi.dst(None), timedelta(0))
        self.assertEqual(zi.tzname(None), "Europe/Vilnius")

if __name__ == "__main__":
    unittest.main()
