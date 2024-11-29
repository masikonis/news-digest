# tests/test_summary_generator.py

import unittest
import os
import tempfile
import json
import logging
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from src.summary_generator import (
    get_latest_json_file,
    read_json_file,
    sort_by_category,
    generate_summary,
    generate_summaries_by_category,
    main,
    deduplicate_news_items,
    evaluate_story_importance,
    cosine_similarity,
    similar_titles,
)

class TestSummaryGenerator(unittest.TestCase):

    def setUp(self):
        self.sample_news_items = [
            {
                "title": "News 1",
                "description": "Description 1",
                "category": "Politics",
                "pub_date": datetime(2023, 1, 1)
            },
            {
                "title": "News 2",
                "description": "Description 2",
                "category": "Technology",
                "pub_date": datetime(2023, 1, 2)
            },
            {
                "title": "News 3",
                "description": "Description 3",
                "category": "Politics",
                "pub_date": datetime(2023, 1, 3)
            },
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

    @patch('src.summary_generator.embeddings_model')
    @patch('src.summary_generator.similar_titles')
    def test_deduplicate_news_items(self, mock_similar_titles, mock_embeddings_model):
        duplicate_news = [
            {"title": "Same News", "description": "Description 1", "category": "Politics", "ai_summary": "Long summary"},
            {"title": "Same News", "description": "Description 2", "category": "Politics", "ai_summary": "Short"},
            {"title": "Different News", "description": "Description 3", "category": "Politics"},
        ]
        # Mock similar_titles to return True when titles are the same, False otherwise
        def mock_similar_titles_func(x, y, threshold=0.8):
            return x == y
        mock_similar_titles.side_effect = mock_similar_titles_func

        # Mock embeddings_model.embed_query to return embeddings with low similarity for different titles
        def mock_embed_query(title):
            if title == "Same News":
                return [1.0, 0.0, 0.0]
            elif title == "Different News":
                return [0.0, 1.0, 0.0]
            else:
                return [0.0, 0.0, 1.0]
        mock_embeddings_model.embed_query.side_effect = mock_embed_query

        result = deduplicate_news_items(duplicate_news)
        self.assertEqual(len(result), 2)  # Should keep only unique stories
        self.assertEqual(result[0]['ai_summary'], "Long summary")
        self.assertEqual(result[0]['title'], "Same News")
        self.assertEqual(result[1]['title'], "Different News")

    @patch('src.summary_generator.model')
    def test_evaluate_story_importance(self, mock_model):
        news_items = [
            {
                "title": f"News {i}",
                "description": f"Description {i}",
                "category": "Politics",
                "pub_date": datetime(2023, 1, i + 1)
            }
            for i in range(20)
        ]
        mock_response = MagicMock()
        # Simulate importance scores cycling from 10 down to 1
        scores = "\n".join(f"{i+1}:{10 - (i % 10)}" for i in range(len(news_items)))
        mock_response.content = scores
        mock_model.invoke.return_value = mock_response
        result = evaluate_story_importance(news_items, "Politics")
        # Should return between min_stories and max_stories
        self.assertGreaterEqual(len(result), 7)
        self.assertLessEqual(len(result), 14)
        # Check that the top item has the highest score and latest date
        self.assertEqual(result[0]['title'], 'News 10')  # Correct highest score item

    @patch('src.summary_generator.embeddings_model')
    @patch('src.summary_generator.model')
    @patch('src.summary_generator.os.path.exists')
    @patch('src.summary_generator.os.makedirs')
    @patch('src.summary_generator.setup_logging')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.get_latest_json_file')
    @patch('src.summary_generator.read_json_file')
    @patch('src.summary_generator.evaluate_story_importance')
    @patch('src.summary_generator.deduplicate_news_items')
    def test_generate_summaries_by_category_full(
        self, mock_deduplicate, mock_evaluate_importance, mock_read_json_file, 
        mock_get_latest_json_file, mock_load_config, mock_setup_logging, 
        mock_makedirs, mock_exists, mock_model, mock_embeddings_model
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup mocks with proper return values
            mock_load_config.return_value = {
                "base_folder": temp_dir,
                "log_file": os.path.join(temp_dir, "test.log")
            }
            mock_exists.return_value = True
            mock_get_latest_json_file.return_value = os.path.join(temp_dir, "test_file.json")

            test_news = [
                {"title": "News 1", "description": "Description 1", "category": "Politics", "pub_date": datetime(2023, 1, 1)},
                {"title": "News 2", "description": "Description 2", "category": "Technology", "pub_date": datetime(2023, 1, 2)},
                {"title": "News 3", "description": "Description 3", "category": "Uncategorized", "pub_date": datetime(2023, 1, 3)},
            ]
            mock_read_json_file.return_value = test_news
            
            # Make sure deduplication returns all items
            mock_deduplicate.side_effect = lambda x: x
            
            # Make sure evaluation returns all items for each category
            mock_evaluate_importance.side_effect = lambda items, category: [
                item for item in items if item['category'] == category
            ]

            # Mock embeddings_model.embed_query
            mock_embeddings_model.embed_query.side_effect = lambda title: [1.0, 0.0, 0.0]

            # Mock model.invoke for generate_summary
            mock_response = MagicMock()
            mock_response.content = "Test summary"
            mock_model.invoke.return_value = mock_response

            # Mock generate_summary
            def mock_generate_summary(news_items):
                if not news_items:  # Add debug logging
                    logging.debug("Empty news items passed to generate_summary")
                    return "Empty summary"
                category = news_items[0]['category']
                return f"Summary for {category}"

            with patch('src.summary_generator.generate_summary', side_effect=mock_generate_summary):
                result = generate_summaries_by_category("test_config.json")

                expected_result = {
                    "Politics": "Summary for Politics",
                    "Technology": "Summary for Technology",
                    "Uncategorized": "Summary for Uncategorized"
                }

                # Add debug output
                print(f"Expected: {expected_result}")
                print(f"Got: {result}")

                self.assertEqual(result, expected_result)

                # Verify the important mock calls
                mock_load_config.assert_called_once()
                mock_get_latest_json_file.assert_called_once()
                mock_read_json_file.assert_called_once()
                mock_evaluate_importance.assert_called()
                mock_deduplicate.assert_called_once()

    @patch('src.summary_generator.logging.error')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.get_latest_json_file')
    def test_generate_summaries_by_category_file_not_found(self, mock_get_latest_json_file, mock_load_config, mock_logging_error):
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_load_config.return_value = {"base_folder": temp_dir, "log_file": os.path.join(temp_dir, "test.log")}
            mock_get_latest_json_file.side_effect = FileNotFoundError("No JSON files found in the directory.")

            result = generate_summaries_by_category("test_config.json")

            self.assertEqual(result, {})
            mock_logging_error.assert_called_once()
            error_message = mock_logging_error.call_args[0][0]
            self.assertEqual(str(error_message), "No JSON files found in the directory.")

    @patch('src.summary_generator.logging.error')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.get_latest_json_file')
    def test_generate_summaries_by_category_unexpected_error(self, mock_get_latest_json_file, mock_load_config, mock_logging_error):
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_load_config.return_value = {"base_folder": temp_dir, "log_file": os.path.join(temp_dir, "test.log")}
            mock_get_latest_json_file.side_effect = Exception("Unexpected error")

            result = generate_summaries_by_category("test_config.json")

            self.assertEqual(result, {})
            mock_logging_error.assert_called_once_with("An unexpected error occurred: Unexpected error")

    @patch('builtins.print')
    @patch('src.summary_generator.generate_summaries_by_category')
    @patch('src.summary_generator.load_config')
    def test_main(self, mock_load_config, mock_generate_summaries_by_category, mock_print):
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_generate_summaries_by_category.return_value = {
                "Politics": "Politics summary",
                "Technology": "Technology summary"
            }
            mock_load_config.return_value = {"base_folder": temp_dir, "log_file": os.path.join(temp_dir, "test.log")}

            main("src/config.json")

            mock_generate_summaries_by_category.assert_called_once_with("src/config.json")
            mock_print.assert_any_call("\nPolitics\nPolitics summary")
            mock_print.assert_any_call("\nTechnology\nTechnology summary")

    def test_generate_summary_empty_content(self):
        """Test generate_summary with empty content"""
        news_items = [
            {"title": "Test", "description": "", "ai_summary": ""}
        ]
        with patch('src.summary_generator.model') as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Empty summary"
            mock_model.invoke.return_value = mock_response
            summary = generate_summary(news_items)
            self.assertEqual(summary, "Empty summary")

    def test_cosine_similarity_zero_vectors(self):
        """Test cosine_similarity with zero vectors"""
        v1 = [0, 0, 0]
        v2 = [1, 1, 1]
        self.assertEqual(cosine_similarity(v1, v2), 0)

    def test_similar_titles_edge_cases(self):
        """Test similar_titles with various cases"""
        self.assertTrue(similar_titles("Same Title", "same title"))
        self.assertFalse(similar_titles("Different", "Title"))
        self.assertTrue(similar_titles("Almost Same Title", "Almost Same Title!"))

    def test_evaluate_story_importance_invalid_response(self):
        """Test evaluate_story_importance with invalid AI response"""
        news_items = [
            {
                "title": "News 1",
                "description": "Description 1",
                "category": "Politics",
                "pub_date": datetime(2023, 1, 1)
            }
        ]
        with patch('src.summary_generator.model') as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Invalid:Format"  # Invalid format
            mock_model.invoke.return_value = mock_response
            result = evaluate_story_importance(news_items, "Politics")
            self.assertEqual(len(result), 1)  # Should fall back to date-based sorting

    @patch('src.summary_generator.model')
    def test_evaluate_story_importance_empty_scores(self, mock_model):
        """Test evaluate_story_importance with empty scores"""
        news_items = [
            {
                "title": "News 1",
                "description": "Description 1",
                "category": "Politics",
                "pub_date": datetime(2023, 1, 1)
            }
        ]
        mock_response = MagicMock()
        mock_response.content = ""  # Empty response
        mock_model.invoke.return_value = mock_response
        result = evaluate_story_importance(news_items, "Politics")
        self.assertEqual(len(result), 1)  # Should fall back to date-based sorting

    @patch('src.summary_generator.model')
    def test_evaluate_story_importance_exception(self, mock_model):
        """Test evaluate_story_importance with exception"""
        news_items = [
            {
                "title": "News 1",
                "description": "Description 1",
                "category": "Politics",
                "pub_date": datetime(2023, 1, 1)
            }
        ]
        # Set up the exception
        mock_model.invoke.side_effect = Exception("Model error")
        
        # Call the function
        result = evaluate_story_importance(news_items, "Politics")
        
        # Verify results
        self.assertEqual(len(result), 1)  # Should fall back to date-based sorting

    @patch('src.summary_generator.logging')
    @patch('src.summary_generator.load_config')
    @patch('src.summary_generator.setup_logging')
    def test_generate_summaries_by_category_invalid_config(self, mock_setup_logging, mock_load_config, mock_logging):
        """Test generate_summaries_by_category with invalid config"""
        # Return a basic config first to set up the function
        mock_load_config.return_value = {
            "base_folder": "test_folder",
            "log_file": "test.log"
        }
        
        # Then make it raise an exception on the actual call
        mock_load_config.side_effect = [
            {"base_folder": "test_folder", "log_file": "test.log"},
            Exception("Invalid config")
        ]
        
        # Call the function
        result = generate_summaries_by_category("invalid_config.json")
        
        # Verify results
        self.assertEqual(result, {})

    @patch('src.summary_generator.model')
    def test_evaluate_story_importance_min_max_stories(self, mock_model):
        """Test evaluate_story_importance with different story counts"""
        # Test with fewer stories than min_stories
        news_items_few = [
            {
                "title": f"News {i}",
                "description": f"Description {i}",
                "category": "Politics",
                "pub_date": datetime(2023, 1, i + 1)
            }
            for i in range(5)  # Less than min_stories
        ]
        result_few = evaluate_story_importance(news_items_few, "Politics")
        self.assertEqual(len(result_few), 5)  # Should return all stories

        # Test with more stories than max_stories
        news_items_many = [
            {
                "title": f"News {i}",
                "description": f"Description {i}",
                "category": "Politics",
                "pub_date": datetime(2023, 1, i + 1)
            }
            for i in range(20)  # More than max_stories
        ]
        mock_response = MagicMock()
        scores = "\n".join(f"{i+1}:5" for i in range(20))
        mock_response.content = scores
        mock_model.invoke.return_value = mock_response
        result_many = evaluate_story_importance(news_items_many, "Politics")
        self.assertLessEqual(len(result_many), 14)  # Should not exceed max_stories

    def test_sort_by_category_empty_list(self):
        """Test sort_by_category with empty list"""
        result = sort_by_category([])
        self.assertEqual(result, {})

    def test_sort_by_category_missing_category(self):
        """Test sort_by_category with missing category"""
        news_items = [{"title": "Test", "description": "Test"}]
        result = sort_by_category(news_items)
        self.assertEqual(result, {"Uncategorized": news_items})

    def test_cosine_similarity_empty_vectors(self):
        """Test cosine_similarity with empty vectors"""
        self.assertEqual(cosine_similarity([], []), 0)

    def test_generate_summary_empty_list(self):
        """Test generate_summary with empty list"""
        with patch('src.summary_generator.model') as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Empty summary"
            mock_model.invoke.return_value = mock_response
            result = generate_summary([])
            self.assertEqual(result, "Empty summary")

    @patch('src.summary_generator.model')
    def test_evaluate_story_importance_empty_list(self, mock_model):
        """Test evaluate_story_importance with empty list"""
        result = evaluate_story_importance([], "Politics")
        self.assertEqual(result, [])

    def test_deduplicate_news_items_empty_list(self):
        """Test deduplicate_news_items with empty list"""
        result = deduplicate_news_items([])
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
