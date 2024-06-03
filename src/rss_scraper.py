import json
import os
import requests
import xml.etree.ElementTree as ET
import re
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

def setup_logging(log_file: str):
    log_file = os.path.abspath(log_file)
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file)
        ]
    )

def load_existing_data(file_path: str) -> List[Dict[str, Any]]:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def clean_html(raw_html: str) -> str:
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def parse_rss_feed(xml_data: str, category: str) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_data)
    news_items = []
    for item in root.findall('./channel/item'):
        news_items.append(parse_rss_item(item, category))
    return news_items

def parse_rss_item(item, category: str) -> Dict[str, str]:
    title = item.find('title').text.strip()
    description = clean_html(item.find('description').text.strip())
    post_id = item.find('guid').text.strip() if item.find('guid') is not None else None
    pub_date = item.find('pubDate').text.strip() if item.find('pubDate') is not None else None
    return {
        'id': post_id,
        'title': title,
        'description': description,
        'category': category,
        'pub_date': pub_date
    }

def fetch_rss_feed(url: str, headers: Dict[str, str]) -> str:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content

def scrape_rss_feed(url: str, category: str, retries: int = 3, delay: int = 2) -> List[Dict[str, str]]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for attempt in range(retries):
        try:
            xml_data = fetch_rss_feed(url, headers)
            return parse_rss_feed(xml_data, category)
        except requests.RequestException as e:
            handle_request_exception(e, url, attempt, retries, delay)
    return []

def handle_request_exception(e, url: str, attempt: int, retries: int, delay: int) -> None:
    logging.error(f"Error fetching {url}: {e}")
    if attempt < retries - 1:
        logging.info(f"Retrying in {delay} seconds...")
        time.sleep(delay)
    else:
        logging.error(f"Failed to fetch {url} after {retries} attempts")

def get_weekly_file_path(base_folder: str, year: int, week: int) -> str:
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
    return os.path.join(base_folder, f'news_{year}_{week:02}.json')

def main(config_path: str) -> None:
    config = load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    
    base_folder = os.path.abspath(os.path.join(config_dir, "..", config["base_folder"]))
    log_file = os.path.abspath(os.path.join(config_dir, "..", config["log_file"]))
    setup_logging(log_file)
    
    year, week = get_current_year_and_week()
    file_path = get_weekly_file_path(base_folder, year, week)
    existing_data, existing_ids = load_existing_news_data(file_path)

    for category, rss_url in config["categories"].items():
        news_items = scrape_rss_feed(rss_url, category, retries=config.get("retry_count", 3), delay=config.get("retry_delay", 2))
        add_new_items(news_items, existing_data, existing_ids)

    save_data(file_path, existing_data)
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"Script completed successfully at {datetime.now()}")
    logging.getLogger().setLevel(logging.ERROR)

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as file:
        return json.load(file)

def get_current_year_and_week() -> Tuple[int, int]:
    current_date = datetime.now()
    year, week, _ = current_date.isocalendar()
    return year, week

def load_existing_news_data(file_path: str) -> Tuple[List[Dict[str, Any]], set]:
    existing_data = load_existing_data(file_path)
    existing_ids = {item['id'] for item in existing_data}
    return existing_data, existing_ids

def add_new_items(news_items: List[Dict[str, str]], existing_data: List[Dict[str, Any]], existing_ids: set) -> int:
    new_items_count = 0
    for item in news_items:
        if item['id'] not in existing_ids:
            existing_data.append(item)
            existing_ids.add(item['id'])
            new_items_count += 1
    return new_items_count

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RSS Scraper for Weekly News")
    parser.add_argument('--config', type=str, default='src/config.json', help='Path to the configuration file')
    args = parser.parse_args()
    main(args.config)
