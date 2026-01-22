"""
Simple logging setup for LewtNanny
"""

import logging
import sys
from pathlib import Path
from src.utils.paths import get_default_log_path, ensure_user_data_dir


def setup_logger(log_file: str = None):
    """Setup logging configuration"""
    if log_file:
        log_path = Path(log_file)
    else:
        log_path = get_default_log_path()
    ensure_user_data_dir()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)