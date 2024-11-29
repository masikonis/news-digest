# News Digest

[![codecov](https://codecov.io/gh/masikonis/news-digest/branch/main/graph/badge.svg)](https://codecov.io/gh/masikonis/news-digest)

This script collects news articles from RSS feeds, uses AI to analyze and highlight the key stories, and sends a short summary via email.

## Rationale

I developed this application to help reduce my news addiction. After deciding to stop checking the news all the time, I needed a way to stay informed without wasting too much time. Instead of spending one hour a day on news, I now get a summary every Sunday evening that I can read in ten minutes. This change has saved me a lot of time.

## Setup & Usage

### Regular Usage

1. **Activate the virtual environment**:
    ```sh
    source langchain_env/bin/activate
    ```

2. **(Optional) Run the tests with coverage**:
    ```sh
    PYTHONPATH=src coverage run -m unittest discover -s tests
    ```

3. **(Optional) Generate a coverage report**:
    ```sh
    coverage report -m
    ```

## Configuration

Edit the `src/config.json` file with the following structure if necessary:
```json
{
    "categories": {
        "Ukraina": "https://www.lrt.lt/tema/rusijos-karas-pries-ukraina?rss",
        "Verslas": "https://www.lrt.lt/naujienos/verslas?rss",
        "Pasaulis": "https://www.lrt.lt/naujienos/pasaulyje?rss",
        "Lietuva": "https://www.lrt.lt/naujienos/lietuvoje?rss",
        "Marijampolė": "https://www.suvalkietis.lt/feed/"
    },
    "base_folder": "weekly_news",
    "retry_count": 3,
    "retry_delay": 2,
    "log_file": "output.log",
    "content_enrichment": {
        "enabled": true,
        "scraping_delay": 2,
        "max_retries": 3,
        "sources": {
            "www.lrt.lt": {
                "selector": "article.article-block"
            },
            "www.suvalkietis.lt": {
                "selector": "div.single-post-content"
            }
        }
    }
}
```

## Automating with Launchd

Automate the RSS scraper to run every hour on a Mac using a plist file with launchd. The `.plist` files required for this Python application are stored in the `~/Library/LaunchAgents/` directory.
