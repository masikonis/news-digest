# src/rss_scraper.py
import json
import os
import requests
import xml.etree.ElementTree as ET
import re
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from utils import setup_logging, load_config

def get_zoneinfo():
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from datetime import tzinfo, timezone, timedelta

        class ZoneInfo(tzinfo):
            def __init__(self, name):
                self.name = name
                self.offset = timezone(timedelta(hours=2))  # Hardcoded offset for Europe/Vilnius

            def utcoffset(self, dt):
                return self.offset.utcoffset(dt)

            def dst(self, dt):
                return timedelta(0)

            def tzname(self, dt):
                return self.name
    return ZoneInfo

ZoneInfo = get_zoneinfo()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

def load_existing_data(file_path: str) -> List[Dict[str, Any]]:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                if not content.strip():
                    logging.warning(f"File {file_path} is empty. Returning an empty list.")
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {file_path}: {e}")
            logging.info("Returning an empty list and backing up the problematic file.")
            backup_file(file_path)
            return []
    return []

def backup_file(file_path: str) -> None:
    backup_path = f"{file_path}.bak"
    try:
        os.rename(file_path, backup_path)
        logging.info(f"Backed up problematic file to {backup_path}")
    except OSError as e:
        logging.error(f"Failed to backup file {file_path}: {e}")

def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False, cls=DateTimeEncoder)

def clean_html(raw_html: str) -> str:
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def parse_rss_feed(xml_data: str, category: str, start_of_week: datetime, end_of_week: datetime) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_data)
    news_items = []
    for item in root.findall('./channel/item'):
        parsed_item = parse_rss_item(item, category)
        if parsed_item and start_of_week <= parsed_item['pub_date'] < end_of_week:
            news_items.append(parsed_item)
    return news_items

def parse_rss_item(item, category: str) -> Dict[str, Any]:
    title = item.find('title').text.strip()
    description = clean_html(item.find('description').text.strip())
    post_id = item.find('guid').text.strip() if item.find('guid') is not None else None
    pub_date_str = item.find('pubDate').text.strip() if item.find('pubDate') is not None else None
    
    # Use guid as URL if link is not present
    url = item.find('link')
    if url is not None:
        url = url.text.strip()
    elif post_id and post_id.startswith('http'):
        url = post_id
    else:
        return None  # Skip items without URL
    
    if pub_date_str:
        try:
            pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
            pub_date = pub_date.astimezone(ZoneInfo("Europe/Vilnius"))
        except ValueError:
            logging.error(f"Unable to parse date: {pub_date_str}")
            return None
    else:
        return None

    return {
        'id': post_id,
        'title': title,
        'description': description,
        'category': category,
        'pub_date': pub_date,
        'url': url
    }

def fetch_rss_feed(url: str, headers: Dict[str, str]) -> str:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content

def scrape_rss_feed(url: str, category: str, start_of_week: datetime, end_of_week: datetime, retries: int = 3, delay: int = 2) -> List[Dict[str, str]]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for attempt in range(retries):
        try:
            xml_data = fetch_rss_feed(url, headers)
            return parse_rss_feed(xml_data, category, start_of_week, end_of_week)
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

def get_week_range(year: int, week: int) -> Tuple[datetime, datetime]:
    start_of_week = datetime.fromisocalendar(year, week, 1).replace(tzinfo=ZoneInfo("Europe/Vilnius"))
    end_of_week = start_of_week + timedelta(days=7)
    return start_of_week, end_of_week

def main(config_path: str) -> None:
    config = load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    
    base_folder = os.path.abspath(os.path.join(config_dir, "..", config["base_folder"]))
    log_file = os.path.abspath(os.path.join(config_dir, "..", config["log_file"]))
    setup_logging(log_file)  # No force parameter here
    
    year, week = get_current_year_and_week()
    file_path = get_weekly_file_path(base_folder, year, week)
    existing_data, existing_ids = load_existing_news_data(file_path)

    start_of_week, end_of_week = get_week_range(year, week)

    for category, rss_url in config["categories"].items():
        news_items = scrape_rss_feed(rss_url, category, start_of_week, end_of_week, retries=config.get("retry_count", 3), delay=config.get("retry_delay", 2))
        add_new_items(news_items, existing_data, existing_ids)

    save_data(file_path, existing_data)
    logging.info(f"Script completed successfully at {datetime.now(ZoneInfo('Europe/Vilnius'))}")

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as file:
        return json.load(file)

def get_current_year_and_week() -> Tuple[int, int]:
    current_date = datetime.now(ZoneInfo("Europe/Vilnius"))
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

def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description="RSS Scraper for Weekly News")
    parser.add_argument('--config', type=str, default='src/config.json', help='Path to the configuration file')
    return parser.parse_args()

def run():
    args = parse_arguments()
    main(args.config)

if __name__ == "__main__":
    run()
