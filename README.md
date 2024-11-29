# News Digest

[![codecov](https://codecov.io/gh/masikonis/news-digest/branch/main/graph/badge.svg)](https://codecov.io/gh/masikonis/news-digest)

This app automates news consumption by transforming RSS feeds into concise email digests. It collects and filters articles, uses AI to summarize content, removes duplicates, ranks by importance, and groups related articles. The result is a well-organized email digest of significant news in an easy-to-read format.

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

## Automating with Launchd

Automate the RSS scraper to run every hour on a Mac using a plist file with launchd. The `.plist` files required for this Python application are stored in the `~/Library/LaunchAgents/` directory.
