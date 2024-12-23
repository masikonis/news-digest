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
import numpy as np

def initialize_models(config_path: str):
    if not os.path.isabs(config_path):
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), config_path))
    
    config = load_config(config_path)
    ai_config = config.get("ai_config", {"provider": "openai"})
    
    model = initialize_model(
        'advanced', 
        temperature=ai_config.get("temperature", {}).get("chat", 0.7),
        provider=ai_config.get("provider", "openai")
    )
    
    embeddings_model = initialize_model(
        'embeddings',
        provider=ai_config.get("provider", "openai")
    )
    
    return model, embeddings_model

default_config = os.path.join(os.path.dirname(__file__), "config.json")
model, embeddings_model = initialize_models(default_config)

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
        "Tu esi patyręs žurnalistas ir naujienų apžvalgininkas. Tavo užduotis:\n\n"
        "1. Sukurti TIKSLIAI 200 žodžių paragrafą (ne ilgesnį!)\n"
        "2. Naudoti formalų ir aiškų stilių\n"
        "3. Sujungti naujienas į rišlų ir nuoseklų pasakojimą\n"
        "4. Pabrėžti 3-4 svarbiausius įvykius\n"
        "5. Vengti detalių, kurios nėra esminės\n"
        "6. Užtikrinti, kad kiekvienas sakinys neštų naują informaciją\n"
        "7. SVARBU: Vengti bendrų frazių kaip 'šie įvykiai atspindi', 'situacija sudėtinga', "
        "'tai rodo pastangas' ir panašių beprasmių apibendrinimų\n"
        "8. Kiekvienas sakinys turi turėti konkrečią informaciją arba faktą\n\n"
        "Ši apžvalga skirta skaitytojui, kuris nesekė naujienų ir nori sužinoti esminius "
        "savaitės įvykius. SVARBU: neviršyti 120 žodžių limito.\n\n"
        "Apibendrink šias naujienas:\n\n"
    )
    
    for item in news_items:
        content = item.get('ai_summary') or item.get('description', '')
        prompt += f"- {item['title']}:\n{content}\n\n"
            
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content

def similar_titles(title1: str, title2: str, threshold: float = 0.8) -> bool:
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio() > threshold

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm1 = sum(x * x for x in v1) ** 0.5
    norm2 = sum(x * x for x in v2) ** 0.5
    return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0

def deduplicate_news_items(news_items: List[Dict[str, Any]], use_semantic: bool = False) -> List[Dict[str, Any]]:
    logging.info(f"Starting deduplication of {len(news_items)} news items")
    
    # Sort by AI summary length (prioritize more detailed items)
    sorted_news = sorted(
        news_items,
        key=lambda x: len(x.get('ai_summary', '')) if isinstance(x.get('ai_summary', ''), str) else 0,
        reverse=True
    )
    
    # Get embeddings only if semantic similarity is enabled
    embeddings = []
    if use_semantic:
        titles = [item['title'] for item in sorted_news]
        embeddings = [
            embeddings_model.embed_query(title) 
            for title in titles
        ]
    
    unique_news = []
    seen_indices = set()
    
    for i, item in enumerate(sorted_news):
        if i in seen_indices:
            continue
            
        for j in range(i + 1, len(sorted_news)):
            if j in seen_indices:
                continue
                
            # Check string similarity
            if similar_titles(sorted_news[i]['title'], sorted_news[j]['title']):
                seen_indices.add(j)
                continue
                
            # Check semantic similarity only if enabled
            if use_semantic:
                similarity = cosine_similarity(embeddings[i], embeddings[j])
                if similarity > 0.70:
                    seen_indices.add(j)
                    logging.debug(f"Semantic duplicate found: '{sorted_news[i]['title']}' and '{sorted_news[j]['title']}' (similarity: {similarity:.2f})")
        
        unique_news.append(item)
    
    logging.info(f"Deduplication complete. Reduced from {len(news_items)} to {len(unique_news)} items")
    return unique_news

def evaluate_story_importance(news_items: List[Dict[str, Any]], category: str, percentage: float = 0.25, min_stories: int = 7, max_stories: int = 14) -> List[Dict[str, Any]]:
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
        "Įvertink kiekvienos naujienos svarbą nuo 1 iki 10 (10 - ypač svarbi, 1 - mažai svarbi), "
        "atsižvelgdamas į šiuos kriterijus:\n\n"
        f"1. Tinkamumas '{category}' kategorijai ir temos aktualumas (2 taškai)\n"
        "2. Poveikis visuomenei ir valstybei (3 taškai)\n"
        "3. Naujienų aktualumas laiko atžvilgiu (2 taškai)\n"
        "4. Ilgalaikė įtaka (2 taškai)\n"
        "5. Visuomenės interesas (1 taškas)\n\n"
        "LABAI SVARBU: Jei yra kelios naujienos apie tą patį įvykį, įvertink jas skirtingai, "
        "kad išvengtume pasikartojančių temų. Pavyzdžiui:\n"
        "- Jei yra 3 naujienos apie tą patį įvykį, pagrindinei naujienai duok aukštesnį įvertinimą (8-10), "
        "o kitoms žemesnį (1-3)\n\n"
        "Pateik įvertinimus tokiu formatu:\n"
        "1:8\n2:5\n3:9\n...\n\n"
        "Naujienos:\n"
    )
    
    for item in news_items:
        prompt += f"#{item['simple_id']}: {item['title']}\n"
        if 'ai_summary' in item and isinstance(item.get('ai_summary'), str):
            prompt += f"Santrauka: {item['ai_summary'][:200]}...\n"
        prompt += "\n"
    
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        
        # Parse importance scores
        importance_scores = {}
        for line in response.content.strip().split('\n'):
            if ':' in line:
                try:
                    idx, score = line.split(':')
                    score = int(score.strip())
                    if 1 <= score <= 10:  # Validate score range
                        importance_scores[idx.strip()] = score
                except (ValueError, IndexError):
                    continue
        
        if not importance_scores:
            raise ValueError("No valid importance scores found in response")
        
        # Sort stories based on scores and handle ties using publication date
        sorted_items = sorted(
            news_items,
            key=lambda x: (
                importance_scores.get(x['simple_id'], 0),
                x.get('pub_date', '1970-01-01')  # Fallback date for sorting
            ),
            reverse=True
        )
        
        for item in sorted_items[:target_stories]:
            score = importance_scores.get(item['simple_id'], 0)
        
        return sorted_items[:target_stories]
        
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
    # Re-initialize models with provided config
    global model, embeddings_model
    model, embeddings_model = initialize_models(config_path)
    
    summaries = generate_summaries_by_category(config_path)
    for category, summary in summaries.items():
        print(f"\n{category}\n{summary}")

if __name__ == "__main__":
    main("src/config.json")
