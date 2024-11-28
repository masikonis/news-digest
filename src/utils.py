# src/utils.py
import logging
import os

def setup_logging(log_file: str, force: bool = False):
    """Configure logging for the application.

    Sets up both file and console logging handlers with standardized formatting.
    Creates the log directory if it doesn't exist.

    Args:
        log_file (str): Path to the log file
        force (bool, optional): Force reconfiguration of logging even if handlers exist. 
            Defaults to False.

    Note:
        - Creates log directory if it doesn't exist
        - Uses INFO level logging
        - Includes timestamp, logger name, level, and message in log format
    """
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

def load_config(config_path: str) -> dict:
    """Load and parse JSON configuration file.

    Args:
        config_path (str): Path to the configuration file

    Returns:
        dict: Parsed configuration data

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is not valid JSON
    """
    import json
    with open(config_path, 'r') as file:
        return json.load(file)
