import json
import os
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

def load_existing_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def scrape_rss_feed(url, category):
    response = requests.get(url)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    news_items = []
    for item in root.findall('./channel/item'):
        title = item.find('title').text.strip()
        description = clean_html(item.find('description').text.strip())
        post_id = item.find('guid').text.strip() if item.find('guid') is not None else None
        pub_date = item.find('pubDate').text.strip() if item.find('pubDate') is not None else None

        # Append the category, ID, title, description, and publish date to the news_items array
        news_items.append({
            'id': post_id,
            'title': title,
            'description': description,
            'category': category,
            'pub_date': pub_date
        })
    return news_items

def get_weekly_file_path(base_folder, year, week):
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
    return os.path.join(base_folder, f'news_{year}_{week:02}.json')

if __name__ == "__main__":
    categories = {
        'Ukraina': 'https://www.lrt.lt/tema/rusijos-karas-pries-ukraina?rss',
        'Verslas': 'https://www.lrt.lt/naujienos/verslas?rss',
        'Pasaulis': 'https://www.lrt.lt/naujienos/pasaulyje?rss',
        'Lietuva': 'https://www.lrt.lt/naujienos/lietuvoje?rss'
    }
    base_folder = 'weekly_news'

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
        # Scrape the RSS feed for the current category
        news_items = scrape_rss_feed(rss_url, category)

        # Add non-duplicate records to the existing data
        for item in news_items:
            if item['id'] not in existing_ids:
                existing_data.append(item)
                existing_ids.add(item['id'])

    # Save the updated data back to the JSON file
    save_data(file_path, existing_data)
