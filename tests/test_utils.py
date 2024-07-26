# tests/test_utils.py
import unittest
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from src.utils import setup_logging, load_config

class TestUtils(unittest.TestCase):
    
    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    @patch("logging.FileHandler")
    @patch("logging.basicConfig")
    def test_setup_logging_creates_directory(self, mock_basicConfig, mock_fileHandler, mock_exists, mock_makedirs):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            setup_logging(log_file)
            mock_exists.assert_called_once_with(temp_dir)
            mock_makedirs.assert_called_once_with(temp_dir)
            mock_fileHandler.assert_called_once_with(log_file)
            mock_basicConfig.assert_called_once()

    @patch("os.path.exists", return_value=True)
    @patch("logging.FileHandler")
    @patch("logging.basicConfig")
    def test_setup_logging_existing_directory(self, mock_basicConfig, mock_fileHandler, mock_exists):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            setup_logging(log_file)
            mock_exists.assert_called_once_with(temp_dir)
            mock_fileHandler.assert_called_once_with(log_file)
            mock_basicConfig.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_config_valid_json(self, mock_file):
        config_path = "config.json"
        config = load_config(config_path)
        mock_file.assert_called_once_with(config_path, 'r')
        self.assertEqual(config, {"key": "value"})

    @patch("builtins.open", new_callable=mock_open)
    def test_load_config_file_not_found(self, mock_file):
        mock_file.side_effect = FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            load_config("nonexistent.json")

    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    def test_load_config_invalid_json(self, mock_file):
        with self.assertRaises(ValueError):
            load_config("invalid.json")

if __name__ == "__main__":
    unittest.main()
