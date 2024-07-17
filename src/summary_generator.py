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

model = initialize_model()

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
        "apie 90 žodžių, pabrėždamas svarbiausius momentus ir labiausiai įtakojančius įvykius. Šis apibendrinimas skirtas žmogui, kuris nesekė naujienų ir nori sužinoti "
        "svarbiausius įvykius per savaitę. Pasirink ir pabrėžk tik pačius svarbiausius ir įtakingiausius įvykius, paversdamas naujienas rišliu ir nuosekliu pasakojimu:\n"
    )
    for item in news_items:
        prompt += f"- {item['title']}: {item['description']}\n"
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content

def generate_summaries_by_category(config_path: str) -> Dict[str, str]:
    config = load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    root_dir = os.path.abspath(os.path.join(config_dir, ".."))
    log_file = os.path.join(root_dir, config.get("log_file", "output.log"))
    log_dir = os.path.dirname(log_file)
    print(f"Log file in summary_generator: {log_file}")
    print(f"Log directory in summary_generator: {log_dir}")
    print(f"Config directory: {config_dir}")
    print(f"Root directory: {root_dir}")
    
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    setup_logging(log_file)

    base_folder = os.path.join(root_dir, config.get("base_folder", "weekly_news"))
    print(f"Base folder: {base_folder}")

    summaries_by_category = {}
    try:
        latest_file = get_latest_json_file(base_folder)
        logging.info(f"Latest JSON file: {latest_file}")

        news_data = read_json_file(latest_file)
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

if __name__ == "__main__":
    summaries = generate_summaries_by_category("src/config.json")
    for category, summary in summaries.items():
        print(f"\n{category}\n{summary}")
