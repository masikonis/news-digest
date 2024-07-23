# AI News Digest

[![codecov](https://codecov.io/gh/masikonis/ai-news-digest/branch/main/graph/badge.svg)](https://codecov.io/gh/masikonis/ai-news-digest)

This script scrapes news articles from RSS feeds, leverages AI to analyze and highlight the most significant stories, and delivers a concise summary via email.

## Rationale

This app was built as a way to fight news addiction. Since I stopped checking the news regularly, I needed a way to still keep up to date with the latest news so that I do not live under a rock. Instead of spending 2 hours per day, I receive a summary each Sunday evening that I can read in 10 minutes. This results in massive time savings.

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
    "log_file": "output.log"
}
```

## Automating with Launchd

You can automate the RSS scraper to run every hour on a Mac using a `plist` file with `launchd`.

The .plist files required for this Python application are stored in the `~/Library/LaunchAgents/` directory.

Refer to the `example-com.example.news-digest-rss-scraper.plist` file in the repository for the setup.
