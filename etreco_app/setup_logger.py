import logging
from datetime import datetime
import os

def setup_logger(log_file_name=None, log_level=logging.INFO):
    """
    Sets up the logger configuration.

    Parameters:
        log_file_name (str): The name of the log file. If None, a default name with the current timestamp will be used.
        log_level (int): Logging level. Default is logging.INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """

    # Define log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create console handler and set format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # If log_file_name is not provided, use a default file name with timestamp
    if not log_file_name:
        log_file_name = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Create log directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Create file handler and set format
    file_handler = logging.FileHandler(os.path.join(log_dir, log_file_name))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger