# AI News Digest

This script scrapes news articles from RSS feeds, leverages AI to analyze and highlight the most significant stories, and delivers a concise summary via email.

## Setup

### First-Time Setup

1. **Clone the repository**:
    ```sh
    git clone https://github.com/masikonis/ai-news-digest.git
    cd news-digest
    ```

2. **Create a virtual environment and activate it**:
    ```sh
    python3 -m venv langchain_env
    source langchain_env/bin/activate
    ```

3. **Install the dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Edit the configuration file if necessary**:
    The configuration file `src/config.json` is already tracked in Git. You can edit it to customize the categories, base folder, retry count, and retry delay.

### Regular Usage

1. **Activate the virtual environment**:
    ```sh
    source langchain_env/bin/activate
    ```

2. **Run the RSS scraper**:
    ```sh
    python src/rss_scraper.py --config src/config.json
    ```

3. **(Optional) Run unit tests**:
    ```sh
    python -m unittest discover tests
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

## Automating with Launchd

You can automate the RSS scraper to run every hour on a Mac using a `plist` file with `launchd`.

Refer to the `example-com.example.news-digest-rss-scraper.plist` file in the repository for the setup.

