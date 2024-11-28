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

model = initialize_model('advanced', temperature=0.7)

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
        content = item.get('ai_summary') or item.get('description', '')
        prompt += f"- {item['title']}:\n{content}\n\n"
            
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
            continue
            
        seen_titles.add(title)
        unique_news.append(item)
    
    logging.info(f"Deduplication complete. Reduced from {len(news_items)} to {len(unique_news)} items")
    return unique_news

def evaluate_story_importance(news_items: List[Dict[str, Any]], category: str, percentage: float = 0.25, min_stories: int = 7, max_stories: int = 14) -> List[Dict[str, Any]]:
    """
    Evaluate and select top stories based on their importance using AI.
    """
    
    # First assign simple numeric IDs to each story
    for idx, item in enumerate(news_items):
        item['simple_id'] = str(idx + 1)
    
    target_stories = max(
        min_stories,
        min(
            max_stories,
            round(len(news_items) * percentage)
        )
    )
    
    if len(news_items) <= target_stories:
        return news_items
        
    prompt = (
        f"Tu esi patyręs naujienų redaktorius, kuris ruošia '{category}' kategorijos naujienų apžvalgą. "
        "Įvertink šių naujienų svarbą ir poveikį, atsižvelgdamas į šiuos kriterijus:\n"
        f"1. Tinkamumas '{category}' kategorijai ir temos aktualumas\n"
        "2. Poveikis visuomenei ir valstybei\n"
        "3. Naujienų aktualumas laiko atžvilgiu\n"
        "4. Ilgalaikė įtaka\n"
        "5. Visuomenės interesas\n\n"
        f"LABAI SVARBU: Išrink {target_stories} SKIRTINGŲ ĮVYKIŲ naujienas. "
        "Jei yra kelios naujienos apie tą patį įvykį, išrink TIK VIENĄ svarbiausią, "
        "kad apžvalga būtų įvairi ir apimtų kuo daugiau skirtingų temų.\n\n"
        "Pavyzdžiui:\n"
        "- Jei yra 5 naujienos apie lėktuvo katastrofą, išrink TIK VIENĄ svarbiausią\n"
        "- Jei yra 3 naujienos apie tą patį politinį sprendimą, išrink TIK VIENĄ išsamiausią\n\n"
        f"Pateik {target_stories} skirtingų įvykių naujienų numerius, atskiriant kableliais (pvz: 1,5,8,12...).\n\n"
        "Naujienos:\n"
    )
    
    # Add each news item to the prompt using simple IDs
    for item in news_items:
        prompt += f"#{item['simple_id']}: {item['title']}\n"
        if 'ai_summary' in item and isinstance(item.get('ai_summary'), str):
            prompt += f"Santrauka: {item['ai_summary'][:200]}...\n"
        prompt += "\n"
    
    response = model.invoke([HumanMessage(content=prompt)])
    
    try:
        # Parse response to get ordered list of IDs
        important_ids = [id.strip() for id in response.content.split(',')]
        
        # Get top stories while preserving AI-determined order
        top_stories = []
        for simple_id in important_ids:
            matching_items = [item for item in news_items if item['simple_id'] == simple_id]
            if matching_items:
                top_stories.append(matching_items[0])
        
        # If we don't have enough stories, add more from the original list
        if len(top_stories) < target_stories:
            remaining_items = [item for item in news_items if item not in top_stories]
            top_stories.extend(remaining_items[:target_stories - len(top_stories)])
        
        return top_stories[:target_stories]
    except Exception as e:
        logging.error(f"Error processing AI response: {e}")
        logging.error(f"AI response was: {response.content}")
        logging.info("Falling back to date-based sorting")
        return sorted(news_items, key=lambda x: x['pub_date'], reverse=True)[:target_stories]

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
            top_stories = evaluate_story_importance(items, category)
            summary = generate_summary(top_stories)
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
