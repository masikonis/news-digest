import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from src.summary_generator import (
    get_latest_json_file,
    read_json_file,
    sort_by_category,
    generate_summary,
    generate_summaries_by_category
)

class TestSummaryGenerator(unittest.TestCase):

    def setUp(self):
        self.sample_news_items = [
            {"title": "News 1", "description": "Description 1", "category": "Politics"},
            {"title": "News 2", "description": "Description 2", "category": "Technology"},
            {"title": "News 3", "description": "Description 3", "category": "Politics"},
        ]

    def test_get_latest_json_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "file1.json")
            file2 = os.path.join(temp_dir, "file2.json")
            open(file1, 'a').close()
            open(file2, 'a').close()

            os.utime(file1, (0, 100))
            os.utime(file2, (0, 200))

            self.assertEqual(get_latest_json_file(temp_dir), file2)

    def test_get_latest_json_file_no_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(FileNotFoundError):
                get_latest_json_file(temp_dir)

    def test_read_json_file(self):
        test_data = [{"key": "value"}]
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as temp_file:
            json.dump(test_data, temp_file)
            temp_file_path = temp_file.name

        try:
            self.assertEqual(read_json_file(temp_file_path), test_data)
        finally:
            os.remove(temp_file_path)

    def test_sort_by_category(self):
        result = sort_by_category(self.sample_news_items)
        self.assertEqual(set(result.keys()), {"Politics", "Technology"})
        self.assertEqual(len(result["Politics"]), 2)
        self.assertEqual(len(result["Technology"]), 1)

    @patch('src.summary_generator.model')
    def test_generate_summary(self, mock_model):
        mock_response = MagicMock()
        mock_response.content = "Test summary"
        mock_model.invoke.return_value = mock_response

        news_items = [{"title": "Test", "description": "Test description"}]
        summary = generate_summary(news_items)

        self.assertEqual(summary, "Test summary")
        mock_model.invoke.assert_called_once()

    @patch('src.summary_generator.os.path.exists')
    @patch('src.summary_generator.os.makedirs')
    @patch('src.summary_generator.setup_logging')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.get_latest_json_file')
    @patch('src.summary_generator.read_json_file')
    @patch('src.summary_generator.generate_summary')
    def test_generate_summaries_by_category_full(self, mock_generate_summary, mock_read_json_file, 
                                                 mock_get_latest_json_file, mock_load_config, 
                                                 mock_setup_logging, mock_makedirs, mock_exists):
        # Setup mocks
        mock_load_config.return_value = {"base_folder": "test_folder", "log_file": "test.log"}
        mock_get_latest_json_file.return_value = "test_file.json"
        mock_read_json_file.return_value = [
            {"title": "News 1", "description": "Description 1", "category": "Politics"},
            {"title": "News 2", "description": "Description 2", "category": "Technology"},
            {"title": "News 3", "description": "Description 3", "category": "Uncategorized"},
        ]
        mock_generate_summary.side_effect = ["Politics summary", "Technology summary", "Uncategorized summary"]
        mock_exists.return_value = False

        # Call the function
        result = generate_summaries_by_category("test_config.json")

        # Assertions
        self.assertEqual(result, {
            "Politics": "Politics summary",
            "Technology": "Technology summary",
            "Uncategorized": "Uncategorized summary"
        })
        mock_load_config.assert_called_once_with("test_config.json")
        mock_get_latest_json_file.assert_called_once()
        mock_read_json_file.assert_called_once()
        self.assertEqual(mock_generate_summary.call_count, 3)
        mock_makedirs.assert_called_once()
        mock_setup_logging.assert_called_once()

    @patch('src.summary_generator.logging.error')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.get_latest_json_file')
    def test_generate_summaries_by_category_file_not_found(self, mock_get_latest_json_file, mock_load_config, mock_logging_error):
        mock_load_config.return_value = {"base_folder": "test_folder", "log_file": "test.log"}
        mock_get_latest_json_file.side_effect = FileNotFoundError("No JSON files found")

        result = generate_summaries_by_category("test_config.json")

        self.assertEqual(result, {})
        mock_logging_error.assert_called_once()
        error_message = mock_logging_error.call_args[0][0]
        self.assertIsInstance(error_message, FileNotFoundError)
        self.assertEqual(str(error_message), "No JSON files found")

    @patch('src.summary_generator.logging.error')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.get_latest_json_file')
    def test_generate_summaries_by_category_unexpected_error(self, mock_get_latest_json_file, mock_load_config, mock_logging_error):
        mock_load_config.return_value = {"base_folder": "test_folder", "log_file": "test.log"}
        mock_get_latest_json_file.side_effect = Exception("Unexpected error")

        result = generate_summaries_by_category("test_config.json")

        self.assertEqual(result, {})
        mock_logging_error.assert_called_once_with("An unexpected error occurred: Unexpected error")

if __name__ == "__main__":
    unittest.main()
