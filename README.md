# AI News Digest

[![codecov](https://codecov.io/gh/masikonis/news-digest/branch/main/graph/badge.svg)](https://codecov.io/gh/masikonis/news-digest)

This script scrapes news articles from RSS feeds, leverages AI to analyze and highlight the most significant stories, and delivers a concise summary via email.

## Rationale

This application was developed to combat news addiction. After deciding to stop checking the news regularly, I needed a way to stay informed without spending excessive time. Instead of spending two hours a day, I now receive a summary every Sunday evening that I can read in ten minutes, resulting in significant time savings.

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
