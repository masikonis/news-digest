# News Digest

[![codecov](https://codecov.io/gh/masikonis/news-digest/branch/main/graph/badge.svg)](https://codecov.io/gh/masikonis/news-digest)

This script collects news articles from RSS feeds, uses AI to analyze and highlight the key stories, and sends a short summary via email.

## Rationale

I developed this application to help reduce my news addiction. After deciding to stop checking the news all the time, I needed a way to stay informed without wasting too much time. Instead of spending one hour a day on news, I now get a summary every Sunday evening that I can read in ten minutes. This change has saved me a lot of time.

## How It Works

1. **Fetch News**: Collects articles from RSS feeds, filtering by publication date.
2. **Enrich Content**: Uses AI to generate concise AI-based summaries of the articles.
3. **Filter & Deduplicate**: Removes duplicates and ranks articles by importance.
4. **Create Summaries**: Groups articles by category and creates clear, short summaries.
5. **Send Email**: Compiles the summaries into an email and sends it to the recipients.

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

## Automating with Launchd

Automate the RSS scraper to run every hour on a Mac using a plist file with launchd. The `.plist` files required for this Python application are stored in the `~/Library/LaunchAgents/` directory.
