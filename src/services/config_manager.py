"""Configuration manager for LewtNanny"""

import asyncio
import json
from pathlib import Path
from typing import Any

from src.utils.paths import ensure_user_data_dir


class ConfigManager:
    def __init__(self, config_path: str = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = ensure_user_data_dir() / "config.json"
        self.config = {}

    async def initialize(self):
        """Load configuration from file"""
        await self.load_config()

    def load(self):
        """Load configuration from file synchronously"""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = asyncio.run(self.get_default_config())
        else:
            self.config = asyncio.run(self.get_default_config())

    async def load_config(self):
        """Load configuration from JSON file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = await self.get_default_config()
        else:
            self.config = await self.get_default_config()
            await self.save_config()

    async def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving config: {e}")

    async def get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "version": "1.0.0",
            "chat_monitoring": {
                "log_file_path": "",
                "auto_detect": True,
                "monitoring_enabled": True,
            },
            "ocr": {
                "enabled": True,
                "tesseract_path": "",
                "confidence_threshold": 60,
                "auto_screenshot": True,
                "screenshot_hotkey": "F12",
            },
            "ui": {
                "theme": "dark",
                "window_size": [1200, 800],
                "window_position": [100, 100],
                "always_on_top": False,
            },
            "twitch": {
                "enabled": False,
                "channel_name": "",
                "bot_token": "",
                "overlay_enabled": False,
                "overlay_position": [10, 10],
            },
            "database": {"backup_enabled": True, "backup_interval_hours": 24, "max_sessions": 1000},
            "markups": {"auto_update": True, "custom_values": {}},
            "loadouts": {"active_loadout_id": None},
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    async def set(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        await self.save_config()

    def set_sync(self, key: str, value: Any):
        """Set configuration value by key synchronously (supports dot notation)"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving config: {e}")

    async def update(self, updates: dict[str, Any]):
        """Update multiple configuration values"""

        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if (
                    key in base_dict
                    and isinstance(base_dict[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(self.config, updates)
        await self.save_config()
