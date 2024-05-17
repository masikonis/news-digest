import json
import os
import requests
import xml.etree.ElementTree as ET
import re
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_existing_data(file_path: str) -> List[Dict[str, Any]]:
    """Load existing data from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_data(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def clean_html(raw_html: str) -> str:
    """Clean HTML tags from a string."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def parse_rss_feed(xml_data: str, category: str) -> List[Dict[str, str]]:
    """Parse RSS feed XML data."""
    root = ET.fromstring(xml_data)
    news_items = []
    for item in root.findall('./channel/item'):
        title = item.find('title').text.strip()
        description = clean_html(item.find('description').text.strip())
        post_id = item.find('guid').text.strip() if item.find('guid') is not None else None
        pub_date = item.find('pubDate').text.strip() if item.find('pubDate') is not None else None

        news_items.append({
            'id': post_id,
            'title': title,
            'description': description,
            'category': category,
            'pub_date': pub_date
        })
    return news_items

def scrape_rss_feed(url: str, category: str, retries: int = 3, delay: int = 2) -> List[Dict[str, str]]:
    """Scrape RSS feed from a URL with retries."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return parse_rss_feed(response.content, category)
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return []

def get_weekly_file_path(base_folder: str, year: int, week: int) -> str:
    """Get the file path for the weekly JSON file."""
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
    return os.path.join(base_folder, f'news_{year}_{week:02}.json')

def main(config_path: str) -> None:
    """Main function to scrape RSS feeds and save news items to a JSON file."""
    # Load configuration
    with open(config_path, 'r') as file:
        config = json.load(file)
    
    categories = config["categories"]
    base_folder = config["base_folder"]
    retry_count = config["retry_count"]
    retry_delay = config["retry_delay"]

    # Get the current year and week number
    current_date = datetime.now()
    year, week, _ = current_date.isocalendar()

    # Determine the file path for the current week
    file_path = get_weekly_file_path(base_folder, year, week)

    # Load existing data
    existing_data = load_existing_data(file_path)

    # Create a set of existing IDs to check for duplicates
    existing_ids = {item['id'] for item in existing_data}

    for category, rss_url in categories.items():
        logging.info(f'Scraping category: {category}')
        news_items = scrape_rss_feed(rss_url, category, retries=retry_count, delay=retry_delay)

        # Add non-duplicate records to the existing data
        new_items_count = 0
        for item in news_items:
            if item['id'] not in existing_ids:
                existing_data.append(item)
                existing_ids.add(item['id'])
                new_items_count += 1
        logging.info(f'Added {new_items_count} new items for category: {category}')

    # Save the updated data back to the JSON file
    save_data(file_path, existing_data)
    logging.info(f'Saved data to {file_path}')

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RSS Scraper for Weekly News")
    parser.add_argument('--config', type=str, default='src/config.json', help='Path to the configuration file')
    args = parser.parse_args()
    main(args.config)
