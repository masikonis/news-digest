import unittest
from unittest.mock import patch, MagicMock
import sys
import runpy
import os
import json

class TestMainExecution(unittest.TestCase):

    def setUp(self):
        # Create a temporary config file
        self.config_path = 'test_data/config.json'
        os.makedirs('test_data', exist_ok=True)
        config_data = {
            "categories": {
                "Test Category": "https://example.com/rss"
            },
            "base_folder": "test_data",
            "retry_count": 3,
            "retry_delay": 2,
            "log_file": "output.log"
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)

    def tearDown(self):
        # Clean up the temporary config file and directory
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        # Remove all files in the test_data directory
        for file in os.listdir('test_data'):
            file_path = os.path.join('test_data', file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        # Remove the test_data directory
        if os.path.exists('test_data'):
            os.rmdir('test_data')

    @patch('src.rss_scraper.run', new_callable=MagicMock)
    def test_if_main_executes_run(self, mock_run):
        # Patch sys.argv to simulate command line arguments
        with patch.object(sys, 'argv', ['src/rss_scraper.py', '--config', self.config_path]):
            # Reload the module to apply the mock
            import src.rss_scraper
            import importlib
            importlib.reload(src.rss_scraper)

            # Run the script
            runpy.run_path('src/rss_scraper.py', run_name="__main__")
        
        # Verify that the run function was called
        mock_run.assert_called_once()
        print(f"Mock run call count: {mock_run.call_count}")  # Debug print to verify mock call

if __name__ == "__main__":
    unittest.main()

