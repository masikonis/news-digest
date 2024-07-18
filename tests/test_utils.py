import unittest
import os
import tempfile
import json
import logging
from unittest.mock import patch
from src.utils import setup_logging, load_config

class TestUtils(unittest.TestCase):

    def test_setup_logging(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, 'test.log')
            setup_logging(log_file)
            
            # Check if the log file is created
            self.assertTrue(os.path.exists(log_file))
            
            # Check if logging works
            logger = logging.getLogger('test_logger')
            handler = logging.FileHandler(log_file)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.info('This is a test log message')
            
            # Ensure all log messages are flushed and the file is closed
            handler.flush()
            handler.close()
            
            logging.shutdown()  # Ensure all log messages are flushed

            with open(log_file, 'r') as f:
                log_content = f.read()
            
            self.assertIn('This is a test log message', log_content)

    def test_load_config(self):
        config_data = {
            "key1": "value1",
            "key2": "value2"
        }
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as temp_config_file:
            json.dump(config_data, temp_config_file)
            temp_config_file_path = temp_config_file.name

        try:
            loaded_config = load_config(temp_config_file_path)
            self.assertEqual(loaded_config, config_data)
        finally:
            os.remove(temp_config_file_path)

if __name__ == "__main__":
    unittest.main()
