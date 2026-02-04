"""Path utilities for LewtNanny
Provides cross-platform user data directory handling
"""

import logging
from pathlib import Path
from platform import system


def get_user_data_dir() -> Path:
    """Get the user data directory for LewtNanny"""
    if system() == "Windows":
        return Path.home() / "Documents" / "LewtNanny"
    elif system() == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "LewtNanny"
    else:  # Linux and others
        return Path.home() / ".local" / "share" / "lewtnanny"


def get_default_db_path() -> Path:
    """Get the default database path in user data directory - user_data.db for session data"""
    return get_user_data_dir() / "user_data.db"


def get_default_log_path() -> Path:
    """Get the default log file path in user data directory"""
    return get_user_data_dir() / "lewtnanny.log"


def ensure_user_data_dir() -> Path:
    """Ensure user data directory exists and return its path"""
    data_dir = get_user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """Get the config directory (same as user data for simplicity)"""
    return get_user_data_dir()


def migrate_from_legacy(legacy_path: Path, new_path: Path) -> bool:
    """Migrate data from legacy app directory to user data directory"""
    if not legacy_path.exists():
        return False

    try:
        import shutil

        if new_path.exists():
            return False  # Don't overwrite existing data

        ensure_user_data_dir()
        shutil.copy2(legacy_path, new_path)
        logger.info(f"Migrated from {legacy_path} to {new_path}")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


import logging

logger = logging.getLogger(__name__)
