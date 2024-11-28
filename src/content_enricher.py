# src/content_enricher.py
import os
import json
import time
import logging
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils import load_config
from model_initializer import initialize_model
from langchain.schema import HumanMessage

class ContentEnricher:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.enrichment_config = self.config.get("content_enrichment", {})
        self.base_folder = self.config["base_folder"]
        self.model = initialize_model('analysis')  # Use analysis model
        
    def get_full_content(self, url: str) -> Optional[str]:
        """Fetch and extract full content from a news article URL."""
        domain = urlparse(url).netloc
        source_config = self.enrichment_config["sources"].get(domain)
        
        if not source_config:
            logging.warning(f"No scraping configuration found for domain: {domain}")
            return None

        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content_div = soup.select_one(source_config["selector"])
            
            if content_div:
                return content_div.get_text(strip=True)
            else:
                logging.warning(f"Content selector not found for URL: {url}")
                return None

        except Exception as e:
            logging.error(f"Error fetching content from {url}: {e}")
            return None

    def generate_article_analysis(self, title: str, content: str) -> str:
        """Generate a concise summary of the article."""
        prompt = (
            "Pateik glaustą ir informatyvią straipsnio santrauką (apie 150 žodžių), "
            "išryškindamas svarbiausius faktus ir įžvalgas. "
            "Santrauka turi būti aiški, nuosekli ir apimti esminius straipsnio aspektus.\n\n"
            f"Straipsnio pavadinimas: {title}\n\n"
            f"Turinys: {content}"
        )
        
        response = self.model.invoke([HumanMessage(content=prompt)])
        return response.content

    def enrich_weekly_news(self, year: int, week: int) -> None:
        """Enrich the weekly news with AI-generated summaries."""
        if not self.enrichment_config.get("enabled", False):
            return

        weekly_file = os.path.join(self.base_folder, f"news_{year}_{week:02}.json")
        if not os.path.exists(weekly_file):
            logging.error(f"Weekly news file not found: {weekly_file}")
            return

        with open(weekly_file, 'r') as f:
            news_items = json.load(f)

        # Find articles that need processing (exclude previously failed ones)
        to_process = [item for item in news_items 
                     if 'ai_summary' not in item 
                     and 'ai_summary_failed' not in item]
        
        if not to_process:
            logging.info("No articles to process")
            return

        processed = 0
        for item in to_process:
            logging.info(f"Processing: {item['title']}")
            
            # Get full content and generate summary
            full_content = self.get_full_content(item['id'])
            if full_content:
                ai_analysis = self.generate_article_analysis(item['title'], full_content)
                
                # Update the article in news_items
                for i, news_item in enumerate(news_items):
                    if news_item['id'] == item['id']:
                        news_items[i]['ai_summary'] = ai_analysis
                        break
                
                processed += 1
                logging.info(f"✓ Processed {processed}/{len(to_process)}")
            else:
                # Mark the article as failed
                for i, news_item in enumerate(news_items):
                    if news_item['id'] == item['id']:
                        news_items[i]['ai_summary_failed'] = True
                        break
                logging.error(f"Failed to fetch content: {item['title']}")
            
            # Save after each article (success or failure)
            with open(weekly_file, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, ensure_ascii=False, indent=4)
            
            # Rate limiting
            time.sleep(self.enrichment_config.get("scraping_delay", 2))

        logging.info(f"Enrichment complete. Successfully processed {processed} articles")

def main(config_path: str):
    from datetime import datetime
    
    # Setup logging first
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',  # Simplified format
        handlers=[logging.StreamHandler()]
    )
    
    enricher = ContentEnricher(config_path)
    current_date = datetime.now()
    year, week, _ = current_date.isocalendar()
    
    weekly_file = os.path.join(enricher.base_folder, f"news_{year}_{week:02}.json")
    
    if os.path.exists(weekly_file):
        with open(weekly_file, 'r') as f:
            news_items = json.load(f)
            unenriched = len([item for item in news_items if 'ai_summary' not in item])
            logging.info(f"Found {unenriched} articles to process")
    
    enricher.enrich_weekly_news(year, week)

def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description="Content Enricher for Weekly News")
    parser.add_argument('--config', type=str, default='src/config.json', help='Path to the configuration file')
    return parser.parse_args()

def run():
    args = parse_arguments()
    main(args.config)

if __name__ == "__main__":
    run() 
    