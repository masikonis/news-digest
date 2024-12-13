# tests/test_content_enricher.py
import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, call, mock_open
from bs4 import BeautifulSoup
from src.content_enricher import ContentEnricher
import requests

class TestContentEnricher(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            "base_folder": "test_folder",
            "content_enrichment": {
                "enabled": True,
                "scraping_delay": 0,
                "sources": {
                    "example.com": {
                        "selector": "div.article-content"
                    }
                }
            }
        }
        self.config_json = json.dumps(self.test_config)

    @patch('src.content_enricher.initialize_model')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.content_enricher.load_config')
    @patch('os.path.dirname')
    def test_initialization(self, mock_dirname, mock_load_config, mock_file, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_model = MagicMock()
        mock_init_model.return_value = mock_model
        
        # Mock the directory paths
        mock_dirname.side_effect = [
            '/path/to/script/dir',  # First call for script directory
            '/path/to/project/root'  # Second call for project root
        ]
        
        enricher = ContentEnricher("mock_config.json")
        
        # Update the assertion to match the absolute path
        expected_path = os.path.join('/path/to/project/root', "test_folder")
        self.assertEqual(enricher.base_folder, expected_path)
        mock_init_model.assert_called_once_with('basic', temperature=0.3, provider='gemini')

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.requests.get')
    @patch('src.content_enricher.load_config')
    def test_get_full_content_success(self, mock_load_config, mock_get, mock_init_model):
        mock_load_config.return_value = self.test_config
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = '<html><div class="article-content">Test content</div></html>'
        mock_get.return_value = mock_response
        
        enricher = ContentEnricher("mock_config.json")
        content = enricher.get_full_content("https://example.com/article")
        
        self.assertEqual(content, "Test content")
        mock_get.assert_called_once()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.requests.get')
    @patch('src.content_enricher.load_config')
    def test_get_full_content_unknown_domain(self, mock_load_config, mock_get, mock_init_model):
        mock_load_config.return_value = self.test_config
        enricher = ContentEnricher("mock_config.json")
        content = enricher.get_full_content("https://unknown-domain.com/article")
        
        self.assertIsNone(content)
        mock_get.assert_not_called()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.requests.get')
    @patch('src.content_enricher.load_config')
    def test_get_full_content_request_error(self, mock_load_config, mock_get, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_get.side_effect = requests.RequestException("Connection error")
        
        enricher = ContentEnricher("mock_config.json")
        content = enricher.get_full_content("https://example.com/article")
        
        self.assertIsNone(content)
        mock_get.assert_called_once()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.requests.get')
    @patch('src.content_enricher.load_config')
    def test_get_full_content_no_matching_selector(self, mock_load_config, mock_get, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_response = MagicMock()
        mock_response.text = '<html><div class="wrong-class">Test content</div></html>'
        mock_get.return_value = mock_response
        
        enricher = ContentEnricher("mock_config.json")
        content = enricher.get_full_content("https://example.com/article")
        
        self.assertIsNone(content)
        mock_get.assert_called_once()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.load_config')
    def test_generate_article_analysis(self, mock_load_config, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "AI generated summary"
        mock_model.invoke.return_value = mock_response
        mock_init_model.return_value = mock_model
        
        enricher = ContentEnricher("mock_config.json")
        summary = enricher.generate_article_analysis("Test Title", "Test Content")
        
        self.assertEqual(summary, "AI generated summary")
        mock_model.invoke.assert_called_once()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.load_config')
    @patch('builtins.open', new_callable=mock_open)
    def test_enrich_weekly_news_disabled(self, mock_file, mock_load_config, mock_init_model):
        # Modify config to disable enrichment
        disabled_config = self.test_config.copy()
        disabled_config["content_enrichment"]["enabled"] = False
        mock_load_config.return_value = disabled_config
        
        enricher = ContentEnricher("mock_config.json")
        enricher.enrich_weekly_news(2024, 1)
        
        mock_file.assert_not_called()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    def test_enrich_weekly_news_file_not_found(self, mock_load_config, mock_exists, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = False
        
        enricher = ContentEnricher("mock_config.json")
        enricher.enrich_weekly_news(2024, 1)
        
        mock_exists.assert_called_once()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    @patch('builtins.open', new_callable=mock_open)
    def test_enrich_weekly_news_success(self, mock_file, mock_load_config, mock_exists, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(content="AI summary")
        mock_init_model.return_value = mock_model
        
        # Mock the news items
        test_news = [
            {
                "id": "https://example.com/article1",
                "title": "Test Article 1"
            }
        ]
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(test_news)
        
        enricher = ContentEnricher("mock_config.json")
        with patch.object(enricher, 'get_full_content', return_value="Full content"):
            enricher.enrich_weekly_news(2024, 1)
        
        # Verify the enrichment process
        mock_exists.assert_called_once()
        mock_file.assert_called()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    @patch('builtins.open', new_callable=mock_open)
    def test_enrich_weekly_news_no_articles_to_process(self, mock_file, mock_load_config, mock_exists, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = True
        
        # All articles already processed
        test_news = [
            {
                "id": "https://example.com/article1",
                "title": "Test Article 1",
                "ai_summary": "Existing summary"
            }
        ]
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(test_news)
        
        enricher = ContentEnricher("mock_config.json")
        enricher.enrich_weekly_news(2024, 1)
        
        # Should only open file for reading, not writing
        self.assertEqual(mock_file.call_count, 1)

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    @patch('builtins.open', new_callable=mock_open)
    def test_enrich_weekly_news_content_fetch_failure(self, mock_file, mock_load_config, mock_exists, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = True
        
        # Mock file read operation
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps([
            {"id": "https://example.com/article1", "title": "Test Article 1"}
        ])
        
        enricher = ContentEnricher("mock_config.json")
        with patch.object(enricher, 'get_full_content', return_value=None):
            enricher.enrich_weekly_news(2024, 1)
        
        # Just verify that write was called
        mock_file.return_value.__enter__.return_value.write.assert_called()

    @patch('argparse.ArgumentParser')
    def test_parse_arguments(self, mock_parser_class):
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(config='test_config.json')
        mock_parser_class.return_value = mock_parser
        
        from src.content_enricher import parse_arguments
        args = parse_arguments()
        
        self.assertEqual(args.config, 'test_config.json')
        mock_parser.add_argument.assert_called_once_with(
            '--config', 
            type=str, 
            default='config.json',
            help='Path to the configuration file'
        )

    @patch('src.content_enricher.main')
    def test_run(self, mock_main):
        from src.content_enricher import run
        
        with patch('src.content_enricher.parse_arguments') as mock_parse_args:
            mock_parse_args.return_value = MagicMock(config='test_config.json')
            run()
            
        mock_main.assert_called_once_with('test_config.json')

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    @patch('builtins.open', new_callable=mock_open)
    def test_enrich_weekly_news_no_items_to_process(self, mock_file, mock_load_config, mock_exists, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = True
        
        # Mock empty news list
        mock_file.return_value.__enter__.return_value.read.return_value = '[]'
        
        enricher = ContentEnricher("mock_config.json")
        enricher.enrich_weekly_news(2024, 1)
        
        # Verify no write operations occurred
        mock_file.return_value.__enter__.return_value.write.assert_not_called()

    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_with_existing_file(self, mock_file, mock_load_config, mock_exists, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps([
            {"id": "test", "title": "test", "ai_summary": "existing"}
        ])
        
        from src.content_enricher import main
        main("test_config.json")
        
        mock_exists.assert_called()
        mock_file.assert_called()

    def test_run_function(self):
        with patch('src.content_enricher.parse_arguments') as mock_parse_args:
            with patch('src.content_enricher.main') as mock_main:
                mock_parse_args.return_value = MagicMock(config='test_config.json')
                
                from src.content_enricher import run
                run()
                
                mock_main.assert_called_once_with('test_config.json')

if __name__ == '__main__':
    unittest.main()
