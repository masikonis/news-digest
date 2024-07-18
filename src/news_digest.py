# src/news_digest.py
import os
import logging
import requests
from datetime import datetime
from typing import Dict
from model_initializer import initialize_model
from summary_generator import generate_summaries_by_category
from utils import setup_logging, load_config

def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
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

def send_email(subject: str, html_content: str, sender_name: str, sender_email: str, recipient_email: str) -> None:
    url = f"https://api.mailgun.net/v3/{get_env_variable('MAILGUN_DOMAIN')}/messages"
    data = {
        "from": f"{sender_name} <{sender_email}>",
        "to": [recipient_email],
        "subject": subject,
        "html": html_content,
    }
    logging.debug(f"Sending email data: {data}")  # Debugging: Print the data being sent
    try:
        response = requests.post(url, auth=("api", get_env_variable('MAILGUN_API_KEY')), data=data)
        response.raise_for_status()
        logging.info(f"Email sent to {recipient_email}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send email: {e}")
        print(f"Failed to send email: {e}")

def main(config_path: str):
    config = load_config(config_path)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    
    # Ensure log file path is correct relative to the root directory
    root_dir = os.path.abspath(os.path.join(config_dir, ".."))
    log_file = os.path.join(root_dir, config.get("log_file", "output.log"))
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    setup_logging(log_file)

    sender_name = get_env_variable('SENDER_NAME')
    sender_email = get_env_variable('SENDER_EMAIL')
    recipient_email = get_env_variable('RECIPIENT_EMAIL')

    summaries = generate_summaries_by_category(config_path)

    # Get the current week number
    current_date = datetime.now()
    week_number = current_date.isocalendar()[1]

    # Generate email content
    email_content = generate_email_content(summaries, week_number)

    # Send email
    subject = f"Savaitės naujienų apžvalga"
    send_email(subject, email_content, sender_name, sender_email, recipient_email)

def run():
    import argparse
    parser = argparse.ArgumentParser(description="Weekly News Digest")
    parser.add_argument('--config', type=str, default='src/config.json', help='Path to the configuration file')
    args = parser.parse_args()
    main(args.config)

if __name__ == "__main__":
    run()
