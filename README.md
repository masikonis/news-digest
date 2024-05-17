# AI News Digest

This script scrapes news articles from RSS feeds, leverages AI to analyze and highlight the most significant stories, and delivers a concise summary via email.

## Setup

1. Clone the repository.
2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv langchain_env
    source langchain_env/bin/activate
    ```
3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Edit the `src/config.json` file with the following structure if necessary:
```json
{
    "categories": {
        "Ukraina": "https://www.lrt.lt/tema/rusijos-karas-pries-ukraina?rss",
        "Verslas": "https://www.lrt.lt/naujienos/verslas?rss",
        "Pasaulis": "https://www.lrt.lt/naujienos/pasaulyje?rss",
        "Lietuva": "https://www.lrt.lt/naujienos/lietuvoje?rss"
    },
    "base_folder": "weekly_news",
    "retry_count": 3,
    "retry_delay": 2
}
