"""
Simple logging setup for LewtNanny
"""

import logging
import sys
from pathlib import Path


def setup_logger(log_file: str = "data/leotnanny.log"):
    """Setup logging configuration"""
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)