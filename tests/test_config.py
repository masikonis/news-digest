# tests/test_config.py
import unittest
from unittest.mock import patch, mock_open
import json
from src.utils import load_config

class TestConfig(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open, read_data='''
    {
        "categories": {
            "Ukraina": "https://www.lrt.lt/tema/rusijos-karas-pries-ukraina?rss",
            "Verslas": "https://www.lrt.lt/naujienos/verslas?rss",
            "Pasaulis": "https://www.lrt.lt/naujienos/pasaulyje?rss",
            "Lietuva": "https://www.lrt.lt/naujienos/lietuvoje?rss",
            "Marijampolė": "https://www.suvalkietis.lt/feed/"
        },
        "base_folder": "weekly_news",
        "retry_count": 3,
        "retry_delay": 2,
        "log_file": "output.log"
    }
    ''')
    def test_load_config(self, mock_file):
        config_path = 'config.json'
        expected_output = {
            "categories": {
                "Ukraina": "https://www.lrt.lt/tema/rusijos-karas-pries-ukraina?rss",
                "Verslas": "https://www.lrt.lt/naujienos/verslas?rss",
                "Pasaulis": "https://www.lrt.lt/naujienos/pasaulyje?rss",
                "Lietuva": "https://www.lrt.lt/naujienos/lietuvoje?rss",
                "Marijampolė": "https://www.suvalkietis.lt/feed/"
            },
            "base_folder": "weekly_news",
            "retry_count": 3,
            "retry_delay": 2,
            "log_file": "output.log"
        }
        
        result = load_config(config_path)
        
        self.assertEqual(result, expected_output)
        mock_file.assert_called_once_with(config_path, 'r')

if __name__ == "__main__":
    unittest.main()
