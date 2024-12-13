# News Digest

[![codecov](https://codecov.io/gh/masikonis/news-digest/branch/main/graph/badge.svg)](https://codecov.io/gh/masikonis/news-digest)

This application collects and filters articles from RSS feeds, uses AI to summarize content, removes duplicates, ranks by importance, and groups related articles. The result is a well-organized email digest of significant news in an easy-to-read format.

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

**Important**: To ensure the scheduled tasks run properly, your Mac needs to be awake when the plist files trigger. You can use the [Amphetamine app](https://apps.apple.com/us/app/amphetamine/id937984704) to schedule wake periods for your Mac. This prevents missing scheduled runs due to sleep mode.

## Tech Stack

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Mailgun](https://img.shields.io/badge/Mailgun-F06B66?style=for-the-badge&logo=mailgun&logoColor=white)](https://www.mailgun.com/)
