# src/news_digest.py
import os
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from model_initializer import initialize_model
from summary_generator import generate_summaries_by_category
from utils import setup_logging, load_config

def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    value = os.getenv(var_name, default)
    if not value:
        logging.error(f"Environment variable {var_name} is not set")
        raise EnvironmentError(f"Environment variable {var_name} is not set")
    return value

def generate_email_content(summaries: Dict[str, str], week_number: int) -> str:
    html_content = "<html><body>"
    for category, summary in summaries.items():
        html_content += f"<p><b>{category}</b></p><p>{summary}</p><br>"
    html_content += "</body></html>"
    return html_content

def send_email(subject: str, html_content: str, sender_name: str, sender_email: str, recipient_email: str, mailgun_domain: str, mailgun_api_key: str) -> None:
    url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
    data = {
        "from": f"{sender_name} <{sender_email}>",
        "to": [recipient_email],
        "subject": subject,
        "html": html_content,
    }
    logging.debug(f"Sending email data: {data}")  # Debugging: Print the data being sent
    try:
        response = requests.post(url, auth=("api", mailgun_api_key), data=data)
        response.raise_for_status()
        logging.info(f"Email sent to {recipient_email}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send email: {e}")
        print(f"Failed to send email: {e}")

def main(config_path: str):
    config = load_config(config_path)
    setup_logging(config.get("log_file"))

    sender_name = get_env_variable('SENDER_NAME')
    sender_email = get_env_variable('SENDER_EMAIL')
    recipient_email = get_env_variable('RECIPIENT_EMAIL')
    mailgun_domain = get_env_variable('MAILGUN_DOMAIN')
    mailgun_api_key = get_env_variable('MAILGUN_API_KEY')

    summaries = generate_summaries_by_category(config_path)

    # Get the current week number
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]

    # Generate email content
    email_content = generate_email_content(summaries, week_number)

    # Send email
    subject = f"Savaitės naujienų apžvalga"
    send_email(subject, email_content, sender_name, sender_email, recipient_email, mailgun_domain, mailgun_api_key)

if __name__ == "__main__":
    config_path = "src/config.json"
    main(config_path)
