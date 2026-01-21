#!/usr/bin/env python3
"""Test the config tab initialization"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.ui.components.config_tab import ConfigTab
from src.services.config_manager import ConfigManager
import asyncio

async def test_config():
    print("=" * 60)
    print("TESTING CONFIG TAB INITIALIZATION")
    print("=" * 60)

    # Initialize config manager
    config = ConfigManager()
    await config.initialize()

    # Create config tab
    tab = ConfigTab()

    print(f"\n1. Config widget created")
    print(f"   Has chat_location_text: {hasattr(tab, 'chat_location_text')}")

    if hasattr(tab, 'chat_location_text'):
        chat_path = tab.chat_location_text.text().strip()
        print(f"   Chat path from config_widget: '{chat_path}'")
        print(f"   Path exists: {Path(chat_path).exists() if chat_path else False}")

    # Check config directly
    saved_path = await config.get("chat_monitoring.log_file_path", "")
    print(f"\n2. Saved chat path in config: '{saved_path}'")
    print(f"   Path exists: {Path(saved_path).exists() if saved_path else False}")

    print("\n" + "=" * 60)

asyncio.run(test_config())
