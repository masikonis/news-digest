# src/utils.py
import logging
import os

def setup_logging(log_file: str, force: bool = False):
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Only configure logging if no handlers are present, or if forced
    if force or not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Suppress third-party logging
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)

def load_config(config_path: str) -> dict:
    import json
    with open(config_path, 'r') as file:
        return json.load(file)
