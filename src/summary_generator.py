# src/summary_generator.py
import os
import glob
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from langchain.schema import HumanMessage
from model_initializer import initialize_model
from utils import setup_logging, load_config
from difflib import SequenceMatcher

model = initialize_model('summary')

def get_latest_json_file(directory: str) -> str:
    json_files = glob.glob(os.path.join(directory, "*.json"))
    if not json_files:
        raise FileNotFoundError("No JSON files found in the directory.")
    return max(json_files, key=os.path.getmtime)

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r') as file:
        return json.load(file)

def sort_by_category(news_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    categorized_news = {}
    for item in news_items:
        category = item.get('category', 'Uncategorized')
        if category not in categorized_news:
            categorized_news[category] = []
        categorized_news[category].append(item)
    return categorized_news

def generate_summary(news_items: List[Dict[str, Any]]) -> str:
    prompt = (
        "Tu esi dirbtinio intelekto naujienų apžvalgininkas. Apibendrink šias naujienas į vieną glaustą paragrafą, "
        "apie 120 žodžių, pabrėždamas svarbiausius momentus ir labiausiai įtakojančius įvykius. Šis apibendrinimas skirtas žmogui, kuris nesekė naujienų ir nori sužinoti "
        "svarbiausius įvykius per savaitę. Pasirink ir pabrėžk tik pačius svarbiausius ir įtakingiausius įvykius, paversdamas naujienas rišliu ir nuosekliu pasakojimu:\n\n"
    )
    
    for item in news_items:
        # Use AI summary if available, otherwise fall back to description
        if 'ai_summary' in item:
            prompt += f"- {item['title']}:\n{item['ai_summary']}\n\n"
        else:
            prompt += f"- {item['title']}: {item['description']}\n"
            
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content

def similar_titles(title1: str, title2: str, threshold: float = 0.8) -> bool:
    """Check if two titles are similar using fuzzy string matching."""
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio() > threshold

def deduplicate_news_items(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate news items, keeping the most detailed version."""
    unique_news = []
    seen_titles = set()
    
    logging.info(f"Starting deduplication of {len(news_items)} news items")
    
    # Sort by AI summary length to prioritize more detailed versions
    sorted_news = sorted(
        news_items,
        key=lambda x: len(x.get('ai_summary', '')) if isinstance(x.get('ai_summary', ''), str) else 0,
        reverse=True
    )
    
    for item in sorted_news:
        title = item['title']
        duplicates = [seen_title for seen_title in seen_titles if similar_titles(title, seen_title)]
        
        if duplicates:
            logging.info(f"Found duplicate: '{title}' is similar to existing title: '{duplicates[0]}'")
            continue
            
        seen_titles.add(title)
        unique_news.append(item)
    
    logging.info(f"Deduplication complete. Reduced from {len(news_items)} to {len(unique_news)} items")
    return unique_news

def generate_summaries_by_category(config_path: str) -> Dict[str, str]:
    config = load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    root_dir = os.path.abspath(os.path.join(config_dir, ".."))
    log_file = os.path.join(root_dir, config.get("log_file", "output.log"))
    log_dir = os.path.dirname(log_file)
    
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    setup_logging(log_file)

    base_folder = os.path.join(root_dir, config.get("base_folder", "weekly_news"))

    summaries_by_category = {}
    try:
        latest_file = get_latest_json_file(base_folder)
        logging.info(f"Latest JSON file: {latest_file}")

        news_data = read_json_file(latest_file)
        news_data = deduplicate_news_items(news_data)
        categorized_news = sort_by_category(news_data)

        for category, items in categorized_news.items():
            logging.info(f"Processing category: {category}")
            summary = generate_summary(items)
            summaries_by_category[category] = summary

    except FileNotFoundError as e:
        logging.error(e)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return summaries_by_category

def main(config_path: str):
    summaries = generate_summaries_by_category(config_path)
    for category, summary in summaries.items():
        print(f"\n{category}\n{summary}")

if __name__ == "__main__":
    main("src/config.json")
