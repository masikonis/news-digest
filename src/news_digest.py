# src/news_digest.py
import os
import logging
import requests
from datetime import datetime
from typing import Dict
from model_initializer import initialize_model
from summary_generator import generate_summaries_by_category
from utils import setup_logging, load_config

# Initialize the model
model = initialize_model()

# Load environment variables from the .env file
mailgun_api_key = os.getenv("MAILGUN_API_KEY")
mailgun_domain = os.getenv("MAILGUN_DOMAIN")
email_user = os.getenv("EMAIL_USER")
recipient_email = os.getenv("RECIPIENT_EMAIL")

def generate_email_content(summaries: Dict[str, str], week_number: int) -> str:
    html_content = "<html><body>"
    for category, summary in summaries.items():
        html_content += f"<h2><b>{category}</b></h2><p>{summary}</p><br>"
    html_content += "</body></html>"
    return html_content

def send_email(subject: str, html_content: str) -> None:
    url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
    data = {
        "from": f"News Digest <mailgun@{mailgun_domain}>",
        "to": [recipient_email],
        "subject": subject,
        "html": html_content,
    }
    print(f"Sending data: {data}")  # Debugging: Print the data being sent
    try:
        response = requests.post(url, auth=("api", mailgun_api_key), data=data)
        response.raise_for_status()
        logging.info(f"Email sent to {recipient_email}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send email: {e}")
        print(f"Failed to send email: {e}")

def main():
    config_path = "src/config.json"
    config = load_config(config_path)
    setup_logging(config.get("log_file"))

    summaries = generate_summaries_by_category(config_path)

    # Get the current week number
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]

    # Generate email content
    email_content = generate_email_content(summaries, week_number)

    # Send email
    subject = f"Naujienos ({week_number} savaitė)"
    send_email(subject, email_content)

if __name__ == "__main__":
    main()
