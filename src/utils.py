# src/utils.py
import os
import json
import logging
from typing import Dict, Any

def setup_logging(log_file: str) -> None:
    log_file = os.path.abspath(log_file)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as file:
        return json.load(file)
