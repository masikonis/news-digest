# tests/test_summary_generator.py
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
from datetime import datetime
from src.summary_generator import (
    get_latest_json_file,
    read_json_file,
    sort_by_category,
    generate_summary,
    generate_summaries_by_category
)
from langchain.schema import HumanMessage

class TestSummaryGenerator(unittest.TestCase):
    @patch('src.summary_generator.glob.glob')
    @patch('src.summary_generator.os.path.getmtime')
    def test_get_latest_json_file(self, mock_getmtime, mock_glob):
        mock_glob.return_value = ['/path/to/file1.json', '/path/to/file2.json']
        mock_getmtime.side_effect = [100, 200]
        
        latest_file = get_latest_json_file('/path/to')
        self.assertEqual(latest_file, '/path/to/file2.json')

    @patch('builtins.open', new_callable=mock_open, read_data='[{"key": "value"}]')
    def test_read_json_file(self, mock_file):
        file_path = '/path/to/file.json'
        data = read_json_file(file_path)
        self.assertEqual(data, [{"key": "value"}])
        mock_file.assert_called_once_with(file_path, 'r')

    def test_sort_by_category(self):
        news_items = [
            {'category': 'Tech', 'title': 'Tech News 1'},
            {'category': 'Tech', 'title': 'Tech News 2'},
            {'category': 'Health', 'title': 'Health News 1'},
            {'title': 'Uncategorized News'}
        ]
        expected_output = {
            'Tech': [
                {'category': 'Tech', 'title': 'Tech News 1'},
                {'category': 'Tech', 'title': 'Tech News 2'}
            ],
            'Health': [{'category': 'Health', 'title': 'Health News 1'}],
            'Uncategorized': [{'title': 'Uncategorized News'}]
        }
        self.assertEqual(sort_by_category(news_items), expected_output)

    @patch('src.summary_generator.model')
    def test_generate_summary(self, mock_model):
        mock_response = MagicMock()
        mock_response.content = 'Summary content'
        mock_model.invoke.return_value = mock_response

        news_items = [
            {'title': 'Title 1', 'description': 'Description 1'},
            {'title': 'Title 2', 'description': 'Description 2'}
        ]
        summary = generate_summary(news_items)
        self.assertEqual(summary, 'Summary content')
        mock_model.invoke.assert_called_once()

    @patch('src.summary_generator.get_latest_json_file')
    @patch('src.summary_generator.read_json_file')
    @patch('src.summary_generator.sort_by_category')
    @patch('src.summary_generator.generate_summary')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.setup_logging')
    def test_generate_summaries_by_category(self, mock_setup_logging, mock_load_config, mock_generate_summary, mock_sort_by_category, mock_read_json_file, mock_get_latest_json_file):
        mock_load_config.return_value = {
            "base_folder": "/path/to",
            "log_file": "/path/to/logfile.log"
        }
        mock_get_latest_json_file.return_value = '/path/to/file.json'
        mock_read_json_file.return_value = [{'category': 'Tech', 'title': 'Tech News', 'description': 'Tech Description'}]
        mock_sort_by_category.return_value = {'Tech': [{'category': 'Tech', 'title': 'Tech News', 'description': 'Tech Description'}]}
        mock_generate_summary.return_value = 'Tech summary'

        summaries = generate_summaries_by_category('config_path')
        self.assertEqual(summaries, {'Tech': 'Tech summary'})

        mock_setup_logging.assert_called_once_with("/path/to/logfile.log")
        mock_load_config.assert_called_once_with('config_path')
        mock_get_latest_json_file.assert_called_once_with("/path/to")
        mock_read_json_file.assert_called_once_with('/path/to/file.json')
        mock_sort_by_category.assert_called_once_with([{'category': 'Tech', 'title': 'Tech News', 'description': 'Tech Description'}])
        mock_generate_summary.assert_called_once_with([{'category': 'Tech', 'title': 'Tech News', 'description': 'Tech Description'}])

if __name__ == "__main__":
    unittest.main()
