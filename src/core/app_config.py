"""Configuration and feature flags for LewtNanny"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class AppConfig:
    """Application configuration with feature flags"""

    # UI Configuration
    ui_framework: str = "pyqt6"  # Options: "pyqt6", "tkinter"
    enable_dark_theme: bool = False
    window_size: tuple = (1200, 800)

    # Feature Flags
    enable_ocr: bool = True
    enable_chat_monitoring: bool = True
    enable_weapon_selector: bool = True
    enable_overlay: bool = True

    # Development Flags
    debug_mode: bool = False
    verbose_logging: bool = False
    enable_profiling: bool = False

    # Performance Flags
    enable_caching: bool = True
    max_events_memory: int = 10000

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables"""
        config = cls()

        # Override from environment variables
        ui_framework = os.getenv("LEWTNANNY_UI_FRAMEWORK")
        if ui_framework is not None:
            config.ui_framework = ui_framework
        debug_env = os.getenv("LEWTNANNY_DEBUG")
        if debug_env is not None:
            config.debug_mode = debug_env.lower() in ("true", "1", "yes")
        enable_ocr_env = os.getenv("LEWTNANNY_ENABLE_OCR")
        if enable_ocr_env is not None:
            enable_ocr_value = enable_ocr_env.lower()
            config.enable_ocr = enable_ocr_value in ("true", "1", "yes")
        enable_chat_env = os.getenv("LEWTNANNY_ENABLE_CHAT")
        if enable_chat_env is not None:
            enable_chat_value = enable_chat_env.lower()
            config.enable_chat_monitoring = enable_chat_value in ("true", "1", "yes")
        window_size_env = os.getenv("LEWTNANNY_WINDOW_SIZE")
        if window_size_env is not None:
            try:
                width, height = map(int, window_size_env.split("x"))
                config.window_size = (width, height)
            except ValueError:
                pass  # Use default if parsing fails

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "ui_framework": self.ui_framework,
            "enable_dark_theme": self.enable_dark_theme,
            "window_size": self.window_size,
            "enable_ocr": self.enable_ocr,
            "enable_chat_monitoring": self.enable_chat_monitoring,
            "enable_weapon_selector": self.enable_weapon_selector,
            "enable_overlay": self.enable_overlay,
            "debug_mode": self.debug_mode,
            "verbose_logging": self.verbose_logging,
            "enable_profiling": self.enable_profiling,
            "enable_caching": self.enable_caching,
            "max_events_memory": self.max_events_memory,
        }


# Global configuration instance
app_config = AppConfig.from_env()
