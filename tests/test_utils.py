# tests/test_utils.py
import unittest
from unittest.mock import patch, mock_open
import logging
import os
import json
from src.utils import setup_logging, load_config

class TestUtils(unittest.TestCase):
    @patch('os.path.abspath')
    @patch('logging.basicConfig')
    def test_setup_logging(self, mock_basicConfig, mock_abspath):
        mock_abspath.return_value = '/path/to/logfile.log'
        
        setup_logging('logfile.log')
        
        mock_abspath.assert_called_once_with('logfile.log')
        mock_basicConfig.assert_called_once_with(
            filename='/path/to/logfile.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )

    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_config(self, mock_file):
        config_path = 'config.json'
        expected_output = {"key": "value"}
        
        result = load_config(config_path)
        
        self.assertEqual(result, expected_output)
        mock_file.assert_called_once_with(config_path, 'r')

if __name__ == "__main__":
    unittest.main()
