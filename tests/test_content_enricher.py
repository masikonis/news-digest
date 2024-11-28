# tests/test_content_enricher.py
import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, call, mock_open
from bs4 import BeautifulSoup
from src.content_enricher import ContentEnricher

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
    def test_initialization(self, mock_load_config, mock_file, mock_init_model):
        mock_load_config.return_value = self.test_config
        mock_model = MagicMock()
        mock_init_model.return_value = mock_model
        
        enricher = ContentEnricher("mock_config.json")
        
        self.assertEqual(enricher.base_folder, "test_folder")
        self.assertTrue(enricher.enrichment_config["enabled"])
        mock_init_model.assert_called_once_with('basic', temperature=0.3)

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

    @patch('src.content_enricher.logging')
    @patch('src.content_enricher.initialize_model')
    @patch('src.content_enricher.os.path.exists')
    @patch('src.content_enricher.load_config')
    def test_main_function(self, mock_load_config, mock_exists, mock_init_model, mock_logging):
        mock_load_config.return_value = self.test_config
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data='[]')):
            from src.content_enricher import main
            main("mock_config.json")
        
        mock_logging.basicConfig.assert_called_once()
        mock_exists.assert_called()

if __name__ == '__main__':
    unittest.main()
